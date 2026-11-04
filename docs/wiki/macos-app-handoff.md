# App Mac NXNative — relais de coordination

Rédigé le 2026-11-04 par `ses_e59a3af88ffeMiB2G5yhgxkJ18` (garde du contexte). Recontrôler chaque fait avant d'agir.

## Objectif et mandat
`NXNative Dashboard.app` installable par DMG, lanceur du workspace `~/Games/NXNative`, qui démarre son serveur et l'arrête à Quitter / crash. Spec et tickets **validés par Sofian** : [`spec.md`](../../.scratch/macos-app/spec.md), [`issues/`](../../.scratch/macos-app/issues/). Décisions datées : [macos-app-decisions.md](macos-app-decisions.md). Flux : implement-spec sous chief-of-staff, sous-agents `implement` sur `kimi-code-plan-global/k3.1-pro-highspeed`. Pas de Goal.

**Autorisé :** travail local sur la branche `desktop-app` et ses worktrees. **Non autorisé sans nouvel accord de Sofian :** fusion dans `main`, push, publication, installation hors test, achat Apple.

## État (à recontrôler)
- Worktree d'intégration `~/Games/NXNative-worktrees/desktop-app`, branche `desktop-app`. Tickets 01, 02, 03 fusionnés et `resolved`.
- **Ticket 04 incomplet** : WIP `c55170d` sur `desktop-app-04-dmg`, worktree `~/Games/NXNative-worktrees/t04` (sous-agent `ses_e596c2563ffehkW6G2MhH1Rr4R` terminé). Détail des cas passés/échoués : ligne « Ticket 04 » de [macos-app-decisions.md](macos-app-decisions.md). Reste : contrôle UI seconde instance par AX ciblant un PID, `swift test` (timeout 120 s à lancer avec délai plus long ou en tmux), `make test`, doc « Ouvrir quand même » dans le README, merge de `desktop-app`, puis fusion ff.
- Le 04 a modifié `snapshot()` (`source_stamp` seulement si des jeux) : changement hors ticket, à juger en revue.
- `defaults local.nxnative.dashboard WorkspacePath` supprimé et symlink `.venv` retiré par le 04 (à recontrôler). `.gitignore` `/.venv/` ne couvre pas un symlink : le 04 a modifié `.gitignore`, vérifier.
- Checkout `~/Games/NXNative` sur `main` `a77506c` : `HANDOFF.md` modifié et `docs/research/` non suivi **appartiennent à des sessions antérieures, à préserver**. `source/` 65501fb + patch PowerA intouché. **`main` n'a pas `--stop-on-stdin-eof`** : l'app installée avec `WorkspacePath` par défaut affichera un échec de démarrage tant que `desktop-app` n'est pas fusionnée dans `main` (accord de Sofian requis).
- Sofian a essayé le DMG de t04 : bloqué par Gatekeeper. Décision : DMG seul + doc « Ouvrir quand même ».

## Prochaines actions
1. Reprendre le 04 (un implémenteur, Kimi K3.1 Pro Highspeed, ≤ 2 cycles) : remplacer System Events par AX par PID, README « Ouvrir quand même », relancer `swift test` (sans timeout 120 s), `make test`, `make dmg`, `make app-test` ; merge `desktop-app` ; fusion ff ; ticket `resolved`.
2. Skill `code-review` (Standards + Spec) sur `desktop-app` depuis `a77506c` ; corrections dans un seul implémenteur.
3. Demander à Sofian la fusion `desktop-app` → `main` (avant : vérifier que `docs/research/macos-app-packaging.md` non suivi est identique à la copie de la branche, puis retirer la copie non suivie ; préserver `HANDOFF.md`).
4. Après fusion : Sofian installe depuis le DMG (Ouvrir quand même) ; coordination : captures (dashboard, conflit, workspace invalide) à 720/360 si pertinent, vérif manuelle localStorage, Cmd+V, lien https → navigateur.
5. Nettoyer les worktrees d'implémenteurs (t04).

## Risques
- Contrôle UI seconde instance non prouvé automatiquement (comportement manuel observé correct par l'implémenteur, non revérifié par la coordination).
- Hindsight injoignable le 2026-11-04 (timeout) : initiative non enregistrée.

## Reprise du 2026-11-04 — `ses_e594dd988ffeaw38KlFY31gjTI`

Cette entrée datée **supersède l'ancien état « Ticket 04 incomplet » et le risque de contrôle AX ci-dessus**, sans réécrire l'historique laissé par `ses_e59a3af88ffeMiB2G5yhgxkJ18`.

- `desktop-app`, initialement propre à `a0c33a8`, a été fusionnée en **fast-forward** avec `desktop-app-04-dmg` après vérification des branches et de l'ascendance. Résultat : `4a560bf`, qui inclut `c55170d` (WIP), `97bbe1c` (résolution du ticket 04) et le merge d'intégration. Aucun push, aucune installation et aucune modification de `main`.
- Preuves de t04 relues dans `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nxnative-t04/`, sans nouvelle recette parallèle : `swift-test.log` = 11 XCTest ; `make-test.log` = 58 + 30 Python et 3 Node ; `make-dmg.log` = DMG vérifié et `DIFF_OK` ; `app-test-ax-1.log` = six PASS, dont seconde instance, avec contrôle AX par PID dans `app_test.py`.
- État recontrôlé : `WorkspacePath` absent des defaults, `.venv` absent de t04, port 8767 libre, session tmux utilisateur `0` intacte. `main` reste à `a77506c` avec `HANDOFF.md` modifié et l'étude non suivie à préserver ; son `docs/research/macos-app-packaging.md` et la copie intégrée ont le même SHA1 `eaf4bca08b35695cdad950fc7797309188e78632`, à recontrôler avant toute future fusion.
- Le changement `snapshot()` de `c55170d`, hors ticket, reste à juger en revue. Installation `/Applications`, captures dashboard/conflit/workspace invalide et vérifications `localStorage`, Cmd+V et lien HTTPS restent **non faits**.

### Prochaines actions actualisées
1. Exécuter la revue **Standards + Spec** de `a77506c..HEAD`, en incluant explicitement `snapshot()` ; traiter ensuite les éventuels correctifs séparément.
2. Demander l'accord de Sofian pour `desktop-app` → `main`. Avant cette fusion, préserver `HANDOFF.md` et recontrôler l'identité SHA1 de l'étude non suivie.
3. Après accord et fusion seulement : installation dans `/Applications`, captures et contrôles manuels restants. Ne pas nettoyer le worktree t04 à ce stade.
