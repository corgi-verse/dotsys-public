## Specific artifact and process

Link the creation's submission.json, actual artifact, editable input/source, producing tool/version and PROCESS.md. Explain what you made and how someone can use it.

## Credit and rights

Identify original author, references, applicable licenses and parent creation for an adaptation. Confirm that every included file is intended for public distribution. Do not include private conversations, records, machine paths, credentials or private repository links.

## Actual use and recovery

Report the exact supported host, commands/user path, saved/reopened result and meaningful change. Include test receipts and known limitations. A prepared prompt or downloaded package is not a completed run.

## Maintainer checklist

- [ ] Run `python3 tools/validate_exchange.py --submission <path>`; inspect files without executing untrusted code.
- [ ] Review rights, privacy, actual use, editable source, credit and recovery; record review against exact artifact hash.
- [ ] Preserve parent author/id credit and original license/notices.
- [ ] Only after review, add submission + review receipt to creations/registry.json and discovery README; run `python3 tools/validate_exchange.py`.
- [ ] Merge through normal repository workflow. A submission does not authorize deployment or external publication.
