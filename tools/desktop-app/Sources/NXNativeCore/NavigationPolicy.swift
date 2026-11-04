import Foundation

public enum NavigationDecision: Equatable {
    case allow
    case openExternally
    case deny
}

public enum NavigationPolicy {
    public static func newWindowIsUserInitiated(
        linkActivated: Bool,
        allowsAutomaticJavaScriptWindows: Bool
    ) -> Bool {
        linkActivated || !allowsAutomaticJavaScriptWindows
    }

    public static func decision(
        for url: URL,
        isUserInitiated: Bool,
        isNewWindow: Bool
    ) -> NavigationDecision {
        if url.scheme == "http", url.host == "127.0.0.1", url.port == 8767 {
            return isNewWindow ? .deny : .allow
        }
        if isUserInitiated, url.scheme == "https", let host = url.host, host != "127.0.0.1" {
            return .openExternally
        }
        return .deny
    }
}
