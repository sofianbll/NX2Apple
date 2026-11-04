import AppKit
import NXNativeCore
import WebKit

final class DashboardNavigationDelegate: NSObject, WKNavigationDelegate, WKUIDelegate {
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
            NSWorkspace.shared.open(url)
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
        if let url = navigationAction.request.url,
           NavigationPolicy.decision(
               for: url,
               isUserInitiated: navigationAction.navigationType == .linkActivated,
               isNewWindow: true
           ) == .openExternally {
            NSWorkspace.shared.open(url)
        }
        return nil
    }
}
