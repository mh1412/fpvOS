# 50 Mbps exploration

The platform changes on this branch configure the AR9311 MMC FIFO depth,
bring up both P1 CPU cores, mark its soldered radio non-removable, and select
SDIO receive-worker/IRQ affinity with FIFO priority through board defaults.
The driver leaves its scheduling unchanged unless a board opts in.

`ar-libre-16k.patch` is an optional experiment against ar_libre commit
`aa94f45394cc76be5fa2955f51bd003a532ac60c`. Apply it in an isolated dependency
checkout with `git apply /path/to/ar-libre-16k.patch`, then rebuild the client
library and applications. It enables 16 KiB host writes and write-path timing.
It is not applied by the normal Buildroot recipe.

Use matching Open8030 and Kestrel exploration patches. Large writes have no
capability negotiation and must not be used with older radio firmware.
These patches do not create an installable high-rate profile. The normal
image still uses its pinned application/radio versions. Raw results, device
calibration, binaries and development logs remain outside Git.

Validation targets are actual received video averaging at least 50 Mbps,
minimum 30-second throughput of 49 Mbps, no steady transport/radio drops or
decoder errors, active display, concurrent USB load, and downshift/recovery.
A bench result does not establish field range or glass-to-glass latency.

## P1 goggles

Use the P1 goggles radio profile and native Kestrel board build, not the
Ascent VRX binaries or RF configuration. The normal P1 goggles MCS table
ends at MCS10. For the experimental build, append MCS11 and MCS13 rows to
`baseband.basic.dev.mcs.slot.mcs_tab`, copying the MCS10 row's thresholds,
and retain `mode: auto` and `init: -1`. Those copied thresholds are an
experimental policy, not vendor-validated thresholds for the higher rates.
Build the radio with `AR_NO_CEILING_40` in addition to its normal P1 goggles
flags. Use the matching radio patch and Kestrel Ground receive-buffer patch.

For a persistent test image, package that native Kestrel build with its
`tools/package_ascent.py` tool. Include the matched radio image, modified
**uncalibrated board template**, and native runtime in the Buildroot image.
The installed paths are `/lib/firmware/open8030.img`,
`/lib/firmware/open8030.json`, and `/usr/share/kestrel/runtime.squashfs`.
Keep the board's normal factory-calibration merge at boot; never package a
configuration copied from one device after calibration. The normal package
recipes do not enable these experiments automatically.

The Air also needs the matching experimental application, client library,
and radio. Flashing only the goggles does not raise an ordinary Air build's
video bitrate limit. The Air patch's transmit-power override is for controlled
bench tests, not a flight default.

Bench validation with P1 Air and P1 goggles reached approximately 50 Mbps of
received video with concurrent USB traffic. Controlled MCS ceilings reduced
video to about 42.5 Mbps at MCS11 and 19 Mbps at MCS8, recovering to 50.3 Mbps
without transport loss or decoder errors in that test. The persistent goggles
image also booted after a full power cycle with visually stable video.

These results do not meet every sustained-rate target above: a separate run
averaged 49.8 Mbps, its lowest 30-second window was 48.7 Mbps, and Air queue
backoffs remained. Startup/reconnect tests also saw damaged slices before the
stream settled. Controlled rate caps are not RF attenuation or range tests;
field reliability and end-to-end latency remain unvalidated.
