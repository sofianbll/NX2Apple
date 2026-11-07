import Foundation

package enum BuildOutput {
    /// A source scan's proposed output is not a player's choice. Older libraries have no `remembered` flag, so a different
    /// path is also kept: that is how their explicit output was recorded.
    package static func defaultDirectory(current: String, scanDefault: String, sourceFolder: String,
                                         gamesFolder: String, remembered: Bool) -> String {
        let differentFromScan = !current.isEmpty && normalized(current) != normalized(scanDefault)
        guard !remembered, !differentFromScan, !gamesFolder.isEmpty else { return current }
        let source = sourceFolder.isEmpty ? scanDefault : sourceFolder
        return contains(gamesFolder, source) ? current : gamesFolder
    }

    private static func normalized(_ path: String) -> URL {
        URL(fileURLWithPath: path).standardizedFileURL.resolvingSymlinksInPath().standardizedFileURL
    }

    private static func contains(_ folder: String, _ path: String) -> Bool {
        let parent = normalized(folder).pathComponents
        let child = normalized(path).pathComponents
        return child.count >= parent.count && Array(child.prefix(parent.count)) == parent
    }
}
