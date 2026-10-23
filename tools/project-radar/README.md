# Project Radar 1.0.0

Input: one explicitly selected project snapshot. Output: completed work with evidence, unresolved items, observed/expected versions with an honest explanation, and next actions. Loading a changed selected file refreshes the report and shows changed evidence rows. Downloading the selected snapshot preserves it for reopening. No Records, cross-chat, live feed, source scraping, account connection or automatic background update exists.

Open index.html in a modern browser. The initial DotSys snapshot is dated and points to public source revision ea31742. Use the file picker to select a reviewed newer JSON snapshot (maximum 256 KB). Nothing leaves the browser page. Invalid input preserves the previous valid report. Use DotSys snapshot resets to the bundled source; download/open restores a selection.

Editable source: index.html, radar.css, radar.js. SAMPLE in radar.js shows the exact format: schema dotsys.radar/1; source {project, revision, as_of in UTC, url}; completed/unresolved arrays of {id, text, evidence}; versions {expected, observed, explanation}; next array of actions. Evidence strings are displayed as text, not executed. Source URLs require HTTPS without credentials. Keep private records out of any snapshot you intend to publish.

Ask your dot to prepare a snapshot from a specific current source and report which evidence is unverified. Select it yourself in this browser. If source access is missing, retain the last valid report and state its date; do not invent a live connection. If file loading fails, retain/fix the source file and retry. If JavaScript is unavailable, the report cannot run.

Qualification: actual Chromium checks cover desktop, emulated mobile/touch and landscape; selected-source and selected-project changes, wrong-version explanation, download/reopen, inert source text and invalid JSON/schema/date/URL/size recovery. Physical phone/Safari checks are not claimed. Exact source hashes and machine-written results are in verification/collection/. Covered original source follows root LICENSE/NOTICE; no third-party library is bundled.
