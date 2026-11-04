# Feuille de route NXNative

Validée par Sofian le 2026-11-04. Une version n'est close que lorsque tous ses critères sont vrais et le tag posé.
Ce qui n'est pas listé ici est hors périmètre jusqu'à nouvelle décision.

## v0.1.0 — Dashboard Cinéma (tag `v0.1.0`, `a77506c`) ✅

Bibliothèque Cinéma sur `127.0.0.1:8767` : pochettes, catalogue, bouton Jouer, réglages natifs. Voir `CHANGELOG.md`.

## v0.1.1 — Ménage

- [ ] Relais et Goal archivés dans `docs/archive/` ; `CHANGELOG.md` et cette feuille de route à la racine.
- [ ] Un `game.json` ou un état JSON abîmé n'arrête plus tout le dashboard.
- [ ] « Verrou occupé » distingué des autres erreurs.
- [ ] `make test` échoue clairement si Node manque.
- [ ] Sonde R/ZR rangée dans le dépôt (elle était dans un dossier temporaire).
- [ ] README à jour (tests, `protos/` encore utilisé à l'exécution).
- [ ] `make test` vert, tag `v0.1.1`.

## v0.2.0 — App Mac (`NXNative Dashboard.app`, DMG)

Spec : `.scratch/macos-app/` sur la branche `desktop-app`.

- [ ] `swift test` se termine toujours (plus de processus `xctest` bloqué).
- [ ] Corrections après revue testées et commitées sur `desktop-app`.
- [ ] `make test`, `swift test`, `make dmg` verts.
- [ ] `make app-test` lancé **avec l'accord de Sofian, quand il n'utilise pas le Mac** : il pilote des fenêtres.
- [ ] Fusion dans `main` (accordée par Sofian si tout est vert), tag `v0.2.0`.
- [ ] Installation par Sofian depuis le DMG (« Ouvrir quand même »).

## v0.3.0 — Vue Console

Vue TV et manette, à partir des prototypes `tools/build-monitor/protos/`. Cadrage à faire avant tout code.

## En attente de Sofian (hors version)

- Appuis physiques R puis ZR sur la manette PowerA : aucune correction de mapping sans ce relevé.
- Premier lancement en jeu de Z-A et de Perle (Perle vient d'un profil provisoire).

## Gelé

- N64 : 1 NRO trouvé sur 73, pas de nouvel essai sans diagnostic.
