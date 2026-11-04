# 04: DMG installable et recette du cycle de vie sur l'app réelle

**What to build:** `make dmg` produit `dist/NXNative Dashboard.dmg` contenant seulement l'app (et un alias Applications) ; `make app-test` prouve sur l'app construite, avec le vrai serveur du workspace, Quitter, crash/SIGKILL, conflit de port, seconde instance et survie des processus indépendants. Documentation README mise à jour. Recette : « Seam 4 » de [`spec.md`](../spec.md).

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] Le DMG ne contient que l'app ; échec si l'app contient autre chose que l'exécutable, l'Info.plist et la signature. Aucun jeu, clé, app de jeu, cache, `source/`, `.venv`, SDK ni secret.
- [ ] Ouverture par `open` : le listener 8767 est l'enfant de l'app ; la page et `GET /status` répondent.
- [ ] Quitter → serveur arrêté, port libre. `kill -9` de l'app → serveur arrêté sous 5 s.
- [ ] Port pris par un faux serveur → conflit affiché, faux serveur intact. `open -n` d'une 2ᵉ instance → conflit, 1ʳᵉ instance intacte.
- [ ] Une session tmux témoin et un processus détaché témoin survivent à chaque cas ; aucun vrai jeu ouvert, aucun `killall`/`pkill`/kill de groupe.
- [ ] Installation depuis le DMG dans `/Applications` puis lancement vérifiés ; captures (dashboard, conflit, workspace invalide) relues par la coordination.
- [ ] README : section « App Mac » (construire, installer, régler `WorkspacePath`, limites : ce Mac seulement, préférences navigateur non migrées).
