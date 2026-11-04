import XCTest
@testable import NXNativeCore

final class PadInputTests: XCTestCase {
    func testButtonsHatAndStick() {
        var pad = PadInput()
        XCTAssertEqual(pad.actions, [])
        pad.buttons = [2]
        XCTAssertEqual(pad.actions, ["confirm"])
        pad.buttons = [1, 7, 8]
        XCTAssertEqual(pad.actions, ["back"], "R/ZR and other buttons do nothing")
        pad.buttons = []
        pad.hat = 1
        XCTAssertEqual(pad.actions, ["up", "right"])
        pad.hat = 8
        XCTAssertEqual(pad.actions, [], "past the 8 directions: centered")
        pad.hat = -1
        pad.x = 0.9
        pad.y = 0.3
        XCTAssertEqual(pad.actions, ["right"])
        pad.y = 0.8
        XCTAssertEqual(pad.actions, ["right", "down"])
    }

    func testOnlyNewPressesCount() {
        XCTAssertEqual(padPresses([], ["confirm"]), ["confirm"])
        XCTAssertEqual(padPresses(["confirm"], ["confirm"]), [])
        XCTAssertEqual(padPresses(["right"], ["right", "back"]), ["back"])
    }
}
