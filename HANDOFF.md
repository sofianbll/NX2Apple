# Relais NXNative — 2026-11-04

## Objectif et limites

Construire une belle ludothèque Mac avec deux vues, **Cinéma et Console**, harmonisées par une seule bibliothèque Web Components. Pour l'instant : expérience et dashboard uniquement. Le dashboard réel reste **gelé** : aucune intégration sans validation visuelle explicite de Sofian. Ne pas lancer de build, import, transfert Drive ou nettoyage sans demande. Conserver caches, sauvegardes, clés, applications, correctif PowerA et Xcode. Les builds longs passent par tmux ; vérifier l'état réel avant toute action.

## Décisions de Sofian

- Une seule implémentation de chaque composant pour les deux vues : fini les copies HTML qui divergent.
- Mêmes couleurs, boutons, pills, icônes, animations et ratios dans Cinéma et Console ; Console adapte seulement l'ergonomie TV/manette.
- Toutes les pochettes d'une rangée ont le même ratio. Un réglage de vue, la manette et le lancement direct des jeux viendront plus tard.
- Utiliser les sous-agents **Kimi K3.1 Pro Highspeed** (`kimi-code-plan-global/k3.1-pro-highspeed`) et déléguer en parallèle.
- Validations avec OpenUI lorsque possible ; le visuel au pixel près reste en HTML/captures. Ne jamais concaténer la note utilisateur dans le `summary` (500 caractères max) : note complète dans `data.note`.
- Les références de menus consoles/launchers doivent guider la prochaine refonte, pas une nouvelle variation gratuite.

## Livrables

- `tools/build-monitor/nx-components.js` : `<nx-pill>`, `<nx-tile>`, `<nx-nav>`, `<nx-dock>`, `<nx-build-card>`, export pur `formatBuildProgress`. Shadow DOM ouvert, constructable stylesheets, tokens `--nx-*`, vrais boutons, reduced motion.
- `tools/build-monitor/protos/nx-shared.css` : tokens et styles partagés.
- `tools/build-monitor/protos/components-demo.html` : les mêmes composants rendus en Cinéma et Console, états fictifs.
- `tools/build-monitor/protos/references-ui.md` : 8 références (PS5, Xbox, Switch, Steam, tvOS, Plex/Jellyfin, Playnite/LaunchBox, ES-DE/Pegasus) et 10 règles actionnables. Les durées sont des cibles NXNative, pas des timings constructeur mesurés.
- Prototypes antérieurs dans `tools/build-monitor/protos/` ; assets et provenance dans les dossiers `*-assets/`.

## Vérifications effectuées

- `make test` : **36 tests bibliothèque + 15 tests moniteur, tous réussis**.
- `node --check tools/build-monitor/nx-components.js` : réussi.
- Démo Web Components inspectée dans le navigateur en desktop : tuiles, pills, rail, dock et build card rendus dans les deux sections. Captures : `.openchamber/screenshots/components-demo-ok-desktop-2026-11-04T00-48-09-012.jpg` et `components-demo-console-2026-11-04T00-48-28-638.jpg`.
- Cause du premier échec de la démo : le serveur racine était `protos/`, donc `../nx-components.js` répondait 404. Le serveur doit être lancé avec `--directory tools/build-monitor` et la page ouverte sous `/protos/components-demo.html`.

## Validations visuelles et gates

- Validés par Sofian : Cinéma bloc 1 (rail + bannière), Cinéma bloc 2 (bibliothèque), Console en-tête + carrousel initial.
- Le dock Console initial a reçu « demander des corrections » avec exigence d'harmonisation.
- Les écrans complets ultérieurs ne sont **pas validés**. Cinéma était « quasi parfait » après corrections de pills/hover, mais Console a ensuite été rejetée et Sofian a imposé la bibliothèque Web Components + recherche de références.
- La nouvelle démo de composants est vérifiée par le coordinateur, **pas encore validée par Sofian**. Ne pas l'intégrer au dashboard réel.

## Builds et processus au moment du relais

- Zelda 1.1.0 : build **tué explicitement par Sofian** à la dernière progression observée **1 756 / 9 698 shaders**. Le cache est conservé. Le dashboard `/status` a ensuite indiqué `stopped`. Ne pas relancer sans demande.
- Mario Kart 8 Deluxe : application existante ouverte pour test par Sofian ; résultat du test inconnu. Ne pas reconstruire.
- Les tentatives de pause SIGSTOP n'ont pas tenu dans cet environnement ; le groupe de build a finalement été tué avec SIGTERM. La fenêtre tmux `builds` a disparu avec le groupe ; la recréer seulement pour une reprise demandée.
- Dashboard réel : tmux `nxnative`, fenêtre `dashboard`, http://127.0.0.1:8767/.
- Prototypes : fenêtre tmux `prototypes` prévue sur le port **8768**, racine `tools/build-monitor`. Vérifier qu'elle tourne avant de la recréer.
- `source/` reste un checkout Git amont séparé ; le correctif local PowerA `dm/host/pad_hid_mac.h` est conservé, non commité ici et ne doit pas être supprimé.

## Prochaines actions

1. Rechecker `git status`, tmux, `/status` et les fichiers livrés ; ne présumer ni build actif ni validation utilisateur.
2. Montrer à Sofian `http://127.0.0.1:8768/protos/components-demo.html` et la synthèse de `references-ui.md` ; recueillir son verdict avec OpenUI.
3. Sur cette base, reconstruire les deux écrans avec `nx-components.js` et les règles de références retenues. Vérifier soi-même les captures avant présentation.
4. Corriger les assets finaux : les crops actuels contiennent encore des badges cuits dans l'image. Les pills HTML les masquent provisoirement ; obtenir des pochettes propres avant les statuts dynamiques en production.
5. N'intégrer au dashboard réel qu'après validation explicite des nouveaux écrans. Manette, lancement direct et réglages de vue restent des étapes ultérieures.

## Risques et points à revérifier

- Aucun résultat de gameplay Mario reçu.
- La démo n'est pas une mise en page finale : hero simplifié et carrousel de démonstration.
- Les références contiennent des liens sources, mais les durées d'animation proposées ne sont pas des mesures constructeur.
- Le serveur de prototypes ne couvre que `127.0.0.1` et ne doit jamais servir clés, jeux ou caches.
- Aucun transfert Drive, nettoyage, suppression de cache ou changement moteur autorisé par ce relais.
- Commit local demandé par la garde du contexte ; aucun remote/push demandé. Voir `git log -1` pour l'identifiant exact.
