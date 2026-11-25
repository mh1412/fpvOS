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
