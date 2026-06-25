# Deduplication And Post-Processing Research

The pipeline uses two deduplication layers: CDX digest collapse before download, and SHA256 over downloaded raw bytes. Normalized output may have different hashes after link rewriting or artifact removal, so manifests should record raw and final hashes separately.

URL normalization should canonicalize scheme and host according to config, fold configured aliases, remove fragments, preserve meaningful query strings, hash query collisions in output paths, and keep a manifest entry for each source capture and output file.
