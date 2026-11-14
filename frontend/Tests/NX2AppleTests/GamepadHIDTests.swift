import XCTest
@testable import NX2Apple

final class GamepadHIDTests: XCTestCase {
    func testAdmissionMirrorsTheEngine() {
        XCTAssertEqual(LauncherGamepad.hidAdmission(vendorID: 0, synthetic: true, gcHint: false, gcListed: false), .skip)
        for vendor in [0x045E, 0x054C, 0x057E] {
            XCTAssertEqual(LauncherGamepad.hidAdmission(vendorID: vendor, synthetic: false, gcHint: false, gcListed: false), .skip)
        }
        XCTAssertEqual(LauncherGamepad.hidAdmission(vendorID: 0, synthetic: false, gcHint: true, gcListed: true), .skip)
        XCTAssertEqual(LauncherGamepad.hidAdmission(vendorID: 0, synthetic: false, gcHint: true, gcListed: false), .wait)
        XCTAssertEqual(LauncherGamepad.hidAdmission(vendorID: 0x2DC8, synthetic: false, gcHint: false, gcListed: false), .use)
    }

    func testReport3FAndDefaultButtonNumbering() {
        XCTAssertEqual(LauncherGamepad.hidButtonMap(report3F: true), [2, 1, 4, 3, 11, 12, 5, 6, 7, 8, 10, 9])
        XCTAssertEqual(LauncherGamepad.hidButtonMap(report3F: false), [2, 1, 5, 4, 14, 15, 7, 8, 9, 10, 12, 11])

        var pro = LauncherGamepad.HIDState(report3F: true, hasZ: true)
        pro.update(page: 9, usage: 4, value: 1, min: 0, max: 1)
        pro.update(page: 9, usage: 10, value: 1, min: 0, max: 1)
        XCTAssertTrue(pro.input.x)
        XCTAssertFalse(pro.input.y)
        XCTAssertTrue(pro.input.plus)
        XCTAssertFalse(pro.input.select)

        var eightBitDo = LauncherGamepad.HIDState(report3F: false, hasZ: true)
        eightBitDo.update(page: 9, usage: 4, value: 1, min: 0, max: 1)
        eightBitDo.update(page: 9, usage: 11, value: 1, min: 0, max: 1)
        XCTAssertTrue(eightBitDo.input.y)
        XCTAssertFalse(eightBitDo.input.x)
        XCTAssertTrue(eightBitDo.input.select)
        XCTAssertFalse(eightBitDo.input.plus)
    }

    func testPlayerLightsUseTheProControllerOutputReport() {
        let neutral: [UInt8] = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]
        for (player, mask) in [(1, UInt8(0x1)), (2, 0x3), (3, 0x7), (4, 0xF)] {
            let report = LauncherGamepad.hidPlayerLights(player: player)
            XCTAssertEqual(report.count, 49)
            XCTAssertEqual(report[0], 0x01)
            XCTAssertEqual(Array(report[2..<10]), neutral)
            XCTAssertEqual(report[10], 0x30)
            XCTAssertEqual(report[11], mask)
            XCTAssertTrue(report[12...].allSatisfy { $0 == 0 })
        }
    }

    func testHIDSnapshotIsAFullSizePadWithoutBatteryAndRequiresWorkingLightsForIdentify() {
        let pro = LauncherGamepad.hidSnapshot(id: "hid-1", name: "Lic Pro Controller", report3F: true, player: 2, lightsWork: true).controller
        XCTAssertEqual(pro.name, "Lic Pro Controller")
        XCTAssertEqual(pro.kind, .fullSize)
        XCTAssertEqual(pro.player, 2)
        XCTAssertNil(pro.battery)
        XCTAssertTrue(pro.canIdentify)
        XCTAssertFalse(LauncherGamepad.hidSnapshot(id: "hid-1", name: "Lic Pro Controller", report3F: true, player: 2, lightsWork: false).canIdentify)
        let generic = LauncherGamepad.hidSnapshot(id: "hid-2", name: "Generic", report3F: false, player: nil, lightsWork: false).controller
        XCTAssertEqual(generic.kind, .gamepad)
        XCTAssertNil(generic.battery)
        XCTAssertFalse(generic.canIdentify)
    }

    func testHatBecomesAllEightDPadDirectionsAndCentersOutsideItsRange() {
        let expected: [(Float, Float)] = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        for (hat, want) in expected.enumerated() {
            var state = LauncherGamepad.HIDState(report3F: true, hasZ: true)
            state.update(page: 1, usage: 0x39, value: hat + 1, min: 1, max: 8)
            XCTAssertEqual(state.input.dpadX, want.0)
            XCTAssertEqual(state.input.dpadY, want.1)
        }
        XCTAssertEqual(LauncherGamepad.hidHat(0, min: 1, max: 8), -1)
        XCTAssertEqual(LauncherGamepad.hidHat(15, min: 0, max: 15), -1)
        XCTAssertEqual(LauncherGamepad.hidDpad(-1).x, 0)
        XCTAssertEqual(LauncherGamepad.hidDpad(-1).y, 0)
    }

    /// Each view makes its own LauncherGamepad. One HID manager each read every report once per gamepad on the main thread.
    func testEveryGamepadSharesOneHIDManager() {
        let first = LauncherGamepad(), second = LauncherGamepad()
        XCTAssertNotNil(first.hid)
        XCTAssertTrue(first.hid === second.hid)
        XCTAssertNil(LauncherGamepad(observeSystem: false).hid)
    }

    func testAxisNormalizationDeadZoneAndRightStickSelection() {
        XCTAssertEqual(LauncherGamepad.normalizeHIDAxis(50, min: 0, max: 100), 0)
        XCTAssertEqual(LauncherGamepad.normalizeHIDAxis(100, min: 0, max: 100), 1)
        XCTAssertEqual(LauncherGamepad.normalizeHIDAxis(1, min: 1, max: 1), 0)
        XCTAssertEqual(LauncherGamepad.hidStick(x: 0.1, y: 0).x, 0)
        XCTAssertEqual(LauncherGamepad.hidStick(x: 1, y: 0).x, 1)
        XCTAssertEqual(LauncherGamepad.hidStick(x: 0.5, y: 0).x, (0.5 - 0.12) / 0.88, accuracy: 0.0001)

        var state = LauncherGamepad.HIDState(report3F: true, hasZ: true)
        state.update(page: 1, usage: 0x30, value: 100, min: 0, max: 100)
        state.update(page: 1, usage: 0x31, value: 0, min: 0, max: 100)
        state.update(page: 1, usage: 0x32, value: 0, min: 0, max: 100)
        state.update(page: 1, usage: 0x35, value: 100, min: 0, max: 100)
        XCTAssertEqual(state.input.leftStickX, 1)
        XCTAssertEqual(state.input.leftStickY, 1)
        XCTAssertEqual(state.input.rightStickX, -1)
        XCTAssertEqual(state.input.rightStickY, -1)

        state = LauncherGamepad.HIDState(report3F: false, hasZ: false)
        state.update(page: 1, usage: 0x33, value: 100, min: 0, max: 100)
        state.update(page: 1, usage: 0x34, value: 0, min: 0, max: 100)
        XCTAssertEqual(state.input.rightStickX, 1)
        XCTAssertEqual(state.input.rightStickY, 1)
    }
}
