# Relais NXNative — 2026-11-04

> **Goal approuvé et actif le 2026-11-04** : périmètre nocturne dans [`GOAL.md`](GOAL.md). Activation native observée (`goalEnabled: true`, `promptDispatched: true`) ; ne pas la répéter. Pour ce Goal seulement, ses bornes datées priment sur les consignes de gel/attente historiques ci-dessous.

## Point de reprise — passation demandée par la garde du contexte

Session suivante **créée, sans prompt au moment de cette rédaction** : `ses_e5b5df55bffeem9Peo7NjuVS7R`, titre `[Jeux] - 🟢 - Nuit Pokémon`, même checkout. Elle reçoit la coordination après le commit local demandé explicitement par la garde ; aucun push. Le Goal nocturne n'est pas terminé : les builds restent à effectuer. Les sections plus basses décrivent l'historique, pas de nouvelles autorisations à demander.

### Vérifié dans cette passe

- **Imports terminés** : Z-A `0100F43008C44000`, trois NSP (base, update `v393216` = 2.0.2, DLC `0100F43008C45002`), slug `pokemon-legends-z-a-0100f43008c44000`, environ 6,01 Gio ; Perle `010018E011D92000`, deux NSP (base, update `010018E011D92800` **v393216** = 1.3.0), slug `pokemon-shining-pearl-010018e011d92000`, environ 7,03 Gio. Perle n'est pas Diamant. Les cinq sources NSP exactes ont été retirées après copie complète identique ; destinations conservées dans `games/`, reçus présents et bornes PFS0 revérifiées par la coordination.
- **Purge effectuée** : seulement `inbox/imported/The-Legend-of-Zelda-Links-Awakening-NSP-Base-Game.rar` (6 467 885 796 octets), test d'archive et CRC des copies réussis. Gain réel de cette passe **5,96 Gio**, libre **22,20 → 28,15 Gio**, puis 28,12 Gio au contrôle indépendant. Budget cumulé archives supprimées : **6,02 Gio sur moins de 25 Gio autorisés**. Rapport privé `.build/storage-goal-report.json`. Ne pas rejouer cette opération ni les six extractions de la passe précédente (gain antérieur séparé : 12,68 Gio).
- **Archives conservées** : les cinq RAR Pokémon et les autres originaux non qualifiés. `7zz t` indique « Unsupported Method » sur les RAR Pokémon : absence de prise en charge, pas preuve de corruption. Ne pas purger sans contrôle complet avec un outil adapté. Le petit RAR Zelda Update110 reste conservé. N64 est entièrement exclu.
- **Code dashboard prêt** : runtime séparé du build ; GET/POST `/settings` limités aux options et valeurs réelles du bundle ; écriture native uniquement après clic, défaut = suppression de clé ; menu local par titre via `--no-launcher`. Aucun réglage natif changé, aucun vrai jeu ouvert. Les sept familles ont une pochette propre, dont Perle (Nlib, provenance locale).
- **Vérifications** : `make test` réussi — 56 tests bibliothèque, 27 moniteur (incluant 46 tests Node frontend), 3 composants ; file nocturne **8 tests**. Lecture native réelle des réglages des quatre apps réussie (11–12 options chacune, runtime arrêté) ; les écritures `defaults` et ouvertures restent mockées. `swiftc -typecheck` de la sonde R/ZR réussi. Les cinq états historiques et `source/dm/host/pad_hid_mac.h` ont les mêmes SHA256 que `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-night-baseline.json`.
- **Rendu vérifié et captures relues à 720 et 360 px** : `.openchamber/screenshots/{cinema,settings,catalogue}-night-{720,360}.png`, sans débordement ni erreur JS. Brouillon conservé après poll/refus, save explicite/relecture, runtime bloquant, menu persistant après reload et lancement intercepté. Rapport `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-night-ui-report.json`, script `nxnative-night-ui-check.cjs` voisin.

### Reprendre dans cet ordre

1. Recontrôler Git, `df`, tmux, processus et `.build/night-goal-20261104.json`. **Aucun build ni reçu de tentative nocturne n'a été lancé/créé dans cette passe.** Les quatre anciens jeux restent à préserver. Le checkout moteur reste `65501fb` avec son seul patch PowerA local.
2. **Recharger le dashboard hérité sur 8767** : les tests d'intégration ont utilisé un serveur isolé et protégé sur 8796, maintenant arrêté. Le processus historique `nxnative:dashboard` n'a pas été redémarré : il sert les nouveaux fichiers statiques mais conserve son ancien backend chargé. Redémarrer seulement ce dashboard, pas les jeux, imports ou téléchargements ; vérifier ensuite GET `/settings`, `/status` et la pochette Perle. Prototypes 8768 laissés intacts.
3. File préparée dans `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-night-builds.py` ; test voisin `test_nxnative_night_builds.py` (8/8). Vérifier notamment le cas d'un enfant ignorant SIGTERM : `stop_owned()` consigne un arrêt incomplet après 35 s, sans SIGKILL ; ne pas prétendre qu'un tel processus serait arrêté. Revalider la marge puis lancer la file finie **dans tmux**, Z-A normal puis Perle expérimental unique. Reçu durable `.build/night-goal-20261104.json`, journal `logs/night-goal-20261104.log`, signal de fin tmux `nxnative-night-20261104-finished`. Avant chaque titre : libre ≥ max(25 Gio, 2×inputs+10 Gio), arrêt de notre seul build sous 15 Gio. À 28 Gio, la marge peut vite manquer : ne pas garantir la fin des deux builds.
4. Si davantage d'espace est nécessaire, poursuivre uniquement les candidats déjà autorisés par `GOAL.md`, après preuves intégrales ; aucune suppression de caches/shaders, apps ou clés. Ne pas relancer un titre ayant déjà une tentative durable.
5. Mettre à jour le résultat réel des builds et le libre final. R/ZR attend les appuis de Sofian au réveil ; aucune correction devinée. Rapport final : compilé/signé n'est pas testé en jeu. Aucun service distant ou production distante touché.

### Sous-agents de cette passe — tous terminés

- `ses_e5b6e5515ffeRiDGiTy2Bzhwe6` : stockage/imports, rapport `.build/storage-goal-report.json`, script temporaire `nxnative_storage_goal.py`.
- `ses_e5b6d0bbfffe3HzbMLXvZX8I1I` : backend `tools/library.py`, `tools/build-monitor/monitor.py` et leurs tests.
- `ses_e5b6c6ee4ffeArfe65lPmaQ4v9` : frontend `index.html`, `test_dashboard.cjs`.
- `ses_e5b6b2fd6ffewCyLlhMypliC7f` : lanceur nocturne et tests temporaires, aucun build réel.

Pas d'agent actif à relancer ; leurs retours sont synthétisés ci-dessus. Les outils Context7 ont refusé les requêtes pour quota mensuel : contrats locaux et documentation officielle embarquée ont servi de référence, sans achat de quota.

## Objectif et limites

Construire une belle ludothèque Mac avec deux vues, **Cinéma et Console**, harmonisées par une seule bibliothèque Web Components. Pour l'instant : expérience et dashboard uniquement. Le dashboard réel était **gelé** (voir « Décision historique » : levé pour Cinéma seul, Console reste gelée). Ne pas lancer de build, import, transfert Drive ou nettoyage sans demande. Conserver caches, sauvegardes, clés, applications, correctif PowerA et Xcode. Les builds longs passent par tmux ; vérifier l'état réel avant toute action.

## Décisions de Sofian

- Une seule implémentation de chaque composant pour les deux vues : fini les copies HTML qui divergent.
- Mêmes couleurs, boutons, pills, icônes, animations et ratios dans Cinéma et Console ; Console adapte seulement l'ergonomie TV/manette.
- Toutes les pochettes d'une rangée ont le même ratio (1:1 en v0.1). Un réglage de vue et la manette viendront plus tard ; le lancement explicite d'apps existantes est livré en v0.1.
- Utiliser les sous-agents **Kimi K3.1 Pro Highspeed** (`kimi-code-plan-global/k3.1-pro-highspeed`) et déléguer en parallèle.
- Validations avec OpenUI lorsque possible ; le visuel au pixel près reste en HTML/captures. Ne jamais concaténer la note utilisateur dans le `summary` (500 caractères max) : note complète dans `data.note`.
- Les références de menus consoles/launchers doivent guider la prochaine refonte, pas une nouvelle variation gratuite.

## Décision historique — jalon v0.1.0 Cinéma (2026-11-04)

Sofian a expressément validé le prototype Cinéma partagé et son intégration, et demande un vrai dashboard utilisable. Cette décision **remplace le gel et les validations ci-dessus pour Cinéma seulement** : le dashboard réel est basé sur `nx-components.js` et `nx-shared.css`, avec `/status`, `/catalog` en direct et `POST /play` (même origine, slug exact, app déjà construite, **sans build** ; app absente = erreur ; sélectionner une tuile ne lance rien, seul le bouton Jouer explicite ouvre l'app). `make run` est inchangé. Console reste un prototype pour v0.2 (dock compacté seulement) ; le rejet antérieur du dock est conservé dans l'historique. Aucun jeu, import ni build n'est lancé par l'UI hormis cette ouverture. Écoute `127.0.0.1` sur Mac uniquement ; Windows non pris en charge.

État du dépôt : worktree sur `f6d231f` + changements **non commités** (aucun nouveau hash). Zelda : `/status` a indiqué `done` après reprise côté Sofian ; ne pas relancer.

Ajout demandé par Sofian (2026-11-04), toujours dans v0.1 : le catalogue est une grille visuelle de pochettes, la même que la bibliothèque (pas un tableau), avec recherche, filtres par propriété et fiches de profil en lecture seule. Assets locaux pour 130 profils (~12 Mo, `art/catalog/`) : 126 pochettes NlibAPI (tiers TitleDB) + 4 captures upstream (`65501fb` : Silver Pines, Splatoon Raiders, DK Bananza, Fire Emblem Fortune's Weave), marquées « pas des pochettes » ; `sources.json` porte le type de source. Récupération manuelle via `tools/build-monitor/fetch_catalog_art.py` ; aucun fetch au runtime, aucun réseau navigateur hors `127.0.0.1`. Console v0.2 : dock 540×116, prototype seulement.

Dernier delta demandé par Sofian (2026-11-04), v0.1 :

- Thème violet cosmique (nuit, nébuleuse, pulsar ; flou décoratif). Pochettes 1:1 réelles de 510 px pour 5 jeux (`/art/catalog` 3 + `/art/library` 2). Fiches 16:9 si l'image est large, 1:1 pour une pochette ; les 4 captures en `contain`. Hero avec Play + colonne de statuts/Détails alignée à 79 px en desktop, responsive mobile.
- Liens Drive/téléchargement HTTPS par Title ID : stockés **uniquement** dans le `localStorage` du navigateur (`nxnative-download-links`) ; pas de backend, Git ni fetch ; ouverture par clic explicite sur « open » ; vider le champ supprime le lien ; non partagés avec un autre navigateur, ni entre les origines `127.0.0.1` et `localhost`. Exception réseau : le navigateur n'émet aucune requête externe **automatique**, mais un lien ajouté par l'utilisateur ouvre un site externe au clic (ne pas affirmer « aucun réseau »).
- Sofian a confirmé explicitement aujourd'hui que 4 apps fonctionnent : Pokémon FR, Mario Kart, Zelda, Stardew. Pas de nouvelle confirmation pour de futurs rebuilds. Suspicion de mapping PowerA RZR non résolue.
- Études en lecture seule (détection du processus `dmhost` ; réglages HUD Metal / menu Startup) : jugées faisables mais **non implémentées dans v0.1**. Le mapping HID utilise par défaut la numérotation 8BitDo ; la correspondance physique PowerA R/ZR nécessite encore un relevé, **aucune correction appliquée**.
- Stockage : après autorisation OpenUI (2026-11-04), les six extractions ciblées ont été supprimées sous verrou `operation()`, après preuve d'autonomie des apps. Gain net mesuré pendant l'opération : **12,68 Gio** (27,36 → 40,04 Gio), et non 30 Gio physiques à cause des clones APFS. Les écritures/téléchargements ultérieurs ont ramené le libre à environ 31 Gio au contrôle de coordination. Apps, sidecars, états et tous les shaders/pipelines inchangés ; les quatre états restent `done`. Rapport : `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nx_cleanup_report.json`. Opération terminée, ne pas la rejouer.
- Nuit Pokémon : inventaire en lecture seule confirmé pour Z-A (`0100F43008C44000` base, update v2.0.2 et DLC 2) déjà extrait dans Downloads, pas encore importé. Trois RAR Z-A (~6,02 Gio) et un petit RAR de mise à jour Zelda (~38 Mio) correspondent par CRC32 aux NSP conservés. Perle Scintillante et sa mise à jour sont encore en `.part` avec écrivains ouverts : les laisser intacts. Les anciens originaux `inbox/imported` (~17,5 Gio) ne sont pas encore validés pour purge. Aucun de ces fichiers n'a été supprimé ni déplacé.
- Sofian a validé « Valider le Goal complet, essai Perle inclus », puis le Goal natif de **cette** session a été activé. [`GOAL.md`](GOAL.md) est le contrat approuvé : tri/purge après preuve, préparation des deux Pokémon, builds tmux séquentiels sous garde-fous d'espace, détection de jeu et réglages natifs bornés. N64 et Console restent exclus ; R/ZR attend les appuis physiques. Sofian a lancé une extraction Keka avant de dormir : laisser toute écriture active finir.

Vérifications finales par la coordination (2026-11-04) : `make test` réussi (43 tests bibliothèque, 23 moniteur dont la suite frontend Node, 3 tests composants), suite Node frontend 33/33 réussie, syntaxe du module et `git diff --check` réussis. Le contrôle de progression garde 99 % pour une fraction strictement inférieure à 1, y compris au voisinage flottant de 1.

Cinéma et catalogue testés en navigateur headless à **1440, 720 et 360 px**, avec captures relues dans `.openchamber/screenshots/{cinema,catalogue}-v010-{1440,720,360}.png` : pochettes carrées chargées, aucune erreur JS ni débordement horizontal, hero et boutons alignés, 130 profils illustrés. Contrôles reproduits : sélection et clavier dans le Shadow DOM, six éditions FireRed, app absente grisée, persistance après rechargement, liens HTTPS enregistrés/refusés/retirés sans requête externe, progression inconnue indéterminée et progression de l'étape courante uniquement. Le bouton Jouer envoie le slug exact dans un test intercepté ; **aucun jeu réellement ouvert par ces essais**. Script reproductible temporaire : `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-v010-check.cjs`.

Dashboard local **en service** dans tmux `nxnative:dashboard` sur `127.0.0.1:8767`, prototypes conservés sur `8768`. Aucun déploiement distant ni commit/push. N64 reste bloqué avant compilation : le dernier essai expérimental trouve 1 NRO sur 73, sans profil enregistré ; ne pas relancer à l'aveugle. Aucun nettoyage/déplacement n'est autorisé sans périmètre et destination clarifiés.

## Livrables

- `tools/build-monitor/nx-components.js` : `<nx-pill>`, `<nx-tile>`, `<nx-nav>`, `<nx-dock>`, `<nx-build-card>`, export pur `formatBuildProgress`. Shadow DOM ouvert, constructable stylesheets, tokens `--nx-*`, vrais boutons, reduced motion.
- `tools/build-monitor/protos/nx-shared.css` : tokens et styles partagés.
- `tools/build-monitor/protos/components-demo.html` : les mêmes composants rendus en Cinéma et Console, états fictifs.
- `tools/build-monitor/protos/references-ui.md` : 8 références (PS5, Xbox, Switch, Steam, tvOS, Plex/Jellyfin, Playnite/LaunchBox, ES-DE/Pegasus) et 10 règles actionnables. Les durées sont des cibles NXNative, pas des timings constructeur mesurés.
- Prototypes antérieurs dans `tools/build-monitor/protos/` ; assets et provenance dans les dossiers `*-assets/`.

## Vérifications effectuées (relais initial, antérieures au jalon v0.1.0)

- `make test` : **36 tests bibliothèque + 15 tests moniteur, tous réussis**.
- `node --check tools/build-monitor/nx-components.js` : réussi.
- Démo Web Components inspectée dans le navigateur en desktop : tuiles, pills, rail, dock et build card rendus dans les deux sections. Captures : `.openchamber/screenshots/components-demo-ok-desktop-2026-11-04T00-48-09-012.jpg` et `components-demo-console-2026-11-04T00-48-28-638.jpg`.
- Cause du premier échec de la démo : le serveur racine était `protos/`, donc `../nx-components.js` répondait 404. Le serveur doit être lancé avec `--directory tools/build-monitor` et la page ouverte sous `/protos/components-demo.html`.

## Validations visuelles et gates (historique — ne plus attendre de validation pour Cinéma)

Section conservée pour mémoire : elle ne contient plus d'instruction d'attente pour Cinéma, déjà validé (voir « Décision historique »). Elle reste valable pour Console v0.2.

- Validés par Sofian : Cinéma bloc 1 (rail + bannière), Cinéma bloc 2 (bibliothèque), Console en-tête + carrousel initial.
- Le dock Console initial a reçu « demander des corrections » avec exigence d'harmonisation.
- Les écrans complets ultérieurs ne sont **pas validés**. Cinéma était « quasi parfait » après corrections de pills/hover, mais Console a ensuite été rejetée et Sofian a imposé la bibliothèque Web Components + recherche de références.
- La nouvelle démo de composants est vérifiée par le coordinateur, **pas encore validée par Sofian**. Ne pas l'intégrer au dashboard réel.

## Builds et processus au moment du relais

- Zelda 1.1.0 : build **tué explicitement par Sofian** à la dernière progression observée **1 756 / 9 698 shaders**. Le cache est conservé. Le dashboard `/status` a ensuite indiqué `stopped` ; après reprise côté Sofian il indique maintenant `done`. Ne pas relancer.
- Mario Kart 8 Deluxe : application existante, ne pas reconstruire (le test initial était sans résultat ; voir la confirmation des 4 apps plus haut).
- Les tentatives de pause SIGSTOP n'ont pas tenu dans cet environnement ; le groupe de build a finalement été tué avec SIGTERM. La fenêtre tmux `builds` a disparu avec le groupe ; la recréer seulement pour une reprise demandée.
- Dashboard réel : tmux `nxnative`, fenêtre `dashboard`, http://127.0.0.1:8767/.
- Prototypes : fenêtre tmux `prototypes` prévue sur le port **8768**, racine `tools/build-monitor`. Vérifier qu'elle tourne avant de la recréer.
- `source/` reste un checkout Git amont séparé ; le correctif local PowerA `dm/host/pad_hid_mac.h` est conservé, non commité ici et ne doit pas être supprimé.

## Prochaines actions

Cinéma v0.1 est intégré et vérifié (voir « Décision historique »). Suites restantes :

1. Rechecker `git status`, tmux, `/status` et les fichiers livrés ; ne présumer aucun build actif.
2. Stockage : faire confirmer suppression ciblée ou destination externe avant toute mutation ; garder les shaders/pipelines, apps, sauvegardes, clés et téléchargements ZA en cours. Un déplacement sur le même volume ne libère pas d'espace.
3. PowerA : la sonde ARM64 `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/rzr-probe` est prête ; sa source `.swift` passe `swiftc -typecheck`. La lancer au réveil, puis appuyer seulement sur R et ZR quand demandé (aucun autre contrôleur utilisé). Aucun relevé physique ni correctif R/ZR n'a été effectué ; le patch PowerA existant est conservé.
4. N64 : diagnostiquer les 72 NRO absents avant un nouveau build ; aucun essai nocturne lancé.
5. Console (v0.2) : reprendre les prototypes avec `nx-components.js` ; le dock prototype fait 540×116 ; validation de Sofian requise avant intégration. Manette et réglages de vue restent ultérieurs.

Les assets `/art` de production sont propres : le problème de badges cuits ne concerne que les anciens prototypes.

## Risques et points à revérifier

- Aucun résultat de gameplay Mario reçu.
- La démo n'est pas une mise en page finale : hero simplifié et carrousel de démonstration.
- Les références contiennent des liens sources, mais les durées d'animation proposées ne sont pas des mesures constructeur.
- Le serveur de prototypes ne couvre que `127.0.0.1` et ne doit jamais servir clés, jeux ou caches.
- Aucun transfert Drive, nettoyage, suppression de cache ou changement moteur autorisé par ce relais.
- Commit local demandé par la garde du contexte ; aucun remote/push demandé. Voir `git log -1` pour l'identifiant exact.
