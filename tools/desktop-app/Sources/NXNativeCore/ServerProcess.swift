import Darwin
import Foundation

public enum ServerProcessError: Error, Equatable {
    case invalidWorkspace
    case portInUse
    case startupFailed(String)
    case readinessTimeout(String)
}

public final class ServerProcess: @unchecked Sendable {
    private enum State {
        case idle
        case starting
        case running
        case stopping
        case stopped
    }

    private let workspace: URL
    private let port: Int
    private let logURL: URL
    private let readinessTimeout: TimeInterval
    private let queue = DispatchQueue(label: "local.nxnative.dashboard.server")

    private var state = State.idle
    private var process: Process?
    private var inputPipe: Pipe?
    private var outputPipe: Pipe?
    private var logHandle: FileHandle?
    private var logData = Data()
    private var lineBuffer = Data()
    private var startContinuation: CheckedContinuation<Void, Error>?
    private var stopContinuations = [CheckedContinuation<Void, Never>]()

    public var onUnexpectedTermination: ((Int32) -> Void)?

    public init(
        workspace: URL,
        port: Int = 8767,
        logURL: URL? = nil,
        readinessTimeout: TimeInterval = 15
    ) {
        self.workspace = workspace
        self.port = port
        self.logURL = logURL ?? FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Logs/NXNative Dashboard/server.log")
        self.readinessTimeout = readinessTimeout
    }

    public func start() async throws {
        try await withCheckedThrowingContinuation { continuation in
            queue.async {
                self.beginStart(continuation: continuation)
            }
        }
    }

    public func stop() async {
        await withCheckedContinuation { continuation in
            queue.async {
                switch self.state {
                case .idle, .stopped:
                    continuation.resume()
                case .stopping:
                    self.stopContinuations.append(continuation)
                case .starting, .running:
                    self.stopContinuations.append(continuation)
                    self.beginStop()
                }
            }
        }
    }

    public func logTail(maxLines: Int = 40) -> String {
        queue.sync {
            logTailOnQueue(maxLines: maxLines)
        }
    }

    private func beginStart(continuation: CheckedContinuation<Void, Error>) {
        guard state == .idle else {
            continuation.resume(throwing: ServerProcessError.startupFailed("Le serveur a déjà été lancé."))
            return
        }

        let python = workspace.appendingPathComponent(".venv/bin/python")
        let library = workspace.appendingPathComponent("tools/library.py")
        guard FileManager.default.fileExists(atPath: python.path),
              FileManager.default.fileExists(atPath: library.path) else {
            continuation.resume(throwing: ServerProcessError.invalidWorkspace)
            return
        }

        guard !portIsInUse() else {
            continuation.resume(throwing: ServerProcessError.portInUse)
            return
        }

        do {
            try prepareLog()
        } catch {
            continuation.resume(throwing: ServerProcessError.startupFailed(error.localizedDescription))
            return
        }

        let input = Pipe()
        let output = Pipe()
        let child = Process()
        child.executableURL = python
        child.arguments = [library.path, "monitor", "--stop-on-stdin-eof"]
        child.currentDirectoryURL = workspace
        child.standardInput = input
        child.standardOutput = output
        child.standardError = output
        child.terminationHandler = { [weak self] process in
            guard let self else { return }
            self.queue.async {
                self.didTerminate(process)
            }
        }
        output.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard let self else { return }
            self.queue.async {
                self.receiveOutput(data)
            }
        }

        state = .starting
        process = child
        inputPipe = input
        outputPipe = output
        startContinuation = continuation

        do {
            try child.run()
            try? input.fileHandleForReading.close()
            try? output.fileHandleForWriting.close()
        } catch {
            output.fileHandleForReading.readabilityHandler = nil
            state = .stopped
            process = nil
            startContinuation = nil
            closeInput()
            continuation.resume(throwing: ServerProcessError.startupFailed(error.localizedDescription))
            return
        }

        queue.asyncAfter(deadline: .now() + readinessTimeout) { [weak self] in
            self?.readinessDidTimeOut()
        }
    }

    private func receiveOutput(_ data: Data) {
        guard !data.isEmpty else {
            outputPipe?.fileHandleForReading.readabilityHandler = nil
            try? outputPipe?.fileHandleForReading.close()
            return
        }

        logData.append(data)
        try? logHandle?.write(contentsOf: data)
        lineBuffer.append(data)
        let readinessLine = "Build monitor: http://127.0.0.1:\(port)"

        while let newline = lineBuffer.firstIndex(of: 0x0a) {
            let lineData = lineBuffer.prefix(upTo: newline)
            lineBuffer.removeSubrange(...newline)
            let line = String(decoding: lineData, as: UTF8.self)
                .trimmingCharacters(in: CharacterSet(charactersIn: "\r"))
            if state == .starting, line == readinessLine {
                state = .running
                let continuation = startContinuation
                startContinuation = nil
                continuation?.resume()
            }
        }
    }

    private func readinessDidTimeOut() {
        guard state == .starting else { return }
        let continuation = startContinuation
        startContinuation = nil
        continuation?.resume(throwing: ServerProcessError.readinessTimeout(logTailOnQueue()))
        beginStop()
    }

    private func didTerminate(_ child: Process) {
        guard process === child else { return }
        let previousState = state
        process = nil
        child.terminationHandler = nil
        closeInput()

        switch previousState {
        case .starting:
            state = .stopped
            let continuation = startContinuation
            startContinuation = nil
            continuation?.resume(throwing: ServerProcessError.startupFailed(logTailOnQueue()))
            resumeStopContinuations()
        case .running:
            state = .stopped
            resumeStopContinuations()
            let callback = onUnexpectedTermination
            DispatchQueue.global().async {
                callback?(child.terminationStatus)
            }
        case .stopping:
            state = .stopped
            resumeStopContinuations()
        case .idle, .stopped:
            break
        }
    }

    private func beginStop() {
        state = .stopping
        if let continuation = startContinuation {
            startContinuation = nil
            continuation.resume(throwing: ServerProcessError.startupFailed("Le serveur a été arrêté."))
        }
        closeInput()
        guard let child = process else {
            state = .stopped
            resumeStopContinuations()
            return
        }
        queue.asyncAfter(deadline: .now() + 3) { [weak self, weak child] in
            guard let self, let child, self.state == .stopping, self.process === child else { return }
            Darwin.kill(child.processIdentifier, SIGTERM)
            self.queue.asyncAfter(deadline: .now() + 2) { [weak self, weak child] in
                guard let self, let child, self.state == .stopping, self.process === child else { return }
                Darwin.kill(child.processIdentifier, SIGKILL)
            }
        }
    }

    private func closeInput() {
        try? inputPipe?.fileHandleForWriting.close()
        inputPipe = nil
    }

    private func resumeStopContinuations() {
        let continuations = stopContinuations
        stopContinuations.removeAll()
        continuations.forEach { $0.resume() }
    }

    private func portIsInUse() -> Bool {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { return false }
        defer { close(fd) }

        let flags = fcntl(fd, F_GETFL, 0)
        guard flags >= 0, fcntl(fd, F_SETFL, flags | O_NONBLOCK) >= 0 else { return false }
        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        address.sin_port = UInt16(port).bigEndian
        let result = withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                connect(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        if result == 0 { return true }
        guard errno == EINPROGRESS else { return false }

        var descriptor = pollfd(fd: fd, events: Int16(POLLOUT), revents: 0)
        guard poll(&descriptor, 1, 250) > 0 else { return false }
        var socketError: Int32 = 0
        var length = socklen_t(MemoryLayout.size(ofValue: socketError))
        guard getsockopt(fd, SOL_SOCKET, SO_ERROR, &socketError, &length) == 0 else { return false }
        return socketError == 0
    }

    private func prepareLog() throws {
        try FileManager.default.createDirectory(
            at: logURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        if !FileManager.default.fileExists(atPath: logURL.path) {
            FileManager.default.createFile(atPath: logURL.path, contents: nil)
        }
        logHandle = try FileHandle(forWritingTo: logURL)
        try logHandle?.seekToEnd()
    }

    private func logTailOnQueue(maxLines: Int = 40) -> String {
        String(decoding: logData, as: UTF8.self)
            .split(separator: "\n", omittingEmptySubsequences: false)
            .suffix(maxLines)
            .joined(separator: "\n")
    }
}
