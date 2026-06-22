# Phase 0 Research: Deduplication and Post-Processing for Wayback Site Recovery

Target site: `kyledurepos.com`

Role: R4

## Scope

This artifact evaluates practical strategies for recovering a website from the Internet Archive Wayback Machine while minimizing duplicate downloads, producing stable local filenames, cleaning saved HTML, and organizing the recovered file tree. It focuses on four recovery concerns:

- CDX digest deduplication before download.
- SHA256 on-disk deduplication after download.
- Removal of residual Wayback artifacts from saved HTML.
- URL normalization, snapshot selection, and local file tree layout.

The recommendations are concrete for `kyledurepos.com`, but the approach is reusable for similar small-to-medium static or mostly static sites.

## Executive Recommendation

Use a two-layer deduplication strategy: first deduplicate CDX records by Internet Archive `digest` to avoid downloading identical archived payloads, then compute SHA256 for every saved file to deduplicate content that remains equivalent after redirects, decompression, post-processing, or archive metadata differences. Select snapshots by quality first, recency second: prefer HTTP `200`, successful captures, expected mimetypes, and the newest capture within each unique digest group. Store recovered files in a mirror-path tree for human review and rebuild usability, with a separate manifest recording original URL, capture timestamp, CDX metadata, SHA256, and any filename collision handling. For `kyledurepos.com`, recover the latest high-quality HTML page set and associated static assets into a readable mirror tree, normalize query-bearing assets safely, strip Wayback toolbar and rewritten archive URLs from HTML, and keep duplicate payloads as manifest references rather than repeated files.

## CDX Digest Deduplication

The Wayback CDX API exposes a `digest` field, usually a base32-encoded content digest used by Internet Archive to identify archived payload identity. Multiple captures of the same URL, or different URLs returning identical content, can share the same digest.

Example CDX fields to request:

```text
urlkey,timestamp,original,mimetype,statuscode,digest,length
```

Recommended CDX query shape:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=urlkey,timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest
```

However, `collapse=digest` alone is not enough for full recovery planning because it may hide useful timestamp and URL variants. For analysis, first fetch the uncollapsed CDX index, then group locally by digest.

Recommended process:

1. Fetch all CDX records for `kyledurepos.com/*` and likely host variants such as `www.kyledurepos.com/*`.
2. Filter out obvious failures: non-`200` status, zero or missing length when suspicious, and non-content captures unless explicitly needed.
3. Group records by `digest`.
4. For each digest group, choose one canonical download record.
5. Preserve all skipped records in the manifest as aliases that point to the selected downloaded file.

Benefits:

- Reduces network usage substantially.
- Avoids saving many identical captures from repeated crawls.
- Keeps recovery deterministic when combined with a manifest.

Limitations:

- CDX `digest` represents the archived payload, not necessarily the final cleaned local file.
- Different archive wrappers or replay transformations may still produce local differences if using replay URLs instead of raw archive content.
- `collapse=digest` can accidentally discard the best URL or timestamp choice if used too early.

Recommendation for `kyledurepos.com`:

- Do not rely only on `collapse=digest` for the primary inventory.
- Build a full CDX inventory first, then locally group by digest.
- Choose the newest `200` record per digest, unless an older record has a better mimetype or URL path for reconstruction.

## SHA256 On-Disk Deduplication

After files are downloaded and optionally cleaned, compute SHA256 over the exact bytes written to disk. This catches duplicates that CDX digest grouping may miss, especially when:

- Different URLs serve identical assets.
- Query strings produce the same static file.
- HTML cleanup removes timestamp-specific archive artifacts.
- Redirect-resolved downloads differ in CDX metadata but not final content.
- The same image, CSS, JS, PDF, or font appears under multiple paths.

Recommended manifest fields:

```json
{
  "original_url": "https://kyledurepos.com/path/?v=1",
  "timestamp": "20240301000000",
  "archive_url": "https://web.archive.org/web/20240301000000id_/https://kyledurepos.com/path/?v=1",
  "statuscode": "200",
  "mimetype": "text/html",
  "cdx_digest": "...",
  "raw_sha256": "...",
  "final_sha256": "...",
  "local_path": "site/path/index.html",
  "duplicate_of": null
}
```

Use two hashes when possible:

- `raw_sha256`: hash of the downloaded raw archive response before cleanup.
- `final_sha256`: hash of the saved post-processed file.

Deduplication policy:

- Keep one physical file for each unique `final_sha256`.
- Keep every URL-to-file mapping in the manifest.
- For mirror-tree output, prefer preserving the canonical path for the best URL and record duplicate aliases in the manifest instead of writing hardlinks or symlinks by default.
- If exact mirror navigability is required, hardlinks can be used for duplicate binary assets, but avoid symlinks for portability.

Recommendation for `kyledurepos.com`:

- Compute SHA256 after Wayback HTML cleanup.
- Deduplicate static assets aggressively.
- Be conservative with HTML page dedup: if two different routes clean to identical HTML, keep one file and record aliases, but review whether route-specific canonical links or titles were stripped accidentally.

## Stripping Residual Wayback Artifacts from HTML

Wayback replay commonly injects or rewrites content. A clean recovered site should remove archive-specific UI, scripts, comments, and URL wrappers while preserving original site behavior as much as possible.

Common Wayback artifacts to remove:

- Toolbar markup such as `id="wm-ipp"`.
- Wayback scripts such as `/static/js/ait-client-rewrite.js`, `/static/js/wbhack.js`, and replay bootstrapping scripts.
- Wayback CSS such as `/static/css/banner-styles.css` and `/static/css/iconochive.css`.
- Comments such as `<!-- BEGIN WAYBACK TOOLBAR INSERT -->` and `<!-- END WAYBACK TOOLBAR INSERT -->`.
- Archive URL prefixes like `https://web.archive.org/web/<timestamp>/`.
- Replay modifiers such as `im_`, `id_`, `js_`, `cs_`, and `if_` embedded in archive URLs.
- Wayback-added JavaScript globals, for example `__wm`, `wbinfo`, or replay rewrite calls.

Use raw archive URLs where possible to reduce injected artifacts:

```text
https://web.archive.org/web/<timestamp>id_/https://kyledurepos.com/path/
```

The `id_` replay mode usually returns the archived file with fewer Wayback decorations. It does not eliminate the need for cleanup because references may still be rewritten or archived content may contain injected metadata.

HTML cleanup recommendations:

1. Parse HTML with an HTML parser rather than regex-only rewriting.
2. Remove known Wayback toolbar nodes by ID, class, script `src`, and stylesheet `href`.
3. Rewrite archive-wrapped URLs back to local relative paths when they target `kyledurepos.com` or `www.kyledurepos.com`.
4. Leave external third-party URLs external unless they were also archived and intentionally recovered.
5. Preserve original query strings during link analysis, then map them through the filename normalizer.
6. Do not strip arbitrary comments or scripts unless they match known Wayback patterns.

Archive URL rewrite examples:

```text
https://web.archive.org/web/20240301000000/https://kyledurepos.com/about/
-> /about/

https://web.archive.org/web/20240301000000im_/https://kyledurepos.com/assets/logo.png
-> /assets/logo.png

/web/20240301000000js_/https://kyledurepos.com/app.js?v=2
-> /app.js?v=2
```

Recommendation for `kyledurepos.com`:

- Download using `id_` URLs where feasible.
- Still run deterministic HTML cleanup.
- Rewrite internal links to local relative paths after final filename normalization so pages work offline.
- Preserve the pre-cleaned raw file only if auditability is important; otherwise, manifest metadata plus hashes are sufficient for Phase 0 recovery.

## URL Normalization for File Naming

URL-to-file normalization must produce safe, deterministic, portable paths while avoiding collisions between distinct URLs.

Key cases:

- Host variants.
- Query strings.
- Fragments.
- Trailing slashes.
- Index pages.
- Percent encoding.
- Case sensitivity.
- Extensionless routes.

Recommended normalization rules:

1. Lowercase scheme and hostname.
2. Treat `kyledurepos.com` and `www.kyledurepos.com` as the same site unless evidence shows distinct content.
3. Remove URL fragments because fragments are client-side only and are not sent to the server.
4. Preserve query strings in the manifest and encode them into filenames only when they affect content identity.
5. Normalize empty path to `/`.
6. Normalize paths ending in `/` to `index.html`.
7. Normalize extensionless HTML routes to `<route>/index.html` unless the mimetype indicates a binary or text asset.
8. Preserve existing file extensions for assets such as `.css`, `.js`, `.png`, `.jpg`, `.webp`, `.svg`, `.pdf`, `.woff`, and `.woff2`.
9. Decode safe percent-encoded characters for readability, but avoid decoding path separators or unsafe filesystem characters.
10. Replace unsafe filename characters with `_`.
11. Resolve collisions by appending a short hash derived from the full normalized URL.

Fragments:

- Drop fragments from file identity.
- Preserve fragment links in rewritten HTML when they point within the same page.
- For links to another page plus fragment, normalize the page path and append the original fragment.

Trailing slash examples:

```text
https://kyledurepos.com/
-> index.html

https://kyledurepos.com/about/
-> about/index.html

https://kyledurepos.com/about
-> about/index.html if mimetype is text/html
```

Index page examples:

```text
https://kyledurepos.com/index.html
-> index.html

https://kyledurepos.com/about/index.html
-> about/index.html
```

Query string examples:

```text
https://kyledurepos.com/app.css?v=123
-> app__q_v-123.css

https://kyledurepos.com/search?q=test
-> search__q_q-test/index.html or search__q_q-test.html, depending on route policy

https://kyledurepos.com/image.png?width=800
-> image__q_width-800.png
```

Recommended query filename rule:

- If a URL has no query, use the clean mirror path.
- If a URL has a query and the final SHA256 matches the no-query version, map it as a duplicate alias and do not create a query filename.
- If a URL has a query and content differs, append `__q_<sanitized-query-hash-or-params>` before the extension.
- For long or sensitive-looking queries, use `__q_<8-char-sha256>` instead of embedding the full query.

Recommendation for `kyledurepos.com`:

- Use `kyledurepos.com` as the canonical host.
- Merge `www.kyledurepos.com` into the same tree after dedup checks.
- Drop fragments from downloaded file identities.
- Preserve query variants only if they produce distinct SHA256 content.

## Snapshot Selection Strategy

The simplest recovery strategy is to choose the most recent `200` capture for every URL. This is easy to explain but can produce poor output if the latest capture is broken, incomplete, blocked, misclassified, or a soft error page.

Better strategy: score snapshots by quality, then use recency as a tie-breaker.

Recommended scoring signals:

- HTTP status `200` is preferred.
- Expected mimetype for the URL extension is preferred.
- Non-empty body length is required.
- Larger body can be better for HTML pages, within reason.
- Captures without obvious error text are preferred.
- Captures near the same date as the selected homepage are preferred for site consistency.
- Newer captures are preferred after quality checks.
- CDX digest uniqueness is used to avoid repeatedly evaluating identical content.

Avoid blindly selecting:

- `3xx` redirect records as final content unless reconstructing redirects intentionally.
- `404`, `403`, `500`, or `0` status records.
- `text/html` captures for expected image, CSS, JS, or font URLs because these are often error pages.
- Very small HTML pages that may be parked-domain, bot-check, or archive failure pages.

Suggested priority order:

1. Same-site content with status `200` and expected mimetype.
2. Most recent unique digest within the preferred quality class.
3. Snapshot timestamp close to the chosen homepage snapshot when reconstructing a consistent point-in-time version.
4. Larger plausible content length for HTML when comparing otherwise similar captures.
5. Manual review for homepage, navigation pages, CSS, JS, and major media assets.

Two viable recovery modes:

- Latest-good composite: choose the latest high-quality capture for each URL independently.
- Point-in-time reconstruction: choose a target date and prefer captures nearest that date.

For `kyledurepos.com`, the recommended Phase 0 default is latest-good composite because the likely goal is maximum recoverable content rather than forensic reconstruction of a single historical day.

Recommendation for `kyledurepos.com`:

- Select the latest high-quality `200` capture per unique digest and URL identity.
- Use the homepage's latest good timestamp as a soft anchor for HTML pages, but do not reject newer or older assets if they are the only valid copies.
- Manually inspect the selected homepage and top-level pages before committing to a final recovery run.

## File Tree Organization

There are two main output layouts: mirror-path and hash-named.

### Mirror-Path Tree

Example:

```text
site/
  index.html
  about/
    index.html
  assets/
    app.css
    logo.png
manifest.json
```

Advantages:

- Human-readable.
- Easy to browse locally.
- Matches expected static-site hosting layout.
- Easier to repair links and deploy.
- Better for recovering an actual website.

Disadvantages:

- Requires collision handling.
- Query-bearing URLs can create awkward filenames.
- Duplicate content may appear under multiple logical paths unless deduped through a manifest.

### Hash-Named Blob Store

Example:

```text
blobs/
  sha256/
    ab/
      abcdef...
manifest.json
```

Advantages:

- Perfect content-addressed deduplication.
- Collision-resistant.
- Good for archival audit trails.
- Easy to verify integrity.

Disadvantages:

- Not human-friendly.
- Not directly browsable as a recovered website.
- Requires a manifest or build step to reconstruct paths.

### Hybrid Layout

Example:

```text
recovered/
  site/
    index.html
    about/index.html
    assets/app.css
  manifest.json
  duplicates.json
  raw/optional/
  blobs/optional/
```

Recommendation:

- Use mirror-path as the primary output.
- Use SHA256 fields in the manifest as the deduplication and verification layer.
- Add a blob store only if preserving all raw downloads or building a repeatable archival pipeline is required.

Recommendation for `kyledurepos.com`:

- Use `recovered/kyledurepos.com/site/` as the primary mirror tree.
- Store `manifest.json` beside the tree.
- Avoid hash-named files in the public recovered site unless required for collision resolution.
- Use short hash suffixes only for true filename collisions or distinct query variants.

## Concrete Recovery Plan for kyledurepos.com

Recommended host scope:

```text
kyledurepos.com/*
www.kyledurepos.com/*
http://kyledurepos.com/*
https://kyledurepos.com/*
http://www.kyledurepos.com/*
https://www.kyledurepos.com/*
```

Recommended CDX inventory fields:

```text
urlkey,timestamp,original,mimetype,statuscode,digest,length
```

Recommended filters:

- Include `statuscode:200` for primary recovery.
- Include `mimetype:text/html`, CSS, JavaScript, image, font, PDF, plain text, JSON, XML, and SVG assets.
- Exclude known archive metadata endpoints and unrelated third-party hosts in the primary pass.
- Review redirects separately only if internal links depend on them.

Recommended selection:

- Use latest-good composite mode.
- Group by normalized URL identity, then by CDX digest.
- Prefer the newest `200` capture with expected mimetype.
- For duplicate digests across multiple URLs, choose the most semantically useful local path and record the others as aliases.

Recommended output structure:

```text
recovered/
  kyledurepos.com/
    site/
      index.html
      ...
    manifest.json
    duplicates.json
    selection-report.md
```

Recommended HTML post-processing:

- Remove Wayback toolbar, CSS, scripts, and comments.
- Rewrite internal archive URLs to local relative paths.
- Keep external links as external links unless those hosts are explicitly recovered.
- Normalize links to `index.html` paths where needed for offline browsing.
- Preserve anchors/fragments after path normalization.

Recommended dedup policy:

- CDX digest dedup before download to reduce redundant fetches.
- SHA256 raw hash immediately after download.
- Clean HTML.
- SHA256 final saved bytes.
- Use final SHA256 for physical deduplication.
- Keep all URL mappings in the manifest.

## Risks and Mitigations

Risk: Latest capture may be a broken or parked-domain page.

Mitigation: Score by mimetype, body length, and visible page quality before accepting the homepage and key pages.

Risk: Query string normalization may collapse distinct generated content.

Mitigation: Keep query strings in URL identity until SHA256 proves equivalence.

Risk: Wayback cleanup may remove legitimate site code.

Mitigation: Match only known Wayback IDs, paths, comments, and replay globals; avoid broad script removal.

Risk: `www` and apex hosts may have different content.

Mitigation: Merge only after CDX digest and SHA256 comparison; otherwise keep both paths or mark one canonical with aliases.

Risk: Mirror-path collisions may overwrite files.

Mitigation: Never write without checking existing path ownership; append short URL hash for collisions and record both in the manifest.

## Final Recommendations

- Use latest-good composite recovery for `kyledurepos.com`.
- Inventory both apex and `www` hosts.
- Deduplicate first by CDX digest, then by final SHA256.
- Use `id_` archive downloads where possible.
- Clean HTML with parser-based removal of known Wayback artifacts.
- Normalize URLs into a mirror-path tree with deterministic query collision handling.
- Drop fragments from downloaded identity but preserve them in rewritten links.
- Store every decision in `manifest.json` so aliases, duplicates, selected timestamps, hashes, and source URLs remain auditable.
- Prefer `recovered/kyledurepos.com/site/` as the usable recovered website layout, with optional raw/blob storage only if later phases require forensic retention.
