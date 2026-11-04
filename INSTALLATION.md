# Installation record

Date: 2026-11-02 (Europe/Paris).

Status: **Stardew Valley confirmed playable with the PowerA fix; library
reorganized. Xcode 27.2 restored and Metal verified. Managed rebuild and
second-run incremental skipping verified.**

The user explicitly selected `~/Games` (capital G), beside `~/Developer`, and
the official nxnative route rather than a community launcher. Game builds will
need an individual space check before using the internal drive. This local
choice replaces the upstream maintainer's machine-specific external-drive layout.

## Versions observed

- Hardware: Apple M1 Pro, 10 CPU cores, 16 GPU cores, 16 GB unified memory.
- macOS: 27.2.
- Selected Xcode: 27.2, build 27B52, `/Applications/Xcode.app`.
- Metal Toolchain: asset 27B47; compiler
  `Apple metal version 32023.922 (metalfe-32023.922.4)`.
- nxnative checkout: `source/`, branch `main`, shallow clone, commit
  `65501fbbaf8526f7aab0a1edd028135888590f8e`. No upstream source edits.
- Python: 3.14.10 ARM64, isolated in `.venv/`, using the existing Homebrew
  interpreter at `/opt/homebrew/opt/python@3.14/bin/python3.14`.
- .NET SDK: 10.0.403, osx-arm64, installed locally in `tools/dotnet/`.
- .NET runtime: 10.0.14.
- Added Homebrew formula: glslang 16.6.0.
- Its added dependencies: spirv-headers 1.4.363.0 and spirv-tools 1.4.363.0.
- Existing tools reused: Git, Homebrew, uv 0.13.6, zstd 1.5.7_1 and
  XcodeGen 2.46.0. XcodeGen is not needed for the Mac-only target.
- Python package snapshot: `requirements-installed.txt`.

No shell profile was edited. `env.sh` applies local .NET/Python paths only to
the shell that sources it, directs .NET/NuGet working files into `tools/`, opts
out of .NET CLI telemetry and disables first-run ASP.NET certificate generation.
No `sudo`, provisioning, signing identity, mobile-device install, security
override, cloud-save configuration or production deployment was used.

## Download integrity

The .NET archive came from Microsoft's .NET 10 release metadata:

https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json

Archive:
https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.403/dotnet-sdk-10.0.403-osx-arm64.tar.gz

Its SHA-512 was checked against the published value before extraction:

```text
5893c66b48ea3674c7da18501059d606e96f3672fabe4d5e41762e692c7c83df3ee0b2b9dc5a0786191da2dc413d7335158101c14c935ab217f31ac2529770f3
```

Metal was installed by Apple's `xcodebuild -downloadComponent MetalToolchain`.
Homebrew handled its own bottle verification. The initial .NET and Metal
downloads hit the command runner's 120-second limit; their state was checked
before resuming, and each completed on its first resumed attempt.

## Checks passed

1. `uv pip check`: all 12 installed Python packages are compatible.
2. `zsh -n env.sh`: environment file syntax is valid.
3. The official packing script's `--help` runs with the isolated interpreter.
4. The official `check_native_python()` and
   `check_prereqs(..., mac=True)` pass, including starting the bundled shader
   translator against the local .NET runtime.
5. `own_compilers.check_tools()` reports no mismatches against the upstream
   shader-tool lock for the default Mac target. No override was used.
6. A synthetic Metal compute kernel compiled to AIR and linked to a nonempty
   metallib with Xcode's macOS tools. No game data was used; no GPU execution
   or performance was measured.
7. The production `dm/tools/nx_extract/nx_extract.csproj` restored LibHac 0.19.0
   and built in Release with zero warnings and zero errors. Outputs and
   intermediate files are preserved in `tools/nx-extract-check/` and
   `tools/nx-extract-obj/`, outside the source checkout.
8. `dotnet --info` confirms an ARM64 SDK/runtime; `metal --version` and
   `glslangValidator --version` execute successfully.

Latest free-space observation after installation: approximately 53.5 GiB on
the internal data volume. This changes with other activity and is not a
per-game space guarantee.

## First game and live viewer (2026-11-03, Europe/Paris)

- Stardew Valley base v0 plus update v1310720 (profile version 1.6.15.13),
  built with French selected. Original packages and key files were not moved
  or modified. The base input is an APFS clone; the update was extracted with
  the existing 7-Zip installation.
- Full official Mac-app pipeline succeeded in approximately 2 minutes 40
  seconds, including 65 shader libraries and the M1 Pro pipeline archive.
- Output: `apps/Stardew Valley.app`, approximately 803.5 MB logically.
- `codesign --verify --deep --strict` passed for that application.
- Read-only local live viewer added under `tools/build-monitor/`. It reads
  the console log, checks whether the original packing process is alive, and
  displays stage progress and any unexpired stage-specific ETA. It has no
  controls for launching, modifying or cancelling the build.
- Viewer checks: seven parser tests passed; HTTP status correctly reports
  eight completed stages; non-status filesystem routes return 404; no key
  filename/path is included in status JSON. It listens only on loopback.
- The page was opened in OpenChamber's browser, its periodic refresh was
  observed, and its 390-pixel mobile rendering was visually inspected.

## Library reorganization (2026-11-03, Europe/Paris)

- Approved layout: `games/<title>/{base,updates,dlc}`, `apps/`, `.build/`,
  `logs/`, `inbox/imported/`, `keys/`, with the existing engine and tools kept.
- Nine editions imported: Stardew Valley, Link's Awakening, Nintendo 64
  Classics and all six FireRed language editions. Archived originals and the
  original duplicate Stardew package are retained in `inbox/imported/`.
- The previous Stardew input folder was migrated to `games/Stardew Valley/`.
  Its existing cache was moved to `.build/stardew-valley-0100e65002bb8000/work/`.
  Only empty legacy directories were removed; saves were not accessed.
- In-progress/empty Mario Kart files remain in Downloads. Zelda's previously
  partial download had finished and passed archive verification before import.
- Key files were not moved/copied: `keys/prod.keys` is a local link to the
  existing private file. Keep the original key folder in Downloads.
- Make commands provide import/list/build/all/run/monitor/clean/test.
  The dashboard reads official JSON build events and refreshes the library
  and pending-download sizes every two seconds, without performing mutations.
- 45 automated tests pass, including real synthetic ZIP extraction, download
  guards, duplicate/conflict preservation, incremental skipping, missing-Xcode
  safety and both JSON/legacy progress parsing.
- Follow-up safety review added companion-download marker checks, immutable
  APFS snapshots for all subsequent imports (including inbox), preservation of
  every original after the initial approved move, and separate extraction work
  directories keyed to package metadata so changed inputs cannot reuse an old
  extraction. Future deletion/moving of retained originals requires a separate
  user-approved cleanup. The existing engine patch was not widened.
- The PowerA source diff remains unchanged. A retained copy is in
  `tools/patches/powera-controller.patch`; `git apply --reverse --check` confirms
  it matches the currently applied patch. Nothing was committed or reset.
- The attempted managed Stardew rebuild stopped in prerequisite checks before
  replacing the application. macOS now selects `/Library/Developer/CommandLineTools`,
  and no Xcode app is present at its original `/Applications` location.
  No Xcode download, selection change or security override was performed.
- The existing Stardew app still passes `codesign --verify --deep --strict`.
  `make run` opens an existing app without rebuilding; an absent app or an
  explicit `make build` still needs a working Xcode/Metal toolchain.
- The initial post-migration real-game build was blocked until Xcode was
  restored. The later successful checks are recorded below.

## Not verified

- Key values were not displayed or collected into setup artifacts.
- The user confirmed Stardew gameplay and PowerA input before reorganization.
  No new game or post-reorganization gameplay/performance test has run.
- The iOS SDK, mobile signing and mobile devices were not checked.
- The full upstream test suite and a security audit were not run; upstream
  source code was not modified.

## Xcode restored (2026-11-03, Europe/Paris)

At the user's explicit request, Xcode was reinstalled through the existing
Mac App Store CLI: `mas install 497799835`. Apple's App Store catalog was
checked first and reported version 27.2. Installation completed at
`/Applications/Xcode.app`; no simulator runtime was requested.

- `xcodebuild -version`: Xcode 27.2, build 27B52.
- `xcode-select -p`: `/Applications/Xcode.app/Contents/Developer`.
- `xcodebuild -checkFirstLaunchStatus`: success.
- `xcrun --sdk macosx metal --version`: compiler 32023.922.4 runs; the existing
  Metal component was reusable without another download.
- `make build GAME=stardew` completed all eight stages in approximately
  129 seconds in the managed layout. App signature verification passed.
- A second identical `make build GAME=stardew` returned
  `À JOUR Stardew Valley — aucune reconstruction`, without starting a build.
- The live `/status` endpoint reports the game as up to date and the build
  complete. The rebuilt application has not been gameplay-retested by the agent.
- The updated local dashboard was visually checked at 390 px during the real
  build: live stage state and the library render without horizontal overflow.

Keep Xcode installed: the user explicitly requested preserving it during future
cleanups. Import new downloads only after completion; preserve originals/saves.

## Explicit Zelda 1.0.1 trial

The user selected an experimental build of the available Link's Awakening
v65536 (1.0.1), rather than waiting for the profile's tested v131072 (1.1.0).
`make build GAME=zelda EXPERIMENTAL=1` opts into nxnative's official derived
profile workflow for this invocation. It does not change registered profile
versions or disable integrity/compiler checks. The library keeps successful
experimental results labelled as unvalidated and reuses them without rebuilding.
Single games without a profile may also be tried with explicit `EXPERIMENTAL=1`
using upstream's provisional-profile workflow; `make all` never opts into these
tests. The guard/label behavior has tests.

The Zelda 1.0.1 trial completed all eight stages successfully in approximately
2,839 seconds. Its app is `apps/The Legend of Zelda: Link's Awakening.app` and
passed `codesign --verify --deep --strict`. Its packaging sidecar was hidden in
Finder. The dashboard correctly labels it experimental; runtime/gameplay has
not been tested.

## Grouped editions and additional trials

The user requested one `games/Pokémon FireRed/` family with all six language
editions nested inside, plus `GAME=pokemon EDITION=fr` selection for build/run.
The manager and dashboard support nested editions; cache slugs and title IDs
are retained, and each edition selects its own language. This behavior and the
public status metadata are covered by automated tests.

After Zelda completed, the queue physically grouped all six editions under
`games/Pokémon FireRed/`. Selection of every code (`fr`, `en`, `de`, `es`, `it`,
`ja`) was checked against its correct folder and package. Mario Kart's base
package was imported and its download original preserved. No Mario compilation
was requested in this queue; the available base version is not registered in
its upstream profile.

The initial queue attempted FireRed French then Nintendo 64 Classics; both
failed and no apps were produced. Initial results are in
`logs/requested-builds.json`.

- Nintendo 64: NRO collection found one of 73 authorized module hashes and
  stopped for 72 missing modules before rewriting. Resource packaging needs
  investigation; no integrity check was disabled and no retry was attempted.
- FireRed French: capture aborted because the heap plus modules exceeded the
  app pool. The log measured 0x6600000 of modules but reported only 0x4000000
  used. Upstream's `heap_signals` independently recommended `mem_used 0x6a00000`
  (measured modules plus 4 MiB). That explicit row was added only to this
  generated provisional profile, not to the engine or shared runtime.
- Failure logs and the original provisional profile were retained under
  `logs/diagnostics/firered-fr-heap-before/`. The correction is cache-local;
  cleaning that game cache discards it.
- The first follow-up stopped in the local manager before reaching the game:
  the staging guard rejected upstream's retained `<title ID>_survey` directory.
  A regression test first reproduced the failure, then passed after allowing
  precisely that directory without deleting it. Unknown staging files remain
  refused. The subsequent FireRed build completed in approximately 68 seconds,
  including successful GLSLC capture, shaders and Mac packaging. The previous
  heap-pool error is absent from the new capture log.
- `apps/Pokémon FireRed Version (French Ver.).app` passes deep/strict signature
  verification and its `.app.key` is hidden in Finder. A second identical
  `make build GAME=pokemon EDITION=fr EXPERIMENTAL=1` skipped reconstruction.
  The result remains experimental and has not been gameplay-tested. Nintendo
  64 Classics remains unavailable because of the missing module collection.

## Mario Kart base-version trial

The requested `make build GAME=mario EXPERIMENTAL=1` stopped after successfully
extracting the base package. Upstream identifies v0 (1.0.0) as a **32-bit ARM**
program from `main.npdm`, which this native AArch64 pipeline cannot execute on
Apple Silicon. No application was produced and no architecture guard was bypassed.
The registered Mario Kart profile targets updates 4.0.0 (v1441792) and 4.0.1
(v1507328). A compatible user-supplied update is needed before another build.
The original package and extracted failure evidence are retained.

The existing Stardew `.app.key` was verified as a generated packaging cache
sidecar and hidden in Finder with `chflags hidden`. Future successful managed
builds apply the same cosmetic flag without moving/deleting the sidecar. These
files are not Nintendo decryption keys; Finder's Show Hidden Files reveals them.

## Compatible updates imported (2026-11-03, Europe/Paris)

The user extracted the new RAR archives with Keka. Their NSP files were checked
and imported from the corresponding Downloads subfolders, preserving both the
extracted originals and the RAR archives:

- Mario Kart 8 Deluxe 4.0.1, v1507328, update ID 0100152000022800:
  4,861,420,107 bytes, CRC32 FBB07D0B.
- Link's Awakening 1.1.0, v131072, update ID 01006BB00C6F0800:
  39,612,694 bytes, CRC32 096CE5AE.

Sizes and independently computed NSP CRC32 values match the RAR member headers;
PFS0 payload bounds pass validation. Both versions are registered in the local
upstream profiles. Evidence is in `logs/imported-updates-2026-11-03.json`.
The dashboard's live status sees both updates. Mario still shows its previous
failed base-version attempt; Zelda's existing app is still the older 1.0.1.
No application was rebuilt or replaced during this import, and gameplay of the
new versions has not been tested. A separate build is needed for each version.

The user then explicitly approved building both apps. A sequential queue was
started for Mario 4.0.1 followed by Zelda 1.1.0, without experimental/integrity
override flags or automatic game launches. Progress and independent signature,
version, packaging-sidecar and incremental-cache checks are recorded in
`logs/updated-app-builds-2026-11-03.json`. Results are pending.

The installed 7-Zip can list these RARs but lacks their decompression codec;
macOS bsdtar also refuses their solid layout. The original archives therefore
still cannot be imported directly with this toolchain. Import their extracted
NSP folders using `make import FROM=/absolute/extracted/folder` instead; do not
disable integrity checks. No extractor was installed or security setting changed.

## Dashboard ambiances and storage investigation (2026-11-04, Europe/Paris)

The live dashboard now has Cinéma and Console layouts using one set of colour,
type, spacing and radius tokens, shared game tiles, status badges, controls,
catalogue, details and build panel. The Console carousel and bottom dock use the
same data as Cinéma's banner/grid. Its compact build panel is the existing panel
relocated in the DOM, not a second tracker. Percentages describe only the current
stage. The selected ambiance is kept in localStorage and in `?ambiance=` when
the switch is used, so an older URL cannot override a new choice on reload.
The upstream checkout and active build processes were not changed for this UI.

Google's documentation confirms that streaming can retain online-only Finder
entries inside My Drive. Adding an arbitrary local folder under "Folders from
your computer" uses mirroring instead and does not provide that space saving.
Under macOS File Provider, dragging on the same volume normally moves files;
an explicit copy is needed to preserve the original. Cloud sync must be complete
before considering eviction or removing any local original. No Drive migration,
sync-mode change, cloud-quota check or app-bundle round-trip test was performed.
Keep the active game inputs, saves, keys and shader caches local for now.

Sources: Google Drive [streaming versus mirroring](https://support.google.com/drive/answer/13401938),
[macOS File Provider](https://support.google.com/drive/answer/12178485).
