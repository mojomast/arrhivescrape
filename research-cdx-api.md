# CDX API Research

Use the Wayback CDX API for inventory and capture metadata. The pipeline should prefer explicit field lists, `output=json`, `filter=statuscode:200`, `collapse=digest` for primary discovery, `showResumeKey=true` for pagination, and a supplemental alias inventory when URL history matters.

Content downloads should use Wayback `id_` replay URLs so archived bytes are fetched with fewer replay rewrites. CDX requests must be sequential by default and should honor `429` responses and `Retry-After` headers.

Example primary query shape:

```text
https://web.archive.org/cdx/search/cdx?url={target_domain}&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```
