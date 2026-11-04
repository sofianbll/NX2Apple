// Read-only: non-exclusive HID read of a gamepad. Prints element usages, then asks R then ZR and reports the Button-page usage seen.
// No serial / address read, nothing written to the device.
import Foundation
import IOKit.hid

let host: [Int: String] = [1:"B", 2:"A", 3:"-", 4:"Y", 5:"X", 6:"-", 7:"L", 8:"R", 9:"ZL", 10:"ZR", 11:"MINUS", 12:"PLUS", 14:"LS", 15:"RS"]
let mgr = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
IOHIDManagerSetDeviceMatchingMultiple(mgr, [
    [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: kHIDUsage_GD_GamePad],
    [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: kHIDUsage_GD_Joystick]] as CFArray)
print("open:", String(format: "0x%x", IOHIDManagerOpen(mgr, IOOptionBits(kIOHIDOptionsTypeNone))))

var steps = ["R", "ZR"], step = 0, seen: [String: Int] = [:], deadline = Date().addingTimeInterval(20)
var shown = false
func prompt() { print(">>> Press and release physical \(steps[step]) now (20 s)"); fflush(stdout); deadline = Date().addingTimeInterval(20) }

let cb: IOHIDValueCallback = { _, _, _, v in
    let e = IOHIDValueGetElement(v)
    let page = IOHIDElementGetUsagePage(e), usage = Int(IOHIDElementGetUsage(e)), x = IOHIDValueGetIntegerValue(v)
    guard page == kHIDPage_Button, x == 1, step < steps.count else { return }
    let dn = IOHIDDeviceGetProperty(IOHIDElementGetDevice(e), kIOHIDProductKey as CFString) as? String ?? "?"
    print("  [\(dn)] physical \(steps[step]) -> Button usage \(usage); host default map gives: \(host[usage] ?? "nothing")"); fflush(stdout)
    step += 1; if step < steps.count { prompt() }
}
IOHIDManagerRegisterInputValueCallback(mgr, cb, nil)
for d in (IOHIDManagerCopyDevices(mgr) as? Set<IOHIDDevice>) ?? [] {
    let name = IOHIDDeviceGetProperty(d, kIOHIDProductKey as CFString) as? String ?? "?"
    let vid = IOHIDDeviceGetProperty(d, kIOHIDVendorIDKey as CFString) as? Int ?? -1, pid = IOHIDDeviceGetProperty(d, kIOHIDProductIDKey as CFString) as? Int ?? -1
    print("device:", name, "vid/pid:", vid, pid)
    var bt: [Int] = [], other: [String] = []
    for el in (IOHIDDeviceCopyMatchingElements(d, nil, IOOptionBits(kIOHIDOptionsTypeNone)) as? [IOHIDElement]) ?? [] {
        let p = Int(IOHIDElementGetUsagePage(el)), u = Int(IOHIDElementGetUsage(el))
        if p == kHIDPage_Button { bt.append(u) } else if IOHIDElementGetType(el) != kIOHIDElementTypeCollection { other.append(String(format: "%02x:%02x", p, u)) }
    }
    print("  Button usages:", bt.sorted()); print("  other (page:usage):", other.joined(separator: " "))
}
prompt()
while step < steps.count && Date() < deadline { RunLoop.main.run(until: Date().addingTimeInterval(0.1)) }
if step < steps.count { print("timeout: no press seen for \(steps[step])") }
