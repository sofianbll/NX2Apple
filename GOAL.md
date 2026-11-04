# Goal NXNative — réveil v0.1

**Statut : APPROUVÉ par Sofian le 2026-11-04 (Europe/Paris), via OpenUI, choix « Valider le Goal complet, essai Perle inclus », sans note.**

Activation native **confirmée par la coordination** : `session.send` a répondu `goalEnabled: true` et `promptDispatched: true` pour cette session. Le Goal est en cours ; ne pas le réactiver après une reprise.

## Résultat attendu

Partir de la **v0.1 déjà intégrée**, sans refonte, et laisser au réveil :

- les deux Pokémon rangés/importés puis construits séquentiellement si leurs entrées et l’espace le permettent ;
- un batch de rangement/purge probant, avec **au moins 25 Gio libres à la fin si c’est matériellement possible** ;
- les améliorations bornées du dashboard et une sonde PowerA prête, sans réglage appliqué ni lancement réel pendant les tests ;
- un compte rendu français : quoi utiliser demain, preuves, espace avant/après et blocages restants.

Console v0.2, N64, transferts Drive et téléchargements automatiques de jeux sont hors objectif. Aucun commit/push non demandé, aucune nouvelle wiki.

## Contexte à charger

- **État et décisions existants** : lire `HANDOFF.md` avant toute action ; pour ce Goal seulement, les bornes approuvées ici lèvent le gel dans leur périmètre exact.
- **Import, build et stockage** : suivre `README.md` et le `Makefile`, notamment les protections des téléchargements et le verrou `operation()`.
- **Travail dans `source/`** : lire `source/AGENTS.md` d’abord, puis la note du profil concerné s’il existe.
- **Runtime, HUD et réglages** : lire `source/docs/frontends.md`, `source/docs/launcher.schema.json` et `source/dm/games/settings.tsv` avant d’implémenter ; le bundle de chaque app reste la source des options réellement offertes.

## Étapes et critères de sortie

### 1. Réconcilier l’état, en lecture seule

Recouper le dernier état utilisateur, les rapports des autres agents, `git status`, tmux, `/status`, `df` et les fichiers sources. Ne pas dupliquer un audit déjà fait ni présumer qu’un processus est actif. Identifier les entrées, écrivains ouverts, métadonnées et copies candidates avant toute mutation.

**Terminé quand** : chaque action envisagée a une source, une destination, une taille et des vérifications associées ; les téléchargements actifs et conflits éventuels sont explicitement bloquants.

### 2. Ranger uniquement les deux Pokémon

- **Perle Scintillante** — Title ID `010018E011D92000` : base et update encore en `.part` au relais. N’y toucher qu’après fin complète du téléchargement, disparition des marqueurs partiels, taille/mtime stables depuis **strictement plus de 60 s** et absence d’écrivain ouvert.
- **Légendes Pokémon Z-A** — Title ID `0100F43008C44000` : base, update **v393216 = 2.0.2** et **DLC 2** disponibles.
- Utiliser le flux d’import existant. « Déplacer les autres » signifie uniquement les NSP extraits complets de ces deux Pokémon et leurs assets/header associés vers `games/`, après intégrité ; jamais un `.part` ou une source encore ouverte/modifiée.

**Terminé quand** : pour chaque jeu prêt, `make list` et les reçus confirment les composants attendus dans `games/` ; sinon le jeu reste intact et le blocage est daté et prouvé.

### 3. Purger un manifest borné, sous verrou

Sous `operation()`, revérifier descripteurs ouverts et métadonnées sources **avant chaque mutation**. Établir et évaluer le manifest complet avant le premier `unlink` : chemin, action, taille, preuve CRC/listing, copie destination vérifiée et caractère non unique. Le volume total d’archives supprimées dans ce batch doit rester **strictement inférieur à 25 Gio**.

- Purge définitive limitée aux archives de **jeux déjà extraites**, avec preuve CRC et copie terminée/vérifiée vers `games/`. Les NSP originaux complets ne sont déplacés qu’après ce contrôle d’intégrité.
- Candidats déjà comparés par CRC, à revérifier avant mutation : trois RAR Z-A, environ **6,02 Gio** au total, et le petit RAR d’update **Zelda 1.1.0**, environ **38 Mio**.
- Les anciens originaux `inbox/imported/`, **au plus 17,5 Gio**, ne sont purgeables qu’après validation complète de leurs copies et des archives des quatre familles dont les apps sont connues jouables : les six éditions FireRed, Mario Kart, Zelda et Stardew.
- Aucun original unique, sans copie validée ou incertain ne passe à `unlink`. Préserver intégralement N64, les autres fichiers non-jeu de Downloads et le dossier ProdKeys lié. Aucune nouvelle suppression de clés, sauvegardes, apps, shaders, PSO, états ou caches.

**Terminé quand** : chaque suppression correspond à une ligne prévalidée du manifest, les exclusions sont intactes, les destinations sont relues et `df` est mesuré après l’opération. Si le manifest dépasse la borne ou laisse un doute, ne pas purger cet élément et le signaler.

### 4. Construire les deux Pokémon, un seul à la fois

Avant **chaque** build, exiger :

```text
espace_libre >= max(25 Gio, 2 × taille_des_entrées_du_jeu + 10 Gio)
```

Si la marge manque, ne pas lancer le build et rendre compte. Sous **15 Gio libres**, arrêter seulement notre propre build si nécessaire, préserver les caches et consigner l’événement ; ne jamais arrêter un jeu ou téléchargement de Sofian.

- Builds dans tmux `nxnative:builds`, séquentiels ; tmux survit à une déconnexion, **pas à un reboot**. Revérifier l’état réel après tout reboot.
- Z-A : pipeline officiel pour **2.0.2**, avec update v393216 et DLC 2 importés.
- Perle : **un seul essai** `EXPERIMENTAL=1` autorisé, uniquement via le workflow officiel de profil dérivé/provisoire.
- Aucun `make all`, aucun rebuild des quatre familles existantes, aucun contournement d’intégrité ou du compilateur.
- Un échec de build stoppe ce build pour la même cause ; aucun retry aveugle. Perle n’a droit qu’à son essai unique.

**Terminé quand** : chaque jeu a soit un build géré réussi et une app présente, soit un blocage/échec documenté avec tentative, cause et preuve. `build done` ou `codesign` vérifié **ne signifie pas gameplay validé**.

### 5. Livrer les améliorations dashboard autorisées

- **Runtime** : distinguer le launcher/menu `nxnative` du moteur `dmhost`, et lire `build.state` séparément. Le statut de build et le statut « jeu ouvert » restent deux états distincts.
- **Réglages** : exposer seulement les options réellement présentes dans `Contents/Resources/dm/launcher.json` / `DMSettings` du bundle, y compris HUD Metal ou FPS lorsqu’elles existent. Ne jamais proposer 30/60 FPS si l’app ne les offre pas. Valeurs strictement validées ; aucun mécanisme d’environnement ou d’exécution générique.
- **Menu au prochain lancement** : option explicite persistée localement par le dashboard et documentée. Elle détermine seulement l’usage de `--no-launcher` ; pas de modification du bundle, pas de `codesign`, pas d’écriture des préférences de l’app par défaut.
- Conserver les protections URL, même origine et CSRF existantes. **Aucun réglage n’est changé sans clic de Sofian.** Tests avec mocks/headless, sans lancer un vrai jeu.
- Pour un bug UI : au maximum **deux cycles** diagnostic → correctif → vérification, puis arrêt et rapport.

**Terminé quand** : les tests couvrent la séparation launcher/`dmhost`/build, la validation des options et la persistance ; aucun lancement réel ni changement de préférence n’a eu lieu, et les captures 720 px et 360 px ont été **relues visuellement**.

### 6. Préparer PowerA sans deviner

Fournir le diagnostic et une sonde prête pour relever les appuis physiques **R puis ZR**. L’absence de ce relevé bloque toute correction de mapping ; conserver le correctif existant et ne pas appliquer de patch supposé.

**Terminé quand** : la procédure de relevé est prête et le blocage « appuis physiques Sofian requis » est explicite, sans prétendre que R/ZR est corrigé.

### 7. Vérifier et rendre le relais du réveil

Exécuter les tests ciblés puis `make test`, relire les captures 720/360, et collecter les états d’import/build, preuves de purge et `df` avant/après. Le rapport français distingue **implémenté, vérifié, compilé/signé et gameplay validé**, puis indique ce que Sofian peut utiliser demain et ce qui reste bloqué. Si les 25 Gio ou un autre objectif ne sont pas atteints, le dire sans promesse de remplacement.

**Terminé quand** : chaque résultat ou non-résultat est adossé à une preuve consultable, les limites de vérification sont explicites et aucune action hors périmètre n’a été effectuée.

## Délégation

Une seule session de coordination visible chez Sofian garde les décisions, l’intégration et la vérification. Déléguer les blocs indépendants en batchs bornés à **Kimi K3.1 Pro Highspeed** en primaire, **Sonnet** en secours, sans achat de quota ; signaler toute bascule. Les builds restent séquentiels malgré la délégation.

## Références de version

Constat du 2026-11-04 à revérifier avant action : `source/` upstream à `65501fb`, racine à `f6d231f` avec changements non commités. Ce Goal ne modifie pas ces références et n’introduit aucun hash nouveau.
