import AppKit
import NXNativeCore
import WebKit

final class DashboardNavigationDelegate: NSObject, WKNavigationDelegate, WKUIDelegate {
    private let openExternal: (URL) -> Void

    init(openExternal: @escaping (URL) -> Void = { NSWorkspace.shared.open($0) }) {
        self.openExternal = openExternal
    }

    func webView(
        _ webView: WKWebView,
        decidePolicyFor navigationAction: WKNavigationAction,
        decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
    ) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }

        let decision = NavigationPolicy.decision(
            for: url,
            isUserInitiated: navigationAction.navigationType == .linkActivated,
            isNewWindow: navigationAction.targetFrame == nil
        )
        switch decision {
        case .allow:
            decisionHandler(.allow)
        case .openExternally:
            decisionHandler(.cancel)
            openExternal(url)
        case .deny:
            decisionHandler(.cancel)
        }
    }

    func webView(
        _ webView: WKWebView,
        createWebViewWith configuration: WKWebViewConfiguration,
        for navigationAction: WKNavigationAction,
        windowFeatures: WKWindowFeatures
    ) -> WKWebView? {
        // Sans popup automatique, WebKit ne délègue window.open que si un geste l'autorise.
        let isUserInitiated = NavigationPolicy.newWindowIsUserInitiated(
            linkActivated: navigationAction.navigationType == .linkActivated,
            allowsAutomaticJavaScriptWindows: webView.configuration.preferences
                .javaScriptCanOpenWindowsAutomatically
        )
        if let url = navigationAction.request.url,
           NavigationPolicy.decision(
               for: url,
               isUserInitiated: isUserInitiated,
               isNewWindow: true
           ) == .openExternally {
            openExternal(url)
        }
        return nil
    }
}
