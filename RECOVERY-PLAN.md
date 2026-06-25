# Generic Recovery Plan

Use this plan for a new archived-site recovery.

1. Run `python -m archive_recovery new` and answer the target interview.
2. Review `configs/<domain>.toml` for scope, aliases, target mode, rate limits, output paths, privacy policy, and serving preference.
3. Initialize or reuse the scaffolded run directory under `runs/<run_id>/`.
4. Inventory CDX captures with the configured filters and pagination.
5. Select captures according to the target mode.
6. Download selected captures through Wayback `id_` URLs into `raw/sha256/`.
7. Normalize static output into the run staging site.
8. Validate links, MIME classes, privacy policy, and serving behavior.
9. Promote only approved output into `recovered/<domain>/releases/<run_id>/site/`.
10. Serve locally, over a tailnet, or publicly only when the configured policy permits it.

Generated files, raw archives, run reports, databases, logs, and publication artifacts are local-only and ignored by git.
