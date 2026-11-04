import XCTest
import NXNativeCore

final class NavigationPolicyTests: XCTestCase {
    func testNewWindowUserGesture() {
        XCTAssertTrue(NavigationPolicy.newWindowIsUserInitiated(
            linkActivated: true,
            allowsAutomaticJavaScriptWindows: true
        ))
        XCTAssertTrue(NavigationPolicy.newWindowIsUserInitiated(
            linkActivated: false,
            allowsAutomaticJavaScriptWindows: false
        ))
        XCTAssertFalse(NavigationPolicy.newWindowIsUserInitiated(
            linkActivated: false,
            allowsAutomaticJavaScriptWindows: true
        ))
    }

    func testNavigationDecisions() throws {
        let cases: [(url: String, userInitiated: Bool, newWindow: Bool, expected: NavigationDecision)] = [
            ("http://127.0.0.1:8767/", false, false, .allow),
            ("http://127.0.0.1:8767/catalogue?vue=cinema", true, false, .allow),
            ("http://127.0.0.1:8767/nouvelle-fenetre", true, true, .deny),
            ("https://example.com/drive", true, false, .openExternally),
            ("https://example.com/drive", true, true, .openExternally),
            ("https://example.com/drive", false, false, .deny),
            ("https://example.com/drive", false, true, .deny),
            ("http://localhost:8767/", true, false, .deny),
            ("http://127.0.0.1:8768/", true, false, .deny),
            ("http://127.0.0.1/", true, false, .deny),
            ("https://127.0.0.1:8767/", true, false, .deny),
            ("file:///tmp/dashboard.html", true, false, .deny),
            ("javascript:alert(1)", true, false, .deny),
            ("http://example.com/", true, false, .deny),
            ("http://example.com/", true, true, .deny),
        ]

        for testCase in cases {
            let url = try XCTUnwrap(URL(string: testCase.url))
            let decision = NavigationPolicy.decision(
                for: url,
                isUserInitiated: testCase.userInitiated,
                isNewWindow: testCase.newWindow
            )
            XCTAssertEqual(
                decision,
                testCase.expected,
                "\(testCase.url), utilisateur=\(testCase.userInitiated), nouvelleFenetre=\(testCase.newWindow)"
            )
        }
    }
}
