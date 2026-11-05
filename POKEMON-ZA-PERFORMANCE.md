# Pokémon Legends: Z-A — frame rate, render scale and mods

Read on **2026-11-05**. Sources are the pinned engine in this checkout,
`seedds/nxnative` at `641d1480021a57840b7acc15f92cbd86ecfae611`, and that repository's
`main` as it stood the same day. Research agents ran no game, installed no mod, made no
build and measured nothing. Sofian's separate successful manual trial is recorded in
`SESSION-HANDOFF.md`. Emulator reports and other hosts' results do not validate nxnative.

## Short answer

- The **Frame rate** setting does not unlock 60 fps in Z-A. At the pin the game's profile
  declares no frame-rate target, so the setting is not offered for this game, and
  `DM_FPS_TARGET=60` set by hand changes nothing: the host keeps the interval the game asks for.
- **Render scale** does not apply to Z-A either, for the same reason (no stub in the profile).
- **RomFS replacement files work** (a mod's `romfs/` folder, through `DM_ROMFS_OVERLAY`).
  **ExeFS code changes do not**: no replacement module, no `.pchtxt` or `.ips` patch at run time.
- **Atmosphère cheat files work on the Mac**, with limits. They never write code on the iPhone.

## 1. Frame rate: `DM_FPS_TARGET`

Facts in this checkout, at the pin:

- `engine/dm/games/0100F43008C44000/game.tsv` has no `fps_target`, no `render_scale` and
  no `patches.py`. The profile's own README says "the profile has no `patches.py`".
- `engine/dm/games/settings.tsv` shows the Frame rate row only when `DM_GAME_FPS_TARGET!=0`,
  a profile macro. Z-A's profile sets no `fps_target`, so the macro is 0 and the row is dropped.
- `engine/dm/host/hle_fpslock.c`, `dm_fps_lock_engine()`: "Without one, and without a frame
  step state page, nothing makes the game follow the cap, so the graphics layer keeps the
  game's own present interval".
- `engine/dm/games/README.md`, profile key `fps_target`: "On a main with neither a frame step
  nor an engine limit the host writes, the host keeps the game's own present interval
  whatever `fps_target` or `DM_FPS_TARGET` says".
- `engine/docs/settings.md`, Frame rate: "Games whose speed the app controls (Breath of the
  Wild, Tears of the Kingdom and a few others) offer **30 fps** or **60 fps**." Z-A is not
  one of them.

Current `main`, same day: `dm/games/0100F43008C44000/` still holds no `patches.py`, and
`game.tsv` has no `fps_target`. Two open proposals would add one, and neither is merged:

- [PR #606](https://github.com/seedds/nxnative/pull/606), "Pokémon Legends: Z-A 2.0.2:
  host-paced 60 fps", sets `fps_target` to 60 with a `FRAME_STEP` patch gated to build
  `b1f12fd919eae86ab8a978317677e64b`. Its author reports no gameplay verification.
- [PR #918](https://github.com/seedds/nxnative/pull/918), "Add adaptive 60 fps support for
  Pokémon Legends: Z-A 2.0.2", records that running `dm/tools/fps_target.py` on the
  unmodified Z-A 2.0.2 `main` prints **"no target frame rate"**, so the rewriter cannot find
  the field and a build-gated hook is needed. It also states the caveat plainly: "This
  enables a 60 fps cap; it does not make the GPU render every scene at 60", with the station
  at about 27 ms of GPU work a frame holding mostly 30 fps, and an unresolved p99 frame-time
  increase (37.6 to 52.3 ms) at the 30 fps cap.

Consequence: choosing 60 in a front end does not turn a game locked at 30 fps into 60. For
Z-A at the pin it is a no-op, not a hidden unlock.

## 2. Render scale: `DM_RENDER_SCALE`

- `settings.tsv` shows the row only when `main`'s fixups table has `RENDER_SCALE`, which
  `patch_nso.py` writes for a build with a render-scale stub. Z-A has no `patches.py`, so no
  stub, so no row.
- `engine/dm/host/loader.c` writes the factor into the frame-step state page
  (`dm_fps_state + 0x10`), which only those stubs read. No stub, nothing reads it.
- Documented meaning (`docs/settings.md`): 1.0 keeps the game's own size and dynamic
  resolution, below 1.0 fixes the 3D views' size at that fraction and turns the game's own
  dynamic resolution off. It is not a resolution unlock and not a performance guarantee.

So `DM_RENDER_SCALE` on Z-A does nothing.

## 3. Mods: what runs and what does not

### RomFS overlay — supported

`DM_ROMFS_OVERLAY` (`engine/dm/host/hle_fs.c`, `engine/docs/env_switches.tsv`):
"`=<dir>[:<dir>…]`: RomFS reads look in these folders first, in order, and fall back to
`DM_ROMFS`". NX2Apple v1.1.0 sets it from the mods switched on
(`frontend/Sources/NX2Apple/Library.swift`), finding `romfs/`,
`atmosphere/contents/<title ID>/romfs` or `contents/<title ID>/romfs`.

### ExeFS — not supported

- Issue [#374](https://github.com/seedds/nxnative/issues/374) (closed, opened by a
  contributor, not a maintainer): "Mods that change the game code (ExeFS) are not supported."
- The fork's own launcher, `Library.swift`: "A mod with only exefs/ changes the game's code,
  which the rewriter does not take: listed, not usable."
- PR [#883](https://github.com/seedds/nxnative/pull/883) (open) is the change that would add
  mods. RomFS folders are appended to the overlay. Code patches (`.pchtxt`, `.ips`, IPS32) go
  through `patch_nso.py` **at build time**, "after the registered cuts and before the
  rewrite". It "stops for mods that ship replacement modules (main, subsdk*, main.npdm),
  since exlaunch-style code can't run here". Not merged at the pin.
- Issue [#1133](https://github.com/seedds/nxnative/issues/1133) (open) describes the same gap
  for Scarlet/Violet: the RomFS half is served through `DM_ROMFS_OVERLAY`, the
  `exefs/subsdk9` exlaunch plugin is skipped.

So a 60 fps `.pchtxt` or `.ips` ExeFS patch for Z-A cannot be dropped in. At the pin there is
no mechanism at all, and the open PR applies such patches only by rebuilding the app.

### Atmosphère cheats — supported on the Mac, with limits

Format and folder (`engine/docs/frontends.md`, `engine/docs/development.md`,
`engine/docs/reference/cheats.md`): `<folder>/<build ID>.txt`, where the build ID is the first
16 hex digits of main's build ID, or the SD tree
`atmosphere/contents/<title ID>/cheats/<build ID>.txt`. Default folder
`~/Library/Application Support/nxnative/<title ID>/cheats`, `DM_CHEATS` overrides it.

Limits that matter for a frame-rate cheat:

- Writes into `main`'s code, from `docs/reference/cheats.md`: "on the Mac, through a writable
  alias of the image, with an icache flush, except into a word the rewriter changed or moved
  (`main.changed.tsv` ...), which turns the cheat off with the reason ... On the iPhone never:
  its code pages are the app's signed pages". A code-patch cheat can therefore work on the
  Mac, never on the iPhone, and one that lands on a rewritten word stays off.
- A cheat file is tied to one build. For Z-A 2.0.2 the profile gives build
  `b1f12fd919eae86ab8a978317677e64b`, so the 1.0.1 files in circulation (build
  `7222E13ECF6ADB32`) do not apply as they are. `scripts/cheat_anchor.py` can carry them, and
  it needs that build's `ExeFS/main`.

## Open questions

- Whether any given Z-A cheat or mod actually produces 60 fps on nxnative: no source read here
  establishes it, and nothing was measured.
- Whether #606 or #918 lands, and in what form: both are open.
- The Z-A 2.0.2 build ID a cheat file must carry is taken from the profile
  (`b1f12fd9…`), not verified against a cheat file.

## Existing mods and the installed Mac app

The earlier catalogue in `~/Games/NXNative/docs/research/za-mods-switch2.md` already covers
Fl4sh9174's static/dynamic FPS mods and older Atmosphère cheats. Do not repeat or treat
that emulator-focused catalogue as nxnative validation. The author's
[GameBanana page](https://gamebanana.com/mods/627350), reopened today, still advertises
**FPS + GFX Mods v2.0.2 (RC3.0)**. Its page title has an inconsistent 2025 update date,
which is not used as evidence. PR #606 explicitly credits this 2.0.2 mod for identifying
the native interval selector, but implements a different host-paced hook. A generic
search summary describing the mod only as 2.0.0 was therefore incomplete.

A read-only check of
`~/Games/Jeux/Pokémon Legends: Z-A.app/Contents/Resources/dm/launcher.json` confirms that
the existing app advertises **no frame-rate or render-scale setting**. It does offer
Docked/Handheld, Standard/MetalFX, pipeline settings and Performance HUD. Its manifest
defaults include Standard upscaling and Metal 4 pipelines/prebuild on. These are
**manifest defaults, not a reading of the player's current choices or a runtime test**.

For a GPU-load comparison, the upstream
[settings guide](https://github.com/seedds/nxnative/blob/main/docs/settings.md) documents
Handheld as lower-resolution and potentially lighter on the GPU, and MetalFX as extra
GPU work. **This does not address Sofian's request to remove the game's 30 fps cap.**
No GPU bottleneck was diagnosed, so reducing picture quality is not the recommended
answer to that request. Keep shader caches. Neither open FPS PR has been applied, and
no settings were changed.

The coordinator independently reread PRs #606, #918 and #883 through GitHub's API.
#606 and #918 are **pull requests**, not ordinary issues, and were both open on
2026-11-05. #918 retains historical tests and an unresolved, load-confounded frame-time
regression. Do not turn those historical measurements into a current performance claim.

## Sources

All read on 2026-11-05.

- Pinned engine in this checkout: `engine/dm/games/0100F43008C44000/game.tsv`,
  `engine/dm/games/README.md`, `engine/dm/games/settings.tsv`, `engine/dm/host/hle_fpslock.c`,
  `engine/dm/host/loader.c`, `engine/dm/host/hle_fs.c`, `engine/docs/settings.md`,
  `engine/docs/env_switches.tsv`, `engine/docs/frontends.md`, `engine/docs/development.md`,
  `engine/docs/reference/cheats.md`
- https://github.com/seedds/nxnative/issues/374
- https://github.com/seedds/nxnative/pull/606
- https://github.com/seedds/nxnative/pull/918
- https://github.com/seedds/nxnative/pull/883
- https://github.com/seedds/nxnative/issues/1133
- https://github.com/seedds/nxnative/blob/main/dm/games/0100F43008C44000/game.tsv
- https://github.com/seedds/nxnative/blob/main/dm/games/settings.tsv
- `frontend/Sources/NX2Apple/Library.swift`, NX2Apple v1.1.0
- https://github.com/seedds/nxnative/blob/main/docs/settings.md
- https://github.com/seedds/nxnative/blob/main/dm/games/0100F43008C44000/README.md
- https://gamebanana.com/mods/627350
- https://gamebanana.com/apiv11/Mod/627350/ProfilePage and https://gamebanana.com/dl/1731160
  (file 1731160, listed and read in memory, see the final section)
- https://api.github.com/repos/borgox/Pokemon-Legends-Z-A-Mods/git/trees/main?recursive=1
  (complete tree read, FPS cheats still named for 1.0.1, no path naming 2.0.2 found)
- Installed Mac app's `Contents/Resources/dm/launcher.json` (settings metadata only)

Initial discovery used one Perplexity Search, followed by primary-source reads. The
search did not surface the two game-specific FPS PRs and is not the authority for their
existence or status. A later request to check file 1731160 used a second targeted Search
and read-only inspection of that public mod archive, documented in the final section.
No mod was installed, no game was rebuilt, and no runtime effect was tested.

## NX2Apple v1.1.0 GameMods contract

Read on 2026-11-05 in this checkout, on `local/launcher-v1.1.0` at `v1.1.0-2-gf5592e5`.
`git diff v1.1.0 -- frontend/Sources/NX2Apple/Library.swift frontend/Sources/NX2Apple/GameStart.swift frontend/l10n/en.json`
is empty, so the lines below are the tag's. No mod was installed, no build made, no game run.

**What is true.** A mod folder dropped in the game's mods folder is offered as a switch in
Launch options, and the mods switched on are given to the game at Play as `DM_ROMFS_OVERLAY`.
The overlay is the engine's RomFS read-first list (`engine/docs/env_switches.tsv:280`,
`engine/dm/host/hle_fs.c:199-200`, `:344`), so **only RomFS file replacement** works.

- Folder: `<library folder>/mods/<title ID>/<mod name>/`, or
  `~/Library/Application Support/NS Port Builder/mods/<title ID>/` when no library folder is set
  (`frontend/Sources/NX2Apple/Library.swift:192-197`).
- Layouts accepted, in this order (`Library.swift:208`): `<mod>/romfs`, the Atmosphère tree
  `<mod>/atmosphere/contents/<title ID>/romfs`, `<mod>/contents/<title ID>/romfs`; failing those,
  the mod folder itself is used as the RomFS root (`:210-212`).
- A folder holding only `exefs/`, `atmosphere/` or `contents/` is listed but **not usable**: the
  switch is disabled and the row says "Changes the game's code (exefs): not supported"
  (`Library.swift:211-212`, `LaunchOptionsView.swift:284-291`, `frontend/l10n/en.json`, keys `launch.modCode` and
  `launch.modsHow`). The tested behaviour is in
  `frontend/Tests/NX2AppleTests/LaunchOptionsTests.swift:102-120`.
- Order: on the Mac the library's list order decides, the higher entry winning a shared file
  (`Library.swift:234-239`, `SavedChoices.swift:149`). On the iPhone it is name order
  (`frontend-ios/Sources/ShellHost/GameMods.swift:26-31`).
- iPhone: a different folder, `Documents/games/<title ID>/mods/`, same layout rules and same
  exefs exclusion; it sets `DM_ROMFS_OVERLAY` only when the game's `env.txt` does not
  (`GameMods.swift:3-31`, `frontend-ios/Sources/ShellHost/EngineLaunchPlan.swift:25-27`, `:66-68`).

**Where the description needs qualifying at this tag.**

1. *"Mods from GameBanana/Nexus"* — the folder does not know where a mod came from. What
   qualifies is the layout: RomFS file replacement. A mod whose payload is a code patch does
   not qualify, whatever site it came from.
2. *"Before finalizing the build"* — nothing in the build pipeline reads the mods folder. No
   `mods` reference exists in `NXModel`, `NXCore` or `NXLauncher`; the only readers are
   `GameStart.swift:17-20` and `LaunchOptionsView.swift:33-37`. Mods are applied at Play, not
   at build.
3. *"The compiled app automatically points there"* — the app is given the path by the launcher
   through the environment at Play (`GameStart.swift:18`, `SavedChoices.swift:149`). Opening
   from Finder does not receive that launcher-added environment. A separately configured
   `env.txt` is a different mechanism, not checked here. The mods folder is not inside
   the `.app`: it sits in the library folder or in Application Support.

**Mod types, stated narrowly.**

- RomFS texture, model, text, audio or data replacement: supported, if the files sit under one
  of the four layouts above.
- `.pchtxt` and `.ips`/IPS32 patches: not supported at run time and not at build time in this
  tag. The build-time path described in PR #883 is not in v1.1.0.
- Replacement ExeFS modules (`main`, `subsdk*`, `main.npdm`): not supported.
- Atmosphère cheats are a separate mechanism (`DM_CHEATS`), not this folder; see section 3.

**Limits worth knowing.**

- A mixed folder, `exefs/` plus any other top-level entry (a readme, a `.pchtxt`), is treated as
  usable and mounted whole as a RomFS root (`Library.swift:210-212`): its code change is still
  ignored, silently, and its stray files appear as RomFS paths.
- Mods can affect saved game state: the UI warns that a save made with a mod may not load
  without it (`frontend/l10n/en.json`, `launch.modsNote`). This is not a claim that the
  RomFS overlay directly replaces save files.
- For Z-A specifically, a RomFS mod qualifies, an FPS mod shipped as an ExeFS patch does not.

**Limits of this contract check.** No archive was opened at this stage. A later inspection
of the specific GameBanana file 1731160 follows below, not a validation of arbitrary
GameBanana or Nexus downloads. Whether the app's own `env.txt` or
`launcher.json` could also set `DM_ROMFS_OVERLAY`, and which side wins, was not tested.

Source at the tag:
https://github.com/sofianbll/NX2Apple/blob/v1.1.0/frontend/Sources/NX2Apple/Library.swift#L183-L239

## Build caches are separate from the mods folder

Checked on 2026-11-05, without changing any paths or starting a build:

- The Settings row **Fichiers de cache** is the shared **iPhone frameworks cache**, not
  an arbitrary Mac shader-cache selector. `frontend/l10n/fr.json:1248` explicitly says
  "Le cache des frameworks iPhone". `BuildStore+ShellRoot.swift:30-35` resolves this
  shell root. Its Move action actually moves the cache after confirmation, rather than
  importing an existing game-build cache (`:48-80`).
- For Mac builds the work folder is `<output folder>/<build key>_build`, or next to the
  inputs when no output folder is selected. The launcher passes that as `--work-dir`
  when the engine supports it (`BuildStore+Run.swift:79-80,102-107,146,154-164`). Its
  comment identifies extracted files, shader cache and RomFS archive as work-folder
  contents. Selecting a fresh output folder is not an automatic adoption of another
  checkout's cache.
- Whether the existing NXNative caches are compatible and reusable here remains
  **unverified**. Their protected paths were not inspected, copied or moved. No fast
  rebuild promise follows from the existence of a cache setting.
- A compatible RomFS mod applied at Play needs no game rebuild for that overlay
  mechanism, so a build-cache migration is not a prerequisite for that use case.

This support for file replacement does not establish that a particular Z-A HD texture
pack exists or works: no such archive was validated in this check.

## GameBanana file 1731160

Inspected on 2026-11-05, read-only. The page itself renders its body in JavaScript, so the
record and the file were read from the site's own JSON endpoint, not from a mirror:
`https://gamebanana.com/apiv11/Mod/627350/ProfilePage`. Download:
`https://gamebanana.com/dl/1731160`.

**The artifact, as observed.** One file, no variants. The name is not a search result: the
record's `_aFiles` array holds exactly one entry, `_idRow` **1731160** — the id in the page
anchor — with `_sDownloadUrl` `https://gamebanana.com/dl/1731160`, and that URL redirects to
`https://files.gamebanana.com/mods/pok_mon_legends_z-a_0100f43008c44000_mods__b8ede.zip`
with `content-length: 30983`, matching the record's `_nFilesize`. The downloaded bytes carry
the record's MD5. The chain id → name → size → checksum is closed on the site's own endpoints.

- `pok_mon_legends_z-a_0100f43008c44000_mods__b8ede.zip`, 30,983 bytes, added
  2026-06-17T21:58:33Z, MD5 `d535bda9a49f312fc8c7ca038cc09efa` (matches the site's own
  checksum), SHA-256 `4e166d04c3f523e1d7ea3660e7c35aa1a22a90a269c1e69d3e976b0c10260043`.
  Kept at
  `/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode/nx2apple-mod-1731160/file1731160.zip`,
  never extracted or executed. Mod record `_sVersion` is `2.0.2`, updated
  2026-06-17T22:00:45Z. The page title's "UPDATED 06/17/2025" carries the wrong year; the
  API dates the file 2026.

**Tree.** 58 entries, 40 files (39 `.pchtxt` and one `Instructions.txt`), 47,028 bytes
uncompressed, no unsafe path and no symlink. Nine mod folders, each holding only
`<mod>/exefs/*.pchtxt` — no `romfs/`, no replacement `main`/`subsdk`, no `.ips`:
21.9 Ultrawide, 4K Shadows, Disable DOF, Disable FXAA, Dynamic 60 FPS (RC3.0), Improved
FOV, Level of Detail, Reduce Bloom, Static 60 FPS. Per-version files are `1.0.0-1.0.1`, `1.0.2`, `2.0.0`,
`2.0.1`, `2.0.2`.

The coordinator independently reopened the ZIP in memory, verified its MD5/SHA-256 and
file list, and matched the site's `_idRow` to this exact file through the JSON endpoint.
Its Git blob SHA-1 is `a41edcd04e14f5733a8fc4ca5012f226028c5b12`, identical to the
30,983-byte archive `Pokémon Legends Z-A [0100F43008C44000][mods].zip` in the author's
repository tree (`https://api.github.com/repos/Fl4sh9174/Switch-Emulator-Ultrawide-FPS-Mods/git/trees/main?recursive=1`).
This also establishes that Disable FXAA has a 2.0.2 file in this specific archive,
which the older general catalogue had left unconfirmed. There are no HD texture assets.

**Build ID.** Every `2.0.2.pchtxt` starts with
`@nsobid-B1F12FD919EAE86AB8A978317677E64BCE443D1F`, which is the profile's Z-A 2.0.2 build
`b1f12fd919eae86ab8a978317677e64b` with the trailing bytes spelled out. Title ID
`0100F43008C44000` is in the file name and the headers. The stray
`[Dynamic 60 FPS v2.0.2] RC3.0/exefs/v2.pchtxt` carries a different `nsobid`
(`DF7A3960C74C3A4803F826C5871532523AA9CF2A`) and a placeholder `vx.x.x` header: it is not
the 2.0.2 file.

**What the headers actually patch** (2.0.2 files, read in memory):

- Static 60 FPS: one instruction, `01B296D8 14008052`. Its own comment: "If FPS drops below
  60, game will slowdown".
- Dynamic 60 FPS: a code cave at `012789F0` plus a frame table written around `0617A700`
  (floats `0x42700000`=60.0 and `0x42380000`=46.0 among them), and `01B296D8` redirected
  to the cave. This is the mod that PR #606 credits for locating the interval selector.
- 4K Shadows: `00A8AAA0 09008252`, "Shadow resolution 4096x4096".
- Level of Detail: `018B58E4` LOD bias and `018B5F68` anisotropic filtering.
- Disable DOF, Disable FXAA, Reduce Bloom, Improved FOV, 21:9: small constant or branch
  edits, each with its own code cave where needed.
- Two reported write-site overlaps require compatibility analysis before combining:
  21:9 and Dynamic 60 FPS both write `012789F0`; Static and Dynamic 60 FPS both write
  `01B296D8`. No combined-mod execution was tested.

**Verdict for NX2Apple v1.1.0: not usable through the mods folder.** The folder mounts
RomFS replacement only; this archive contains no `romfs/` at all, and every payload is an
ExeFS code patch. The author's own Switch instructions say the same thing — convert to IPS
and place it under `atmosphere/exefs_patches/` — and the description states the mods were
tested on Kenji-NX, a Ryujinx fork, not on a native host. Dropped in as-is, the folder is
either listed and disabled as a code mod or mounted with its `exefs/` ignored.

**Unknown, not claimed here.** Whether nxnative's build-time `patch_nso.py` could apply
these `.pchtxt` to Z-A 2.0.2 was not tested and is not in v1.1.0 (PR #883 is open). The
`nsobid` matches, but no application, no offset validation against the rewritten image and
no measurement were done. Nothing here says the Dynamic mod yields 60 fps on nxnative.
