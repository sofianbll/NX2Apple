import Foundation

/// Applies a player's icon to an already packed Mac game. The image is rendered before the bundle is touched, then the two files
/// that change are backed up so a failed write, signature, verification or Launch Services refresh can be rolled back.
package enum MacAppIcon {
    package enum Failure: Error, Equatable {
        case noChoice, cropTooSmall, running, unreadable, sourceUnavailable, applyFailed, restoreFailed

        package var messageKey: String {
            switch self {
            case .noChoice: return "artwork.error.iconChoice"
            case .cropTooSmall: return "artwork.error.iconSmall"
            case .running: return "artwork.error.iconRunning"
            case .unreadable, .sourceUnavailable: return "artwork.error.iconSource"
            case .applyFailed: return "artwork.error.iconApply"
            case .restoreFailed: return "artwork.error.iconRestore"
            }
        }
    }

    /// The guards that do not need a bundle or an image decoder. A nil crop side means it has not been measured yet.
    package static func rejection(hasChoice: Bool, cropSide: Int? = nil, running: Bool) -> Failure? {
        guard hasChoice else { return .noChoice }
        if let cropSide, cropSide < 512 { return .cropTooSmall }
        return running ? .running : nil
    }

    /// The panel warns only when a chosen icon would replace one the game already carries.
    package static func replacesGameIcon(hasChoice: Bool, existingIcon: Bool) -> Bool { hasChoice && existingIcon }

    /// `render` writes a complete ICNS to the supplied temporary URL and returns the source crop's side in pixels.
    package static func apply(app: URL, source: URL?, focusX: Double, focusY: Double, running: () -> Bool,
                              temporaryDirectory: URL = FileManager.default.temporaryDirectory,
                              render: (URL, URL, Double, Double) throws -> Int, runner: ProcessRunner) throws {
        if let rejection = rejection(hasChoice: source != nil, running: running()) { throw rejection }
        let source = source!
        let fm = FileManager.default
        let work = temporaryDirectory.appendingPathComponent("nx2apple-icon-" + UUID().uuidString, isDirectory: true)
        let contents = app.appendingPathComponent("Contents", isDirectory: true)
        let resources = contents.appendingPathComponent("Resources", isDirectory: true)
        let info = contents.appendingPathComponent("Info.plist")
        let icon = resources.appendingPathComponent("AppIcon.icns")
        let backup = work.appendingPathComponent("backup", isDirectory: true)
        let backupInfo = backup.appendingPathComponent("Info.plist")
        let backupIcon = backup.appendingPathComponent("AppIcon.icns")
        let rendered = work.appendingPathComponent("AppIcon.icns")
        let hadIcon = fm.fileExists(atPath: icon.path)
        var backedUp = false
        do {
            try fm.createDirectory(at: backup, withIntermediateDirectories: true)
            let cropSide = try render(source, rendered, focusX, focusY)
            if let rejection = rejection(hasChoice: true, cropSide: cropSide, running: running()) { throw rejection }
            guard fm.fileExists(atPath: rendered.path) else { throw Failure.unreadable }
            try fm.copyItem(at: info, to: backupInfo)
            if hadIcon { try fm.copyItem(at: icon, to: backupIcon) }
            backedUp = true

            try replace(at: icon, with: rendered)
            var plist = try PropertyListSerialization.propertyList(from: Data(contentsOf: info), options: [], format: nil) as? [String: Any]
            guard plist != nil else { throw Failure.unreadable }
            plist!["CFBundleIconFile"] = "AppIcon"
            let updated = work.appendingPathComponent("Updated-Info.plist")
            try PropertyListSerialization.data(fromPropertyList: plist!, format: .xml, options: 0).write(to: updated)
            try replace(at: info, with: updated)
            try sign(app: app, runner: runner)
            guard runner.runOK("/usr/bin/codesign", ["--verify", "--strict", app.path]) else { throw Failure.applyFailed }
            try fm.setAttributes([.modificationDate: Date()], ofItemAtPath: app.path)
            let lsregister = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
            guard runner.runOK(lsregister, ["-f", app.path]) else { throw Failure.applyFailed }
            try? fm.removeItem(at: work)
        } catch {
            guard backedUp else {
                try? fm.removeItem(at: work)
                if let failure = error as? Failure, failure != .applyFailed { throw failure }
                throw Failure.applyFailed
            }
            do {
                if hadIcon { try replace(at: icon, with: backupIcon) }
                else if fm.fileExists(atPath: icon.path) { try fm.removeItem(at: icon) }
                try replace(at: info, with: backupInfo)
                // A failed bundle signing may already have replaced CodeResources. Make the restored bytes usable when codesign works.
                try? sign(app: app, runner: runner)
                try? fm.removeItem(at: work)
            } catch {
                try? fm.removeItem(at: work)
                throw Failure.restoreFailed
            }
            throw Failure.applyFailed
        }
    }

    private static func sign(app: URL, runner: ProcessRunner) throws {
        let host = app.appendingPathComponent("Contents/MacOS/dmhost")
        for target in [host, app] {
            guard runner.runOK("/usr/bin/codesign", ["--force", "--sign", "-", target.path]) else { throw Failure.applyFailed }
        }
    }

    private static func replace(at target: URL, with source: URL) throws {
        let fm = FileManager.default
        if fm.fileExists(atPath: target.path) {
            _ = try fm.replaceItemAt(target, withItemAt: source, options: .usingNewMetadataOnly)
        } else {
            try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
            try fm.moveItem(at: source, to: target)
        }
    }
}
