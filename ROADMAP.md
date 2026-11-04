# Feuille de route NXNative

Validée par Sofian le 2026-11-04. Une version n'est close que lorsque tous ses critères sont vrais et le tag posé.
Ce qui n'est pas listé ici est hors périmètre jusqu'à nouvelle décision.

## v0.1.0 — Dashboard Cinéma (tag `v0.1.0`, `a77506c`) ✅

Bibliothèque Cinéma sur `127.0.0.1:8767` : pochettes, catalogue, bouton Jouer, réglages natifs. Voir `CHANGELOG.md`.

## v0.1.1 — Ménage (tag `v0.1.1`, `8e93867`) ✅

- [x] Relais et Goal archivés dans `docs/archive/` ; `CHANGELOG.md` et cette feuille de route à la racine.
- [x] Un `game.json` ou un état JSON abîmé n'arrête plus tout le dashboard.
- [x] « Verrou occupé » distingué des autres erreurs.
- [x] `make test` échoue clairement si Node manque.
- [x] Sonde R/ZR rangée dans le dépôt (elle était dans un dossier temporaire).
- [x] README à jour (tests, `protos/` encore utilisé à l'exécution).
- [x] `make test` vert, tag `v0.1.1`.

## v0.2.0 — App Mac (`NXNative Dashboard.app`, DMG)

Spec : `.scratch/macos-app/`. Fusionnée dans `main` le 2026-11-04 (`f592f23`).

- [x] `swift test` se termine toujours (plus de processus `xctest` bloqué).
- [x] Corrections après revue testées et commitées sur `desktop-app`.
- [x] `make test`, `swift test`, `make dmg` verts.
- [ ] Test à la main par Sofian (remplace `make app-test`, qui pilote des fenêtres) : ouverture, Quitter, Dock, liens, préférences gardées.
- [x] Fusion dans `main`.
- [ ] Tag `v0.2.0` après le test de Sofian.
- [ ] Installation par Sofian depuis le DMG (« Ouvrir quand même »).

## v0.2.1 — Manette dans la vue Cinéma

API Gamepad standard du navigateur (app Mac et navigateur), dans `nx-components.js` (événement `nx-pad`) et `index.html`.

- [x] Croix et stick gauche : passer d'une pochette à l'autre (bibliothèque et catalogue), même sélection que le clavier.
- [x] Bouton du bas (A en mapping standard) : clique le bouton **Jouer** lui-même ; rien ne se lance à la simple sélection.
- [x] Bouton de droite (B standard) : ferme la fiche ouverte, sinon revient à la bibliothèque.
- [x] Tests Node sans UI (mapping, appuis uniques, A passe par le bouton), `make test` vert, preuve headless.
- [x] Manette non standard ignorée (1er test de Sofian : boutons muets, sélection qui bouge en secouant). La PowerA (0000:0000) n'est sans doute pas reconnue par WebKit.
- [x] Diagnostic `#manette` : WebKit ne voit pas du tout la PowerA, comme GameController pour nxnative.
- [x] L'app Mac lit les manettes que WebKit ne voit pas en HID direct (même règle et mêmes numéros que `pad_hid_mac.h` de nxnative : bouton 2 = A, 1 = B, croix, stick X/Y ; capteurs ignorés), seulement quand sa fenêtre est au premier plan. `swift test` 15/15.
- [ ] Test de Sofian avec sa manette PowerA, dans l'app : mapping par position, sur une manette Nintendo le bouton du bas porte la lettre B. À inverser si Sofian préfère la convention Nintendo.
- [ ] Tag `v0.2.1` après son retour.

## v0.3.0 — Vue Console

Vue TV et manette, à partir des prototypes `tools/build-monitor/protos/`. Cadrage à faire avant tout code.

## En attente de Sofian (hors version)

- Appuis physiques R puis ZR sur la manette PowerA : aucune correction de mapping sans ce relevé.
- Premier lancement en jeu de Z-A et de Perle (Perle vient d'un profil provisoire).

## Gelé

- N64 : 1 NRO trouvé sur 73, pas de nouvel essai sans diagnostic.
