# 03: La fenêtre reste confinée au dashboard local

**What to build:** la fenêtre n'affiche que l'origine `http://127.0.0.1:8767` ; les liens `https` externes cliqués (liens Drive privés) et les nouvelles fenêtres s'ouvrent dans le navigateur par défaut ; tout le reste est refusé. Aucun pont JS natif ; ATS limité à `NSAllowsLocalNetworking`. Règles : « Politique de navigation » de [`spec.md`](../spec.md).

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] `NavigationPolicy` testée par table (XCTest) : `allow` pour l'origine exacte ; `openExternally` pour `https` externe sur action utilisateur et pour `target=_blank`/`window.open` ; `deny` pour `localhost:8767`, `127.0.0.1:8768`, `file:`, `javascript:`, `http` externe.
- [ ] Aucune nouvelle WebView n'est jamais créée ; aucune page externe ne s'affiche dans la fenêtre.
- [ ] Aucun `WKScriptMessageHandler` ni schéma personnalisé ; l'Info.plist ne contient ni `NSAllowsArbitraryLoads` ni autre exception ATS.
- [ ] Préférences (`localStorage`) conservées après Quitter puis réouverture (vérification manuelle notée).
