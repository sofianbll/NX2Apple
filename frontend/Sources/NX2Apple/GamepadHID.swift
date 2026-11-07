import Foundation
import GameController
import IOKit.hid
import os

extension LauncherGamepad {
    enum HIDAdmission { case skip, wait, use }

    /// The engine's ownership rule: native Xbox, PlayStation and Nintendo pads stay with GameController. Another pad it
    /// claims gets two seconds to appear in its controller list before the launcher reads the HID device instead.
    static func hidAdmission(vendorID: Int, synthetic: Bool, gcHint: Bool, gcListed: Bool) -> HIDAdmission {
        if synthetic || [0x045E, 0x054C, 0x057E].contains(vendorID) || (gcHint && gcListed) { return .skip }
        return gcHint ? .wait : .use
    }

    static func hidButtonMap(report3F: Bool) -> [Int] {
        // A, B, X, Y, LS, RS, L, R, ZL, ZR, PLUS, MINUS. The default is 8BitDo's numbering.
        report3F ? [2, 1, 4, 3, 11, 12, 5, 6, 7, 8, 10, 9] : [2, 1, 5, 4, 14, 15, 7, 8, 9, 10, 12, 11]
    }

    /// Pro Controller subcommand 0x30 after neutral rumble data, as nxnative's pad_hid_lights.
    static func hidPlayerLights(player: Int) -> [UInt8] {
        let neutral: [UInt8] = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]
        let lights: [UInt8] = [0x1, 0x3, 0x7, 0xF, 0x9, 0x5, 0xD, 0x6]
        var report = [UInt8](repeating: 0, count: 49)
        report[0] = 0x01
        report.replaceSubrange(2..<10, with: neutral)
        report[10] = 0x30
        report[11] = lights[(player - 1) & 7]
        return report
    }

    static func hidSnapshot(id: String, name: String, report3F: Bool, player: Int?, lightsWork: Bool) -> ConsolePadSnapshot {
        ConsolePadSnapshot(id: id, name: name, category: report3F ? "Nintendo Switch Pro Controller" : nil,
                           playerIndex: player, battery: nil, charging: false, canIdentify: report3F && lightsWork)
    }

    static func normalizeHIDAxis(_ value: Int, min: Int, max: Int) -> Float {
        max > min ? Float(2.0 * Double(value - min) / Double(max - min) - 1) : 0
    }

    static func hidHat(_ value: Int, min: Int, max: Int) -> Int {
        value >= min && value <= max && value - min < 8 ? value - min : -1
    }

    static func hidDpad(_ hat: Int) -> (x: Float, y: Float) {
        let directions: [(Float, Float)] = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        guard directions.indices.contains(hat) else { return (0, 0) }
        return directions[hat]
    }

    /// The engine's round dead zone, rescaled so deflection starts at zero at its edge. HID's Y grows down, the launcher's up.
    static func hidStick(x: Float, y: Float) -> (x: Float, y: Float) {
        let radius = sqrt(x * x + y * y), dead: Float = 0.12
        guard radius > dead else { return (0, 0) }
        let scale = (radius - dead) / (1 - dead) / radius
        return (max(-1, min(1, x * scale)), max(-1, min(1, y * scale)))
    }

    struct HIDState {
        var buttons: UInt32 = 0
        var hat = -1
        var axes = [Float](repeating: 0, count: 6)   // X, Y, Z, Rx, Ry, Rz
        let report3F: Bool, hasZ: Bool

        init(report3F: Bool, hasZ: Bool) {
            self.report3F = report3F
            self.hasZ = hasZ
        }

        @discardableResult
        mutating func update(page: UInt32, usage: UInt32, value: Int, min: Int, max: Int) -> Bool {
            if page == UInt32(kHIDPage_Button), (1...32).contains(usage) {
                let bit = UInt32(1) << (usage - 1)
                buttons = value != 0 ? buttons | bit : buttons & ~bit
            } else if page == UInt32(kHIDPage_GenericDesktop), usage == UInt32(kHIDUsage_GD_Hatswitch) {
                hat = LauncherGamepad.hidHat(value, min: min, max: max)
            } else if page == UInt32(kHIDPage_GenericDesktop), (0x30...0x35).contains(usage) {
                axes[Int(usage - 0x30)] = LauncherGamepad.normalizeHIDAxis(value, min: min, max: max)
            } else {
                return false
            }
            return true
        }

        var input: RawPadInput {
            let map = LauncherGamepad.hidButtonMap(report3F: report3F)
            func button(_ index: Int) -> Bool { buttons & (UInt32(1) << (map[index] - 1)) != 0 }
            let dpad = LauncherGamepad.hidDpad(hat)
            let left = LauncherGamepad.hidStick(x: axes[0], y: -axes[1])
            let right = LauncherGamepad.hidStick(x: axes[hasZ ? 2 : 3], y: -axes[hasZ ? 5 : 4])
            return RawPadInput(
                dpadX: dpad.x, dpadY: dpad.y,
                leftStickX: left.x, leftStickY: left.y,
                rightStickX: right.x, rightStickY: right.y,
                a: button(0), b: button(1), x: button(2), y: button(3),
                l: button(6), r: button(7), plus: button(10), select: button(11)
            )
        }
    }
}

final class LauncherHIDDevice {
    let device: IOHIDDevice, id: String, name: String, vendorID: Int, gcHint: Bool
    var state: LauncherGamepad.HIDState
    var waiting: DispatchWorkItem?
    var active = false
    var player: Int?
    var lightsWork = false
    let onInput: (String, LauncherGamepad.RawPadInput) -> Void

    init(device: IOHIDDevice, id: String, name: String, vendorID: Int, gcHint: Bool,
         state: LauncherGamepad.HIDState, onInput: @escaping (String, LauncherGamepad.RawPadInput) -> Void) {
        self.device = device
        self.id = id
        self.name = name
        self.vendorID = vendorID
        self.gcHint = gcHint
        self.state = state
        self.onInput = onInput
    }

    func read(_ value: IOHIDValue) {
        let element = IOHIDValueGetElement(value)
        if state.update(page: IOHIDElementGetUsagePage(element), usage: IOHIDElementGetUsage(element),
                        value: IOHIDValueGetIntegerValue(value), min: IOHIDElementGetLogicalMin(element),
                        max: IOHIDElementGetLogicalMax(element)) {
            onInput(id, state.input)
        }
    }

    var consoleDevice: ConsolePadDevice {
        ConsolePadDevice(id: id, snapshot: {
            LauncherGamepad.hidSnapshot(id: self.id, name: self.name, report3F: self.state.report3F,
                                        player: self.player, lightsWork: self.lightsWork)
        }, battery: nil,
        setPlayer: { self.player = $0 },
        showPlayer: { self.player = $0; self.writeLights($0) },
        identify: { _ in await self.identify() })
    }

    @discardableResult
    private func writeLights(_ player: Int) -> Bool {
        guard active, state.report3F, (1...4).contains(player) else { return false }
        let report = LauncherGamepad.hidPlayerLights(player: player)
        let result: IOReturn = report.withUnsafeBytes {
            guard let bytes = $0.bindMemory(to: UInt8.self).baseAddress else { return kIOReturnError }
            return IOHIDDeviceSetReport(device, kIOHIDReportTypeOutput, 0x01, bytes, CFIndex(report.count))
        }
        lightsWork = result == kIOReturnSuccess
        if !lightsWork { LauncherHIDManager.log.error("Cannot set HID gamepad player lights \(self.name, privacy: .public) (\(result))") }
        return lightsWork
    }

    private func identify() async {
        guard lightsWork else { return }
        for step in 0..<8 {
            guard !Task.isCancelled else { break }
            writeLights(step % 4 + 1)
            try? await Task.sleep(nanoseconds: 140_000_000)
        }
        if let player { writeLights(player) }
    }
}

/// Raw HID pads enter LauncherGamepad's existing RawPadInput pipeline, on the same run loop as GameController.
final class LauncherHIDManager {
    private var manager: IOHIDManager?
    private var devices: [ObjectIdentifier: LauncherHIDDevice] = [:]
    private var gcNames = Set(GCController.controllers().compactMap(\.vendorName))
    private var nextID = 0
    private let onInput: (String, LauncherGamepad.RawPadInput) -> Void
    private let onRemove: (String) -> Void
    private let onChange: () -> Void
    static let log = Logger(subsystem: "NX2Apple", category: "console.controllers")

    var hasPads: Bool { devices.values.contains(where: { $0.active }) }
    var consolePadDevices: [ConsolePadDevice] {
        devices.values.filter(\.active).sorted { $0.id < $1.id }.map(\.consoleDevice)
    }

    init(onInput: @escaping (String, LauncherGamepad.RawPadInput) -> Void,
         onRemove: @escaping (String) -> Void, onChange: @escaping () -> Void) {
        self.onInput = onInput
        self.onRemove = onRemove
        self.onChange = onChange
        // kIOHIDManagerOptionIndependentDevices (0x8): open only admitted pads and share them with GameController.
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(0x8))
        self.manager = manager
        let matches: [[String: Any]] = [
            [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: kHIDUsage_GD_GamePad],
            [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: kHIDUsage_GD_Joystick],
        ]
        IOHIDManagerSetDeviceMatchingMultiple(manager, matches as CFArray)
        let context = Unmanaged.passUnretained(self).toOpaque()
        IOHIDManagerRegisterDeviceMatchingCallback(manager, { context, result, _, device in
            guard let context, result == kIOReturnSuccess else { return }
            Unmanaged<LauncherHIDManager>.fromOpaque(context).takeUnretainedValue().found(device)
        }, context)
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            guard let context else { return }
            Unmanaged<LauncherHIDManager>.fromOpaque(context).takeUnretainedValue().removed(device)
        }, context)
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        let result = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        if result != kIOReturnSuccess {
            Self.log.error("Cannot open HID gamepads (\(result)): only GameController controllers are read")
            IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            self.manager = nil
        }
    }

    deinit {
        for device in devices.values { stop(device) }
        if let manager {
            IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        }
    }

    func gameControllersChanged(_ names: Set<String>) {
        gcNames = names
        var changed = false
        for device in devices.values {
            let listed = names.contains(device.name)
            if device.active {
                if device.gcHint && listed {
                    stop(device)
                    onRemove(device.id)
                    changed = true
                }
            } else if let waiting = device.waiting {
                if listed { waiting.cancel(); device.waiting = nil }
            } else if !listed {
                admit(device)
            }
        }
        if changed { onChange() }
    }

    private func found(_ hid: IOHIDDevice) {
        let key = ObjectIdentifier(hid)
        guard devices[key] == nil else { return }
        let synthetic = (IOHIDDeviceGetProperty(hid, kIOHIDGCSyntheticDeviceKey as CFString) as? NSNumber)?.boolValue ?? false
        let vendorID = (IOHIDDeviceGetProperty(hid, kIOHIDVendorIDKey as CFString) as? NSNumber)?.intValue ?? 0
        if synthetic || [0x045E, 0x054C, 0x057E].contains(vendorID) { return }
        let name = IOHIDDeviceGetProperty(hid, kIOHIDProductKey as CFString) as? String ?? "HID gamepad"
        var report3F = false, hasZ = false
        if let elements = IOHIDDeviceCopyMatchingElements(hid, nil, IOOptionBits(kIOHIDOptionsTypeNone)) as? [IOHIDElement] {
            for element in elements {
                if IOHIDElementGetUsagePage(element) == UInt32(kHIDPage_Button), IOHIDElementGetReportID(element) == 0x3F { report3F = true }
                if IOHIDElementGetUsagePage(element) == UInt32(kHIDPage_GenericDesktop), IOHIDElementGetUsage(element) == 0x32 { hasZ = true }
            }
        }
        nextID += 1
        let device = LauncherHIDDevice(device: hid, id: "hid-\(nextID)", name: name, vendorID: vendorID,
                                       gcHint: GCController.supportsHIDDevice(hid),
                                       state: LauncherGamepad.HIDState(report3F: report3F, hasZ: hasZ), onInput: onInput)
        devices[key] = device
        admit(device)
    }

    private func admit(_ device: LauncherHIDDevice) {
        switch LauncherGamepad.hidAdmission(vendorID: device.vendorID, synthetic: false, gcHint: device.gcHint,
                                            gcListed: gcNames.contains(device.name)) {
        case .skip:
            return
        case .use:
            activate(device)
        case .wait:
            let key = ObjectIdentifier(device.device)
            let work = DispatchWorkItem { [weak self, weak device] in
                guard let self, let device, self.devices[key] === device else { return }
                device.waiting = nil
                if !self.gcNames.contains(device.name) { self.activate(device) }
            }
            device.waiting = work
            DispatchQueue.main.asyncAfter(deadline: .now() + 2, execute: work)
        }
    }

    private func activate(_ device: LauncherHIDDevice) {
        guard !device.active else { return }
        device.waiting = nil
        let result = IOHIDDeviceOpen(device.device, IOOptionBits(kIOHIDOptionsTypeNone))
        guard result == kIOReturnSuccess else {
            Self.log.error("Cannot open HID gamepad \(device.name, privacy: .public) (\(result))")
            return
        }
        device.active = true
        let context = Unmanaged.passUnretained(device).toOpaque()
        IOHIDDeviceRegisterInputValueCallback(device.device, { context, result, _, value in
            guard let context, result == kIOReturnSuccess else { return }
            Unmanaged<LauncherHIDDevice>.fromOpaque(context).takeUnretainedValue().read(value)
        }, context)
        IOHIDDeviceScheduleWithRunLoop(device.device, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        Self.log.debug("Reading \(device.name, privacy: .public) as raw HID (report 0x3F: \(device.state.report3F))")
        onChange()
    }

    private func removed(_ hid: IOHIDDevice) {
        guard let device = devices.removeValue(forKey: ObjectIdentifier(hid)) else { return }
        device.waiting?.cancel()
        let wasActive = device.active
        stop(device)
        if wasActive { onRemove(device.id); onChange() }
    }

    private func stop(_ device: LauncherHIDDevice) {
        guard device.active else { return }
        IOHIDDeviceRegisterInputValueCallback(device.device, nil, nil)
        IOHIDDeviceUnscheduleFromRunLoop(device.device, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        IOHIDDeviceClose(device.device, IOOptionBits(kIOHIDOptionsTypeNone))
        device.active = false
        device.player = nil
    }
}
