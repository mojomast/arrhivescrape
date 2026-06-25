# Wayback Recovery Tooling Comparison for kyledurepos.com

Phase 0 research comparing tooling options for recovering `kyledurepos.com` from the Internet Archive Wayback Machine.

## Evaluation Criteria

- **Resumability**: Can interrupted downloads continue without redoing all work?
- **Parallel worker support**: Can multiple captures/files be fetched concurrently?
- **Binary file handling**: Can images, PDFs, archives, fonts, videos, and other non-HTML assets be recovered safely?
- **Rate-limit compliance**: Does the tool make it easy to avoid overloading the Wayback Machine?
- **`id_` support / clean captures**: Can it request raw archived payloads using Wayback `id_` mode instead of rewritten Wayback playback HTML?
- **Clean file tree output**: Does it produce a local tree resembling the original site, without Wayback wrapper paths or excessive post-processing?

## Summary Matrix

| Tool | Resumability | Parallel Workers | Binary Handling | Rate-Limit Compliance | `id_` / Clean Captures | Clean File Tree | Best Fit |
|---|---:|---:|---:|---:|---:|---:|---|
| `waybackpack` | Medium | Limited / batchable externally | Good | Medium | Yes, commonly supports raw URLs | Good | Simple static-site recovery from CDX snapshots |
| `wget --mirror` | High | Low built-in; external sharding possible | Good | Good with wait options | Only if carefully using `id_` URLs | Medium to poor unless configured carefully | Mirroring known URL lists or small recoveries |
| Python `wayback` library / `WaybackClient` | High if implemented | High if implemented | Good if streamed correctly | High if implemented | Yes | High if implemented | Custom controlled recovery pipeline |
| `internetarchive` CLI | Medium | Limited | Mixed for Wayback use | Good | Not ideal for Wayback playback recovery | Poor for reconstructed web trees | Archive item metadata/files, not primary Wayback site recovery |
| Scrapy + Wayback middleware | High | High | Good with pipelines | High | Yes if middleware requests raw captures | High if customized | Large, policy-controlled crawls and transformations |

## Tool Evaluations

### `waybackpack`

`waybackpack` is one of the most directly relevant tools for recovering a historical website from Wayback captures. It queries CDX data, selects captures, downloads archived files, and writes them into a local directory structure that generally resembles the original site.

**Strengths**

- Purpose-built for Wayback site recovery rather than live-web mirroring.
- Usually produces a cleaner output tree than raw `wget` against Wayback playback URLs.
- Can use raw capture-style downloads, avoiding much of the Wayback toolbar and rewrite layer.
- Handles common binary assets such as images, CSS, JavaScript, fonts, and PDFs reasonably well.
- Good fit for Phase 0/Phase 1 recovery when the goal is to quickly establish what can be reconstructed.

**Weaknesses**

- Parallelism is limited compared with a custom crawler or Scrapy project.
- Resumability depends on output already present and how the command is re-run; it is not a full checkpointed job system.
- Rate limiting is less explicit than in a custom pipeline. Care is still needed to avoid aggressive repeated CDX and capture requests.
- Capture selection can require multiple passes if the site has inconsistent archival coverage across timestamps.

**Criterion Notes**

- **Resumability**: Medium. Re-running can often skip existing files or overwrite predictably depending on options, but it is not a robust job queue.
- **Parallel worker support**: Limited. Parallelism can be approximated by splitting URL scopes or timestamp ranges, but this must be managed externally.
- **Binary file handling**: Good. It is generally suitable for static assets and documents.
- **Rate-limit compliance**: Medium. Acceptable for modest use, but external throttling or conservative execution is recommended.
- **`id_` support / clean captures**: Good. This is one of the reasons to prefer it over naive Wayback `wget` mirroring.
- **Clean file tree output**: Good. Usually one of the cleaner outputs among off-the-shelf tools.

**Recommended Use**

Use `waybackpack` when the objective is a straightforward static recovery of `kyledurepos.com`, especially if the site is mostly HTML, CSS, JavaScript, images, and documents. It is a strong first practical tool after CDX reconnaissance.

### `wget --mirror`

`wget --mirror` is powerful for mirroring live sites or known URL sets, but it is not Wayback-aware by default. When pointed at normal Wayback playback URLs, it can capture rewritten pages, Wayback chrome, timestamped paths, and transformed links instead of clean original assets.

**Strengths**

- Mature, reliable downloader with excellent resume behavior.
- Handles binary files well.
- Built-in throttling options such as `--wait`, `--random-wait`, `--limit-rate`, and retry controls.
- Useful when given a curated list of raw `id_` capture URLs.
- Easy to script and available on most systems.

**Weaknesses**

- Not inherently CDX-aware.
- Naive mirroring of Wayback playback pages often produces polluted output.
- Link conversion can preserve Wayback URLs unless carefully configured and post-processed.
- Built-in parallelism is poor; parallel downloading requires sharding input or using external tools.
- Timestamp and capture selection must be handled separately.

**Criterion Notes**

- **Resumability**: High. `wget -c`, timestamping, retry controls, and existing-file behavior are mature.
- **Parallel worker support**: Low. Use external sharding, multiple processes, or a different downloader if concurrency is required.
- **Binary file handling**: Good. Reliable for images, documents, fonts, scripts, archives, and similar assets.
- **Rate-limit compliance**: Good. Strong throttle controls make it easy to be polite.
- **`id_` support / clean captures**: Conditional. It can download `id_` URLs, but it will not discover or prefer them automatically.
- **Clean file tree output**: Medium to poor. Clean output requires careful URL construction, `--cut-dirs`, `--no-host-directories`, `--adjust-extension`, and often post-processing.

**Recommended Use**

Use `wget --mirror` only when you already have a curated list of raw capture URLs or a narrow recovery target. It is less appropriate as the primary discovery mechanism for `kyledurepos.com`, but useful as a controlled fetcher in a pipeline built around CDX output.

### Python `wayback` Library / `WaybackClient`

The Python `wayback` library, especially `WaybackClient`, is best treated as a programmable CDX and capture retrieval layer. It is not a complete recovery product by itself, but it can be the foundation of a high-quality custom recovery pipeline.

**Strengths**

- Fine-grained control over CDX queries, timestamp selection, MIME filtering, status filtering, deduplication, and retry behavior.
- Can explicitly request raw captures using `id_`-style URLs or equivalent replay URL construction.
- Can implement durable resumability through manifests, SQLite, JSONL checkpoints, or content-addressed storage.
- Can implement controlled concurrency with worker pools or async clients.
- Allows site-specific cleanup, canonical path mapping, duplicate suppression, and asset rewriting.

**Weaknesses**

- Requires engineering effort.
- Clean output depends entirely on implementation quality.
- Binary handling must be implemented carefully with streaming writes, content-type checks, extension inference, and no accidental text decoding.
- Rate-limit compliance must be designed rather than assumed.

**Criterion Notes**

- **Resumability**: High if implemented with a manifest or database. Low if written as a one-off script without state.
- **Parallel worker support**: High if implemented. Worker count, backoff, and retries can be tuned precisely.
- **Binary file handling**: Good if responses are streamed as bytes and metadata is preserved.
- **Rate-limit compliance**: High if implemented with global throttling, exponential backoff, retry-after handling, and conservative CDX usage.
- **`id_` support / clean captures**: High. This is one of the strongest reasons to use a custom Python pipeline.
- **Clean file tree output**: High if implemented with deterministic URL-to-path mapping and rewrite rules.

**Recommended Use**

Use `WaybackClient` when recovery quality matters more than immediate convenience. For `kyledurepos.com`, this is the best choice if Phase 0 discovers inconsistent captures, multiple timestamp eras, missing assets, duplicate URLs, or a need for auditable manifests and repeatable recovery.

### `internetarchive` CLI

The `internetarchive` CLI is excellent for interacting with Internet Archive items, metadata, and uploaded files. It is not primarily designed to reconstruct websites from Wayback CDX captures.

**Strengths**

- Strong for listing, downloading, and inspecting archive.org item files and metadata.
- Useful if `kyledurepos.com` has been saved as a dedicated Archive item, WARC package, uploaded ZIP, or collection entry.
- Mature authentication, metadata, and file-management workflows for archive.org items.

**Weaknesses**

- Not a natural fit for Wayback Machine site reconstruction.
- Does not provide a clean local website tree from CDX captures by default.
- Not ideal for selecting best captures across timestamps.
- Limited relevance for `id_` playback recovery compared with Wayback-specific tools.

**Criterion Notes**

- **Resumability**: Medium. Good for item-file downloads, less relevant for reconstructed Wayback fetches.
- **Parallel worker support**: Limited for this use case.
- **Binary file handling**: Mixed. Good for archive item files; not a focused Wayback asset fetcher.
- **Rate-limit compliance**: Good for intended archive.org operations.
- **`id_` support / clean captures**: Poor to not applicable for website reconstruction.
- **Clean file tree output**: Poor for this task unless the Archive item already contains a prepared tree or WARC.

**Recommended Use**

Use `internetarchive` CLI as a supporting tool, not the primary recovery mechanism. It is appropriate if research finds existing archive.org items, WARCs, ZIPs, or metadata related to `kyledurepos.com`. It should not be the default choice for CDX-based Wayback site reconstruction.

### Scrapy With Wayback Middleware

Scrapy with Wayback-aware middleware is the most scalable and customizable crawler-style approach. It can combine CDX discovery, raw capture fetching, link extraction, pipelines, deduplication, and structured logging.

**Strengths**

- Strong concurrency model with configurable worker counts.
- Built-in retry, throttling, AutoThrottle, caching, pipelines, and request scheduling.
- Can maintain resumable crawl state with job directories and custom manifests.
- Handles large URL spaces better than ad hoc scripts.
- Good place to implement canonical path mapping, content hashing, duplicate detection, link rewriting, and asset validation.
- Can request raw `id_` captures if the middleware constructs replay URLs correctly.

**Weaknesses**

- More setup than `waybackpack` or `wget`.
- Requires careful middleware design to avoid crawling Wayback chrome or rewritten playback links.
- Binary file output requires custom pipeline handling or FilesPipeline customization.
- Overkill for a small mostly-static site unless recovery needs are complex.

**Criterion Notes**

- **Resumability**: High with Scrapy job persistence plus an explicit manifest.
- **Parallel worker support**: High. This is one of Scrapy's core strengths.
- **Binary file handling**: Good if implemented through byte-preserving pipelines and content-type-aware naming.
- **Rate-limit compliance**: High. AutoThrottle, download delays, retry policies, and concurrency caps are mature.
- **`id_` support / clean captures**: High if the middleware consistently requests raw captures and strips Wayback wrappers from discovered links.
- **Clean file tree output**: High if a custom item pipeline maps original URLs to deterministic local paths.

**Recommended Use**

Use Scrapy when `kyledurepos.com` requires a larger crawl, many timestamp fallbacks, robust auditing, concurrent but polite fetching, or nontrivial post-processing. It is the best long-running crawler architecture, but not the fastest path to an initial proof-of-recovery.

## Recommendations for kyledurepos.com

### Best Initial Tool

Start with **`waybackpack`** after CDX reconnaissance. It is purpose-built for this job and should provide the fastest useful answer about how much of `kyledurepos.com` can be recovered into a clean tree.

### Best High-Quality Pipeline

Use **Python `WaybackClient`** if the recovery needs to be repeatable, auditable, resumable, and capture-aware. It provides the best balance of control and implementation effort for a custom reconstruction workflow.

### Best Large-Scale Architecture

Use **Scrapy with Wayback middleware** if the site has many URLs, complex asset dependencies, multiple viable capture windows, or requires crawler-grade scheduling and throttling.

### Best Supporting Downloader

Use **`wget --mirror`** only after producing a curated list of raw `id_` capture URLs. It is reliable for downloading, but weak for Wayback discovery and clean reconstruction by itself.

### Best Archive Metadata Tool

Use **`internetarchive` CLI** only for checking archive.org items, WARCs, uploaded snapshots, or related metadata. It should not be the main Wayback recovery tool.

## Practical Ranking

1. **`waybackpack`**: Best first recovery attempt for a static site.
2. **Python `WaybackClient`**: Best controlled custom recovery path.
3. **Scrapy with Wayback middleware**: Best for large or complex crawl recovery.
4. **`wget --mirror`**: Useful fetcher when paired with CDX-derived `id_` URLs.
5. **`internetarchive` CLI**: Useful support tool, not a primary site reconstructor.

## Phase 0 Conclusion

For `kyledurepos.com`, the recommended Phase 0 path is to use CDX reconnaissance to identify viable timestamp ranges, run `waybackpack` for a quick clean-tree recovery, and keep Python `WaybackClient` as the fallback or next-step implementation if capture selection, resumability, or auditability becomes important. Scrapy should be reserved for a larger recovery job where crawler infrastructure is justified. `wget` and `internetarchive` remain useful supporting tools but should not drive the primary workflow.
