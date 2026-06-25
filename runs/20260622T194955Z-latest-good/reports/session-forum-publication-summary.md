# Forum Publication And Enhancement Summary

Run ID: `20260622T194955Z-latest-good`  
Updated: `2026-06-25T21:57:40Z`

## Current Access URLs

- Tailnet full recovered site: `http://100.72.41.9:18081/`
- Tailnet capture browser: `http://100.72.41.9:18081/captures/`
- Tailnet forum: `http://100.72.41.9:18081/BB/`
- Tailnet forum archive index: `http://100.72.41.9:18081/BB/archive-index/`
- Public forum: `https://ussy.host/archives/websites/pwnedforums/`
- Public forum archive index: `https://ussy.host/archives/websites/pwnedforums/archive-index/`

## Capture Browser

- Added static capture browser at `/captures/`.
- Later changed the browser to lazy-load data instead of loading all captures at once.
- Initial JSON index: `captures-index.json`, about 260 KB.
- Capture shards: 432 JSON files under `/captures/shards/`.
- Capture rows represented: 30,080.
- URL/path groups represented: 432.

## Forum Navigation

- Repaired phpBB links where recovered static query pages existed.
- Added deterministic archive wiring with `tools/wire_forum_archive.py`.
- Generated `BB/archive-index/` and 13 index pages.
- Added archive/backlink navigation to 2,273 previously unreachable `/BB` pages.
- Total promoted `/BB` HTML pages audited: 2,481.

## Forum Coverage Findings

- Recovered `viewforum.php?f=` pages exist for five forums: lollercade, Games, Music, Movies/Television/Books, and Sports.
- Metadata/jumpboxes mention additional forums including `Pr0n`, `the DANGERZONE`, `Clipsey's House of Debauchery`, `Alcohol`, and `Technology`.
- No recovered dedicated `Pr0n` forum landing page or topic membership was found in the selected/promoted captures.

## Forum UI Assets

- Initial best-effort pass relinked 248,623 forum image references and created placeholders for missing phpBB chrome/smilies.
- Real phpBB 2.0.6 subSilver assets were then restored from official `phpbb/phpbb` tag `release-2.0.6`.
- Replaced stock phpBB assets: 43.
- Remaining placeholder assets: 7 custom/non-stock smilies not present in phpBB 2.0.6.

## Public Publication

- Published only the forum subtree to `https://ussy.host/archives/websites/pwnedforums/`.
- Implemented by copying to `/home/mojo/web/out/archives/websites/pwnedforums` using `tools/publish_pwnedforums.py`.
- Existing nginx configuration was not changed.
- Published files: 2,558.
- Published HTML files: 2,494.
- Public HTML includes `noindex,nofollow` meta tags.
- First-party forum links were rewritten from `/BB/` or `http(s)://kyledurepos.com/BB/` to `/archives/websites/pwnedforums/`.
- Verified public index, archive index, topic page, assets, and missing-path 404.

## Media Recovery

- First-party avatar/upload/post image audit found 3,565 missing first-party image refs across 47 unique assets.
- Exact Wayback recovery attempted for the top 80 first-party assets and recovered 0 usable images.
- External image audit found 22,393 external image refs across 250 unique URLs and 69 hosts.
- Exact Wayback recovery attempted for the top 50 external image URLs and recovered 8 real archived images.
- Recovered external images are stored under `BB/recovered-external/` and were republished publicly.
- HTML files rewritten for recovered external media: 1,446.

## Key Reports

- `forum-coverage-audit.md`
- `forum-hidden-audit.md`
- `forum-wiring-plan.md`
- `forum-image-audit.md`
- `forum-image-fix-report.md`
- `phpbb-asset-source-research.md`
- `phpbb-asset-replacement-report.md`
- `pwnedforums-public-publish.md`
- `forum-missing-media-audit.md`
- `forum-media-recovery-report.md`
- `forum-external-media-recovery-report.md`

## Remaining Limitations

- Login, posting, private messages, profile edits, and other dynamic phpBB actions remain non-functional static archive pages.
- Some forum sections are visible only in metadata/jumpboxes and have no recovered landing pages.
- Most first-party avatars/uploads/post images were not recoverable through exact Wayback queries.
- Seven custom smiley assets remain placeholders because they were not part of stock phpBB 2.0.6.
