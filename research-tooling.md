# Tooling Research

Existing tools such as `wget --mirror`, `waybackpack`, and library wrappers are useful for quick exports, but a reusable recovery toolkit needs stronger control over CDX pagination, alias preservation, capture selection, MIME validation, retries, manifests, and publication policy.

The recommended core is a custom Python CLI with small, config-driven stages. Specialized tools can still be used as optional plugins or external helpers when they produce auditable artifacts under the ignored run directory.
