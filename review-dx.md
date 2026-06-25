# Developer Experience Review

The best operator experience is an interactive `archive-recovery new` command followed by non-interactive, config-driven stages. Human-authored TOML is easier to review than generated JSON, while per-run frozen JSON keeps executions reproducible.

Reports should be short, stage-specific, and stored under ignored run directories. Tracked docs should explain concepts and templates, not contain private run evidence.
