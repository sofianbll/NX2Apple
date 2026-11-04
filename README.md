# NXNative on this Mac

Official project: https://github.com/seedds/nxnative

This folder is a local installation, not a game download service. Use only your
own game files and keys where permitted by applicable law. Do not share game
files, keys, extracted resources or the applications built from them.

## Everyday commands

```sh
cd ~/Games/NXNative
make import                 # Import completed game downloads, keeping originals in place
make list                   # Titles, identifiers and readiness
make build GAME=stardew     # Build only when inputs or engine changed
make run GAME=stardew       # Open the existing app; build only if it is absent
make monitor                # Live library: http://127.0.0.1:8767
```

FireRed's six editions share `games/Pokémon FireRed/`, with language folders
`Français`, `Anglais`, `Allemand`, `Espagnol`, `Italien`, `Japonais` and each
edition's own `base/`, `updates/`, `dlc/`. Select one without moving files:

```sh
make build GAME=pokemon EDITION=fr EXPERIMENTAL=1
make run GAME=pokemon EDITION=fr
```

Edition codes are `fr`, `en`, `de`, `es`, `it`, `ja`. Each uses its own title ID,
cache, output application and language. Omitting `EDITION` for an ambiguous
family is an error, not a guess. The dashboard groups these editions together.

`GAME` accepts a unique part of a name (`stardew`, `zelda`) or the exact
identifier printed by `make list`. `make all` processes only supported titles
with a tested version available. It does not try experimental profiles.

## Folder layout

```text
~/Games/NXNative/
  source/              Official nxnative Git checkout; no game files or keys
  .venv/               Isolated Python 3.14 environment
  tools/dotnet/        Local .NET 10 SDK; no system-wide installation
  tools/dotnet-home/   .NET working files
  tools/nuget/         .NET package cache
  Makefile             Import, build, run, monitor and clean commands
  inbox/               Drop game files here, especially archives without ID/NSP labels
    imported/          Original archives from the initial move, then verified snapshots
  games/<Game>/
    game.json          Title identity used by the commands
    base/              Base game packages
    updates/           Update packages
    dlc/               DLC packages
  .build/<identifier>/  Per-game staging, original build caches, build state
  logs/                JSON progress and separate error logs
  keys/prod.keys       Local link to the existing private key file
  apps/                Finished Mac applications
  env.sh               Environment for this installation, current shell only
  INSTALLATION.md      Observed versions, checks and remaining limitations
```

The previous `library/StardewValley/` was migrated without discarding its cache.
Every language edition with a different title ID is a separate game; all six
FireRed editions were retained. The controller fix remains in the engine checkout.
Only project sources, documentation and small artwork are tracked in Git. Games,
keys, applications, the upstream checkout, local environments, outputs, logs,
caches and OpenChamber files stay ignored.

## Import safely

`make import` checks game-labelled files in Downloads and files dropped in
`inbox/`. `make import FROM=/absolute/folder` selects another source folder.
Unknown archives in Downloads are not opened. A package's filename needs its
`[16-digit Title ID]`; packages without it are left in place with a diagnostic.

The initial user-approved move is complete. Subsequent imports keep **all
originals in place**, even in `inbox/`: a downloader may resume after any check.
The importer tests an APFS snapshot instead, never renaming the original inode.
Original cleanup is a separate user-approved operation after downloads finish.
Receipts skip repeated imports with unchanged source metadata.

Partial downloads (`.part`, `.crdownload`, `.download`, `.aria2`, `.tmp`), empty
files and their companion download markers, files modified less than a minute
ago, symlinks and files with an open write handle are left alone. Archives are
tested and extracted to scratch space; headers, PFS0 table/payload bounds,
sizes and unchanged source metadata are checked before publishing.
Any error preserves the original. Rerun `make import` after downloads finish;
there is no automatic import watcher.

Only game packages are extracted. Base, update and DLC are associated by title
ID, not by the outer archive's sometimes damaged spelling. Verified archive
snapshots go to `inbox/imported/`; the initial moved originals remain there too.
No original is deleted to deduplicate it, and a different existing file is never
overwritten. Interrupted imports can be rerun.

Keys were not moved or copied. `keys/prod.keys` links to the existing file in
`~/Downloads/ProdKeys.-v22.5.0/`: **do not delete that original folder**. It is not
exposed by the dashboard. Never paste key values into chat or reports.

## Build without repeating work

`make build GAME=…` uses the installed Python/.NET environment automatically,
stages links to the game's packages, and calls the official Mac-app pipeline
with French selected. Upstream caches are reused only within the same package
generation. Changed package sizes/timestamps select a new work directory, so an
old extraction cannot silently replace new input. Migrated legacy caches are
preserved, but not trusted without a managed generation stamp. An app is considered
up to date after a successful managed build if input sizes/timestamps, the engine
commit, local patch content and build options are unchanged and the app exists.
Local untracked engine files also invalidate the build. Files deliberately
restored with identical sizes and timestamps require `make clean GAME=…` first.

`make all` skips missing bases, unsupported titles and versions not registered
in the profile. This is a safety filter, not proof that other versions cannot
work. Do not bypass integrity/compiler checks. Save and quit a running game
before rebuilding it; the manager refuses to replace a running app.

An explicitly accepted test of an unregistered version or a game without a
profile can use `EXPERIMENTAL=1` on a single `make build` invocation. This permits
nxnative's official derived/provisional profile workflow, not compiler/integrity
overrides. The result stays labelled as unvalidated in the dashboard. `make all`
never starts these tests automatically. Nintendo 64 Classics and FireRed are
experimental; requesting a build is not a compatibility guarantee.

`make run` deliberately opens an existing application without rebuilding it,
including when Xcode is unavailable. Use `make build` explicitly to apply new
packages or engine changes. A missing app still needs a working toolchain.

```sh
make clean GAME=stardew     # Deletes only that game's .build cache, never saves/apps
make test                  # Synthetic importer, incrementality and progress checks
```

## Live build monitor

`make monitor` starts the read-only library dashboard. It listens only on
`127.0.0.1:8767`, exposes no filesystem or keys, and refreshes every two seconds.
Leave it running in one terminal and run builds/imports in another:

```sh
make monitor
```

Open http://127.0.0.1:8767 on this Mac. The library shows readiness and pending
downloads; managed builds send official JSON events for stage progress and ETA.
ETA describes the current stage only; there is no fabricated total countdown.
Ctrl+C stops the dashboard without stopping a build. The old single-log monitor
invocation still works, but is no longer necessary for everyday use.

The dashboard is a dark, cover-based library: search, filter available apps or
games needing preparation, and click a cover for files, missing requirements and
the appropriate Make command. FireRed remains one tile with an edition selector.
A “Catalogue” tab lists the engine’s referenced profiles (regional variants count
separately); “Dans ta bibliothèque” means that Title ID’s files are present, not
that a Mac app is built or tested.
Search, filters and selected editions are retained locally in the browser.
Buttons copy commands; they do not launch games, builds or imports. A built app
is not labelled gameplay-verified unless that build has been confirmed.

The Cinéma / Console switch uses the same game cards, status badges, catalogue
and game details. Cinéma shows the large artwork banner; Console uses a square
tile carousel and a bottom dock. The choice is retained locally and can also be
set with `?ambiance=cinema` or `?ambiance=console`. In Console, focus a game tile
and use arrow keys to select another; Enter opens its details. The compact build
card reuses the Constructions panel; its percentage describes only the current
stage, never the entire build.

For long jobs, keep the build queue and dashboard in the detached `nxnative`
tmux session (`builds` and `dashboard` windows), rather than agent-owned
background commands. Check for an existing process before starting another.
This survives a disconnected agent, not a reboot of the Mac. Preserve `.build`
shader caches: rebuilding them may take hours.

Artwork is stored in `tools/build-monitor/art/`, with official source URLs in
`sources.json`; viewing the dashboard makes no external image requests. The
server serves only six allowlisted JPEGs, not arbitrary local files. No frontend
dependencies were added. `make test` also checks the dashboard logic when Node
is available; importer and progress tests remain Python-only.

## Play

The `apps/*.app.key` sidecars are packaging-cache fingerprints, not Nintendo
keys. They are kept beside the app because upstream expects them there, and
hidden in Finder with macOS's hidden flag after successful builds. Do not delete
them to tidy the folder: that can force repacking. They remain visible to tools
that show hidden files; showing hidden files in Finder also reveals them.

Open the finished `.app` in `apps/` from Finder, choose its settings and play.
You do not need to source `env.sh` or rebuild for every session. A compatible
controller is optional. Pin a finished game to the Dock if useful.

Default Mac locations, kept separate from replaceable application bundles:

- Saves, settings and runtime caches:
  `~/Library/Application Support/nxnative/<title ID>/`
- Runtime logs: `~/Library/Logs/nxnative/<title ID>.log`
- Build logs: `.build/<identifier>/work/<generation>/logs/`; live events: `logs/*.jsonl`

Do not delete saves when cleaning build caches. Updating the engine or changing
a game version may require rebuilding the application; do not auto-update a
known-working installation. Local ad-hoc signing does not require a paid Apple
Developer account; it is not notarization. Do not disable macOS security controls.

## Storage and scope

Keep free disk space for macOS. Upstream estimates roughly twice the game's size
plus 10 GB free for a first build; this is not a guaranteed upper bound. Tools,
compressed-package expansion and additional versions also use space.

An external APFS SSD is preferable for a larger library. Keep builds and output
apps on the same APFS volume to benefit from copy-on-write clones. FAT32 cannot
hold individual files over 4 GiB. Moving this installation later requires
recreating the Python environment and updating paths; it is not a portable USB
installation for arbitrary Macs.

System-level additions for this installation are Homebrew's glslang (with its
SPIR-V dependencies) and Xcode's Metal Toolchain component. Existing Xcode,
Homebrew and Python are reused. No shell profile, macOS security setting, mobile
device, cloud-save setting or existing game save is changed by this setup.
