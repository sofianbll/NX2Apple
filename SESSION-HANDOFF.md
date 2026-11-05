# NX2Apple first-launch handoff

Updated: 2026-11-05 01:03 Europe/Paris (00:03 UTC).

## Objective and agreed order

Sofian wants to try the **unchanged launcher built from his fork first**, configure its folders himself with short guidance, and manually try his existing Mac games. Only after that trial should PowerA implementation be considered. The agent handles code and written artifacts. Do not substitute the upstream release ZIP for this source-built app.

The separate, approved PowerA audit is finished. Its proposals are **not authorization to implement** them.

## Workspace and ownership

- Fork: <https://github.com/sofianbll/NX2Apple>.
- Checkout: `/Users/sofian/Games/Fabrique/NX2Apple`.
- Branch: `local/launcher-v1.1.0`, based on release tag `v1.1.0`, source commit `2f788d6b55192952dfacaf97f24700d7668610b6`.
- This is a shallow, single-tag clone. The remote fork's `main` is newer (`8d13135e2a1eec10406f6b486157ec1d2f56eafd` when checked). Do not silently change the baseline or auto-update it.
- Git hooks are installed with `core.hooksPath=.githooks`. Follow `AGENTS.md`: no bypasses and no direct push to main.
- Outgoing coordinator: `ses_e5715d3ecffeY1gwHkoZjk2xYF`.
- Session `ses_e576718d7ffeqk0pZw5ppuzrqD` owns NXNative disk management and game builds. **Do not touch `/Users/sofian/Games/NXNative/source`, `.build` or `games`.** Do not start duplicate game builds.

## Verified result

The official `tools/try-local --no-open` completed with exit code **0**, in **726 seconds**. No launcher source was modified, and no game was rebuilt, moved or opened by this session.

- App: `.build/local-app/NX2Apple.app`.
- Version: `1.1.0-local`; bundle ID: `org.nxnative.NSPortBuilder`.
- Engine ID: `641d1480021a57840b7acc15f92cbd86ecfae611-de8d83152878`.
- Build provenance printed `8d8776a5ba5d` because the audit-only commit landed while the build ran. `git diff v1.1.0 -- frontend tools patches .upstream-ref` was empty afterwards.
- Official bundle verification: **20 checks passed**; engine-tree and bundled SPIRV-Cross checks passed.
- Independent `codesign --verify --deep --strict` passed.
- Version, bundle ID, build exit code and compiled `__TEXT,__text` section matched expectations. An initial raw-byte comparison was rejected as an invalid expectation because ad-hoc signing changes executable bytes; the text-section comparison passed.
- Full log: `.build/launcher-v1.1.0.log`; exit record: `.build/launcher-v1.1.0.exit`.
- Cache: `.build/local-cache/`. Preserve it; the first bundled-tools build took 150 seconds.
- The tmux build and its completion watcher have finished. The first relative-path attempt failed before compilation; the successful run used the absolute script path. Use absolute paths with the existing tmux server.
- No NX2Apple process was found at handoff. **The app has not been opened, configured or gameplay-tested.** Swift emitted warnings, but the build succeeded. No Swift test suite or UI automation was run.

## Folders and existing games

- `/Users/sofian/Games/Jeux`: six existing `.app` bundles and their `.app.key` sidecars. All six passed read-only checks for a 16-digit `DMTitleID` and executable launcher plus `dmhost`. Actual NX2Apple discovery remains untested.
- `Jeux/Sauvegardes/` contains links to the existing saves under `~/Library/Application Support/nxnative/<ID>/save`; `Jeux/Mods/` is empty, according to the prior session. Do not relocate or rewrite saves.
- `/Users/sofian/Games/NXNative/apps` points to `../Jeux` (prior session's arrangement).
- `/Users/sofian/Games/Fabrique/Sorties` was created, empty, for a later output-folder selection. No app setting was changed.
- Choosing the games folder can also reset the output folder. Guide Sofian through **Settings → Library → Your games folder** = `~/Games/Jeux`, then choose **Output folder** = `~/Games/Fabrique/Sorties` if he agrees. Do not initiate a game build.

## Next actions and safety gates

1. Read `AGENTS.md`, `README.md`, this handoff and `POWERA-AUDIT.md`. Recheck git state, app existence, signature and running processes; do not rebuild merely to resume.
2. Arrange the **first launcher opening** with Sofian. He requested opening the app, but has a strict rule against surprise windows, clicks or Mac automation: obtain his fresh approval before doing it in the successor session, or let him open it himself. Never launch games or UI-driving tests without current explicit consent.
3. Guide folder configuration in as few steps as possible. Sofian performs the configuration. Check that six games appear; let him try **Jouer** and report observed behavior. The source opens an already-ready Mac app directly (`frontend/Sources/NX2Apple/LauncherView.swift:590-620`), but runtime behavior is not yet verified. If a rebuild is proposed, stop instead of accepting it.
4. Only after that trial, discuss whether and how to implement PowerA navigation. Do not apply patches now.

The official build printed this opening command (use only after fresh approval and checking no NX2Apple instance is running):

```sh
open -n /Users/sofian/Games/Fabrique/NX2Apple/.build/local-app/NX2Apple.app --args \
  -autoUpdateApp '<false/>' -engineChannel stable \
  -engineID 641d1480021a57840b7acc15f92cbd86ecfae611-de8d83152878 \
  -autoUpdateRepo '<false/>'
```

The development app shares preferences and Application Support with an installed NX2Apple. Do not open two copies concurrently. It is ad-hoc signed, not notarized or an upstream release. Do not disable Gatekeeper or bypass update/signature safeguards.

## Audit and evidence

- `POWERA-AUDIT.md`, committed as `8d8776a` (`docs: audit event-driven PowerA launcher integration`). It proposes an event-driven, nonexclusive IOHID connector feeding existing actions, with explicit focus and duplicate-input handling. Home in the game is separate. Hardware behavior and permissions remain unknown.
- Workflow `wf_UHsdFA5rluWJCo6U` (`nx2apple-powera-audit`): **all four agents completed**. Three readings used `mistral/deepseek-v4-1-flash-1017#low`; synthesis used `openai/gpt-6.1-terra`. Results remain available through `workflow.result`; do not restart it.
- Prior authoritative research: `/Users/sofian/Games/NXNative/docs/research/nx2apple-emplacements.md`, `nx2apple-manette-pr989.md`, `nx2apple-manette-launcher.md`, and the latest entry in `/Users/sofian/Games/NXNative/docs/wiki/index.md`.
- Game patch reference: <https://github.com/seedds/nxnative/pull/989>, linked to the outgoing session. Existing patches may be read under `/Users/sofian/Games/NXNative/tools/patches/`; do not modify their engine checkout.

## Communication and scope

Speak simple French. Keep the main goal ahead of the audit. No Claude subagents: Anthropic credit is exhausted. One build at a time, in a fresh detached tmux session, preserving caches. Commit ready work without bypassing hooks; do not publish or push unrelated changes.

Sofian requires final replies through a short `openchamber_render` page, starting with what he should do now. Prefer simple native UI components if a custom page cannot be headlessly checked at 720 and 360 px. Decisions use a clickable mini-app with **Aucune ne me va** and a free remark; keep the submitted summary short and remarks only in data. Do not repeat the page in the following text. Link issues/PRs used for work to the successor session. Current session handoff is not completion of installation or gameplay validation.
