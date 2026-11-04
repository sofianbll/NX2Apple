# 04: DMG installable et recette du cycle de vie sur l'app réelle

**What to build:** `make dmg` produit `dist/NXNative Dashboard.dmg` contenant seulement l'app (et un alias Applications) ; `make app-test` prouve sur l'app construite, avec le vrai serveur du workspace, Quitter, crash/SIGKILL, conflit de port, seconde instance et survie des processus indépendants. Documentation README mise à jour. Recette : « Seam 4 » de [`spec.md`](../spec.md).

**Blocked by:** 01, 03

**Status:** resolved

- [x] Le DMG ne contient que l'app ; échec si l'app contient autre chose que l'exécutable, l'Info.plist et la signature. Aucun jeu, clé, app de jeu, cache, `source/`, `.venv`, SDK ni secret.
- [x] Ouverture par `open` : le listener 8767 est l'enfant de l'app ; la page et `GET /status` répondent.
- [x] Quitter → serveur arrêté, port libre. `kill -9` de l'app → serveur arrêté sous 5 s.
- [x] Port pris par un faux serveur → conflit affiché, faux serveur intact. `open -n` d'une 2ᵉ instance → conflit, 1ʳᵉ instance intacte.
- [x] Une session tmux témoin et un processus détaché témoin survivent à chaque cas ; aucun vrai jeu ouvert, aucun `killall`/`pkill`/kill de groupe.
- [ ] Installation depuis le DMG dans `/Applications` puis lancement vérifiés ; captures (dashboard, conflit, workspace invalide) relues par la coordination.
- [x] README : section « App Mac » (construire, installer, régler `WorkspacePath`, limites : ce Mac seulement, préférences navigateur non migrées).

## Answer

Le contrôle de conflit utilise désormais `AXUIElementCreateApplication(pid)` et les attributs Accessibility de cette seule instance, via la bibliothèque standard Python et les frameworks système, sans dépendance ajoutée. Le README documente **Réglages Système → Confidentialité et sécurité → Ouvrir quand même**, sans Developer ID ni désactivation de Gatekeeper.

Vérifié le 2026-11-04 : `swift test --package-path tools/desktop-app` (11 tests), `make test` (58 + 30 tests Python, 3 tests Node), `make dmg` (allowlist, contenu monté et `diff -r` conformes) et `make app-test` (ouverture, Quitter, SIGKILL, conflit simple, seconde instance et témoins) passent. Journaux dans `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-t04/`.

L'installation dans `/Applications`, les captures et les contrôles manuels de persistance, raccourcis et lien externe restent à faire par la coordination ; ils ne sont pas réputés réussis. Le changement `snapshot()` introduit par `c55170d` est hors ticket, inchangé ici et reste à revoir.
