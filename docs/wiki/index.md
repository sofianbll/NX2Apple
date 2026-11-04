# Wiki NXNative

Historique daté des initiatives. Ne décrit jamais l'état présent sans date ou commit.

## App Mac (packaging desktop)

- [Décisions de cadrage](macos-app-decisions.md) — choix validés par Sofian pendant le cadrage, datés.
- [Relais de coordination](macos-app-handoff.md) — état et prochaines actions au changement de session.
- **2026-11-04** — Reprise par `ses_e594dd988ffeaw38KlFY31gjTI` depuis `ses_e59a3af88ffeMiB2G5yhgxkJ18` : ticket 04 intégré en fast-forward dans `desktop-app` à `4a560bf` (`c55170d`, `97bbe1c`, puis merge d'intégration) ; les nouvelles entrées datées des deux pages ci-dessus marquent l'ancien état du ticket comme supersédé. Prochaine étape : revue **Standards + Spec** depuis `a77506c`, puis demande d'accord pour la fusion dans `main`.

## Sources

- Étude : [`docs/research/macos-app-packaging.md`](../research/macos-app-packaging.md) (recherche du 2026-11-04, non décisionnelle).
- **2026-11-04 (soir)** — Corrections après revue commitées, `swift test` borné (13 tests, 3 passes), puis `desktop-app` fusionnée dans `main` (`f592f23`) sur décision de Sofian ; worktrees `desktop-app` et `t04` supprimés. État et suite : `ROADMAP.md` (v0.2.0). Le relais ci-dessus est historique.

## Manette dans la vue Cinéma (v0.2.1)

- **2026-11-04 (nuit)** — Relais de `ses_e57dd7714ffeUN7ieoyhqiW4PM`. Navigation manette livrée sur `main` (`184ad0d`, `520aa96`, `f399541`) : API Gamepad pour les manettes standard ; la PowerA (0000:0000) est invisible pour WebKit, elle est donc lue en HID direct par l'app Mac (`HIDGamepads.swift`, mêmes règles que `pad_hid_mac.h`). DMG reconstruit après `f399541`. Zelda, Rouge Feu FR, Mario Kart 8 et Z-A marqués « Jouable » (`c533571`). En attente : test de Sofian avec la manette dans l'app, puis tags `v0.2.0` et `v0.2.1`. État et critères : `ROADMAP.md`.
