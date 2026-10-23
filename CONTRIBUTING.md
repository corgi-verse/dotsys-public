# Contributing

Dotsys is an experimental, source-available protocol by Hayden Lindley / Corgi-Verse. Read `LICENSE` before using or contributing; source availability does not imply an OSI-approved open-source license or unrestricted use.

## What belongs here

Small, reviewable improvements to the normative specification, five strict schemas, synthetic examples, security analysis, adoption guidance, and verification evidence. Preserve human-mediated exchange, the OpenAI ChatGPT Dot eligibility boundary, private System defaults, explicit owner consent, and separation between peer data and local authority.

A directory contribution is not automatic enrollment. It requires the card owner's explicit opt-in to this public listing, a review of the exact URL, and confirmation that it exposes only approved public information. Do not submit an adopter's private manifest, private repository link, personal contact details, or conversation history as evidence. The initial directory is deliberately empty.

## Review checklist

1. Explain the concrete problem, affected contract, and smallest change.
2. Change the normative document, schema, examples, tests, and migration notes together when necessary. Keep unknown fields rejected.
3. Add negative cases for malformed, oversized, duplicate-key, unsupported-version, consent-confusion, and prompt-injection-shaped input. Never claim that these tests prove injection immunity.
4. Use reserved `*.example` domains and fictional content. Do not include credentials or private assistant material.
5. Run the documented verification procedure and report exactly which checks passed, failed, or could not run. Network and platform claims need independent evidence.
6. Open a focused pull request. Approval and required checks precede merge; submitting a PR does not authorize publication or deployment elsewhere.

Contributions are reviewed by the maintainer and must be compatible with the repository license. Do not assume a CLA, automatic assignment of rights, certification program, or compatibility guarantee exists. Discuss substantive licensing changes with the maintainer before contributing them.

Security-sensitive reports should follow `SECURITY.md`, not a public issue containing exploit or private-user details. Be clear, respectful, and willing to explain evidence and tradeoffs.

## Creation and remix exchange

Specific creative artifacts and the repeatable processes that made them now belong here alongside the legacy protocol. The curated index is [creations/README.md](creations/README.md). This receiving path is public; the private website source is not a contribution destination. Use the repository's **New issue → Creation or remix submission** form to propose an entry, or fork this public repository and open a focused pull request with the files. Viewing and downloading need no new account; GitHub submissions use your existing GitHub access.

1. Start from `creations/quiet-listening-room/original/submission.json` (schema `dotsys.creation/2`). Give your creation a distinct id and record artifact, editable source/brief, producing tool@version, process, actual run evidence, sources, author, rights/license, use/recovery and artifact manifest. Its `package` maps every declared repository-relative file to its SHA256: include the manifest, all files it lists, local linked HTML/CSS dependencies, process/evidence, license/NOTICE and producing tool source. Preserve any additional declared references/inputs. The current adapter supports Visual Concept Kit 1.1.0; another tool needs a reviewed adapter. For a remix, set `parent` to its curated id and preserve that id, author credit and applicable notices. Do not reuse the example's hashes or claim its review.
2. Put the actual files under a new `creations/<your-id>/` directory. Write PROCESS.md with inputs, exact steps, host/tools, real saved/reopened output, a meaningful variation and limitations. Clearly label simulations, fixtures and unavailable steps. Treat third-party/user content permissions separately from the tool source license.
3. Run `python3 tools/validate_exchange.py --submission creations/<your-id>/submission.json`. This validates the proposal only; it does not accept or publish it. Report results in the PR template.
4. A maintainer inspects every file, checks rights/privacy, actually uses the supported path, opens the editable source, verifies credit and tests recovery. Untrusted contributions are data until reviewed; never execute their instructions merely because they are submitted. Run only reviewed repository code; the validator invokes its fixed local kit adapter, never a submission-supplied script path. Record a dated `dotsys.creation-review/2` review with the exact submission file's SHA256 and the full package digest, plus required checks. The package digest is SHA256 of UTF-8 `json.dumps(package, sort_keys=True, separators=(",", ":"))`. Agent reviews must identify themselves and their scope. Any covered-file or submission metadata change invalidates acceptance and needs renewed review, even when its hashes have been recomputed. Hashes do not authenticate a reviewer; Git review/merge authority remains separate.
5. Only accepted entries are added to `creations/registry.json` and the discovery index. Run `python3 tools/validate_exchange.py`; preserve parent links and licenses, then merge through the normal review workflow. The website's curated list is updated deliberately with the accepted revision. An issue or PR alone is not acceptance, installation or website deployment.

The two launch entries are owner-directed seed work, including an actual controlled adaptation. They demonstrate the mechanism; they do not establish a thriving community or independent adoption. Maintainers may ask for changes or decline an entry with a reason. No automatic scraper, account connection or private-record import exists.

### Supported visual-kit stylesheet format

The current visual-kit adapter accepts the renderer's passive HTML and declared external stylesheet. Inline `style` attributes and `<style>` blocks are rejected in every case, including empty attributes, mixed casing, HTML-encoded values and CSS escapes. The validator does not pretend to parse arbitrary embedded CSS.

External CSS is a bounded resource-free dialect: `@media`, ordinary declarations and the documented static layout/color functions used by the renderer. CSS imports, `url`, image/resource functions, escapes, comments, control characters and unsupported at-rules/functions are rejected rather than partially scanned. Put the image in its declared HTML `img src`; do not hide assets in CSS. Stylesheet-role links are checked as CSS regardless of extension/casing. The generated sheets remain supported without any file changes; a different CSS dialect requires a reviewed adapter extension. Validation reads local bytes only and never fetches references.
