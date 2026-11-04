import Darwin
import Foundation

final class FakeWorkspace: @unchecked Sendable {
    enum Mode {
        case eof
        case failBeforeReady
        case hangBeforeReady
        case ignoreEOF
        case ignoreEOFAndSIGTERM
    }

    let workspace: URL
    let logURL: URL
    let port: Int

    private let root: URL
    private let records: URL

    init(mode: Mode = .eof) throws {
        root = FileManager.default.temporaryDirectory
            .appendingPathComponent("NXNativeFakeServer-\(UUID().uuidString)")
        workspace = root.appendingPathComponent("workspace")
        records = root.appendingPathComponent("records")
        logURL = root.appendingPathComponent("server.log")
        port = try Self.unusedPort()

        try FileManager.default.createDirectory(
            at: workspace.appendingPathComponent(".venv/bin"),
            withIntermediateDirectories: true
        )
        try FileManager.default.createDirectory(
            at: workspace.appendingPathComponent("tools"),
            withIntermediateDirectories: true
        )
        try FileManager.default.createDirectory(at: records, withIntermediateDirectories: true)
        try FileManager.default.createSymbolicLink(
            at: workspace.appendingPathComponent(".venv/bin/python"),
            withDestinationURL: URL(fileURLWithPath: "/Applications/Xcode.app/Contents/Developer/usr/bin/python3")
        )
        try Self.script(records: records, port: port, mode: mode).write(
            to: workspace.appendingPathComponent("tools/library.py"),
            atomically: true,
            encoding: .utf8
        )
    }

    var hasLaunched: Bool {
        FileManager.default.fileExists(atPath: records.appendingPathComponent("pid").path)
    }

    func pid() throws -> pid_t {
        let value = try String(contentsOf: records.appendingPathComponent("pid"), encoding: .utf8)
        guard let pid = Int32(value) else { throw TestError.invalidPID }
        return pid
    }

    func isAlive() throws -> Bool {
        Darwin.kill(try pid(), 0) == 0
    }

    func waitForExit(timeout: TimeInterval = 1) throws -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if try !isAlive() { return true }
            Thread.sleep(forTimeInterval: 0.02)
        }
        return try !isAlive()
    }

    func signalNames() throws -> String {
        try String(contentsOf: records.appendingPathComponent("signals"), encoding: .utf8)
    }

    func waitForSignal(timeout: TimeInterval) throws -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if let signals = try? signalNames(), !signals.isEmpty { return true }
            Thread.sleep(forTimeInterval: 0.02)
        }
        return false
    }

    func forceStop() throws {
        guard hasLaunched else { return }
        let ownedPID = try pid()
        if Darwin.kill(ownedPID, 0) == 0 {
            Darwin.kill(ownedPID, SIGKILL)
        }
        _ = try waitForExit()
    }

    func arguments() throws -> [String] {
        try String(contentsOf: records.appendingPathComponent("arguments"), encoding: .utf8)
            .split(separator: "\n").map(String.init)
    }

    func workingDirectory() throws -> String {
        try String(contentsOf: records.appendingPathComponent("cwd"), encoding: .utf8)
    }

    func canonicalWorkspacePath() throws -> String {
        guard let path = realpath(workspace.path, nil) else { throw TestError.pathFailed }
        defer { free(path) }
        return String(cString: path)
    }

    func cleanUp() throws {
        try? forceStop()
        try FileManager.default.removeItem(at: root)
    }

    private static func script(records: URL, port: Int, mode: Mode) -> String {
        let exitsOnSIGTERM = mode != .ignoreEOFAndSIGTERM ? "os._exit(0)" : ""
        let behavior: String
        switch mode {
        case .eof:
            behavior = """
            def watch_stdin():
                sys.stdin.buffer.read()
                os._exit(0)

            threading.Thread(target=watch_stdin, daemon=True).start()
            \(readyAndWait(port: port))
            """
        case .failBeforeReady:
            behavior = """
            sys.stderr.write("échec volontaire\\n")
            sys.stderr.flush()
            sys.exit(7)
            """
        case .hangBeforeReady:
            behavior = "while True:\n    time.sleep(1)"
        case .ignoreEOF, .ignoreEOFAndSIGTERM:
            behavior = readyAndWait(port: port)
        }

        return """
        import os
        import signal
        import socket
        import sys
        import threading
        import time

        records = \(pythonString(records.path))
        with open(records + "/pid", "w") as file:
            file.write(str(os.getpid()))
        with open(records + "/arguments", "w") as file:
            file.write("\\n".join(sys.argv[1:]))
        with open(records + "/cwd", "w") as file:
            file.write(os.getcwd())

        def on_term(signum, frame):
            with open(records + "/signals", "a") as file:
                file.write("SIGTERM\\n")
            \(exitsOnSIGTERM)

        signal.signal(signal.SIGTERM, on_term)
        \(behavior)
        """
    }

    private static func readyAndWait(port: Int) -> String {
        """
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", \(port)))
        listener.listen()
        print("Build monitor: http://127.0.0.1:\(port)", flush=True)
        while True:
            time.sleep(1)
        """
    }

    private static func unusedPort() throws -> Int {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { throw TestError.socketFailed }
        defer { Darwin.close(fd) }
        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        address.sin_port = 0
        let bindResult = withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        guard bindResult == 0 else { throw TestError.socketFailed }
        var length = socklen_t(MemoryLayout<sockaddr_in>.size)
        let nameResult = withUnsafeMutablePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                getsockname(fd, $0, &length)
            }
        }
        guard nameResult == 0 else { throw TestError.socketFailed }
        return Int(UInt16(bigEndian: address.sin_port))
    }

    private static func pythonString(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "\\'") + "'"
    }
}

final class PortOccupant {
    private var fd: Int32?

    init(port: Int) throws {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { throw TestError.socketFailed }
        var yes: Int32 = 1
        setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, socklen_t(MemoryLayout.size(ofValue: yes)))
        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        address.sin_port = UInt16(port).bigEndian
        let bound = withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        guard bound == 0, listen(fd, 1) == 0 else {
            Darwin.close(fd)
            throw TestError.socketFailed
        }
        self.fd = fd
    }

    func canConnect(port: Int) -> Bool {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { return false }
        defer { Darwin.close(fd) }
        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        address.sin_port = UInt16(port).bigEndian
        return withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                connect(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        } == 0
    }

    func close() {
        if let fd { Darwin.close(fd) }
        fd = nil
    }

    deinit { close() }
}

enum TestError: Error {
    case invalidPID
    case pathFailed
    case socketFailed
}
