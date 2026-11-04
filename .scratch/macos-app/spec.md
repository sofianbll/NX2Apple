# Spec : app Mac « NXNative Dashboard »

**Statut :** validée par Sofian le 2026-11-04 (propositions incluses). Base : `main` à `a77506c`.
**Sources :** [étude](../../docs/research/macos-app-packaging.md) · [décisions datées](../../docs/wiki/macos-app-decisions.md).

## Problem Statement

Pour voir sa ludothèque, Sofian doit lancer `make monitor` dans un terminal (ou tmux), ouvrir `http://127.0.0.1:8767` dans un navigateur, puis penser à arrêter le serveur. Il veut une vraie app Mac, installée depuis un DMG, qui démarre le dashboard à l'ouverture et l'arrête quand il la quitte, même après un crash ou un « Forcer à quitter », sans toucher à ses jeux ni à ses builds.

## Solution

Une petite app native Swift/AppKit, `NXNative Dashboard.app`, installée depuis un DMG local signé ad hoc. À l'ouverture, elle lance le serveur du dashboard **du dossier NXNative existant** (Python du `.venv`, code du workspace), attend que **son** serveur soit prêt, puis affiche le dashboard Cinéma actuel dans une fenêtre WebKit. Fermer la fenêtre laisse l'app dans le Dock ; Quitter arrête le serveur. Si l'app meurt brutalement, le serveur s'arrête seul. Si le port 8767 est déjà pris, l'app le dit et ne touche à rien.

L'app ne contient ni Python, ni jeux, ni clés, ni code du dashboard : elle est un lanceur de ce workspace, utilisable seulement sur ce Mac.

## User Stories

1. En tant que Sofian, je veux installer l'app en glissant `NXNative Dashboard.app` du DMG vers Applications, afin de ne plus passer par le terminal.
2. En tant que Sofian, je veux que l'ouverture de l'app démarre le dashboard, afin de ne plus lancer `make monitor` à la main.
3. En tant que Sofian, je veux voir le dashboard Cinéma actuel, identique au navigateur, afin de garder mes habitudes.
4. En tant que Sofian, je veux que la fenêtre n'affiche la page qu'une fois le serveur prêt, afin de ne jamais voir une page d'erreur de connexion au démarrage.
5. En tant que Sofian, je veux que Quitter (Cmd+Q ou menu) arrête le serveur, afin de ne laisser aucun processus derrière.
6. En tant que Sofian, je veux que fermer la fenêtre garde l'app dans le Dock avec le serveur actif, afin de rouvrir vite.
7. En tant que Sofian, je veux qu'un clic sur l'icône du Dock rouvre la fenêtre, afin de retrouver le dashboard.
8. En tant que Sofian, je veux qu'après un crash ou un « Forcer à quitter » de l'app le serveur s'arrête seul, afin que le port ne reste pas bloqué.
9. En tant que Sofian, je veux que mes jeux ouverts depuis le dashboard continuent après Quitter, afin de ne pas perdre une partie.
10. En tant que Sofian, je veux que mes builds dans tmux continuent après Quitter ou un crash de l'app, afin de ne pas perdre des heures de shaders.
11. En tant que Sofian, je veux, si `make monitor` tourne déjà, un message clair au lieu d'un arrêt de ce serveur, afin de garder la main sur mes processus.
12. En tant que Sofian, je veux, dans ce cas, un bouton pour ouvrir le dashboard existant dans mon navigateur, afin de continuer quand même.
13. En tant que Sofian, je veux qu'une seconde ouverture de l'app ramène la fenêtre existante, et qu'une seconde instance forcée affiche le conflit sans casser la première, afin de ne jamais avoir deux serveurs.
14. En tant que Sofian, je veux un message clair si le dossier NXNative ou son `.venv` est introuvable, afin de savoir quoi réparer.
15. En tant que Sofian, je veux pouvoir indiquer un autre emplacement du dossier NXNative par un réglage simple, afin de déplacer l'installation plus tard.
16. En tant que Sofian, je veux un message clair si le serveur s'arrête tout seul pendant l'utilisation, avec la fin de son journal et un bouton pour le relancer, afin de comprendre et repartir.
17. En tant que Sofian, je veux que mes filtres, éditions choisies, liens privés et choix de menu natif saisis dans l'app soient conservés d'une ouverture à l'autre, afin de ne les saisir qu'une fois.
18. En tant que Sofian, je sais que les réglages déjà saisis dans mon navigateur ne sont pas copiés dans l'app, et je l'accepte.
19. En tant que Sofian, je veux que mes liens Drive privés s'ouvrent dans mon navigateur habituel, afin que des pages externes ne s'affichent jamais dans la fenêtre de l'app.
20. En tant que Sofian, je veux que **Jouer** et **Enregistrer pour le prochain lancement** marchent comme dans le navigateur, afin de tout faire depuis l'app.
21. En tant que Sofian, je veux que le serveur garde ses protections (127.0.0.1 seulement, contrôle Host/Origin strict), afin que l'app n'ouvre aucune nouvelle porte.
22. En tant que Sofian, je veux que la page n'ait accès à aucune commande native de l'app, afin qu'un bug du JS ne puisse rien lancer d'autre.
23. En tant que Sofian, je veux que `make monitor` dans tmux marche comme avant, afin de garder mon usage actuel.
24. En tant que Sofian, je veux construire l'app avec `make app` et le DMG avec `make dmg`, afin de les reconstruire en une commande.
25. En tant que Sofian, je veux que le DMG ne contienne que l'app, sans jeux, clés, apps de jeux, caches, `source/`, `.venv`, SDK ni secrets, afin de pouvoir le garder sans risque.
26. En tant que Sofian, je veux que les modifications du dashboard (HTML, Web Components, Python) apparaissent sans reconstruire l'app, afin d'itérer vite.
27. En tant que Sofian, je veux un journal du serveur dans `~/Library/Logs`, afin de diagnostiquer un problème.
28. En tant que Sofian, je veux que l'app fonctionne sans compte Apple payant, afin de ne rien acheter.
29. En tant que Sofian, je veux que `make test` vérifie aussi l'arrêt du serveur sur fin de canal, afin de ne pas casser ce comportement plus tard.
30. En tant que Sofian, je veux un test de recette qui prouve Quitter, crash, SIGKILL, conflit de port et survie des processus indépendants sur l'app réellement construite, afin de croire au résultat.

## Implementation Decisions

**Décisions validées** (voir le wiki daté) : niveau d'autonomie A (lanceur du workspace) ; coque Swift/AppKit + WKWebView ; fermer la fenêtre ne quitte pas ; usage personnel, signature ad hoc ; arrêt du serveur sur EOF d'un canal de contrôle.

**Proposées dans cette spec, à confirmer à la validation :**

- **Nom et identité :** `NXNative Dashboard.app`, identifiant de bundle `local.nxnative.dashboard`, icône générique en v1. Journal serveur : `~/Library/Logs/NXNative Dashboard/server.log` (distinct de `~/Library/Logs/nxnative/` des jeux).
- **Workspace :** réglage `WorkspacePath` (préférences de l'app), défaut `~/Games/NXNative`, modifiable par `defaults write local.nxnative.dashboard WorkspacePath <chemin>`. Valide seulement si le dossier contient `tools/library.py` et `.venv/bin/python` ; sinon message d'erreur, aucun lancement. Pas d'écran de réglages en v1.
- **Contrat du serveur (seam Python) :** la coque lance `<workspace>/.venv/bin/python <workspace>/tools/library.py monitor --stop-on-stdin-eof`, cwd = workspace, stdin = pipe tenu par la coque seule (jamais dupliqué ni hérité ailleurs), stdout/stderr = pipe lu par la coque et recopié dans le journal.
  - La ligne existante `Build monitor: http://127.0.0.1:8767`, imprimée **après** le bind, est le signal de disponibilité. Un code de sortie avant cette ligne = échec de démarrage (port pris ou erreur).
  - Avec `--stop-on-stdin-eof`, un thread lit stdin jusqu'à EOF puis appelle `shutdown()` du serveur ; le processus se termine avec le code 0. Sans l'option, comportement actuel inchangé (`make monitor`, Ctrl+C).
  - Port, hôtes admis, contrôle `Host`/`Origin`, routes et en-têtes : inchangés.
- **Cycle de vie (module Swift `ServerProcess`) :**
  - Avant le lancement : si une connexion TCP à `127.0.0.1:8767` réussit, état « conflit », aucun lancement, rien n'est tué ni adopté.
  - Démarrage : attente de la ligne de disponibilité, délai max 15 s ; sinon arrêt de l'enfant possédé et état « échec » avec la fin du journal.
  - Arrêt normal (Quitter) : `applicationShouldTerminate` répond « plus tard », ferme le côté écriture du pipe, attend ≤ 3 s, puis `SIGTERM` au **seul PID possédé**, attend ≤ 2 s, puis `SIGKILL` à ce PID, puis termine. Jamais de signal à un groupe, jamais `killall`/`pkill`.
  - Mort brutale de la coque : rien côté Swift ; macOS ferme le pipe, le serveur reçoit EOF et s'arrête.
  - Mort inattendue du serveur pendant l'usage : page d'erreur native avec fin du journal et bouton « Relancer le serveur » (refait la vérification de conflit).
- **Fenêtre :** une seule fenêtre WKWebView, data store par défaut (persistant, lié à l'identifiant de bundle), chargement de `http://127.0.0.1:8767/` uniquement après disponibilité.
  - `applicationShouldTerminateAfterLastWindowClosed` = faux ; réouverture par le Dock (`applicationShouldHandleReopen`) réaffiche la fenêtre.
  - Instance unique : comportement LaunchServices par défaut (une 2ᵉ ouverture active la 1ʳᵉ) ; une 2ᵉ instance forcée (`open -n`) tombe sur l'état « conflit » sans toucher à la 1ʳᵉ.
- **Politique de navigation (module Swift pur `NavigationPolicy`) :** décision par URL → `allow` | `openExternally` | `deny`.
  - `allow` : schéma `http`, hôte `127.0.0.1`, port 8767 (exactement l'origine chargée).
  - `openExternally` (navigateur par défaut via `NSWorkspace`) : `https` vers un autre hôte, seulement sur action utilisateur ; les demandes de nouvelle fenêtre (`target=_blank`, `window.open`) suivent la même règle et ne créent jamais de WebView.
  - `deny` : tout le reste (`file:`, `javascript:`, `http` externe, `localhost`, autres ports…).
- **Aucun pont JS natif :** pas de `WKScriptMessageHandler`, pas de schéma personnalisé, pas de commande shell exposée. Copier une commande Make passe par l'API presse-papiers web existante ; si WebKit la refuse, c'est noté, pas contourné.
- **ATS :** `NSAppTransportSecurity` avec seulement `NSAllowsLocalNetworking = true` ; pas de `NSAllowsArbitraryLoads`.
- **Construction :** paquet SwiftPM (cible bibliothèque `ServerProcess` + `NavigationPolicy`, cible exécutable, tests XCTest) ; `make app` assemble `dist/NXNative Dashboard.app` (Info.plist écrit à la main, `codesign --sign -` ad hoc), `make dmg` produit `dist/NXNative Dashboard.dmg` via `hdiutil create`. `dist/` et `.build` SwiftPM ignorés par Git. Architecture arm64 seulement.
- **Contenu du DMG :** allowlist = le seul `.app` (et éventuellement un alias vers `/Applications`). `make dmg` échoue si l'app contient autre chose que l'exécutable de la coque, son `Info.plist` et ses ressources de signature.

## Testing Decisions

- Un bon test vérifie un comportement observable (processus vivant/arrêté, port écouté, URL acceptée/refusée), jamais un détail interne.
- **Seam 1 — contrat serveur (Python, `make test`) :** test unitaire d'un serveur sur port 0 avec un pipe : fermer le pipe arrête `serve_forever` en moins de 3 s ; sans l'option, rien ne lit stdin. Test de la ligne de disponibilité imprimée après bind. Prior art : `tools/build-monitor/test_monitor.py` (serveurs sur port 0, `HTTPConnection`).
- **Seam 2 — `ServerProcess` (XCTest via `swift test`) :** contre un faux serveur (petit script fourni par le test, pas le vrai dashboard) : disponibilité, échec avant disponibilité, délai dépassé, conflit de port détecté sans lancement, arrêt par EOF, repli SIGTERM puis SIGKILL limité au PID possédé, un processus non lié lancé par le test survit.
- **Seam 3 — `NavigationPolicy` (XCTest) :** table d'URL → décision, incluant les refus (`localhost:8767`, `127.0.0.1:8768`, `file:`, `javascript:`, `http://example.com`, nouvelle fenêtre).
- **Seam 4 — recette bout en bout (`make app-test`, sur l'app construite) :** lance l'app par `open`, vérifie que le listener 8767 est l'enfant de l'app ; Quitter → serveur parti ; `kill -9` de l'app → serveur parti sous 5 s ; port pris par un faux serveur → conflit affiché, faux serveur intact ; une session tmux témoin et un processus détaché témoin survivent à chaque cas ; DMG ne contient que l'app. N'ouvre aucun vrai jeu.
- **Contrôle visuel (coordination) :** captures de la fenêtre (dashboard, conflit, workspace invalide) relues ; vérification manuelle de la persistance des préférences après relance et de l'ouverture d'un lien `https` dans le navigateur.

## Out of Scope

- Python embarqué (PyInstaller), autonomie sans `.venv`, Git ou `source/` (niveaux B et C).
- Developer ID, notarisation, diffusion à d'autres personnes, universal2/Intel.
- Migration du `localStorage` du navigateur vers l'app.
- Console v0.2, refonte visuelle, nouvelles fonctions du dashboard, écran de réglages natif.
- Lancement/pilotage de builds, imports ou nettoyages depuis l'app (inchangés : Make/tmux).
- Changement du port ou d'origine, CORS, ouverture réseau local.
- Démarrage automatique à la session, mise à jour automatique, Tauri, Electron.

## Further Notes

- Interdits pendant l'implémentation : relancer les builds Pokémon, réimporter/purger, toucher `source/` (patch PowerA), `keys/`, `games/`, `apps/`, `.build/` des jeux ; tuer un processus non possédé ; push ou publication.
- Une app ad hoc copiée depuis un DMG local n'a normalement pas d'attribut de quarantaine ; si Gatekeeper bloque malgré tout, ne pas désactiver la sécurité macOS : le noter et ouvrir via clic droit → Ouvrir.
