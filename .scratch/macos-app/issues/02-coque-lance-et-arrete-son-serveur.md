# 02: L'app s'ouvre, démarre son serveur, affiche le dashboard et l'arrête en quittant

**What to build:** premier `NXNative Dashboard.app` construit par `make app` (SwiftPM + Info.plist + signature ad hoc). À l'ouverture, valide le workspace, vérifie le port, lance le serveur du workspace selon le contrat, attend sa ligne de disponibilité puis affiche `http://127.0.0.1:8767/` dans une fenêtre WKWebView. Quitter suit la séquence EOF → SIGTERM → SIGKILL sur le seul PID possédé. Fermer la fenêtre garde l'app dans le Dock ; le Dock la rouvre. Contrat et cycle de vie : [`spec.md`](../spec.md).

**Blocked by:** None (construit contre le contrat de 01 ; tests contre un faux serveur). La recette sur le vrai serveur est dans 04.

**Status:** ready-for-agent

- [ ] `swift test` couvre `ServerProcess` contre un faux serveur : disponibilité, échec avant disponibilité, délai 15 s, conflit détecté sans lancement, arrêt par EOF, repli SIGTERM puis SIGKILL au seul PID possédé, processus témoin non lié toujours vivant.
- [ ] Port déjà pris : état conflit affiché, bouton « Ouvrir dans le navigateur », aucun processus tué ni adopté.
- [ ] Workspace absent ou sans `.venv/bin/python` / `tools/library.py` : message clair, aucun lancement. Réglage `WorkspacePath`, défaut `~/Games/NXNative`.
- [ ] Mort inattendue du serveur : fin du journal + bouton « Relancer le serveur ».
- [ ] Journal dans `~/Library/Logs/NXNative Dashboard/server.log`.
- [ ] `make app` produit l'app ad hoc signée (`codesign --verify --strict` OK) ; `dist/` et `.build` SwiftPM ignorés par Git.
