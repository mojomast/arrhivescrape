# Internet Archive Wayback CDX Server API Research For Recovering kyledurepos.com

This document summarizes how to use the Internet Archive Wayback CDX Server API from a blank Linux folder to discover, deduplicate, page through, and download archived captures of `kyledurepos.com`.

## Core CDX Endpoint

The primary CDX Server API endpoint is:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json
```

The CDX API returns metadata rows for archived captures. It does not return the captured resource body itself. Resource bodies should be fetched separately from Wayback replay URLs.

## Important Query Parameters

### `url`

The `url` parameter selects the target URL or URL pattern to query.

Examples:

```text
https://web.archive.org/cdx?url=kyledurepos.com&output=json
https://web.archive.org/cdx?url=www.kyledurepos.com&output=json
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json
https://web.archive.org/cdx?url=*.kyledurepos.com/*&output=json
```

Common recovery patterns:

- `kyledurepos.com` retrieves exact homepage captures depending on `matchType` behavior.
- `kyledurepos.com/*` retrieves captures beneath the host.
- `*.kyledurepos.com/*` retrieves captures across subdomains.

URL values should be shell-quoted when used with tools like `curl` because `*`, `&`, and `?` have shell meaning.

### `output`

The `output` parameter controls response format.

Useful values:

- `json`: easiest for scripts; first row is field names unless `fl` and API behavior omit it in some contexts.
- `txt`: plain CDX text rows.

Recommended for recovery automation:

```text
output=json
```

Example:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest,length
```

### `fl`

The `fl` parameter selects fields returned for each capture.

Common fields:

- `urlkey`: SURT-normalized key used internally for sorting and grouping.
- `timestamp`: capture timestamp in `YYYYMMDDhhmmss` UTC format.
- `original`: original captured URL.
- `mimetype`: detected MIME type.
- `statuscode`: HTTP status returned by the origin at capture time.
- `digest`: content hash used for duplicate detection.
- `length`: archived payload length or record length metadata.
- `offset`: WARC record offset, useful for advanced direct WARC retrieval.
- `filename`: WARC file name, useful for advanced direct WARC retrieval.

Best practical field selection for deduplicated discovery and later download:

```text
fl=timestamp,original,mimetype,statuscode,digest,length
```

Best practical field selection when planning advanced WARC-level retrieval:

```text
fl=timestamp,original,mimetype,statuscode,digest,length,offset,filename
```

For a normal website recovery workflow using Wayback replay URLs, `timestamp`, `original`, `mimetype`, `statuscode`, `digest`, and `length` are usually sufficient.

### `collapse`

The `collapse` parameter removes adjacent duplicate rows by a field.

Common values:

- `collapse=digest`
- `collapse=urlkey`
- `collapse=timestamp:N`, such as `collapse=timestamp:8`

#### `collapse=digest`

`collapse=digest` collapses adjacent captures with the same content digest. This is usually the best deduplication mode for downloading because it avoids repeatedly fetching identical bytes captured at different times.

Example:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest
```

Use `collapse=digest` when the goal is to recover unique files/content with fewer downloads.

Important nuance: CDX collapse generally collapses adjacent records after sorting, so the exact deduplication effect can depend on sort/order and query shape. For full offline deduplication, still track seen `digest` values in your downloader.

#### `collapse=urlkey`

`collapse=urlkey` collapses adjacent captures that have the same normalized URL key. This usually keeps one representative capture per canonicalized URL, regardless of whether content changed over time.

Example:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest&filter=statuscode:200&collapse=urlkey
```

Use `collapse=urlkey` when the goal is to get a URL inventory, such as one row per unique archived path.

Do not use `collapse=urlkey` as the only deduplication strategy for content recovery if historical changes matter, because it may hide earlier or later versions of the same URL.

#### Practical Difference

`collapse=digest` answers: "Which unique content blobs exist?"

`collapse=urlkey` answers: "Which unique normalized URLs exist?"

For recovering a static site, a common approach is:

1. Use `collapse=urlkey` to build a broad URL inventory.
2. Use `collapse=digest` or local digest tracking to avoid redundant downloads.
3. Prefer successful `200` captures with useful MIME types.

### `filter`

The `filter` parameter includes or excludes rows matching field expressions.

Common filters:

- `filter=statuscode:200`: only successful origin responses.
- `filter=mimetype:text/html`: only HTML.
- `filter=mimetype:image/.*`: image captures, using a regular expression style match.
- `filter=!mimetype:warc/revisit`: exclude revisit records if they are not useful for a workflow.

Examples:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&filter=mimetype:text/html
```

For site recovery, `filter=statuscode:200` is usually the first filter to apply. Be cautious about over-filtering by MIME type too early because CSS, JavaScript, fonts, PDFs, images, JSON, XML, and text files may all be needed.

### `from`

The `from` parameter limits results to captures at or after a date/time.

Accepted values can be partial timestamps such as year, year-month, full date, or full timestamp.

Examples:

```text
from=2018
from=201801
from=20180101
from=20180101000000
```

Example CDX URL:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest&filter=statuscode:200&from=2018
```

### `to`

The `to` parameter limits results to captures at or before a date/time.

Examples:

```text
to=2020
to=202012
to=20201231
to=20201231235959
```

Example CDX URL:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest&filter=statuscode:200&from=2018&to=2021
```

### `limit`

The `limit` parameter caps the number of rows returned.

Examples:

```text
limit=100
limit=1000
```

Example:

```text
https://web.archive.org/cdx?url=kyledurepos.com/*&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&limit=1000
```

For large recovery jobs, use a moderate `limit` and paginate with `resumeKey` rather than requesting huge result sets in one call.

### `matchType`

The `matchType` parameter controls how the `url` parameter is matched.

Useful values:

- `exact`: match the exact URL.
- `prefix`: match URLs starting with the supplied URL/prefix.
- `host`: match the host.
- `domain`: match the registered domain and subdomains.

Examples:

```text
https://web.archive.org/cdx?url=kyledurepos.com/&matchType=exact&output=json
https://web.archive.org/cdx?url=kyledurepos.com/&matchType=prefix&output=json
https://web.archive.org/cdx?url=kyledurepos.com&matchType=host&output=json
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json
```

For a broad recovery of `kyledurepos.com`, use either wildcard URL patterns or `matchType=domain`:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200
```

### `resumeKey`

`resumeKey` is used for cursor-style pagination through large CDX result sets.

Workflow:

1. Request a page with `limit=N` and `showResumeKey=true`.
2. Read the returned resume key.
3. Request the next page with the same query parameters plus `resumeKey=<key>`.
4. Repeat until no new resume key is returned or the result page is empty.

Example first page:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&limit=1000&showResumeKey=true
```

Example next page shape:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&limit=1000&showResumeKey=true&resumeKey=PASTE_RETURNED_RESUME_KEY_HERE
```

Keep all other query parameters identical between pages. Changing `url`, `filter`, `fl`, `collapse`, date bounds, or match type while reusing a resume key can produce invalid or inconsistent traversal.

## Why Download URLs Must Use `id_`

Wayback replay URLs have this general form:

```text
https://web.archive.org/web/{timestamp}/{original_url}
```

For recovery downloads, use the `id_` replay modifier:

```text
https://web.archive.org/web/{timestamp}id_/{original_url}
```

Concrete example:

```text
https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/
```

The `id_` modifier requests the archived object as close to the original captured payload as Wayback can serve it, without the normal Wayback browser toolbar and without most replay rewriting intended for interactive browsing. This matters for recovery because normal replay can inject HTML, rewrite links, rewrite scripts, and otherwise alter bytes for browser playback.

All content fetch URLs in a recovery downloader should use:

```text
https://web.archive.org/web/{ts}id_/{url}
```

Reasons:

- It avoids saving the Wayback toolbar as part of recovered HTML.
- It avoids depending on rewritten replay URLs as recovered source content.
- It provides cleaner CSS, JavaScript, image, font, JSON, XML, PDF, and binary downloads.
- It makes local path mapping and checksum/digest validation more predictable.

Do not use plain replay URLs for downloaded site files:

```text
https://web.archive.org/web/{ts}/{url}
```

Plain replay URLs are useful for human inspection in a browser, but they are the wrong default for automated content recovery.

## Rate Limits And Politeness

Observed and commonly recommended practical limits:

- CDX API: about 60 requests per minute.
- Memento/availability-style APIs: about 30 requests per second.

For this recovery workflow:

- Treat CDX as the slower metadata API and keep it near or below `~60 req/min`.
- Use `limit` plus `resumeKey` to reduce CDX calls.
- Add retries with exponential backoff for `429`, `503`, transient network errors, and timeouts.
- Avoid many concurrent CDX requests.
- Keep content download concurrency conservative because large downloads can stress the service even if metadata calls are within limits.

Suggested conservative defaults from a blank Linux recovery script:

- CDX requests: one request at a time, sleep at least 1 second between requests.
- Content downloads: 2 to 4 concurrent downloads initially, reduce on `429` or `503`.
- Retry delay: start around 5 seconds, then back off.

## Best Field Selection For Deduplication And Download

Recommended CDX query for broad deduplicated download candidates:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```

Why these fields:

- `timestamp`: required to build `https://web.archive.org/web/{timestamp}id_/{original}`.
- `original`: required to know the original URL and derive a local output path.
- `mimetype`: useful to classify files and avoid accidentally treating binary data as text.
- `statuscode`: confirms successful origin captures; usually filter to `200`.
- `digest`: useful for deduplication across repeated captures and different URLs with identical content.
- `length`: useful for validation, prioritization, logging, and detecting suspicious tiny/error captures.

Recommended CDX query for full URL inventory:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=urlkey,timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=urlkey&limit=1000&showResumeKey=true
```

Recommended CDX query for historical versions of HTML pages:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&filter=mimetype:text/html&limit=1000&showResumeKey=true
```

## Concrete Example Workflow From A Blank Linux Folder

Create working directories:

```bash
mkdir -p cdx downloads logs
```

Fetch a first CDX page of successful captures:

```bash
curl -fsSL 'https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true' -o cdx/kyledurepos-page-001.json
```

Convert each returned row into a content fetch URL using `id_`:

```text
https://web.archive.org/web/{timestamp}id_/{original}
```

Example if a CDX row contains:

```json
["20200101000000", "https://kyledurepos.com/style.css", "text/css", "200", "DIGESTVALUE", "1234"]
```

The recovery download URL must be:

```text
https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/style.css
```

## Additional Useful CDX URLs For kyledurepos.com

Exact homepage captures:

```text
https://web.archive.org/cdx?url=https://kyledurepos.com/&matchType=exact&output=json&fl=timestamp,original,statuscode,mimetype,digest,length
```

Homepage and paths by prefix:

```text
https://web.archive.org/cdx?url=https://kyledurepos.com/&matchType=prefix&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200
```

Domain-wide successful captures:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200
```

Domain-wide unique content:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&collapse=digest
```

Domain-wide unique URLs:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=urlkey,timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&collapse=urlkey
```

HTML only:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&filter=mimetype:text/html
```

Images only:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&filter=mimetype:image/.*
```

Date-bounded captures:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&from=2018&to=2021
```

Paginated captures:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```

Next page with resume key:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true&resumeKey=PASTE_RETURNED_RESUME_KEY_HERE
```

## Recommended Recovery Strategy

1. Query `matchType=domain` with `filter=statuscode:200`, `fl=timestamp,original,mimetype,statuscode,digest,length`, `limit=1000`, and `showResumeKey=true`.
2. Page with `resumeKey` until exhausted.
3. Store all CDX rows locally before downloading content.
4. Deduplicate by `digest` for downloads, while preserving URL-to-digest mappings.
5. For each selected row, fetch `https://web.archive.org/web/{timestamp}id_/{original}`.
6. Map original URLs to safe local paths under a recovery folder.
7. Keep logs of original URL, timestamp, digest, MIME type, status, length, local path, HTTP download status, and final file size.
8. Re-run narrower CDX queries for missing asset classes or specific dates if the recovered site has broken references.
