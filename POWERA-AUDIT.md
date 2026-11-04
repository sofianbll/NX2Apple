# PowerA launcher input audit

Baseline: 2026-11-05, NX2Apple v1.1.0, HEAD `2f788d6b55192952dfacaf97f24700d7668610b6`. The tracked working tree was clean when inspected. The PowerA `0000:0000`, claimed but not listed by GameController, is the reported situation, not a measurement in this audit. The dashboard and patches cited below are external working files, not proven to belong to this pinned commit.

External `NXNative/` paths below refer to `~/Games/NXNative/`. This audit is separate from the coordinating session's unchanged-launcher build.

## Verdict

A small, event-driven, nonexclusive HID input source feeding the existing launcher actions is plausible. It is not yet proven to work on this controller or to coexist safely with GameController. It does not require polling HID or rewriting game binaries. Wait until Sofian has tried the unchanged launcher before proposing implementation.

## Reuse and limits

`frontend/Sources/NX2Apple/Gamepad.swift:14,38-51,79-108` defines 12 actions, per-controller edges, GC callbacks and an input funnel. It gates capture and actions on app activity and repeats directions after 0.4 seconds, then every 0.12 seconds (`:100-123`). The dashboard's `NXNative/tools/desktop-app/Sources/NXNativeDashboard/HIDGamepads.swift:16-33,44-61` uses matching, removal and input callbacks on the main run loop, not HID polling. Its nonexclusive open return value is ignored, so successful or concurrent access is not established.

The dashboard decodes hat, X/Y and button usages (`HIDGamepads.swift:47-56`) but only produces directions, A and B (`NXNative/tools/desktop-app/Sources/NXNativeCore/PadInput.swift:11-19`). Its PowerA validation is a source comment (`:2`), not hardware evidence from this audit. The external `NXNative/tools/patches/pr989-powera-hid.patch:56-65,169-176` describes two different button tables selected by report ID 0x3F. Both map A/B to 2/1, but X/Y, shoulders and plus/minus differ. Its axis calibration has a rest and per-side reach (`:96-105`). Actual device descriptors, complete mapping, neutral position and range remain unverified.

## Minimal proposal and affected consumers

Extract a source-neutral state-ingestion seam from `Gamepad.swift:88-108`. A separate connector should track per-device state, decode changes into the existing 12 actions and deliver them on a consistent queue. Check open and callback errors, remove callbacks, release devices, clear held state and close the manager on teardown. Exclude synthetic devices. Do not claim unsupported mappings as verified. Reuse capture, routing and direction repeat rather than introducing another navigation stack.

Use one appropriately owned source across onboarding, desktop and console. `frontend/Sources/NX2Apple/OnboardingRoot.swift:22,31-40` owns a pad but does not pass it to the latter views, which can instantiate their own (`LauncherView.swift:38,65`, `ConsoleView.swift:34-46`). Simultaneous handlers and view transition cleanup need explicit design, not an assumption that sharing alone fixes them.

Update `connected` only for usable GC or accepted HID devices, with honest failure handling. It affects the desktop prompt (`LauncherView.swift:122-127`). Controller assignment remains GC-only: `LiveConsoleDriver.swift:370-381,583-601` consumes assignment presses and builds entries from GC. A HID press during assignment can be swallowed without assigning a player. Decide explicitly how to avoid this misleading behavior. HID battery, player lights, Identify and controller entries are out of scope. `ConsoleGlyphs.swift:100-104` chooses GC glyphs or keyboard, so HID hints may be misleading. Console ignores L/R/Select (`ConsoleView.swift:12-24`), while desktop Select enters console mode (`LauncherView.swift:503-507`).

`frontend/Tests/NX2AppleTests/ConsoleLiveTests.swift:622-635` protects GC-only controller entries and bans HID-related strings in four files and a specific watcher filename. A separate navigation connector can preserve that contract. Do not amend or bypass the test without a deliberate contract decision.

## Focus and duplicate input

Specify one active source per physical device. The dashboard skips GC-supported devices with nonzero IDs but accepts 0:0 (`HIDGamepads.swift:36-41`), so it cannot prevent late GC duplication. The external engine patch waits about three seconds, then reconciles on GC changes (`pr989-powera-hid.patch:130-132,195-225`). Its name-and-count fallback (`:73-81`) is heuristic: with unrelated or identically named devices it can suppress the wrong HID pad. A timer alone cannot establish identity. Define and test an explicit conservative ambiguity policy, including late GC, disconnect and two controllers, and disclose potential missed input.

Existing edges update before the activity check (`Gamepad.swift:100-111`): an inactive press can be recorded without being replayed on focus return. A direction can also start its repeat timer while inactive, and a shared action-only repeat can be stopped by another controller's release (`:105-108,113-123`). Specify focus loss, held buttons, release, disconnect and source handover so no stale or background action fires.

## Home is separate

Desktop Select is not physical Home. The external game-host patch describes a two-second Home hold and quit prompt in the game process (`NXNative/tools/patches/pr989-home-quit.patch:121-125`), with system gesture handling (`:39-45`). A launcher HID connector neither implements nor forwards in-game Home. No game binary changes are proposed.

## Order and verification

1. Sofian first tries the unchanged launcher and records observable behavior. Do not infer success from this audit.
2. After separate approval, settle mapping, identity, focus and assignment behavior, then implement the smallest connector and shared ownership.
3. Add pure tests for decoding and calibration boundaries, per-device edges, disconnect and handover, focus, capture, repeat, ambiguous and late GC discovery, plus existing action routing. Use a controllable scheduler only if needed. These tests were not run here.
4. Only with explicit later authorization, a human checks the actual device over available USB/Bluetooth connections, descriptor and button usages, focus and return from game, hotplug, simultaneous GC devices, nonexclusive game access and denied or permitted input access. TCC, sandbox and signed-app behavior are unknown.

Risk: name-based arbitration can lose legitimate input or still duplicate it. The audit itself changed only this report. It did not edit source code, alter runtime state, build, run tests, launch an app, change git configuration, commit or touch production.
