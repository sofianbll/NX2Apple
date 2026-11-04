import AppKit
import NXNativeCore
import WebKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let dashboardURL = URL(string: "http://127.0.0.1:8767/")!
    private let navigationDelegate = DashboardNavigationDelegate()
    private var window: NSWindow!
    private var webView: WKWebView!
    private var server: ServerProcess?
    private var isLaunching = false
    private var isQuitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        installMainMenu()

        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = navigationDelegate
        webView.uiDelegate = navigationDelegate

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1100, height: 760),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "NXNative Dashboard"
        window.minSize = NSSize(width: 640, height: 480)
        window.isReleasedWhenClosed = false
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)
        launchServer()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        if !hasVisibleWindows { window.makeKeyAndOrderFront(nil) }
        sender.activate(ignoringOtherApps: true)
        return false
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if !isQuitting {
            isQuitting = true
            let server = self.server
            Task { @MainActor in
                await server?.stop()
                sender.reply(toApplicationShouldTerminate: true)
            }
        }
        return .terminateLater
    }

    private func launchServer() {
        guard !isLaunching, !isQuitting else { return }
        isLaunching = true
        showState(title: "Démarrage du serveur…", message: "Le dashboard s’ouvrira dès qu’il sera prêt.")

        let configuredPath = UserDefaults.standard.string(forKey: "WorkspacePath") ?? "~/Games/NXNative"
        let workspacePath = (configuredPath as NSString).expandingTildeInPath
        let workspace = URL(fileURLWithPath: workspacePath)
        let server = ServerProcess(workspace: workspace)
        self.server = server

        server.onUnexpectedTermination = { [weak self, weak server] _ in
            Task { @MainActor in
                guard let self, let server, self.server === server, !self.isQuitting else { return }
                self.isLaunching = false
                self.showState(
                    title: "Le serveur s’est arrêté de façon inattendue",
                    message: "La fin du journal est affichée ci-dessous.",
                    logTail: server.logTail(maxLines: 30),
                    buttonTitle: "Relancer le serveur",
                    action: #selector(self.restartServer)
                )
            }
        }

        Task { @MainActor in
            do {
                try await server.start()
                guard self.server === server, !self.isQuitting else { return }
                self.isLaunching = false
                self.window.contentView = self.webView
                self.webView.load(URLRequest(url: self.dashboardURL))
            } catch {
                guard self.server === server, !self.isQuitting else { return }
                self.isLaunching = false
                self.showStartupError(error, workspacePath: workspacePath)
            }
        }
    }

    private func showStartupError(_ error: Error, workspacePath: String) {
        guard let error = error as? ServerProcessError else {
            showState(title: "Le serveur n’a pas pu démarrer", message: error.localizedDescription)
            return
        }

        switch error {
        case .invalidWorkspace:
            showState(
                title: "Le dossier NXNative est introuvable ou incomplet",
                message: "Le dossier doit contenir .venv/bin/python et tools/library.py.\n\nDossier actuel : \(workspacePath)\n\nModifiez le réglage WorkspacePath si nécessaire."
            )
        case .portInUse:
            showState(
                title: "Le port 8767 est déjà utilisé",
                message: "Un autre serveur répond déjà. L’app ne l’a ni arrêté ni adopté.",
                buttonTitle: "Ouvrir dans le navigateur",
                action: #selector(openDashboardInBrowser)
            )
        case .startupFailed(let tail):
            showState(
                title: "Le serveur s’est arrêté au démarrage",
                message: "La fin du journal est affichée ci-dessous.",
                logTail: tail,
                buttonTitle: "Relancer le serveur",
                action: #selector(restartServer)
            )
        case .readinessTimeout(let tail):
            showState(
                title: "Le serveur n’est pas prêt",
                message: "Aucune disponibilité n’a été annoncée dans les 15 secondes.",
                logTail: tail,
                buttonTitle: "Relancer le serveur",
                action: #selector(restartServer)
            )
        }
    }

    @objc private func openDashboardInBrowser() {
        NSWorkspace.shared.open(dashboardURL)
    }

    @objc private func restartServer() {
        launchServer()
    }

    private func showState(
        title: String,
        message: String,
        logTail: String? = nil,
        buttonTitle: String? = nil,
        action: Selector? = nil
    ) {
        let container = NSView()
        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .centerX
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false

        let titleLabel = NSTextField(wrappingLabelWithString: title)
        titleLabel.font = .boldSystemFont(ofSize: 22)
        titleLabel.alignment = .center
        stack.addArrangedSubview(titleLabel)

        let messageLabel = NSTextField(wrappingLabelWithString: message)
        messageLabel.font = .systemFont(ofSize: 14)
        messageLabel.alignment = .center
        messageLabel.maximumNumberOfLines = 0
        stack.addArrangedSubview(messageLabel)

        if let logTail {
            let scrollView = NSScrollView(frame: NSRect(x: 0, y: 0, width: 560, height: 220))
            scrollView.hasVerticalScroller = true
            scrollView.borderType = .bezelBorder
            let textView = NSTextView(frame: scrollView.bounds)
            textView.isEditable = false
            textView.font = .monospacedSystemFont(ofSize: 11, weight: .regular)
            textView.autoresizingMask = [.width]
            textView.textContainer?.widthTracksTextView = true
            textView.string = logTail.isEmpty ? "Le journal est vide." : logTail
            scrollView.documentView = textView
            stack.addArrangedSubview(scrollView)
            scrollView.widthAnchor.constraint(equalToConstant: 560).isActive = true
            scrollView.heightAnchor.constraint(equalToConstant: 220).isActive = true
        }

        if let buttonTitle, let action {
            let button = NSButton(title: buttonTitle, target: self, action: action)
            button.bezelStyle = .rounded
            stack.addArrangedSubview(button)
        }

        container.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: container.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: container.centerYAnchor),
            stack.widthAnchor.constraint(equalToConstant: 560),
            stack.topAnchor.constraint(greaterThanOrEqualTo: container.topAnchor, constant: 24),
            stack.bottomAnchor.constraint(lessThanOrEqualTo: container.bottomAnchor, constant: -24),
        ])
        window.contentView = container
    }

    private func installMainMenu() {
        let mainMenu = NSMenu()
        let appMenuItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quitter NXNative Dashboard", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appMenuItem.submenu = appMenu
        mainMenu.addItem(appMenuItem)

        let editMenuItem = NSMenuItem()
        let editMenu = NSMenu(title: "Édition")
        editMenu.addItem(withTitle: "Annuler", action: Selector(("undo:")), keyEquivalent: "z")
        let redoItem = editMenu.addItem(withTitle: "Rétablir", action: Selector(("redo:")), keyEquivalent: "z")
        redoItem.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(withTitle: "Couper", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copier", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Coller", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Tout sélectionner", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editMenuItem.submenu = editMenu
        mainMenu.addItem(editMenuItem)

        NSApplication.shared.mainMenu = mainMenu
    }
}
