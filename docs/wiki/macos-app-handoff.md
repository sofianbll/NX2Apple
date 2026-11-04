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
