# Références UI pour NXNative — Cinéma & Console

Revue du 2026-11-04, à partir des captures, vidéos et documentations liées. **Les durées et dimensions proposées sont des cibles NXNative, pas des timings constructeur vérifiés** ; aucune analyse image par image n’a été faite. Les ratios non documentés ou dépendants des thèmes sont signalés.

## 1. PlayStation 5 — Home *(Cinéma + Console)*
- **Copier — layout :** une rangée horizontale courte d’icônes carrées **1:1**, beaucoup de fond libre, puis des cartes contextuelles ; le Control Center est un overlay inférieur appelé à la demande, pas une barre permanente encombrante.
- **Copier — focus & données :** icône active légèrement agrandie, titre du seul jeu sélectionné, artwork plein écran synchronisé ; activités/progression sous la sélection plutôt que du texte sur chaque icône.
- **Motion cible :** agrandissement spring **200–250 ms**, très léger dépassement ; fondu du fond **250–350 ms**, sans déplacer toute la page.
- **Éviter :** empiler activités, actualités et promotions ; multiplier les halos ; faire défiler dix cartes avant de retrouver sa bibliothèque.
- **Sources :** [PlayStation Blog — official PS5 UX walkthrough, screenshots and video](https://blog.playstation.com/2020/10/15/first-look-playstation-5s-next-generation-user-experience/).

## 2. Xbox Series X|S — Home *(Cinéma)*
- **Copier — layout :** raccourcis Library/Store/Search/Settings tout en haut, jeux récents vers le bas, grand espace réservé au fond personnalisé ; groupes épinglés pour les collections utiles.
- **Copier — focus & ratios :** bord lumineux et tuiles carrées/rectangulaires regroupées par type ; fond assorti au jeu survolé. Pour NXNative, normaliser à **1:1** pour les systèmes et **16:9** pour les bannières, sans tailles arbitraires dans une même rangée.
- **Motion cible :** focus **160–220 ms**, changement de fond **250–350 ms** ; déplacement linéaire du contenu minimal.
- **Éviter :** la densité des rangées recommandées/publicitaires et les tuiles promotionnelles concurrentes des jeux ; ne pas reproduire le mélange de formats dans la grille Cinéma.
- **Sources :** [Xbox Wire — annotated new Home layout](https://news.xbox.com/en-us/2023/07/26/welcome-to-your-new-xbox-home/) · [Xbox Support — pin and customize Home](https://support.xbox.com/en-US/help/account-profile/customize-xbox-home/customize-your-home).

## 3. Nintendo Switch — HOME Menu *(Console)*
- **Copier — layout :** rangée unique de jeux **1:1**, raccourcis système circulaires en bas, profil en haut à gauche et état système en haut à droite ; entrée « All Software » pour la grille complète.
- **Copier — focus & données :** contour clair très lisible, titre du seul logiciel actif au-dessus de la rangée, aucun texte répété sous toutes les icônes ; dock direct pour News/Controllers/Settings/Sleep.
- **Motion cible :** réponse presque immédiate, contour/déplacement **120–180 ms**, petit rebond facultatif terminé en **200 ms**.
- **Éviter :** une file horizontale sans fin ni raccourci vers la grille ; les icônes de dock ambiguës sans libellé au focus ; les animations décoratives permanentes.
- **Sources :** [Nintendo Support — HOME Menu overview and labeled screenshot](https://en-americas-support.nintendo.com/app/answers/detail/a_id/22308/~/nintendo-switch-home-menu-overview).

## 4. Steam Big Picture / Steam Deck *(Cinéma + Console)*
- **Copier — layout :** navigation conçue manette/TV, rangées de jeux récents puis capsules ; page jeu avec grand hero, logo détouré, action Play dominante et détails de progression.
- **Copier — ratios & données :** capsule bibliothèque officielle **600×900 (2:3)**, hero **3840×1240 (~3,1:1)**, logo PNG au-dessus ; sous la sélection : dernière session, temps de jeu, succès/statut, pas une fiche complète par tuile.
- **Copier — focus & dock :** capsule agrandie + contour, commandes avec glyphes contextuels en bas ; cible **180–240 ms** pour le focus et **250–400 ms** pour le hero.
- **Éviter :** transposer les petits filtres du client desktop ; faire concurrence au bouton Play ; lancer automatiquement bande-annonce ou audio à chaque déplacement.
- **Sources :** [Steamworks — exact Library asset dimensions](https://partner.steamgames.com/doc/store/assets) · [Valve — Big Picture redesigned from Steam Deck UI](https://steamcommunity.com/games/593110/announcements/detail/3394051164709183117).

## 5. Apple TV / tvOS *(Cinéma)*
- **Copier — layout :** contenu d’abord, hero/Top Shelf cinématographique et rangées homogènes ; cibles NXNative : posters **2:3**, bannières **16:9**. tvOS n’impose pas un ratio unique pour toutes les apps.
- **Copier — focus & données :** un seul élément focalisé, doucement agrandi et mis en relief ; métadonnées révélées pour cet élément seulement. Parallaxe d’images en calques très discrète si pointeur/trackpad disponible.
- **Motion cible :** spring **200–250 ms**, ombre/échelle simultanées, parallaxe bornée ; aucune temporisation constructeur publique vérifiée.
- **Éviter :** forte inclinaison 3D, zoom excessif, texte minuscule « 10-foot UI », ou métadonnées qui font sauter la grille à chaque focus.
- **Sources :** [Apple HIG — focus system and gentle expansion](https://developer.apple.com/design/human-interface-guidelines/designing-for-tvos) · [Apple HIG — layered images and parallax](https://developer.apple.com/design/human-interface-guidelines/images).

## 6. Plex / Jellyfin *(Cinéma)*
- **Copier — layout :** rail latéral de sources personnalisable, onglets Recommended/Library, accueil en rangées Continue Watching/Recently Added ; bibliothèque avec tri/filtres en haut et page détails séparée.
- **Copier — ratios & focus :** posters **2:3**, paysages/episodes **16:9** (conventions NXNative, ratios non spécifiés par les docs) ; sélection nette, métadonnées détaillées sur l’élément ouvert, titre court au focus dans la grille.
- **Motion cible :** ouverture du rail **180–220 ms**, focus **160–220 ms**, simple fondu des détails **200–300 ms**.
- **Éviter :** recommandations infinies avant la bibliothèque, actions multiples sur chaque poster, filtres permanents qui réduisent la grille, et publicité/contenu en ligne sans rapport avec la collection locale.
- **Sources :** [Plex Support — big-screen sidebar, rows and Library tabs](https://support.plex.tv/articles/navigating-the-big-screen-apps/) · [Jellyfin — official Home, Library and Details screenshots](https://jellyfin.org/).

## 7. Playnite / LaunchBox Big Box *(Cinéma + build card)*
- **Copier — layout :** Playnite Details View associe liste compacte et panneau droit média/métadonnées ; Grid View privilégie les jaquettes ; Big Box fournit le mode home-cinema/manette. C’est une bonne base pour la carte Build à droite.
- **Copier — données :** titre, plateforme, état installé, temps de jeu et média dans le panneau de sélection ; recherche/tri disponibles sans recouvrir les jaquettes. Ratios et placement dépendent des thèmes/réglages : **pas de ratio fixe vérifié**, retenir **2:3**.
- **Motion cible :** interface surtout utilitaire ; ajouter seulement un fondu de panneau **150–220 ms** et conserver le focus pendant les changements de vue.
- **Éviter :** chrome desktop, colonnes et filtres exposés par défaut, multiplicité des thèmes/options, et panneau de détails plus large que la bibliothèque.
- **Sources :** [Playnite manual — Details, Grid and List views](https://api.playnite.link/docs/manual/gettingStarted/playniteDesktopMode.html) · [LaunchBox — official Big Box positioning](https://www.launchbox-app.com/).

## 8. EmulationStation ES-DE / Pegasus *(Console)*
- **Copier — layout :** séparation System View → Gamelist View ; logos/artworks de consoles d’abord, puis jaquette, capture/vidéo et métadonnées du jeu actif. Idéal pour le carrousel TV/manette de Console.
- **Copier — ratios & focus :** système central nettement dominant, systèmes voisins visibles pour annoncer le déplacement ; ratios **dépendants du thème**, non standardisés. Convention NXNative proposée : systèmes **1:1**, jeux **2:3**, captures **16:9**.
- **Motion cible :** snap du carrousel **200–250 ms**, métadonnées en fondu **150–250 ms** ; si vidéo, démarrer seulement après **500–800 ms** d’immobilité, sans son par défaut.
- **Éviter :** thèmes visuellement incohérents d’un système à l’autre, listes denses, métadonnées complètes permanentes et vidéos qui redémarrent à chaque appui répété.
- **Sources :** [ES-DE — System/Gamelist screenshots and theme examples](https://es-de.org/) · [Pegasus — theme system and layout flexibility](https://pegasus-frontend.org/docs/themes/overview/).

## Synthèse — 10 règles actionnables pour NXNative
1. **Un seul focus dominant :** échelle **1,04–1,08**, contour **2–3 px**, spring **200–250 ms** ; assombrir les voisins seulement si nécessaire, jamais plusieurs zooms simultanés.
2. **Cinéma en trois zones stables :** rail sombre étroit à gauche, hero sur environ **35–40 %** de la hauteur, grille de jaquettes dessous ; aucun changement de largeur pendant la navigation.
3. **Une géométrie par type :** jaquettes **2:3** partout, systèmes **1:1**, bannières **16:9** ; recadrer sans déformer et prévoir un placeholder du même ratio.
4. **Métadonnées sur la sélection uniquement :** titre + plateforme/build + dernière session ou état ; au maximum **deux badges** par tuile (ex. update, running), sans chiffres décoratifs.
5. **Hero réactif mais stable :** focus immédiat, artwork après **100–150 ms** de stabilisation, crossfade **250–350 ms** ; annuler les chargements devenus obsolètes lors d’un défilement rapide.
6. **Console centrée sur le système actif :** TV/manette du choix au centre, voisins partiellement visibles, snap **200–250 ms** ; dock inférieur limité à **5–6 actions**, icône + libellé au focus.
7. **Build card concise :** version, canal, état et date du dernier build, plus **une action principale** ; logs, options avancées et diagnostics dans un écran secondaire.
8. **Barre d’aide toujours prévisible :** en bas, `A/Cross` lancer, `B/Circle` retour, `X/Square` détails, `Y/Triangle` filtrer ; adapter les glyphes à la manette et afficher les équivalents clavier si utile.
9. **Mouvement sobre et accessible :** pas de parallaxe permanente ni autoplay sonore ; avec Reduce Motion, supprimer zoom/parallaxe et utiliser un fondu **≤150 ms** tout en gardant le contour de focus.
10. **Navigation sans perte de contexte :** restaurer focus et scroll au retour, garder les positions rail/grille/dock constantes, et garantir clavier, souris et manette sans impasse de focus.
