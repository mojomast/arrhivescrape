# Tools Directory

The reusable entry point is the `archive_recovery` package and `archive-recovery` CLI.

Historical one-off scripts from completed recoveries are local-only and ignored by git. If a script becomes reusable, move the logic into `archive_recovery`, make the target domain and paths config-driven, and add documentation or tests before tracking it.
