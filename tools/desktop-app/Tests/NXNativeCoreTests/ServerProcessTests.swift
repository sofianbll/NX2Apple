import XCTest
@testable import NXNativeCore

final class ServerProcessTests: XCTestCase {
    func testMissingWorkspaceFailsWithoutLaunching() async throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("NXNativeServerTests-\(UUID().uuidString)")
        let server = ServerProcess(
            workspace: root.appendingPathComponent("absent"),
            port: 43123,
            logURL: root.appendingPathComponent("server.log")
        )

        do {
            try await server.start()
            XCTFail("Le lancement devait refuser un workspace absent")
        } catch let error as ServerProcessError {
            XCTAssertEqual(error, .invalidWorkspace)
        }
    }

    func testWorkspaceWithoutPythonIsInvalid() async throws {
        try await assertInvalidWorkspace(removing: ".venv/bin/python")
    }

    func testWorkspaceWithoutLibraryIsInvalid() async throws {
        try await assertInvalidWorkspace(removing: "tools/library.py")
    }

    func testUnexpectedTerminationIsObservedWithLogTail() async throws {
        let fixture = try FakeWorkspace()
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        defer { try? fixture.cleanUp() }
        let terminated = expectation(description: "Mort inattendue observée")
        server.onUnexpectedTermination = { _ in terminated.fulfill() }
        try await server.start()

        Darwin.kill(try fixture.pid(), SIGTERM)
        await fulfillment(of: [terminated], timeout: 1)

        XCTAssertTrue(try fixture.waitForExit())
        XCTAssertTrue(server.logTail().contains("Build monitor:"))
        await server.stop()
    }

    func testExitBeforeReadinessReturnsLogTail() async throws {
        let fixture = try FakeWorkspace(mode: .failBeforeReady)
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        defer { try? fixture.cleanUp() }

        do {
            try await server.start()
            XCTFail("La sortie avant disponibilité devait faire échouer le lancement")
        } catch let error as ServerProcessError {
            guard case .startupFailed(let tail) = error else {
                return XCTFail("Erreur inattendue : \(error)")
            }
            XCTAssertTrue(tail.contains("échec volontaire"), tail)
        }

        XCTAssertTrue(try fixture.waitForExit())
        await server.stop()
        let log = try String(contentsOf: fixture.logURL, encoding: .utf8)
        XCTAssertTrue(log.contains("échec volontaire"))
    }

    func testOccupiedPortIsAConflictWithoutLaunchingOrAdopting() async throws {
        let fixture = try FakeWorkspace()
        let occupant = try PortOccupant(port: fixture.port)
        defer { occupant.close(); try? fixture.cleanUp() }
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )

        do {
            try await server.start()
            XCTFail("Le lancement devait signaler le conflit de port")
        } catch let error as ServerProcessError {
            XCTAssertEqual(error, .portInUse)
        }

        XCTAssertFalse(fixture.hasLaunched)
        XCTAssertTrue(occupant.canConnect(port: fixture.port))
        await server.stop()
    }

    func testReadinessTimesOutAfterFifteenSecondsAndStopsChild() async throws {
        let fixture = try FakeWorkspace(mode: .hangBeforeReady)
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        defer { try? fixture.cleanUp() }

        let started = Date()
        do {
            try await server.start()
            XCTFail("Un serveur muet devait dépasser le délai de disponibilité")
        } catch let error as ServerProcessError {
            guard case .readinessTimeout = error else {
                return XCTFail("Erreur inattendue : \(error)")
            }
        }
        XCTAssertGreaterThanOrEqual(Date().timeIntervalSince(started), 14.5)
        XCTAssertLessThan(Date().timeIntervalSince(started), 19)

        await server.stop()
        XCTAssertLessThan(Date().timeIntervalSince(started), 19)
        XCTAssertTrue(try fixture.waitForExit())
        XCTAssertTrue(try fixture.signalNames().contains("SIGTERM"))
    }

    func testReadinessTimeoutStopsOldProcessBeforeImmediateRetry() async throws {
        let fixture = try FakeWorkspace(mode: .bindAndHangBeforeReady)
        let first = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL,
            readinessTimeout: 0.1
        )
        defer { try? fixture.cleanUp() }

        do {
            try await first.start()
            XCTFail("Le premier serveur ne devait pas annoncer sa disponibilité")
        } catch let error as ServerProcessError {
            guard case .readinessTimeout = error else {
                return XCTFail("Erreur inattendue : \(error)")
            }
        }

        let oldPID = try fixture.pid()
        XCTAssertFalse(try fixture.isAlive(), "L'ancien PID doit être arrêté avant de permettre le retry")

        try fixture.switchToReady()
        let second = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        try await second.start()
        XCTAssertNotEqual(try fixture.pid(), oldPID)
        XCTAssertTrue(try fixture.isAlive())
        await second.stop()
    }

    func testServerIgnoringEOFAndSIGTERMIsKilledWithoutTouchingWitness() async throws {
        let fixture = try FakeWorkspace(mode: .ignoreEOFAndSIGTERM)
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        let witness = Process()
        witness.executableURL = URL(fileURLWithPath: "/bin/sleep")
        witness.arguments = ["30"]
        let witnessExited = DispatchSemaphore(value: 0)
        witness.terminationHandler = { _ in witnessExited.signal() }
        try witness.run()
        defer {
            stopWitness(witness, exited: witnessExited)
            try? fixture.cleanUp()
        }
        try await server.start()

        let started = Date()
        let stopTask = Task { await server.stop() }
        let exited = try fixture.waitForExit(timeout: 6)
        if !exited { try fixture.forceStop() }
        await stopTask.value

        XCTAssertTrue(exited, "SIGKILL devait terminer le seul serveur possédé")
        XCTAssertLessThan(Date().timeIntervalSince(started), 6)
        XCTAssertTrue(try fixture.signalNames().contains("SIGTERM"))
        XCTAssertTrue(witness.isRunning)
        XCTAssertEqual(Darwin.kill(witness.processIdentifier, 0), 0)
    }

    func testServerIgnoringEOFFallsBackToSIGTERM() async throws {
        let fixture = try FakeWorkspace(mode: .ignoreEOF)
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        defer { try? fixture.cleanUp() }
        try await server.start()

        let started = Date()
        let stopTask = Task { await server.stop() }
        let signaled = try fixture.waitForSignal(timeout: 4)
        if !signaled { try fixture.forceStop() }
        await stopTask.value

        XCTAssertTrue(signaled, "SIGTERM devait suivre l'absence d'arrêt sur EOF")
        XCTAssertLessThan(Date().timeIntervalSince(started), 4)
        XCTAssertTrue(try fixture.signalNames().contains("SIGTERM"))
        XCTAssertTrue(try fixture.waitForExit())
    }

    func testReadyServerStopsOnStdinEOF() async throws {
        let fixture = try FakeWorkspace()
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        addTeardownBlock { try? fixture.cleanUp() }
        addTeardownBlock { await server.stop() }

        try await server.start()
        XCTAssertTrue(try fixture.isAlive())
        XCTAssertEqual(try fixture.arguments(), ["monitor", "--stop-on-stdin-eof"])
        XCTAssertEqual(try fixture.workingDirectory(), try fixture.canonicalWorkspacePath())

        let started = Date()
        await server.stop()

        XCTAssertLessThan(Date().timeIntervalSince(started), 3)
        XCTAssertTrue(try fixture.waitForExit())
        XCTAssertNil(try? fixture.signalNames())
        let log = try String(contentsOf: fixture.logURL, encoding: .utf8)
        XCTAssertTrue(log.contains("Build monitor: http://127.0.0.1:\(fixture.port)"))
    }

    private func stopWitness(_ witness: Process, exited: DispatchSemaphore) {
        if witness.isRunning { witness.terminate() }
        if exited.wait(timeout: .now() + 2) == .timedOut {
            Darwin.kill(witness.processIdentifier, SIGKILL)
            _ = exited.wait(timeout: .now() + 2)
        }
    }

    private func assertInvalidWorkspace(removing path: String) async throws {
        let fixture = try FakeWorkspace()
        try FileManager.default.removeItem(at: fixture.workspace.appendingPathComponent(path))
        let server = ServerProcess(
            workspace: fixture.workspace,
            port: fixture.port,
            logURL: fixture.logURL
        )
        defer { try? fixture.cleanUp() }

        do {
            try await server.start()
            XCTFail("Le workspace incomplet devait être refusé")
        } catch let error as ServerProcessError {
            XCTAssertEqual(error, .invalidWorkspace)
        }
        XCTAssertFalse(fixture.hasLaunched)
        await server.stop()
    }
}
