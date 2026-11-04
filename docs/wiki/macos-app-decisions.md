# App Mac NXNative — décisions de cadrage

Session de coordination `ses_e59a3af88ffeMiB2G5yhgxkJ18`, à partir de `a77506c`. Source : [étude](../research/macos-app-packaging.md).

- **2026-11-04** — Outillage : tracker local `.scratch/macos-app/`, wiki `docs/wiki/`, `AGENTS.md` + `docs/agents/` créés (labels par défaut, domaine single-context).
- **2026-11-04** — Autonomie : **A, lanceur du dossier NXNative**. L'app ne contient que la coque ; elle lance le Python et le dashboard du workspace (`~/Games/NXNative`, chemin configurable). Ne fonctionne que sur ce Mac avec ce dossier. B (Python figé) et C (portable sans Git/`source/`) écartés pour la v1 ; B reste un passage possible plus tard sans jeter la coque.
- **2026-11-04** — Coque : **Swift/AppKit + fenêtre WKWebView** sur `http://127.0.0.1:8767`. Écartés : variante navigateur (`NSWorkspace.open`) et Tauri 2. Conséquence acceptée : les préférences `localStorage` du navigateur (filtres, liens privés, menu natif) ne migrent pas ; à ressaisir une fois dans l'app.
- **2026-11-04** — Fermer la dernière fenêtre **ne quitte pas** : l'app reste dans le Dock, le serveur tourne jusqu'à Quitter (Cmd+Q) ; clic Dock = fenêtre rouverte.
- **2026-11-04** — Diffusion : **usage personnel sur ce Mac**, signature ad hoc, aucun compte Apple payant, pas de notarisation.
- **2026-11-04** — Mort brutale de l'app (crash, Forcer à quitter, SIGKILL) : **le serveur s'arrête seul** sur EOF d'un canal de contrôle tenu par la coque (à prouver par test).
- **2026-11-04** — Spec [`.scratch/macos-app/spec.md`](../../.scratch/macos-app/spec.md) et tickets 01–04 **validés tels quels**, propositions incluses (nom `NXNative Dashboard.app`, `WorkspacePath`, `make app`/`dmg`/`app-test`, icône générique, Kimi K3.1 Pro Highspeed). Implémentation sur la branche locale `desktop-app`, sans push.
- **2026-11-04** — Ticket 01 fusionné dans `desktop-app` (`3014c1c`) : `make test` 57+30+3 OK (implémenteur) ; contrôle coordination en CLI réel : `GET /` 200 puis EOF → exit 0, port libéré.
