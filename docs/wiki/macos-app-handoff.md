# App Mac NXNative — relais de coordination

Rédigé le 2026-11-04 par `ses_e59a3af88ffeMiB2G5yhgxkJ18` (garde du contexte). Recontrôler chaque fait avant d'agir.

## Objectif et mandat
`NXNative Dashboard.app` installable par DMG, lanceur du workspace `~/Games/NXNative`, qui démarre son serveur et l'arrête à Quitter / crash. Spec et tickets **validés par Sofian** : [`spec.md`](../../.scratch/macos-app/spec.md), [`issues/`](../../.scratch/macos-app/issues/). Décisions datées : [macos-app-decisions.md](macos-app-decisions.md). Flux : implement-spec sous chief-of-staff, sous-agents `implement` sur `kimi-code-plan-global/k3.1-pro-highspeed`. Pas de Goal.

**Autorisé :** travail local sur la branche `desktop-app` et ses worktrees. **Non autorisé sans nouvel accord de Sofian :** fusion dans `main`, push, publication, installation hors test, achat Apple.

## État (à recontrôler)
- Worktree d'intégration `~/Games/NXNative-worktrees/desktop-app`, branche `desktop-app`. Tickets 01, 02, 03 fusionnés et `resolved` (voir décisions).
- Ticket 04 (DMG + `make app-test`) : sous-agent `ses_e596c2563ffehkW6G2MhH1Rr4R`, worktree `~/Games/NXNative-worktrees/t04`, branche `desktop-app-04-dmg`. Résultat : voir la ligne « Ticket 04 » des décisions si présente ; sinon lire la session du sous-agent avant toute relance (ne pas dupliquer).
- Checkout `~/Games/NXNative` sur `main` `a77506c` : `HANDOFF.md` modifié et `docs/research/` non suivi **appartiennent à des sessions antérieures, à préserver**. `source/` 65501fb + patch PowerA intouché.
- Le 04 peut avoir posé `defaults local.nxnative.dashboard WorkspacePath` (doit être supprimé à sa fin) et un symlink `.venv` gitignoré dans t04.

## Prochaines actions
1. Revue du diff 04, contrôle que rien ne reste (port 8767, tmux témoin, `defaults read local.nxnative.dashboard`), fusion ff dans `desktop-app`, ticket 04 `resolved`.
2. Coordination : installer depuis le DMG dans `/Applications`, lancer, captures (dashboard, conflit, workspace invalide) relues ; vérif manuelle persistance localStorage, Cmd+V, lien https → navigateur. Le checkout `main` n'a pas `--stop-on-stdin-eof` : tester avec `WorkspacePath` = worktree d'intégration (+ symlink `.venv`), ou après fusion dans main si Sofian l'accepte.
3. Skill `code-review` (Standards + Spec) sur `desktop-app` depuis `a77506c` ; corrections dans un seul implémenteur.
4. Demander à Sofian : fusion `desktop-app` → `main` (préserver HANDOFF.md / docs/research non suivi : `docs/research/macos-app-packaging.md` est identique sur la branche, à vérifier puis retirer la copie non suivie avant merge).
5. Nettoyer les worktrees d'implémenteurs.

## Risques
- Héritage du côté écriture du pipe par l'enfant (EOF jamais reçu après `kill -9`) : prouvé seulement si `make app-test` passe.
- Hindsight injoignable le 2026-11-04 (timeout) : initiative non enregistrée.
