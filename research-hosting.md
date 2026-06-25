# Hosting Research

Recovered output should be static files. Serving should prefer exact files, directory indexes, and optional `.html` fallback; it should not use an SPA fallback that masks missing assets.

Caddy is a good default for local review because its configuration is compact and MIME handling is reliable. nginx is a good production option when already available. Tailscale Serve or Funnel can be used only when the privacy policy allows the selected exposure mode.

Generated operational files belong under `runs/<run_id>/ops/` and should not be committed.
