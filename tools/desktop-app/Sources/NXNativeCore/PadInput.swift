// One raw HID gamepad's state turned into dashboard actions ('nx-pad' events in index.html).
// Same reading as nxnative's pad_hid.h default map, validated with the PowerA in Stardew: HID button 2 = A (right), 1 = B (bottom).
// Only the hat and the left stick (X/Y) move: other axes, such as motion sensors, are ignored.
public struct PadInput: Equatable {
    public var buttons: Set<Int> = []   // HID button usages held
    public var hat = -1                 // -1 centered, 0 up, then clockwise to 7 up-left
    public var x = 0.0, y = 0.0         // -1...1, y down positive as HID reports it

    public init() {}

    public var actions: Set<String> {
        var held = Set<String>()
        if buttons.contains(2) { held.insert("confirm") }
        if buttons.contains(1) { held.insert("back") }
        if [7, 0, 1].contains(hat) || y <= -0.5 { held.insert("up") }
        if [1, 2, 3].contains(hat) || x >= 0.5 { held.insert("right") }
        if [3, 4, 5].contains(hat) || y >= 0.5 { held.insert("down") }
        if [5, 6, 7].contains(hat) || x <= -0.5 { held.insert("left") }
        return held
    }
}

// Only new presses count: a held button never repeats.
public func padPresses(_ before: Set<String>, _ after: Set<String>) -> [String] {
    ["up", "down", "left", "right", "confirm", "back"].filter { after.contains($0) && !before.contains($0) }
}
