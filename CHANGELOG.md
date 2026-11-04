# Changelog

Versions selon `ROADMAP.md`. Dates en Europe/Paris.

## [Non publié]

- Navigation à la manette dans la vue Cinéma (v0.2.1) : croix et stick gauche entre les pochettes, bouton du bas = le même bouton **Jouer** (jamais de lancement à la simple sélection), bouton de droite = fermer la fiche ou revenir. Mapping standard W3C, par position.
- Icône de l'app Mac (manette lumineuse sur fond violet cosmique), `tools/desktop-app/AppIcon.icns`.
- App Mac `NXNative Dashboard.app` fusionnée dans `main` (`make app`, `make dmg`, `make app-test`) : fenêtre WKWebView confinée à `127.0.0.1:8767`, serveur lancé par l'app et arrêté à Quitter ou en cas de crash (`--stop-on-stdin-eof`), DMG non notarisé (« Ouvrir quand même »). `swift test` ne peut plus bloquer (attentes bornées). Le tag `v0.2.0` sera posé après le test à la main de Sofian.

## [0.1.1] — 2026-11-04

- Relais de sessions et Goal nocturne archivés dans `docs/archive/`.
- Ajout de `ROADMAP.md` et de ce changelog.
- Les `game.json` et états JSON corrompus ou incomplets ne bloquent plus tout le dashboard.
- Le message de verrou occupé est réservé aux vrais conflits d’opération.
- `make test` exige Node.js et affiche les sorties des tests JavaScript en cas d’échec.
- Ajout de la sonde manette R/ZR en lecture seule et de sa cible `make rzr-probe`.
- README corrigé pour les tests, les ressources `protos/` utilisées et la taille des visuels.

## [0.1.0] — 2026-11-04

- Dashboard **Cinéma** réel sur `127.0.0.1:8767`, construit avec les Web Components partagés (`nx-components.js`, `nx-shared.css`).
- Bibliothèque et catalogue en grille de pochettes 1:1, recherche, filtres, fiches de profil en lecture seule.
- Bouton **Jouer** : `POST /play` même origine, ouvre seulement une app déjà construite.
- Réglages natifs limités aux options du bundle ; menu natif au lancement par titre (`--no-launcher`).
- Statut d'exécution (`nxnative` / `dmhost`) séparé du statut de build.
- Thème violet cosmique ; liens de téléchargement privés dans le `localStorage`.
- Jeux construits : FireRed (6 éditions), Mario Kart 8 Deluxe, Zelda Link's Awakening, Stardew Valley (jouables, confirmés par Sofian) ; Légendes Pokémon Z-A et Perle Scintillante (compilés et signés, gameplay non vérifié).
