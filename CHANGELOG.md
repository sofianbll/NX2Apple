# Changelog

Versions selon `ROADMAP.md`. Dates en Europe/Paris.

## [Non publié]

- Relais de sessions et Goal nocturne archivés dans `docs/archive/`.
- Ajout de `ROADMAP.md` et de ce changelog.

## [0.1.0] — 2026-11-04

- Dashboard **Cinéma** réel sur `127.0.0.1:8767`, construit avec les Web Components partagés (`nx-components.js`, `nx-shared.css`).
- Bibliothèque et catalogue en grille de pochettes 1:1, recherche, filtres, fiches de profil en lecture seule.
- Bouton **Jouer** : `POST /play` même origine, ouvre seulement une app déjà construite.
- Réglages natifs limités aux options du bundle ; menu natif au lancement par titre (`--no-launcher`).
- Statut d'exécution (`nxnative` / `dmhost`) séparé du statut de build.
- Thème violet cosmique ; liens de téléchargement privés dans le `localStorage`.
- Jeux construits : FireRed (6 éditions), Mario Kart 8 Deluxe, Zelda Link's Awakening, Stardew Valley (jouables, confirmés par Sofian) ; Légendes Pokémon Z-A et Perle Scintillante (compilés et signés, gameplay non vérifié).
