import XCTest
@testable import NXCore

final class MacAppIconTests: XCTestCase {
    private var temporary: URL!
    private var app: URL!
    private var info: URL!
    private var icon: URL!
    private var source: URL!

    override func setUpWithError() throws {
        temporary = FileManager.default.temporaryDirectory.appendingPathComponent("nx2apple-icon-tests-" + UUID().uuidString)
        app = temporary.appendingPathComponent("Game.app")
        let resources = app.appendingPathComponent("Contents/Resources")
        try FileManager.default.createDirectory(at: resources, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: app.appendingPathComponent("Contents/MacOS"), withIntermediateDirectories: true)
        info = app.appendingPathComponent("Contents/Info.plist")
        icon = resources.appendingPathComponent("AppIcon.icns")
        source = temporary.appendingPathComponent("source.jpg")
        try Data("source".utf8).write(to: source)
        try Data("host".utf8).write(to: app.appendingPathComponent("Contents/MacOS/dmhost"))
        try writeInfo(["CFBundleName": "Game"])
    }

    override func tearDownWithError() throws { try FileManager.default.removeItem(at: temporary) }

    private func writeInfo(_ plist: [String: Any]) throws {
        try PropertyListSerialization.data(fromPropertyList: plist, format: .xml, options: 0).write(to: info)
    }

    private func readInfo() throws -> [String: Any] {
        try XCTUnwrap(PropertyListSerialization.propertyList(from: Data(contentsOf: info), options: [], format: nil) as? [String: Any])
    }

    private func render(_ output: URL, side: Int = 512) throws {
        try Data("new icon".utf8).write(to: output)
        XCTAssertEqual(side, 512)
    }

    func testGuardRequiresAChoiceAndLeavesTheGameIconAlone() throws {
        XCTAssertEqual(MacAppIcon.rejection(hasChoice: false, running: false), .noChoice)
        try Data("game icon".utf8).write(to: icon)
        var rendered = false
        XCTAssertThrowsError(try MacAppIcon.apply(app: app, source: nil, focusX: 0.5, focusY: 0.5, running: { false }, temporaryDirectory: temporary,
                                                  render: { _, _, _, _ in rendered = true; return 1024 }, runner: FakeProcessRunner())) {
            XCTAssertEqual($0 as? MacAppIcon.Failure, .noChoice)
        }
        XCTAssertFalse(rendered)
        XCTAssertEqual(try Data(contentsOf: icon), Data("game icon".utf8))
        XCTAssertNil(try readInfo()["CFBundleIconFile"])
    }

    func testGuardRefusesOnlyCropsBelow512Pixels() {
        XCTAssertEqual(MacAppIcon.rejection(hasChoice: true, cropSide: 511, running: false), .cropTooSmall)
        XCTAssertEqual(MacAppIcon.Failure.cropTooSmall.messageKey, "artwork.error.iconSmall")
        XCTAssertNil(MacAppIcon.rejection(hasChoice: true, cropSide: 512, running: false))
        XCTAssertNil(MacAppIcon.rejection(hasChoice: true, cropSide: 1024, running: false))
    }

    func testGuardRefusesARunningGame() {
        XCTAssertEqual(MacAppIcon.rejection(hasChoice: true, cropSide: 1024, running: true), .running)
        XCTAssertNil(MacAppIcon.rejection(hasChoice: true, cropSide: 1024, running: false))
    }

    func testReplacementNoticeNeedsBothAChoiceAndAGameIcon() {
        XCTAssertFalse(MacAppIcon.replacesGameIcon(hasChoice: false, existingIcon: true))
        XCTAssertFalse(MacAppIcon.replacesGameIcon(hasChoice: true, existingIcon: false))
        XCTAssertTrue(MacAppIcon.replacesGameIcon(hasChoice: true, existingIcon: true))
    }

    func testApplyWritesTheIconAndPlistThenSignsVerifiesAndRegisters() throws {
        let runner = FakeProcessRunner()
        try MacAppIcon.apply(app: app, source: source, focusX: 0.25, focusY: 0.75, running: { false }, temporaryDirectory: temporary,
                             render: { _, output, _, _ in try self.render(output); return 512 }, runner: runner)
        XCTAssertEqual(try Data(contentsOf: icon), Data("new icon".utf8))
        XCTAssertEqual(try readInfo()["CFBundleIconFile"] as? String, "AppIcon")
        XCTAssertEqual(runner.launches.map(\.executable), [
            "/usr/bin/codesign", "/usr/bin/codesign", "/usr/bin/codesign",
            "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister",
        ])
        XCTAssertEqual(runner.launches[0].arguments, ["--force", "--sign", "-", app.appendingPathComponent("Contents/MacOS/dmhost").path])
        XCTAssertEqual(runner.launches[1].arguments, ["--force", "--sign", "-", app.path])
        XCTAssertEqual(runner.launches[2].arguments, ["--verify", "--strict", app.path])
        XCTAssertEqual(runner.launches[3].arguments, ["-f", app.path])
    }

    func testFailedVerificationRestoresTheOriginalIconAndInfo() throws {
        let originalIcon = Data("game icon".utf8), originalInfo = try Data(contentsOf: info)
        try originalIcon.write(to: icon)
        let runner = FakeProcessRunner()
        runner.answer = { $0.arguments.contains("--verify") ? ProcessResult(status: 1) : ProcessResult() }
        XCTAssertThrowsError(try MacAppIcon.apply(app: app, source: source, focusX: 0.5, focusY: 0.5, running: { false }, temporaryDirectory: temporary,
                                                  render: { _, output, _, _ in try self.render(output); return 512 }, runner: runner)) {
            XCTAssertEqual($0 as? MacAppIcon.Failure, .applyFailed)
        }
        XCTAssertEqual(try Data(contentsOf: icon), originalIcon)
        XCTAssertEqual(try Data(contentsOf: info), originalInfo)
        XCTAssertNil(try readInfo()["CFBundleIconFile"])
    }

    func testFailedSigningRemovesANewIconWhenThereWasNone() throws {
        let originalInfo = try Data(contentsOf: info)
        let runner = FakeProcessRunner()
        runner.answer = { $0.arguments.contains("--force") && $0.arguments.last == self.app.path ? ProcessResult(status: 1) : ProcessResult() }
        XCTAssertThrowsError(try MacAppIcon.apply(app: app, source: source, focusX: 0.5, focusY: 0.5, running: { false }, temporaryDirectory: temporary,
                                                  render: { _, output, _, _ in try self.render(output); return 512 }, runner: runner))
        XCTAssertFalse(FileManager.default.fileExists(atPath: icon.path))
        XCTAssertEqual(try Data(contentsOf: info), originalInfo)
    }
}
