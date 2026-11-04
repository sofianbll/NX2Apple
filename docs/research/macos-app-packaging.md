# NXNative : application macOS distribuée en DMG

**Recherche seulement — 4 novembre 2026.** Aucune implémentation, compilation, installation, exécution du serveur ou inspection des jeux/clés n’a été effectuée. Les constats de code fournis par le coordinateur sont repris sans refaire leur audit. Les sources externes sont primaires : documentation Tauri 2, code officiel Tauri, documentation Python/PyInstaller et Apple.

## Réponse courte

**Oui, NXNative peut devenir une application `.app` distribuée en `.dmg`, avec le serveur Python intégré, mais ce n’est pas une simple conversion du dossier actuel en DMG.** L’effort est **moyen** : il faut figer Python, rendre les chemins du workspace explicites, traiter la dépendance à Git/`source/`, écrire la coque et prouver le cycle de vie ainsi que la signature/notarisation.

**Recommandation Mac-only : une petite coque Swift/AppKit/WKWebView, conservant le backend Python et chargeant l’UI existante depuis `http://127.0.0.1:8767`.** Tauri 2 est techniquement adapté et fournit déjà le DMG, mais apporte ici surtout une chaîne Rust, un plugin shell et des règles de cycle de vie supplémentaires, sans besoin multiplateforme qui les justifie. Le nom pressenti « Torii » est traité comme l’hypothèse **Tauri 2**, pas comme une certitude ni comme un choix déjà validé.

La première version devrait être limitée au **launcher/monitor et à l’ouverture des apps déjà construites**, pas au pipeline de build. Deux niveaux d’autonomie doivent être distingués :

- **V1 attachée au workspace actuel — recommandée pour réduire le périmètre.** Le DMG n’a pas besoin de Python/Homebrew pour exécuter le backend figé, mais le monitor conserve sa dépendance fonctionnelle au workspace, à Git et au checkout `source/`. Il n’est donc **pas portable tel quel sur un Mac vierge**.
- **Launcher réellement autonome — étape ultérieure.** Il faut découpler les métadonnées moteur/profils de Git et de `source/`, par exemple avec des métadonnées versionnées produites au packaging, tout en laissant jeux, apps, caches et données à l’extérieur du DMG.

**Aucune des deux coques ne peut, à elle seule, garantir l’arrêt du serveur après un crash ou `SIGKILL`.** La solution proposée est un canal de contrôle : le serveur surveille la fin d’un pipe détenu par la coque et s’arrête lui-même quand le noyau ferme ce canal, y compris lorsque la coque disparaît brutalement. C’est une architecture à tester, pas un comportement déjà vérifié dans NXNative.

## 1. Périmètre réel du produit

### Constats locaux vérifiés ou fournis

Le README décrit un dashboard uniquement local sur `127.0.0.1:8767`, une UI en Web Components sans dépendance frontend, des apps existantes ouvertes sans rebuild et un arrêt du dashboard qui n’arrête pas un build ([README.md, § Live build monitor](../../README.md#live-build-monitor), [§ Play](../../README.md#play)). Les builds longs sont confiés à une session tmux détachée ; cette session survit à une déconnexion, pas à un reboot ([README.md, lignes 210-214](../../README.md#live-build-monitor)).

Les constats locaux fournis pour cette recherche, non rejoués ici, sont :

- `tools/library.py:21` : `ROOT = Path(__file__).resolve().parents[1]`. Le root actuel est donc déduit du code source, pas d’une configuration installée.
- `monitor.py:117` : `GAMES_README` dépend du checkout `source/` ; `monitor.py:152` : les fichiers statiques sont relatifs au module.
- `library.py:300-309` : `source_stamp` appelle `git rev-parse`, `git diff` et `git ls-files` ; `snapshot:472-479` l’utilise à chaque polling. **Figer Python ne supprime donc pas la dépendance à Git et au checkout.**
- `monitor.py:143/210/261-273` : les hôtes admis sont `127.0.0.1:8767` et `localhost:8767`, et `Origin` doit être `http://<hôte>`. Une UI servie depuis un protocole Tauri, `file://` ou une autre origine remettrait en cause les POST same-origin actuels.
- `index.html` utilise `localStorage` pour la sélection, les liens privés et le menu. Les données d’un navigateur ne migrent pas automatiquement vers une WKWebView ; changer de port change aussi l’origine.
- Les jeux ouverts via `/usr/bin/open` et les builds tmux doivent continuer après la fermeture du dashboard.

### Ce que le DMG doit contenir

**Proposition de contenu, exhaustive pour la v1 :**

- la coque `.app` Swift ou Tauri ;
- un backend Python minimal figé avec ses modules et ressources strictement nécessaires ;
- les ressources UI nécessaires, dont les visuels explicitement allowlistés par le serveur ;
- les métadonnées non sensibles indispensables au mode choisi, sans recopier le checkout moteur.

**Données externes configurées, jamais absorbées dans le bundle :** racine du workspace, `games/`, `apps/`, `source/`, `.build/`, logs et autres données d’état nécessaires au monitor.

**Exclus du DMG :** jeux, clés, apps construites, `source/`, `.venv`, caches, sorties de build, SDK .NET, Xcode/Metal Toolchain, tmux, environnements Homebrew et secrets de signature. Le README impose déjà que jeux, clés, applications, checkout, environnements et caches restent hors Git et que les clés ne soient pas exposées ([README.md, lignes 65-67 et 90-98](../../README.md#import-safely)).

### Limite launcher / moteur

Le **launcher autonome en Python** n’est pas un **moteur NXNative empaqueté**. La v1 peut afficher le workspace et ouvrir des apps existantes ; le README confirme que l’ouverture d’une app déjà construite ne demande pas Xcode ([README.md, lignes 122-127](../../README.md#build-without-repeating-work)). En revanche, construire ces apps continue à exiger le checkout moteur, ses outils et ses caches, notamment .NET, Xcode/Metal et les dépendances système déjà documentées ([README.md, § Storage and scope](../../README.md#storage-and-scope)). Le DMG ne doit prétendre ni inclure ce toolchain, ni rendre les builds autonomes, ni transporter les jeux et leurs clés.

## 2. Backend Python sans installation Python/Homebrew

### Faits PyInstaller

PyInstaller collecte l’interpréteur Python actif, les modules et les bibliothèques nécessaires ; l’utilisateur n’a alors besoin d’installer ni Python ni modules. La sortie est propre au système et à l’environnement Python de construction, pas universelle à tous les OS ([P1]). Sur macOS, PyInstaller cible par défaut l’architecture courante ; `universal2` est possible seulement avec un environnement et des binaires collectés compatibles. Fusionner deux exécutables PyInstaller avec `lipo` n’est pas une méthode valide ([P4]).

**Conséquence vérifiée :** les deux coques peuvent supprimer la dépendance d’exécution à une installation Python/Homebrew. Elles peuvent produire des artefacts par architecture, ou un artefact `universal2` seulement si toute la chaîne figée le permet et si ce résultat est testé. Aucun poids ni délai de démarrage n’est estimé ici.

PyInstaller redéfinit aussi `__file__` vers l’intérieur du bundle figé ; `sys._MEIPASS` identifie ce répertoire interne ([P2]). Le calcul actuel `ROOT = Path(__file__).resolve().parents[1]` pointerait donc vers les ressources figées, **pas** vers `/Users/sofian/Games/NXNative`.

**Proposition indispensable :** séparer deux racines :

1. une racine de ressources en lecture seule, compatible avec le bundle et les fichiers statiques du module ;
2. une racine de workspace externe, passée explicitement au backend par configuration/argument validé, jamais déduite de l’emplacement du binaire figé.

PyInstaller permet d’ajouter des données avec `--add-data` et de choisir leur destination dans le bundle ([P3]). Cela traite les ressources UI, mais ne résout ni les jeux externes, ni `source/`, ni Git.

### Le point qui empêche encore de dire « autonome »

Même avec un Python figé, le polling actuel appelle Git dans le checkout `source/` à chaque snapshot. Un Mac sans Git, ou sans ce checkout, ne peut pas fournir le même statut moteur. Il faut donc choisir explicitement :

- **attaché au workspace (v1 minimale)** : documenter Git + `source/` comme prérequis fonctionnels, sans emballer ce checkout ;
- **portable (cible ultérieure)** : remplacer la lecture Git en ligne par des métadonnées moteur/profils versionnées et distinguer clairement leur date/version de l’état réel du workspace. Une absence de Git ne devrait pas être transformée en « moteur à jour » ou en `null` implicite.

Le comportement actuel en cas d’absence de Git n’a pas été testé dans cette recherche.

### `onefile` contre `onedir`

En mode `onefile`, PyInstaller extrait le support dans un répertoire temporaire et le supprime à la sortie normale ; après un crash, `kill -9` ou « Force Quit », ce répertoire peut rester ([P1]). Le mode `onedir` est le mode par défaut et conserve les dépendances dans un dossier ([P1], [P3]).

**Proposition pour la coque Swift :** partir sur `onedir`, afin de limiter la hiérarchie bootloader/processus et les résidus temporaires. Son emplacement dans le `.app`, la signature de chaque binaire et la notarisation constituent un jalon de prototype, pas un résultat déjà prouvé. Pour Tauri, `externalBin` attend un exécutable suffixé par le target triple et cite justement un serveur/API Python empaqueté avec PyInstaller ([T1]). Un sidecar `onefile` est donc le chemin le plus direct ; un layout `onedir` demanderait des ressources et une validation supplémentaires, sans supposer qu’il est pris en charge automatiquement.

## 3. Conserver l’UI, les origines et les préférences

Tauri accepte une URL comme `frontendDist` ; dans ce cas, il charge cette URL au lieu d’embarquer les assets frontend ([T2]). WKWebView peut charger du contenu depuis un serveur avec une `URLRequest` ([A1]). **Les deux coques peuvent donc naviguer directement vers `http://127.0.0.1:8767`, sans réécrire les Web Components ni changer leur même origine.**

**Proposition commune :** conserver l’UI servie par Python sur cette URL fixe, plutôt que l’embarquer via `file://` ou le protocole personnalisé de Tauri. Cela préserve `Host`, `Origin`, les POST same-origin et la validation stricte existante. Si une autre origine devenait indispensable, il faudrait revoir précisément le bridge/allowlist, jamais désactiver la validation `Host`/`Origin` ni accepter des origines arbitraires.

Le port reste fixe en v1. Un port aléatoire créerait une nouvelle origine à chaque lancement et isolerait les préférences. En cas de port occupé, la coque doit signaler le conflit et **ne jamais tuer un serveur préexistant** pour se l’approprier. Elle doit attendre que son propre serveur soit prêt avant de charger la page.

Pour WKWebView, le data store par défaut conserve les données web sur disque entre les sessions ([A2]). Cela permet à la nouvelle app de retrouver ses propres préférences avec une origine stable. **Cela ne transfère pas les données déjà présentes dans Safari/Chrome/Firefox.** Aucune lecture ou migration des liens privés du navigateur n’est proposée en v1. Tauri demande également un identifiant de bundle unique, utilisé notamment pour le chemin des données de la WebView ([T2]).

Le chargement HTTP local doit aussi être validé avec **App Transport Security (ATS)** sur la version de macOS ciblée. Apple documente `NSAllowsLocalNetworking` et les exceptions pour adresses IP ; il ne faut donc pas supposer que `http://127.0.0.1` sera accepté sans configuration. Limiter une éventuelle exception aux besoins locaux et ne pas désactiver globalement ATS ([A16]). Les liens HTTPS externes doivent s’ouvrir dans le navigateur système, sans permettre à ces pages de naviguer dans la fenêtre privilégiée du launcher.

### Variante minimale : ouvrir le navigateur

Une coque AppKit peut démarrer le backend puis appeler `NSWorkspace.open` sur l’URL ; Apple documente cette API pour ouvrir une URL ([A15]). Cette variante conserve le `localStorage` du navigateur et évite WKWebView.

Elle reste **minimale mais moins intégrée** : l’onglet appartient au navigateur, sa fermeture n’est pas celle de la coque et l’onglet peut rester affiché après l’arrêt du serveur. Elle est acceptable seulement si une fenêtre d’app native n’est pas un objectif. Elle ne supprime pas le besoin du canal EOF ; la politique de signature/notarisation dépend ensuite du mode de distribution.

## 4. Comparaison des deux architectures

| Critère | Tauri 2 + Python sidecar | Swift/AppKit/WKWebView + Python figé |
|---|---|---|
| Conservation UI/backend | Oui, en réglant `frontendDist` sur l’URL HTTP ([T2]). | Oui, en chargeant la même URL dans WKWebView ([A1]). |
| Frontend/bridge | Aucun framework JS requis ; Node n’est un prérequis Tauri que pour un framework JS ([T6]). Le sidecar peut être détenu par Rust, sans exposer de commande shell au JS. | Aucun bridge JS natif nécessaire ; seules les requêtes HTTP actuelles sont utilisées. |
| Chaîne de construction | Xcode et Rust sont requis pour développer avec Tauri ([T6]). | Xcode/Swift et les outils Apple pour la coque ; pas de chaîne Rust. |
| Python à l’exécution | Inutile si le sidecar PyInstaller est correctement figé ([P1]). | Identique ([P1]). |
| Autres dépendances fonctionnelles | Git/`source/` subsistent tant que `source_stamp` n’est pas découplé ; tmux/builds restent externes. | Exactement identique : la coque ne change pas cette dépendance. |
| Sidecar/bundle | `externalBin` copie le binaire externe et exige le suffixe du target triple par architecture ([T1]). | Le backend est placé manuellement dans le `.app` ; plus de liberté pour `onedir`, mais plus de travail de layout/signature. |
| DMG | `cargo tauri build --bundles dmg` produit directement le DMG autour du `.app` ([T4]). | Apple documente `hdiutil create`, puis signature du DMG ([A12]). |
| Signature/notarisation | Tauri documente identité, certificat Developer ID, variables d’identifiants et notarisation au build ([T5]). Les binaires Python imbriqués restent à vérifier. | Workflow Apple manuel : signer chaque code de l’intérieur vers l’extérieur, notariser et stapler ([A11]–[A14]). |
| Sortie normale | Les enfants suivis par l’API JS du plugin shell sont tués sur `RunEvent::Exit` ([T8], [T9]). En Rust, `kill_on_drop` vaut `false` par défaut : il faut une politique explicite ([T7]). | `applicationWillTerminate` permet le nettoyage normal ; `Process.terminate()` envoie `SIGTERM` ([A3], [A6]). |
| Crash/force quit | Aucun `RunEvent` ou `Drop` ne doit être supposé après une mort brutale. | `applicationWillTerminate` n’est pas appelé lors d’une « sudden termination » ([A3]). |
| Adéquation au besoin | Bon choix si le bundler Tauri, Rust ou une future cible multiplateforme apporte une valeur réelle. | **Meilleur ajustement Mac-only** : moins de couches, contrôle direct d’AppKit et de Foundation. |

Electron n’est pas proposé : le besoin est déjà couvert par la WebView système et le backend existant, sans fonctionnalité Electron identifiée qui compenserait une nouvelle pile.

## 5. Cycle de vie : faits exacts et garanties

### 5.1 Ce que Tauri fait réellement

Le guide officiel définit un sidecar comme un binaire externe embarqué, notamment pour éviter d’installer Python, et montre son lancement depuis Rust ou JavaScript ([T1]). **Il ne faut pas en déduire que tout sidecar est automatiquement supprimé à la sortie.**

Dans le code officiel consulté, figé au commit `738c323cfc41fc1bb248991de9620383de788d4d` :

- `Command::new` initialise `kill_on_drop: false` ; le destructeur de `CommandChild` ne tue que si cette option a été activée ([T7]).
- `CommandChild.kill()` envoie le kill et attend la sortie. Sur Unix, le chemin direct utilise le kill de l’enfant ; avec `process_group`, le code appelle `killpg(..., SIGKILL)` ([T7]).
- les processus lancés via la commande JS `spawn` sont insérés dans le registre `children` du plugin ([T9]) ; sur `RunEvent::Exit`, le plugin retire ces enfants du registre et appelle `kill()` sur chacun ([T8]).

**Conclusion vérifiée :** la sortie normale de la boucle Tauri tue les enfants **suivis par l’API JavaScript du plugin**. Un sidecar lancé et détenu directement en Rust n’a pas ce nettoyage implicite par défaut. Pour ce dernier, il faut conserver le handle et programmer la fermeture ; `kill_on_drop(true)` ne doit pas être l’unique garantie, d’autant que `App::run` documente une fin directe par `std::process::exit` et fournit `RunEvent::ExitRequested`/`Exit` pour le cycle applicatif ([T10]).

Le kill Tauri n’est pas un arrêt gracieux du serveur. Activer `process_group` pour rattraper un wrapper PyInstaller élargit en outre le `SIGKILL` à tout le groupe ([T7]). **Ce n’est pas acceptable comme politique par défaut ici**, tant que l’on n’a pas prouvé qu’aucun jeu ou build tmux ne partage ce groupe.

### 5.2 Ce qu’AppKit/Foundation garantit

`applicationWillTerminate` permet un dernier nettoyage avant la fin normale de l’app, mais Apple précise qu’il n’est pas appelé pendant une « sudden termination » ([A3]). `applicationShouldTerminateAfterLastWindowClosed` permet de décider si la fermeture de la dernière fenêtre doit terminer l’app ([A5]) ; ce choix devra être explicite et testé, plutôt que confondre fermeture de fenêtre et fin de processus.

`Process.terminate()` envoie `SIGTERM`, qu’un processus peut ignorer ([A6]). C’est donc un mécanisme de sortie normale avec attente et repli ciblé, pas une garantie absolue.

### 5.3 `SIGKILL` : limite commune non négociable

Apple indique qu’un handler ne peut ni intercepter ni ignorer `SIGKILL` ([A8]) ; Python dit également qu’il ne peut être capturé, bloqué ou ignoré ([PY2]). **Ni un callback Tauri, ni un `Drop`, ni `applicationWillTerminate`, ni un handler Python ne peut être promis après `SIGKILL`.** Toute réponse « la coque nettoie forcément son sidecar au force quit » serait donc fausse sans mécanisme extérieur à ce callback.

### 5.4 Proposition : le serveur s’arrête sur EOF du canal de contrôle

Le mécanisme commun le plus petit est un **pipe de contrôle détenu par la coque** :

1. La coque démarre son propre backend avec un pipe dédié, ou l’entrée standard configurée comme tel. Tauri configure stdin comme `piped` dans son `Command` ([T7]) ; Foundation accepte un `Pipe` comme `standardInput` d’un `Process` ([A7]).
2. Le backend surveille ce descripteur dans un thread de contrôle. À EOF, il déclenche son propre arrêt ordonné et ferme le socket HTTP. `socketserver.shutdown()` doit justement être appelé depuis un thread différent de celui qui exécute `serve_forever()` ([PY1]).
3. À la sortie normale, la coque ferme le côté écriture et attend la fin du backend. Le repli éventuel est strictement limité au processus serveur possédé, sans propagation à ses descendants tant que leur isolation n’est pas prouvée. Elle ne tue ni groupe, ni `/usr/bin/open`, ni tmux.
4. Si la coque meurt, macOS libère les descripteurs du processus ([A9]). Quand le côté écriture du pipe est fermé, le pipe devient « widowed » et la lecture finit par retourner zéro ([A10]). Le backend reçoit ainsi EOF **sans qu’un callback de la coque ne soit nécessaire**.
5. Le côté écriture ne doit pas être dupliqué dans d’autres processus, sinon EOF pourrait ne pas survenir. Le handle du serveur reste possédé par la coque pendant toute sa vie.

**Garantie visée, non encore vérifiée :** pendant que macOS fonctionne et que le backend reste capable d’exécuter son thread de contrôle, ce mécanisme couvre sortie normale, crash et `SIGKILL` de la coque, sans toucher aux jeux ou builds détachés. Il ne promet pas un arrêt instantané si le backend est lui-même bloqué, ni quoi que ce soit après une coupure machine/kernel panic. L’héritage du descripteur à travers le mode PyInstaller choisi doit être testé ; `onedir` réduit cette incertitude.

Un second mécanisme de sortie normale peut rester présent : fermeture explicite du canal, puis `SIGTERM`/kill ciblé en dernier recours. Il ne remplace pas l’EOF, qui est la couche couvrant la mort brutale.

## 6. Signature, notarisation et DMG

**Usage personnel d’abord :** produire un DMG de test local ne nécessite pas d’acheter un compte Apple Developer. Une app signée ad hoc pour usage local n’est pas une distribution Developer ID notariée ; le README distingue déjà ces niveaux ([README.md, § Play](../../README.md#play)). La chaîne de distribution ci-dessous est un périmètre supplémentaire, à retenir seulement si l’on veut distribuer l’application, pas un achat implicite pour ce prototype.

### Exigences communes Apple

Pour une distribution directe Developer ID, Apple demande de signer chaque élément de code, de signer de l’intérieur vers l’extérieur et d’activer Hardened Runtime ainsi qu’un timestamp sécurisé pour les exécutables concernés ([A11]). Apple déconseille de compter sur `codesign --deep` pour une structure complexe et rappelle que le code placé dans une zone de données peut ne pas être signé par cette option ([A11]).

PyInstaller refait par défaut une signature **ad hoc** des binaires collectés ; avec `--codesign-identity`, il peut les signer avec une identité réelle et active Hardened Runtime ([P4]). **Ad hoc n’est pas une notarisation.** La chaîne doit donc signer correctement les binaires Python, puis le sidecar/helper, puis la coque, avant le conteneur final. La notarisation et un test Gatekeeper doivent valider le résultat réel ; il ne faut pas supposer que le bundler extérieur a signé tout le contenu Python.

Apple accepte notamment les apps et images disque UDIF à la notarisation ; les logiciels Developer ID doivent être notariés, et le ticket peut être agrafé pour Gatekeeper ([A13]). Le workflow en ligne de commande utilise `notarytool`, puis `stapler` ([A14]).

### Différence pratique

- **Tauri :** son bundler documente directement le `.app` et le `.dmg` ([T4]), ainsi que la configuration de l’identité et des identifiants de notarisation ([T5]). C’est un avantage réel, mais pas une preuve que chaque binaire PyInstaller embarqué est correctement signé sans vérification.
- **Swift :** Apple documente `hdiutil create -srcFolder`, la signature du `.dmg`, la notarisation du conteneur externe et `xcrun stapler staple` ([A12], [A14]). C’est davantage de script de release, mais entièrement compatible avec la petite coque.

Dans les deux cas, il faut tester l’artefact téléchargé et mis en quarantaine, y compris le premier lancement avec translocation éventuelle, puis un lancement après déplacement du `.app`. Apple recommande ces scénarios pour la distribution directe ([A12]). Une configuration de workspace absolue et externe évite de dépendre de fichiers situés à côté du bundle déplacé/transloqué.

## 7. Recommandation de v1 et critères d’acceptation

### Architecture recommandée

1. **Swift/AppKit/WKWebView**, sans bridge JS privilégié, sur `http://127.0.0.1:8767`.
2. **Backend PyInstaller figé**, avec préférence pour `onedir` dans cette variante native ; ressources UI incluses, workspace externe explicite.
3. **V1 attachée au workspace** pour conserver le monitor actuel, avec prérequis Git + `source/` affiché honnêtement. L’ouverture d’apps existantes reste dans le périmètre ; démarrer/importer/rebuilder ne l’est pas.
4. **Pipe EOF + arrêt normal ciblé**, sans kill de groupe. Les jeux et builds détachés restent hors du cycle de vie du serveur HTTP.
5. **DMG de test local d’abord** ; si une distribution est demandée, Developer ID + notarisation + stapling, avec chaque binaire Python signé de l’intérieur vers l’extérieur.

Tauri 2 reste le repli raisonnable si l’équipe préfère son bundler ou anticipe une cible non-Mac. Dans ce cas, le sidecar devrait être lancé et possédé côté Rust, sans permission shell générale dans le frontend, avec le même canal EOF et une fermeture explicite sur les événements de sortie.

### Vérifications nécessaires avant de dire « distribuable »

- Au lancement : seul le serveur possédé par l’app écoute sur `127.0.0.1:8767` ; la page et les POST existants fonctionnent sans assouplir `Host`/`Origin`.
- Port déjà occupé : erreur visible, aucun processus préexistant tué ou adopté implicitement.
- Menu Quit et, si ce comportement est choisi, fermeture de la dernière fenêtre : arrêt effectif du serveur possédé.
- `SIGKILL` de la coque et crash simulé : EOF reçu, serveur arrêté, aucun résidu de processus ; le cas du backend bloqué est documenté.
- Après chaque arrêt : jeux précédemment ouverts et builds tmux toujours vivants ; aucune commande `killall`, `pkill` ou kill de groupe.
- Relance dans la même app : préférences conservées avec l’origine fixe. Les préférences du navigateur historique ne sont pas attendues sans migration explicite.
- Environnement sans Python/Homebrew : backend fonctionnel. Si la v1 reste attachée, le test distingue ensuite clairement les erreurs dues à Git/`source/` de celles dues à Python.
- Pour le test local : installation depuis le DMG, copie dans `/Applications`, lancement et signature locale vérifiés. Pour une distribution Developer ID : signature de chaque exécutable/bibliothèque, notarisation acceptée, log contrôlé, ticket staplé et premier lancement Gatekeeper testé.
- Architecture cible testée sur le Mac correspondant ; `universal2` revendiqué seulement si le résultat est effectivement validé.
- Aucun jeu, clé, `.venv`, checkout, SDK ou cache ne figure dans le DMG ; les builds et le toolchain moteur restent hors du périmètre annoncé.

## 8. Inconnues et limites de cette recherche

- Aucun prototype n’a été construit ou lancé ; le comportement EOF avec le layout PyInstaller final, la fermeture de la dernière fenêtre, les préférences WebKit et la notarisation restent à vérifier.
- Le comportement Tauri décrit ci-dessus est fondé sur le code officiel aux commits cités, notamment `738c323…` pour le plugin shell. Les versions devront être épinglées ; il ne faut pas transposer ce constat à une version antérieure sans relire son code.
- La viabilité du layout `onedir` dans un `.app` notarié est une proposition de prototype, pas un fait établi. Le mode `onefile` laisse possiblement des répertoires temporaires après une mort brutale ([P1]).
- Le comportement actuel de `source_stamp` sans Git, et la manière exacte de présenter des métadonnées moteur découplées sans fabriquer un état « à jour », restent à spécifier/tester.
- La migration éventuelle du `localStorage` du navigateur n’est ni conçue ni autorisée ici ; les liens privés ne doivent pas être lus pour ce packaging.
- Aucune taille, durée de démarrage ou estimation chiffrée de travail n’est revendiquée. La conclusion « effort moyen » reflète uniquement le nombre de contrats techniques à modifier et à vérifier.

## Sources primaires

### Tauri 2 — documentation et code officiel

- **[T1]** Embedding External Binaries / sidecar et target triple : https://v2.tauri.app/develop/sidecar/
- **[T2]** Configuration, notamment `frontendDist`, `externalBin` et `identifier` : https://v2.tauri.app/reference/config/#frontenddist — https://v2.tauri.app/reference/config/#externalbin — https://v2.tauri.app/reference/config/#identifier
- **[T4]** DMG : https://v2.tauri.app/distribute/dmg/
- **[T5]** macOS Code Signing : https://v2.tauri.app/distribute/sign/macos/
- **[T6]** Prerequisites, macOS/Rust/Node : https://v2.tauri.app/start/prerequisites/
- **[T7]** Plugin shell, `Command`, `CommandChild`, kill/drop/process group et stdin, commit `738c323…` : https://github.com/tauri-apps/plugins-workspace/blob/738c323cfc41fc1bb248991de9620383de788d4d/plugins/shell/src/process/mod.rs
- **[T8]** Plugin shell, nettoyage sur `RunEvent::Exit`, même commit : https://github.com/tauri-apps/plugins-workspace/blob/738c323cfc41fc1bb248991de9620383de788d4d/plugins/shell/src/lib.rs
- **[T9]** Plugin shell, registre des enfants JS, même commit : https://github.com/tauri-apps/plugins-workspace/blob/738c323cfc41fc1bb248991de9620383de788d4d/plugins/shell/src/commands.rs
- **[T10]** Tauri `RunEvent` et `App::run`, commit `8062864…` : https://github.com/tauri-apps/tauri/blob/8062864a5e70b97dd738a96dc063f28ce6e0e2e2/crates/tauri/src/app.rs

### Python / PyInstaller

- **[P1]** Fonctionnement, autonomie, `onefile`/`onedir` et résidus après kill : https://pyinstaller.org/en/stable/operating-mode.html
- **[P2]** `__file__`, `sys._MEIPASS` et ressources au runtime : https://pyinstaller.org/en/stable/runtime-information.html
- **[P3]** Options `onedir`, `onefile`, données, architecture et identité : https://pyinstaller.org/en/stable/usage.html
- **[P4]** Architectures macOS et signature des binaires : https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support — https://pyinstaller.org/en/stable/feature-notes.html#macos-binary-code-signing
- **[PY1]** `socketserver.shutdown()` et threading : https://docs.python.org/3/library/socketserver.html#socketserver.BaseServer.shutdown
- **[PY2]** `SIGKILL` non capturable : https://docs.python.org/3/library/signal.html#signal.SIGKILL

### Apple

- **[A1]** WKWebView, chargement de contenu web : https://developer.apple.com/documentation/webkit/wkwebview
- **[A2]** `WKWebsiteDataStore.default()`, persistance : https://developer.apple.com/documentation/webkit/wkwebsitedatastore/default()
- **[A3]** `applicationWillTerminate(_:)`, cleanup et sudden termination : https://developer.apple.com/documentation/appkit/nsapplicationdelegate/applicationwillterminate(_:)
- **[A5]** `applicationShouldTerminateAfterLastWindowClosed(_:)` : https://developer.apple.com/documentation/appkit/nsapplicationdelegate/applicationshouldterminateafterlastwindowclosed(_:)
- **[A6]** `Process.terminate()`, `SIGTERM` : https://developer.apple.com/documentation/foundation/process/terminate()
- **[A7]** `Process.standardInput` et `Pipe` : https://developer.apple.com/documentation/foundation/process/standardinput — https://developer.apple.com/documentation/foundation/pipe
- **[A8]** `sigaction(2)`, impossibilité de capter/ignorer `SIGKILL` : https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/sigaction.2.html
- **[A9]** `close(2)`, descripteurs libérés à la sortie du processus : https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/close.2.html
- **[A10]** `pipe(2)`, pipe « widowed » et EOF : https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/pipe.2.html
- **[A11]** Signature de distribution, ordre inside-out et limites de `--deep` : https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac
- **[A12]** Packaging DMG, signature, stapling et tests de distribution : https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution
- **[A13]** Notarisation Developer ID : https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- **[A14]** Workflow `notarytool` / `stapler` : https://developer.apple.com/documentation/security/customizing-the-notarization-workflow
- **[A15]** `NSWorkspace.open(_:)` : https://developer.apple.com/documentation/appkit/nsworkspace/open(_:)
- **[A16]** ATS et chargement local/IP : https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nsallowslocalnetworking
