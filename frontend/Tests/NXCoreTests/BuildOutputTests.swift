import XCTest
@testable import NXCore

final class BuildOutputTests: XCTestCase {
    func testSourceInsideGamesFolderKeepsScanDefault() {
        let output = "/Games/Sources/Hades/Packages"
        XCTAssertEqual(BuildOutput.defaultDirectory(current: output, scanDefault: output,
                                                    sourceFolder: "/Games/Sources/Hades",
                                                    gamesFolder: "/Games", remembered: false), output)
    }

    func testSourceOutsideGamesFolderUsesGamesFolder() {
        let output = "/ROMs/Switch/Hades/Packages"
        XCTAssertEqual(BuildOutput.defaultDirectory(current: output, scanDefault: output,
                                                    sourceFolder: "/ROMs/Switch/Hades",
                                                    gamesFolder: "/Games", remembered: false), "/Games")
    }

    func testUnsetGamesFolderKeepsScanDefault() {
        let output = "/ROMs/Switch/Hades"
        XCTAssertEqual(BuildOutput.defaultDirectory(current: output, scanDefault: output,
                                                    sourceFolder: output, gamesFolder: "", remembered: false), output)
    }

    func testRememberedOutputAlwaysWins() {
        let output = "/ROMs/Switch/Hades"
        XCTAssertEqual(BuildOutput.defaultDirectory(current: output, scanDefault: output,
                                                    sourceFolder: output, gamesFolder: "/Games", remembered: true), output)
        let olderChoice = "/Elsewhere/Built games"
        XCTAssertEqual(BuildOutput.defaultDirectory(current: olderChoice, scanDefault: output,
                                                    sourceFolder: output, gamesFolder: "/Games", remembered: false), olderChoice)
    }

    func testRelativePathComponentsAreNormalized() {
        XCTAssertEqual(BuildOutput.defaultDirectory(current: "/ROMs/Switch/Hades/../Hades",
                                                    scanDefault: "/ROMs/Switch/Hades",
                                                    sourceFolder: "/ROMs/Switch/./Hades",
                                                    gamesFolder: "/Games", remembered: false), "/Games")
    }

    func testSymlinkedGamesFolderContainsItsRealSourceFolder() throws {
        let temporary = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: temporary) }
        let games = temporary.appendingPathComponent("Games")
        let source = games.appendingPathComponent("Sources/Hades")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        let alias = temporary.appendingPathComponent("Alias")
        try FileManager.default.createSymbolicLink(at: alias, withDestinationURL: games)

        XCTAssertEqual(BuildOutput.defaultDirectory(current: source.path, scanDefault: source.path,
                                                    sourceFolder: source.path, gamesFolder: alias.path,
                                                    remembered: false), source.path)
    }
}
