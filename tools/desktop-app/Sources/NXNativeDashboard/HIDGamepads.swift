import GameController
import IOKit.hid
import NXNativeCore

// Raw HID gamepads WebKit cannot see. Like nxnative's pad_hid_mac.h: GameController claims some pads without IDs
// (PowerA "Lic Pro Controller", 0000:0000) but never lists them, so WebKit's Gamepad API misses them too. A pad
// with real IDs that GameController supports is left to WebKit's Gamepad API, so no press is counted twice.
final class HIDGamepads {
    private let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    private var pads: [IOHIDDevice: PadInput] = [:]
    private var held: [IOHIDDevice: Set<String>] = [:]
    private let onPress: (String) -> Void

    init(onPress: @escaping (String) -> Void) {
        self.onPress = onPress
        let matching = [kHIDUsage_GD_GamePad, kHIDUsage_GD_Joystick].map {
            [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: $0]
        }
        IOHIDManagerSetDeviceMatchingMultiple(manager, matching as CFArray)
        let context = Unmanaged.passUnretained(self).toOpaque()
        IOHIDManagerRegisterDeviceMatchingCallback(manager, { context, _, _, device in
            Unmanaged<HIDGamepads>.fromOpaque(context!).takeUnretainedValue().found(device)
        }, context)
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            let pads = Unmanaged<HIDGamepads>.fromOpaque(context!).takeUnretainedValue()
            pads.pads[device] = nil
            pads.held[device] = nil
        }, context)
        IOHIDManagerRegisterInputValueCallback(manager, { context, _, _, value in
            Unmanaged<HIDGamepads>.fromOpaque(context!).takeUnretainedValue().changed(value)
        }, context)
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))   // nonexclusive: games keep reading the pad
    }

    private func found(_ device: IOHIDDevice) {
        if IOHIDDeviceGetProperty(device, kIOHIDGCSyntheticDeviceKey as CFString) as? Bool == true { return }
        let vendor = IOHIDDeviceGetProperty(device, kIOHIDVendorIDKey as CFString) as? Int ?? 0
        let product = IOHIDDeviceGetProperty(device, kIOHIDProductIDKey as CFString) as? Int ?? 0
        if (vendor != 0 || product != 0) && GCController.supportsHIDDevice(device) { return }
        pads[device] = PadInput()
    }

    private func changed(_ value: IOHIDValue) {
        let element = IOHIDValueGetElement(value), device = IOHIDElementGetDevice(element)
        guard var pad = pads[device] else { return }
        let page = Int(IOHIDElementGetUsagePage(element)), usage = Int(IOHIDElementGetUsage(element))
        let raw = IOHIDValueGetIntegerValue(value)
        let min = IOHIDElementGetLogicalMin(element), max = IOHIDElementGetLogicalMax(element)
        let axis = max > min ? Double(raw - min) / Double(max - min) * 2 - 1 : 0
        switch (page, usage) {
        case (kHIDPage_Button, _): if raw != 0 { pad.buttons.insert(usage) } else { pad.buttons.remove(usage) }
        case (kHIDPage_GenericDesktop, kHIDUsage_GD_Hatswitch): pad.hat = raw >= min && raw - min < 8 ? raw - min : -1
        case (kHIDPage_GenericDesktop, kHIDUsage_GD_X): pad.x = axis
        case (kHIDPage_GenericDesktop, kHIDUsage_GD_Y): pad.y = axis
        default: return
        }
        pads[device] = pad
        let actions = pad.actions
        for action in padPresses(held[device] ?? [], actions) { onPress(action) }
        held[device] = actions
    }
}
