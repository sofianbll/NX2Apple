# NX2Apple coordination handoff

Updated: 2026-11-05 02:00 Europe/Paris (01:00 UTC, latest process snapshot).

## Coordination and permissions

- Successor coordinator: `ses_e56c6f395ffeuzg2lIe5Q4GIVz`, titled **[NX2Apple] - 🟢 - Jeux et mods Z-A**.
- Outgoing coordinator: `ses_e56fa33a3ffemNK0NPzODIxyWI`. The earlier handoff came from `ses_e5715d3ecffeY1gwHkoZjk2xYF`. Continue this initiative in the successor only.
- Sofian wanted the **unchanged launcher built from his fork**, his own short-guided folder configuration, then manual trials of six existing Mac games. The launcher was opened with fresh consent and **Sofian confirmed Pokémon Z-A works**. Do not repeat the build or first opening.
- The latest request, inspection of the exact GameBanana file below, is complete. The context guard requested this committed handoff and a successor, **not implementation**. Await Sofian's next direction before starting another substantive task.
- No mod installation, FPS patch, PowerA implementation, cache migration, game rebuild or source-baseline change has been authorized. Research and an approved audit do not grant those permissions.
- Session `ses_e576718d7ffeqk0pZw5ppuzrqD` owns NXNative disk management and game builds. **Do not touch `/Users/sofian/Games/NXNative/source`, `.build` or `games`.** One build at a time, never start a duplicate.

## Checkout and ready launcher

- Fork: <https://github.com/sofianbll/NX2Apple>.
- Checkout: `/Users/sofian/Games/Fabrique/NX2Apple`.
- Branch: `local/launcher-v1.1.0`, based on tag `v1.1.0`, source commit `2f788d6b55192952dfacaf97f24700d7668610b6`. This shallow, single-tag clone must stay on that baseline unless explicitly agreed otherwise.
- Previous documentation commits: `8d8776a` (PowerA audit), `f5592e5` (first handoff). This successor handoff and `POKEMON-ZA-PERFORMANCE.md` are committed together. Use `git log -1` for their commit ID.
- `core.hooksPath=.githooks` was rechecked. Git author identity is Sofian's, not upstream's. No hook bypass, direct push to main, release or publication is authorized by this handoff.
- `git diff v1.1.0 -- frontend tools patches .upstream-ref` remained empty. **No runtime source was changed.**
- Official `tools/try-local --no-open`: exit **0**, **726 seconds**, **20 bundle checks passed**, engine-tree/SPIRV-Cross checks passed. Independent `codesign --verify --deep --strict` passed again when this session resumed.
- App: `/Users/sofian/Games/Fabrique/NX2Apple/.build/local-app/NX2Apple.app`, version **1.1.0-local**, bundle ID `org.nxnative.NSPortBuilder`, executable **NSPortBuilder**, not NX2Apple.
- Engine ID: `641d1480021a57840b7acc15f92cbd86ecfae611-de8d83152878`. Build provenance prints `8d8776a5ba5d` because the audit-only commit landed during compilation.
- Evidence: `.build/launcher-v1.1.0.log`, `.build/launcher-v1.1.0.exit`. Preserve `.build/local-cache/` and the finished app. The build and tmux completion watcher finished before this session. There is nothing to compile merely to resume.

## First opening and manual trial: completed, with evidence limits

Sofian chose **Ouvre le launcher maintenant** in the native decision form. After checking no other copy was running, the agent used the official command below. `open` returned 0 and the actual `NSPortBuilder` process was observed. No UI was driven and no game was opened by the agent.

```sh
open -n /Users/sofian/Games/Fabrique/NX2Apple/.build/local-app/NX2Apple.app --args \
  -autoUpdateApp '<false/>' -engineChannel stable \
  -engineID 641d1480021a57840b7acc15f92cbd86ecfae611-de8d83152878 \
  -autoUpdateRepo '<false/>'
```

**Do not run that command again by default.** At 02:00 Paris the launcher was still running as PID **70849**. No `dmhost` or common build-tool process matched the read-only snapshot. Recheck live state before any later action, without stopping another session's work.

Sofian configured the app himself with the short instruction **Settings → Library → Your games folder = `~/Games/Jeux`**, then manually tried Pokémon Z-A and said **"c'est nice, ça fonctionne"**. This is his observed success, not an automated test. The window, exact saved settings, discovery of all six games, frame rate and the other five games were not independently verified. No Swift suite or UI automation ran.

The app shares preferences/Application Support with other NX2Apple copies. Do not open two copies. No Gatekeeper bypass. No app, game, window, click or Mac-driving test without fresh explicit consent at the time. **If a game launch offers a rebuild, stop instead of accepting it.**

## Files and paths to preserve

- `~/Games/Jeux`: six existing game `.app` bundles and their `.app.key` sidecars, unchanged. The prior handoff verified their title IDs and executables. Keep games and saves intact.
- `Jeux/Sauvegardes/` links existing saves under `~/Library/Application Support/nxnative/<ID>/save`. Do not relocate or rewrite them. `Jeux/Mods/` was empty when previously listed.
- `~/Games/NXNative/apps` points to `../Jeux` (earlier arrangement).
- `~/Games/Fabrique/Sorties` was created earlier for a later output-folder choice. Whether Sofian selected it is unknown. The agent changed no app setting. Choosing the games folder can also reset the output folder.
- Sofian asked where `prod.keys` was. Metadata-only checks found `~/Downloads/prod.keys` and `~/Downloads/ProdKeys.-v22.5.0/prod.keys`, none under `~/Games/NXNative/keys`. No key content was read, compared, moved or copied. This question did not authorize reorganizing keys.

## Pokémon Z-A research: completed, do not restart

Read **`POKEMON-ZA-PERFORMANCE.md`**, the evidence report, before giving more advice. It distinguishes the pinned engine, current upstream proposals and the installed app's settings metadata.

- **Sofian's correction:** his concern is the game's **30 FPS cap**, not a diagnosed GPU bottleneck. Do not offer lower resolution/Handheld as the answer to unlocking 60 FPS. Explain clearly what changes code, frame pacing or graphics. No hardware bottleneck or stable frame rate was measured here.
- The installed Z-A app's read-only `Contents/Resources/dm/launcher.json` has **no FPS or render-scale control**. This records available settings/defaults, not active choices or a runtime measurement. The exact installed game's version/build ID has not been matched against a real patch file.
- NX2Apple v1.1.0 **does support RomFS file-replacement mods**, potentially textures/models/data. The launcher passes enabled folders as `DM_ROMFS_OVERLAY` at **Play**, without rebuilding for that mechanism. This does not mean every GameBanana/Nexus mod works. Launching from Finder does not receive that launcher-added environment.
- The folder does **not apply ExeFS `.pchtxt`/`.ips` code patches** in this tag. A mixed folder can misleadingly appear usable while code changes are ignored. Cheats are a separate mechanism, with version and rewritten-code limits.
- **Fichiers de cache** in Settings is the **iPhone frameworks/shell cache**, not a Mac shader-cache import. A Mac build's work folder follows `<output>/<build key>_build`. Existing NXNative cache reuse is **unverified**. No cache was moved or imported and no fast rebuild is promised.

### Exact GameBanana artifact, inspected rather than inferred

Sofian supplied <https://gamebanana.com/mods/627350#FileInfo_1731160>.

- Exact file **1731160** is `pok_mon_legends_z-a_0100f43008c44000_mods__b8ede.zip`, **30,983 bytes**, pack **2.0.2 RC3.0**. The site's API ID, download URL, length and MD5 were matched, not guessed from a search result.
- Source metadata: <https://gamebanana.com/apiv11/Mod/627350/ProfilePage>. Download: <https://gamebanana.com/dl/1731160>.
- Preserved public mod artifact: `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nx2apple-mod-1731160/file1731160.zip`. **Not extracted, executed or installed.** SHA-256 `4e166d04c3f523e1d7ea3660e7c35aa1a22a90a269c1e69d3e976b0c10260043`.
- **9 mods, 39 `.pchtxt` files and one instruction file**, no RomFS/texture assets. All payloads are ExeFS code patches. The first subagent count of eight omitted Reduce Bloom and was corrected after independent ZIP listing.
- It contains Static/Dynamic 60 FPS, 4K Shadows (4096×4096 shadows, not a 4K texture pack), LOD/16× anisotropy, FOV, 21:9, Disable DOF/FXAA and Reduce Bloom. There really are graphics changes, but implemented as code, not replacement textures.
- The 2.0.2 patch headers name build `B1F12FD919EAE86AB8A978317677E64BCE443D1F`. Their byte/offset applicability to the installed game or rewritten image was **not tested**. The stray `v2.pchtxt` is a different build, not the 2.0.2 patch.
- Author tests are on Kenji-NX, not nxnative. Static FPS warns of slowdown below 60, Dynamic has historical movement/softlock warnings. Reported write-site overlaps need analysis before combining variants. No native 60 FPS or GFX effect was tested.
- **Verdict:** this exact ZIP cannot work merely by dropping it into v1.1.0's GameMods folder. It is a candidate for a separately approved adaptation investigation, **not authorization to adapt, install or rebuild**. No compatible Z-A HD texture pack was established by this check.

### Upstream proposals, not integrated

These were read and open on 2026-11-05. Recheck status if using them for a new decision, not to redo completed research:

- <https://github.com/seedds/nxnative/pull/606>: build-gated host-paced Z-A 2.0.2 60 FPS proposal, no gameplay validation claimed by its author.
- <https://github.com/seedds/nxnative/pull/918>: adaptive native timing hook, historical limited gameplay tests and unresolved, load-confounded frame-time regression. **60 FPS cap enabled does not prove 60 FPS sustained.** These are PRs, not ordinary issues.
- <https://github.com/seedds/nxnative/pull/883>: proposed generic ExeFS patch support **at build time**, not included in the local release baseline.
- <https://github.com/seedds/nxnative/issues/374> and <https://github.com/seedds/nxnative/issues/1133>: supporting mod-format context, not proof of runtime validation.

All five are already linked to both the outgoing and successor coordination sessions. The exact archive is also byte-identical to the author's GitHub ZIP, independently verified by Git blob SHA-1 `a41edcd04e14f5733a8fc4ca5012f226028c5b12`.

## Workers and previous PowerA audit

All workers started here have **completed**, including the last follow-up:

- `ses_e56da05abffekf8S1P57m39u0R`: native FPS/settings/mod limitations.
- `ses_e56cf2a81ffe8eSlnzRfPRcMU3`: v1.1.0 GameMods contract.
- `ses_e56cadb18ffeAyofMEnFDXfk6V`: exact GameBanana artifact and provenance follow-up.

They used `mistral/deepseek-v4-1-flash-1017#low`. Do not relaunch them. Their results are integrated and independently checked where stated in the report.

`POWERA-AUDIT.md` is finished, committed as `8d8776a`. It is **not implementation approval**. Prior workflow `wf_UHsdFA5rluWJCo6U` also has all four agents completed. Do not restart it or create a new workflow unasked. Prior controller research remains under `~/Games/NXNative/docs/research/`. PR <https://github.com/seedds/nxnative/pull/989> is background game-controller context only, not work performed here.

## Resume and communication

1. Read `AGENTS.md`, `README.md`, this file, `POWERA-AUDIT.md` and `POKEMON-ZA-PERFORMANCE.md`. Load the `session-coordination` skill when needed.
2. Recheck the local commit/clean state and running processes. No repeat build, first opening, audit, archive download or finished worker launch is needed. Do not close the launcher to tidy up.
3. Confirm takeover briefly, then **await Sofian's next instruction**. Remaining directions could be his manual trials of the other games or a separately scoped mod-adaptation investigation. No path has been selected or authorized in advance.
4. Before any future implementation, build, cache operation or actual mod test, obtain the relevant explicit scope/consent. Preserve the unchanged working app and existing games. Keep the six-game trial ahead of PowerA changes.

Use simple French, very few steps, and explain jargon. Sofian learns the settings himself, the agent handles code/writing. No Claude subagents. Prefer the approved DeepSeek model for short atomic readings, Kimi only where justified. Community/mod discovery starts with Perplexity, followed by primary-source verification. Search summaries are not proof. Do not start a new workflow without the user's model/plan approval. Future authorized long builds use detached tmux and preserve caches.

Final replies go through a short `openchamber_render` page, starting with what Sofian should do now. Prefer simple native UI unless custom HTML has been checked at 720/360 px. Every decision is a clickable mini-app with **Aucune ne me va** and a free remark kept only in data, not the short submitted summary. Do not repeat the rendered content afterwards. End with evidence limits/risks. No production mutation, publication, release or push was performed in this research phase.
