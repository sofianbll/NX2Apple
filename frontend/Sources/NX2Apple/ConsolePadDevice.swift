import Foundation
import GameController

/// One controller source behind the console's shared listing, player slots and Identify action.
/// GameController and raw HID supply the same small interface, as the engine's DMController registry does.
struct ConsolePadDevice {
    let id: String
    let snapshot: () -> ConsolePadSnapshot
    let battery: NSObject?
    /// Changes the stored player without an output report (1...4, nil when unset).
    let setPlayer: (Int?) -> Void
    /// Shows the player on the hardware, including a light bar when the source has one.
    let showPlayer: (Int) -> Void
    let identify: (String) async -> Void
    let gameController: GCController?

    static func gameController(_ c: GCController, id: String, identify: @escaping (GCController, String) async -> Void) -> ConsolePadDevice {
        func index(_ player: Int?) -> GCControllerPlayerIndex {
            guard let player else { return .indexUnset }
            return GCControllerPlayerIndex(rawValue: player - 1) ?? .indexUnset
        }
        return ConsolePadDevice(id: id, snapshot: {
            let reading = c.battery.map { b -> (level: Double?, charging: Bool) in
                let state: PadBatteryState = b.batteryState == .charging ? .charging : b.batteryState == .full ? .full : b.batteryState == .discharging ? .discharging : .unknown
                return ConsolePadSnapshot.batteryReading(level: Double(b.batteryLevel), state: state)
            }
            let player = c.playerIndex.rawValue
            return ConsolePadSnapshot(id: id, name: c.vendorName ?? c.productCategory, category: c.productCategory,
                                      playerIndex: (0...3).contains(player) ? player + 1 : nil, battery: reading?.level,
                                      charging: reading?.charging ?? false, canIdentify: !LiveConsoleDriver.identifyActions(c).isEmpty)
        }, battery: c.battery,
        setPlayer: { c.playerIndex = index($0) },
        showPlayer: {
            c.playerIndex = index($0)
            if let light = c.light {
                let color = LiveConsoleDriver.playerLightColor($0)
                light.color = GCColor(red: color.red, green: color.green, blue: color.blue)
            }
        },
        identify: { await identify(c, $0) }, gameController: c)
    }
}
