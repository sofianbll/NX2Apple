# Manette PowerA NANO : un pilote macOS pour la faire passer pour une Pro Controller ?

Date : 2026-11-05 (Europe/Paris), avec un complément demandé ensuite sur la sortie Switch Pro. Recherche documentaire et lecture seule des métadonnées système. Aucune app de pont n'a été téléchargée ou exécutée, aucune manette virtuelle créée, aucun réglage modifié.

Légende utilisée dans tout le document :

- **[Fait]** : écrit dans une source lue.
- **[Témoignage]** : rapporté par un développeur ou un utilisateur, sans preuve indépendante.
- **[Déduction]** : notre raisonnement, pas écrit dans une source.
- **[Inconnu]** : aucune source ne répond.

Déjà établi le 2026-11-04 (non refait ici) : PowerA dit que ses manettes Switch ne sont pas compatibles Mac. Il n'existe ni mise à jour de firmware PowerA ni pilote ou extension DriverKit connu pour ce cas. Les adaptateurs 8BitDo et Steam Input ne sont pas prouvés pour cette manette. Le moteur nxnative lit déjà la manette en HID brut (seedds/nxnative #859 et #989).

## Réponse courte

**Une sortie Switch Pro existe déjà dans `libvirtualhid` sur macOS.** Elle publie `057e:2009` et répond au dialogue Nintendo. En revanche, le pont complet **PowerA → Switch Pro virtuelle → GameController** n'est pas validé. Le service signé de libvirtualhid exige une licence machine payante. Sofian préfère cette identité Nintendo à Xbox, ne pas substituer cette dernière par défaut. La vraie manette ne change ni de firmware ni d'identité. Voir le complément Switch Pro ci-dessous.

- **[Fait documentaire]** Apple permet de définir l'identité d'un HID virtuel. **[Témoignage de mainteneur]** OJD rapporte une Xbox virtuelle `045e:0b13` reconnue dans GameController avec des entrées fonctionnelles. Cela n'a pas été reproduit ici, ni avec cette PowerA. Voir [O1], [O2].
- **[Fait local]** Sur ce Mac sous macOS **27.2**, les entrées Apple de la Switch Pro `057e:2009` et de la Xbox Series `045e:0b13` portent **`GCIOMatchVirtual = true`**. **[Inconnu]** Une imitation Nintendo complète fournirait-elle des entrées GameController ? Ce drapeau seul ne le prouve pas. Voir le relevé ci-dessous.
- **[Fait documentaire]** OJD fournit déjà un hôte qui demande l'entitlement virtuel et annonce une distribution signée et notariée, SIP/AMFI actifs. **Il n'est donc pas établi que Sofian doive payer un compte développeur ou demander lui-même l'entitlement pour réutiliser ce binaire.** Sa signature effective n'a pas encore été inspectée. Recompiler un fork ne conserve pas les autorisations de son auteur. Voir [O1], [O3], [O4].
- **[Fait source]** OJD n'est pas prêt à l'emploi pour notre cas : son passage à macOS repose sur `supportsHIDDevice`, et ses fiches refusent un vendor ID nul. **[Déduction]** Un petit lecteur HID externe alimentant sa commande `virtual feed` permettrait d'éviter ces deux règles sans modifier le binaire signé. Cette chaîne reste à tester. Voir [O5] à [O9].

## Complément Perplexity et vérification ciblée

Deux requêtes **Perplexity Search** ont complété les six recherches et six vérifications DeepSeek, puis la synthèse. Budget consommé : une première requête générale et **une seconde demandée explicitement sur la sortie Switch Pro**, aucune relance automatique. Les réponses ont servi de pistes, pas de preuves. Context7 a répondu « Monthly quota exceeded », les pages Apple ont donc été ouvertes directement. Toutes les nouvelles sources ci-dessous ont été consultées le **2026-11-05**.

### Complément demandé : une sortie Switch Pro, pas Xbox

**[Fait source] Oui, la brique de sortie existe.** `libvirtualhid` propose `lvh::profiles::switch_pro()`. Dans le tag **`v2026.1104.2126.25`**, commit **`4847ea017f02115a02f57bd9372c0d2d8fe7c06f`**, `src/core/profiles.cpp:2027-2045` construit un périphérique USB `057e:2009`, version `0210`, nommé `(libvirtualhid) Nintendo Pro Controller`, avec son descripteur Nintendo. Le broker macOS appelle `switch_pro_protocol::make_switch_pro_reply` lors des commandes de sortie. Le code partagé fournit notamment les réponses `0x21` et la calibration SPI. Il ne s'agit donc pas de renommer un rapport Xbox. [N1], [N2], [N3]

- **Disponible à la distribution, signature non inspectée ici.** La préversion du 4 novembre 2026 contient `libvirtualhid-macOS-universal.dmg`. La documentation annonce un broker signé/notarié et un outil graphique Virtual HID Control. Le broker porte l'entitlement Apple et crée les HID virtuels, le client C++ ordinaire lui transmet les états. Il n'est pas nécessaire, selon cette architecture, de recompiler le broker pour choisir le profil Switch Pro. [N4], [N5]
- **Ce qui manque pour la PowerA.** Un petit client doit lire ses rapports HID, vérifier son identité et son descripteur, normaliser les entrées puis appeler l'API libvirtualhid. `examples/gamepad_adapter.cpp` sélectionne déjà le profil avec le nom `switch`, crée un `GamepadStateAdapter`, puis lui envoie boutons et axes. Cet exemple simule des entrées, ce n'est pas un pont PowerA. Aucune entrée JSON prête à l'emploi comparable à OJD n'a été identifiée pour ce service. [N6]
- **Coût et installation.** Une licence machine **payante** est requise pour les gamepads macOS, avec options annuelle et perpétuelle. Le montant n'a pas été vérifié. Le service est un LaunchDaemon, son installation demande l'autorisation administrateur et son utilisation une permission étendue de contrôle des périphériques/Accessibilité. Bibliothèque MIT, broker LB-SAL. Ni achat ni installation autorisés par cette recherche. [N4], [N7]
- **Ce qui a réellement été testé par le projet.** Le guide rapporte des boutons, sticks, croix, gâchettes numériques, vibration, mouvement et Capture pour le backend Switch Pro macOS, mais situe ces essais dans **le testeur Steam**, notamment par Sunshine/Moonlight. Ce n'est pas une preuve de GameController, ni de prise en charge du matériel PowerA. Le guide indique aussi des limites de batterie et de LED. Home et son maintien pour NX2Apple doivent être vérifiés séparément. [N8]
- **Pas de verdict négatif définitif sur GameController.** La seconde réponse Perplexity s'appuie sur une ancienne comparaison de branche pour dire que GameController ignore les HID virtuels. Cette généralisation est contredite par les résultats Xbox de la PR #208 et d'OJD. Elle n'établit rien sur l'admission de la Switch Pro virtuelle. Le résultat correct demeure **inconnu**, malgré le drapeau local `GCIOMatchVirtual = true`. [O2], [N9]
- **OJD : pas un simple fichier de configuration Nintendo.** Il accepte des identités personnalisées, mais `VirtualDeviceLayout` n'encode que `OJDGenericGamepad`, `XboxOneGIP` et `XboxSeriesBluetooth`. Changer uniquement VID/PID et le nom ne fournit ni rapports Nintendo ni réponses aux sous-commandes. Ajouter cette sortie demanderait une modification du programme signé, avec la question de sa signature/autorisation ou une contribution upstream. [N10]
- **Autre résultat ppxq écarté pour ce Mac.** `ns2pro-bridge` cible Switch 2 BLE, Linux et Windows, avec une sortie USB `057e:2069`. Son README ne propose pas de backend macOS, ni d'entrée PowerA Switch 1. Ce n'est pas le pont recherché. [N11]

**Conclusion ciblée.** La voie Nintendo la plus concrète trouvée est **lecteur PowerA → petit client C++ → broker libvirtualhid signé → Switch Pro virtuelle `057e:2009`**. Les briques de sortie et de protocole existent, mais pas un pont prêt à l'emploi démontré pour cette manette et NX2Apple. Ne pas acheter une licence sur la seule promesse d'une compatibilité GameController. Une première preuve utile serait la création temporaire du seul profil Switch Pro et des entrées synthétiques observées dans un lecteur GameController, avant d'écrire tout le raccordement PowerA, avec accord séparé pour l'installation et l'activation.

### Ce que dit réellement OpenJoystickDriver

Périmètre source : tag **`0.6.0-alpha.1`**, publié le **2026-10-23**, commit **`3552be925d7dacef3fd895ac0c6cbf39e9d3cd70`**. Le `main` consulté pointe aussi sur ce commit. Les wikis sont des pages vivantes, pas des preuves de signature du DMG. [O1], [O10]

- **Sortie déjà implémentée.** `GameControllerCompatible` publie une Xbox Wireless `045e:0b13` avec des rapports Xbox Series Bluetooth. OJD utilise **`IOHIDUserDevice` dans l'app**, pas un DEXT pour cette sortie. Le DEXT fourni sert à certaines Xbox physiques en USB, pas à la PowerA Bluetooth. Le README annonce macOS 12+, sans désactiver SIP/AMFI. [O1], [O3], [O4], [O11]
- **Preuves GameController, pas seulement Steam.** Le wiki rapporte une apparition dans Réglages > Manettes, des entrées dans un jeu GameController et dans Safari. Guide et Share ont des limites, notamment liées au focus. Le profil `GameControllerCompatible` n'est **jamais choisi automatiquement**. Le profil par défaut pour SDL/Steam est différent et n'établit pas une compatibilité GameController. [O2]
- **Premier obstacle précis.** `HIDDeviceStream.nativePassThrough` renvoie `supportsHIDDevice(device) && !catalog.takesOwnership(...)`. Avec le résultat `YES` déjà observé pour la PowerA, le chemin par défaut la laisse donc à macOS, même si `GCController.controllers()` reste vide. C'est une déduction du code pour nos observations, pas un essai d'OJD sur cette manette. [O5]
- **Le réglage existant ne suffit pas pour `0000:0000`.** `DeviceCatalog.makeRuntimeProfile` exige un vendor dans `1...65535`. La prise en charge forcée exige une fiche valide et s'applique au modèle VID/PID, pas au nom « Lic Pro Controller ». Une simple fiche PowerA à vendor 0 est donc refusée par ce code. L'identité observée zéro n'est pas une identité manquante : `ControllerModelID` peut représenter zéro. Ne pas élargir aveuglément la capture à tous les périphériques `0000:0000`. [O6], [O7], [O12]
- **Voie de réutilisation à évaluer avant un fork.** `ojd virtual feed --as game-controller-compatible` reçoit des états de boutons/sticks en JSON sur stdin. Son registre construit le périphérique à partir du profil virtuel, **sans exiger de fiche de manette physique**. Le CLI officiel parle au service par son canal RPC. Un lecteur externe pourrait lire uniquement la PowerA, traduire ses rapports, puis alimenter le CLI signé sans demander lui-même l'entitlement de création virtuelle. La commande et les tests existent, mais nous ne les avons pas exécutés. [O7], [O8], [O9]
- **Limites de cette proposition.** Le lecteur et la traduction n'existent pas encore dans cette chaîne. Il faut vérifier la sélection précise, les autorisations, la reconnexion, les relâchements et les boutons Home/Capture. Un test de parseur hors ligne n'établit ni l'admission GameController, ni la latence, ni le fonctionnement du launcher. L'app demande Surveillance de l'entrée et Accessibilité, autorisations étendues à accepter séparément. [O3], [O9]

### Relevé local, sans activation de périphérique

Fichier lu : `/System/Library/Extensions/AppleGameControllerPersonality.kext/Contents/Info.plist`.

SHA-256 : `245f008839566c3f860bf69f123f1ca874b4da60e374f9313702e7de4b3ef857`.

- `Nintendo Switch Pro Controller IOService` : `VendorID = 1406`, `ProductID = 8201`, `GCIOMatchVirtual = true`.
- `Xbox Series X Wireless Controller` : `VendorID = 1118`, `ProductIDArray = [2835, 2851, 2895]`, `GCIOMatchVirtual = true`. `2835` correspond à `0x0b13`.
- Ces deux entrées visent `AppleGCHIDUserEventDriver` via `IOHIDInterface`. Il s'agit de critères de configuration privés observés sur **cette version**, pas d'une garantie d'API ni d'un test d'entrées.

### switch2mac n'est pas le pont PowerA recherché

**[Fait source]** Le filtre d'entrée exige une annonce BLE Nintendo, vendor `057e`, et un modèle Switch 2 parmi `2066`, `2067`, `2069`, `2073`. Le protocole GATT n'est pas celui de notre PowerA Switch 1 en HID. **[Témoignage]** L'issue #3 signale aussi une signature refusée pour le DMG v0.2.0 sur macOS 27. Ce n'est ni une solution prête pour la NANO, ni une preuve GameController pour une Pro Controller virtuelle. Le sous-agent a lu le code à `a8f2e61e85c3`, le coordinateur a recoupé le filtre et l'issue. [S1], [S2]

## Comment ça marche, et où ça casse

1. **Bluetooth → identité.** **[Fait]** En Bluetooth classique, l'identité vendor/product ne figure pas dans le descripteur HID. Elle vient de l'enregistrement SDP « Device ID » (classe PnP Information `0x1200`, attributs `0x0201` vendor, `0x0202` product, `0x0205` source). Le profil HID impose un serveur SDP avec les enregistrements HID et DID (sources btstack, Bluetooth DID TS, bluez#4). **[Déduction]** La PowerA omet probablement cet enregistrement DID ou le forme mal, d'où `0000:0000`. **[Inconnu]** Absent ou mal formé : seule une lecture SDP de la manette le dirait. Aucune source lue ne décrit comment macOS remplit vendorID/productID en Bluetooth.
2. **HID → IOKit.** **[Fait, contexte]** La manette est lisible en HID brut ; nxnative la lit déjà dans le rapport simple `0x3F`.
3. **IOKit → GameController : c'est ici que ça casse.** **[Fait documentaire]** Apple décrit des manettes prises en charge. Aucune API publique permettant d'en enregistrer une nouvelle n'a été identifiée dans les sources consultées. D'après la doc, `supportsHIDDevice` = YES signifie qu'on peut utiliser les API GameController avec ce périphérique. **[Témoignage]** Un post MacRumors (lecture du code de macOS 26.7) affirme que macOS compare le vendor ID et le product code à « sa liste de périphériques connus ». Un fil Apple Forums (iOS 27, manette BLE à vendor 0) montre `gamecontrollerd` qui journalise `vendorID = 0 productID = 0` sans créer de `GCController`. nxnative #965 montre le même symptôme sur une 8BitDo `2DC8:301B` : `supportsHIDDevice=1`, `GC count=0`. **[Déduction]** L'identité compte parmi les critères d'admission, mais les sources ne prouvent pas que les zéros soient à eux seuls la cause de notre échec. L'écart entre `supportsHIDDevice` et la liste vide mérite un rapport Feedback, sans diagnostic définitif du défaut interne d'Apple.
4. **Couche de compatibilité.** **[Fait]** Depuis macOS 14, pour une manette *déjà prise en charge*, macOS peut créer un HID synthétique (clé `kIOHIDGCSyntheticDeviceKey`) qui imite une manette Xbox 360 filaire, pour les anciennes apps IOKit. Elle est **désactivée par défaut** (réglage par jeu « Augmenter la compatibilité des manettes »). Elle s'ajoute à la vraie manette ; elle n'aide pas une manette refusée.

## Variantes de sortie et alternatives

### 1. Pro Controller virtuelle en espace utilisateur : préférence demandée, GameController non validé

- **Principe.** Une app lit la PowerA en HID brut, puis publie un périphérique virtuel `057e:2009` avec le descripteur et les rapports Nintendo (`0x30` ou `0x3F`).
- **Exigences.** L'entitlement de l'hôte est `com.apple.developer.hid.virtual.device` (documenté depuis macOS 10.15), distinct de celui d'un DEXT HID virtuel. CoreHID `HIDVirtualDevice` est documenté depuis macOS **15**, pas seulement 26. Un nouvel exécutable doit obtenir sa propre signature et les autorisations nécessaires, celles d'une app existante ne se copient pas. Réutiliser un binaire autorisé existant est une autre option. **[Témoignage]** Des prototypes Sunshine non autorisés ont réduit AMFI. Ce contournement n'est ni nécessaire pour toute solution ni proposé pour ce Mac. [A1], [A2], [O3], [O4]
- **Ce qu'il faut imiter.** **[Fait]** Le dialogue Nintendo : l'hôte envoie le rapport de sortie `0x01` (sous-commande à l'octet 10). La sous-commande `0x03` choisit le mode `0x30` (49 octets, 60/120 Hz, boutons, sticks 12 bits, batterie, IMU) ou `0x3F` (12 octets, hat, sticks 16 bits). Les réponses arrivent en `0x21` (ACK octet 13, sous-commande octet 14), y compris les lectures SPI de calibration `0x10`. Les commandes `0x80` sont propres à l'USB. **[Déduction]** Un périphérique virtuel n'a pas de transport : pas d'appairage ni de `0x80`. Il faudra peut-être répondre aux `0x21` et à la calibration.
- **Effort.** Pour une implémentation maison : traduire les rapports et simuler les réponses aux sous-commandes. Avec libvirtualhid, les réponses Nintendo sont déjà implémentées, il reste le lecteur PowerA et son raccordement, les contrôles de signature/licence et les essais dans les consommateurs visés. [N2], [N3], [N6]
- **Risques.** Apple peut refuser une nouvelle demande d'entitlement. Même avec le drapeau virtuel présent, le dialogue ou le descripteur peut ne pas convenir. Le comportement peut changer avec macOS. **[Témoignage de projet]** Un descripteur inexact peut donner une manette « sans entrées » (libvirtualhid #208).
- **GameController l'accepterait-il ?** L'entrée Nintendo locale porte bien le drapeau virtuel. Aucune preuve consultée ne montre pour autant cette identité virtuelle dans `GCController.controllers()` avec des entrées fonctionnelles. OJD rapporte seulement `supportsHIDDevice = yes` pour sa publication Switch expérimentale, ce qui ne suffit justement pas dans notre cas. Les résultats Xbox GameController sont distincts et mieux étayés. [O2], [O13]
- **Niveau de preuve.** Moyen pour le mécanisme, nul pour `057e:2009` dans GameController.

### 2. Xbox virtuelle `045e:0b13` : solution de repli, pas la préférence de Sofian

- **[Déduction]** Même chaîne que l'option 1, mais avec une identité dont on sait qu'elle passe. Les jeux voient une manette Xbox (libellés A/B inversés par rapport à Nintendo), pas une Pro Controller.
- **Exigences et risques.** Le profil GameController doit être choisi explicitement. Le wiki OJD rapporte des limites de Guide/Share et l'absence d'entrées dans Steam avec ce profil, distinct du profil SDL. Ni les libellés Nintendo ni toutes les fonctions physiques ne sont garantis. [O2]
- **Niveau de preuve.** Meilleur pour la sortie GameController, mais **aucune validation de bout en bout avec cette PowerA**. La voie `virtual feed` évite en principe de modifier ou re-signer OJD, pas de vérifier les autorisations et les entrées.

### 3. Extension DriverKit / HIDDriverKit (dext)

- **Principe.** Un pilote s'attache à la manette, ou publie un périphérique virtuel.
- **Exigences.** **[Fait]** Compte payant, approbation séparée d'Apple pour `com.apple.developer.driverkit` et `userclient-access`, entitlement de famille HID (`com.apple.developer.driverkit.family.hid.virtual.device` pour le virtuel), Developer ID, notarisation. Le SIP ne peut être désactivé qu'en développement. **[Déduction]** En distribution, il faut le SIP actif, l'accord de l'utilisateur et parfois un redémarrage.
- **Attache en Bluetooth.** **[Témoignage, ingénieur Apple, forum lu par miroir]** On ne peut pas prendre la propriété exclusive de la manette source, et la propriété via DriverKit « ne marcherait que pour les connexions filaires ». **[Témoignage]** Un développeur dit avoir attaché un dext à un périphérique HID BLE.
- **Effort.** Élevé (pilote, signature, installation système).
- **Risques.** Les plus élevés : approbations Apple, code noyau-adjacent, installation lourde pour l'utilisateur.
- **GameController ?** Aucun avantage connu sur l'option 1. Le même ingénieur parle de vérifications qui ignorent le HID virtuel. Précédent : `SillyUtility/VirtualController` (manette NES en DriverKit), lue par les apps HID, pas prouvée dans GameController.
- **Niveau de preuve.** Faible.

### 4. Autres pistes écartées

- **Karabiner-DriverKit-VirtualHIDDevice** : clavier et souris seulement ; la demande joystick (#22) est ouverte depuis 2022. **[Fait]**
- **`GCVirtualController`** : iOS/iPadOS/Mac Catalyst, limité à une seule app, affiché à l'écran. Ne sert pas aux autres apps. **[Fait]**
- **Changer l'identité de la manette réelle** : **[Déduction]** aucune API ne permet de réécrire vendorID/productID d'un vrai périphérique. Le mode d'appairage ne change pas le contenu SDP ; l'identité vit dans le firmware.

## Prochain essai concret le moins risqué

1. **Terminé en lecture seule** : vérifier les entrées Apple, le code OJD et la différence entre GameController et SDL. Pas de pilote maison justifié à ce stade.
2. **Choix préalable, aucune autorisation acquise** : décider si la voie Switch Pro libvirtualhid avec service et licence payante convient. OJD/Xbox reste une alternative, pas un remplacement implicite de la demande Nintendo. L'examen statique de la distribution et la préparation sur données simulées peuvent être séparés de l'installation.
3. **Accord séparé avant essai réel** : installation/activation du service choisi et acceptation des permissions, puis création temporaire d'une seule manette virtuelle, mesure de `GCController.controllers()` et des entrées Home/Capture, arrêt et disparition du périphérique. Tester d'abord les entrées synthétiques, puis les vrais appuis PowerA. Arrêter si une réduction SIP/AMFI ou une extension non prévue est demandée. Ne pas démarrer de jeu pour la première vérification.
4. **Option indépendante** : préparer un rapport Feedback Apple sur `supportsHIDDevice = YES` sans `GCController`, sans le soumettre à la place de l'utilisateur.

## Inconnues

- Le fonctionnement de la PowerA avec OJD, directement ou par son flux JSON, n'a pas été testé.
- L'attente éventuelle, par le pilote Nintendo d'Apple, d'un ACK `0x21` ou d'une calibration SPI avant de créer le `GCController`.
- Les critères supplémentaires au-delà des entrées du `Info.plist`, notamment le descripteur ou les noms.
- Les changements de critères dans macOS 27.2, et si le filtrage du virtuel se fait par transport ou par VID/PID.
- La réponse d'Apple à une demande d'entitlement d'un développeur particulier.
- La cause des identifiants zéro de la PowerA : enregistrement DID absent, mal formé ou autre comportement de macOS. Aucune lecture SDP n'a été réalisée.

## Sources

Fiabilité : **A** = doc officielle Apple ou spécification ; **B** = code ou doc d'un projet, résultat matériel seulement lorsqu'explicitement rapporté ; **C** = témoignage de forum ou d'issue ; **D** = lu seulement par un miroir, ou en partie contredit.

Sources du complément, ouvertes le 2026-11-05. Pour les sources B, le code établit son contrat, mais ne prouve pas un fonctionnement matériel. Les résultats du wiki restent des témoignages de mainteneur. Aucune signature de DMG inspectée, aucun test OJD exécuté ici.

- [A1] https://developer.apple.com/documentation/corehid/hidvirtualdevice (A, métadonnées JSON officielles : introduction macOS 15.0)
- [A2] https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.hid.virtual.device (A, clé documentée depuis macOS 10.15)
- [O1] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/README.md (B, fonctionnalités annoncées)
- [O2] https://github.com/xsyetopz/OpenJoystickDriver/wiki/Playing-Games (B/C, tests rapportés et limites par profil)
- [O3] https://github.com/xsyetopz/OpenJoystickDriver/wiki/Permissions-and-Security (B/C, signature annoncée et permissions)
- [O4] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriver/App/Host.entitlements (B, entitlements demandés, pas preuve d'octroi)
- [O5] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverMacOSPlatform/HID/HIDDeviceStream%2BDeviceLifecycle.swift (B, `nativePassThrough`)
- [O6] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverKit/Protocol/Catalog/DeviceCatalog.swift (B, `takesOwnership` et validation du vendor non nul)
- [O7] https://github.com/xsyetopz/OpenJoystickDriver/wiki/Command-Reference (B, `controller claim` et `virtual feed`)
- [O8] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverCLI/Commands/Virtual/VirtualFeedCommand.swift (B, stdin JSON et RPC)
- [O9] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverService/Runtime/VirtualFeedRegistry.swift (B, identité virtuelle sans fiche source, fermeture du flux)
- [O10] https://github.com/xsyetopz/OpenJoystickDriver/releases/tag/0.6.0-alpha.1 (B, publication et asset DMG, API GitHub lue)
- [O11] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverMacOSPlatform/Output/IOHIDVirtualDeviceBackend.swift (B, périphérique virtuel en espace utilisateur)
- [O12] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverKit/Device/ControllerModelID.swift (B, identité observée zéro représentable)
- [O13] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/docs/testing/consumer-binding.md (B/C, Switch virtuel : `supportsHIDDevice` seulement côté Apple)
- [S1] https://github.com/Peterksharma/switch2mac/blob/a8f2e61e85c3/Sources/FinallyTheControllerWorks/Protocol/Switch2Protocol.swift (B, filtre des modèles Switch 2)
- [S2] https://github.com/Peterksharma/switch2mac/issues/3 (C, signature refusée rapportée par un utilisateur, non reproduite)

Sources du complément Switch Pro, ouvertes le 2026-11-05. Les URLs ppxq utilisées sont conservées telles que retournées, les liens de code figés précisent la vérification :

- [N1] https://github.com/LizardByte/libvirtualhid/blob/v2026.1104.2126.25/src/core/profiles.cpp#L2027-L2045 (B, identité et descripteur)
- [N2] https://github.com/LizardByte/libvirtualhid/blob/v2026.1104.2126.25/src/platform/macos/broker/libvirtualhid_macos_broker.cpp#L203-L207 (B, réponses Nintendo dans le broker)
- [N3] https://github.com/LizardByte/libvirtualhid/blob/v2026.1104.2126.25/src/shared/switch_pro_protocol.hpp (B, initialisation et calibration)
- [N4] https://github.com/LizardByte/libvirtualhid/blob/master/docs/macos-gamepad.md (B, source ppxq, service signé annoncé, installation, licence et limites réseau)
- [N5] https://github.com/LizardByte/libvirtualhid/releases (B, source ppxq, préversion `v2026.1104.2126.25`, API lue)
- [N6] https://github.com/LizardByte/libvirtualhid/blob/master/examples/gamepad_adapter.cpp (B, source ppxq, API d'entrée et profil `switch`)
- [N7] https://github.com/LizardByte/libvirtualhid/blob/master/README.md (B, source ppxq, licence machine obligatoire et licences logicielles)
- [N8] https://github.com/LizardByte/libvirtualhid/blob/master/docs/end-user-gamepad-guide.md (B/C, source ppxq, résultats Switch Pro situés dans Steam)
- [N9] https://github.com/LizardByte/libvirtualhid/pull/208 (B/C, contre-preuve primaire à la généralisation « aucun HID virtuel dans GameController », cas Xbox uniquement)
- [N10] https://github.com/xsyetopz/OpenJoystickDriver/blob/3552be925d7dacef3fd895ac0c6cbf39e9d3cd70/Sources/OpenJoystickDriverKit/Output/Profiles/VirtualDevice.swift (B, trois formats de rapports acceptés)
- [N11] https://github.com/Cookiekira/ns2pro-bridge (B, source ppxq, README lu : Switch 2 et Linux/Windows)

Apple :
- https://developer.apple.com/documentation/gamecontroller/understanding-game-controller-backward-compatibility (A)
- https://developer.apple.com/documentation/gamecontroller/gccontroller/supportshiddevice(_:) (A)
- https://developer.apple.com/documentation/gamecontroller/gcvirtualcontroller (A)
- https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.hid.virtual.device (A)
- https://developer.apple.com/tutorials/data/documentation/bundleresources/entitlements/com.apple.developer.hid.virtual.device.json (A)
- https://developer.apple.com/documentation/corehid (A)
- https://developer.apple.com/tutorials/data/documentation/corehid/creatingvirtualdevices.json (A)
- https://developer.apple.com/documentation/corehid/hiddeviceclient/vendorid (A)
- https://developer.apple.com/documentation/corehid/hidvirtualdevice/properties/vendorid (A)
- https://developer.apple.com/system-extensions/ (A)
- https://developer.apple.com/documentation/driverkit/requesting-entitlements-for-driverkit-development (A)
- https://developer.apple.com/documentation/hiddriverkit (A)
- https://developer.apple.com/documentation/hiddriverkit/match-criteria (A)
- https://developer.apple.com/programs/whats-included/ (A)
- https://raw.githubusercontent.com/opensource-apple/IOKitUser/master/hid.subproj/IOHIDUserDevice.h (A, code source Apple ancien)
- https://developer.apple.com/forums/tags/hiddriverkit (C, réponse d'ingénieur Apple citée)
- https://developer.apple.com/forums/thread/812774 (D : accès direct bloqué, lu par r.jina.ai par une recherche et inaccessible pour une autre)
- https://developer.apple.com/forums/thread/768586 (D : lu par r.jina.ai)
- https://developer.apple.com/forums/thread/848602 (D : lu par https://r.jina.ai/https://developer.apple.com/forums/thread/848602 ; cas iOS/BLE, sans réponse)

Bluetooth :
- https://files.bluetooth.com/wp-content/uploads/2024/10/DID.TS_.p6.pdf (A)
- https://raw.githubusercontent.com/bluekitchen/btstack/master/src/bluetooth_sdp.h (B)
- https://github.com/bluez/bluez/issues/4 (C, mainteneur BlueZ, contexte Linux)

Protocole Nintendo :
- https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/bluetooth_hid_subcommands_notes.md (B)
- https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/bluetooth_hid_notes.md (B)
- https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/USB-HID-Notes.md (B)

Manettes virtuelles et pilotes :
- https://github.com/xsyetopz/OpenJoystickDriver (B)
- https://github.com/xsyetopz/OpenJoystickDriver/wiki/Playing-Games (B)
- https://github.com/xsyetopz/OpenJoystickDriver/blob/main/docs/development/apple-controller-ownership.md (C, observation sur macOS 26.6.1)
- https://github.com/xsyetopz/OpenJoystickDriver/blob/main/docs/development/xbox-identities.md (B)
- https://github.com/xsyetopz/OpenJoystickDriver/blob/main/docs/development/wire-protocols.md (B)
- https://github.com/LizardByte/libvirtualhid/pull/208 (B, fusionnée le 2026-10-30)
- https://raw.githubusercontent.com/LizardByte/libvirtualhid/master/docs/macos-gamepad.md (B)
- https://raw.githubusercontent.com/LizardByte/libvirtualhid/master/docs/platform-support.md (B)
- https://raw.githubusercontent.com/LizardByte/libvirtualhid/master/docs/end-gamepad-guide.md (B)
- https://github.com/LizardByte/Sunshine/pull/5171 (B, tests de l'auteur sur macOS 26.5)
- https://github.com/LizardByte/Sunshine/pull/5203 (C)
- https://github.com/Peterksharma/switch2mac (C, README et code non testés par nous)
- https://github.com/SillyUtility/VirtualController (B)
- https://github.com/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice/blob/main/README.md (B)
- https://github.com/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice/issues/22 (B)
- https://github.com/nabekhan/X360MacOSReceiverBridge/blob/main/docs/RESEARCH.md (C)

Contexte nxnative et NX2Apple :
- https://github.com/seedds/nxnative/issues/965 (C, sonde de 4 s, autre manette : 8BitDo 2DC8:301B)
- https://github.com/LNPANDY/NX2Apple/issues/740 (C, plan du mainteneur, sans capture de paquets)
- https://forums.macrumors.com/threads/apple-is-working-on-two-unreleased-game-controllers.2488482 (C, post d'un utilisateur)

Écartées car illisibles : https://github.com/trollzem/Lumen (404) et un post Reddit sur macOS 27 (403). Elles ne fondent aucune affirmation ici.
