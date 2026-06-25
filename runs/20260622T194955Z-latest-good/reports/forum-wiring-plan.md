# Forum Wiring Plan

Run ID: `20260622T194955Z-latest-good`

Site root: `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site`

No site files were modified. This plan is based on a local crawl from `BB/index.html`, promoted `/BB/**/*.html` files on disk, and `site.manifest.jsonl` / `inventory.canonical.jsonl` metadata.

## Executive Decision

Wire the 2,273 promoted but unreachable `/BB` HTML pages through a new recovered archive section at `BB/archive-index/`, not by fabricating missing forum pages or synthetic topic content. The archive index should link only to already-promoted static HTML files and should label uncertain membership as `Unknown/Recovered orphan pages`.

The only recovered `viewforum.php?f=` forum index pages backed by manifest URLs are the five already-visible forums: `lollercade`, `Games`, `Music`, `Movies/Television/Books`, and `Sports`. Jumpbox references to `the DANGERZONE`, `Pr0n`, `Clipsey's House of Debauchery`, `Alcohol`, and `Technology` should not become invented forum landing pages unless future recovery finds corresponding captures.

## Reachability

| Set | Count |
| --- | ---: |
| Promoted `/BB/**/*.html` files on disk | 2,481 |
| Reachable by local crawl from `BB/index.html` | 208 |
| Unreachable promoted `/BB` HTML files | 2,273 |

Crawl rule: start at `BB/index.html`; parse local `a[href]`, `link[href]`, and `form[action]`; resolve only same-site/local `/BB` targets that exist as HTML files under the recovered site root.

## Unreachable Classification

| Class | Count |
| --- | ---: |
| viewtopic query page | 2,263 |
| viewforum query page | 0 |
| posting dynamic/query page | 3 |
| profile dynamic/query page | 3 |
| search dynamic/query page | 2 |
| login dynamic/query page | 1 |
| memberlist dynamic/query page | 0 |
| groupcp dynamic/query page | 0 |
| privmsg dynamic/query page | 0 |
| admin-ish dynamic/query page | 0 |
| generic alias/error page | 1 |
| asset misclassified as HTML | 0 |

| Route family | Count |
| --- | ---: |
| `viewtopic` | 2,264 |
| `viewforum` | 0 |
| `posting` | 3 |
| `profile` | 3 |
| `search` | 2 |
| `login` | 1 |
| `memberlist` | 0 |
| `groupcp` | 0 |
| `privmsg` | 0 |
| `admin` | 0 |

Asset misclassification check: `0` non-HTML assets were found in the unreachable HTML set. No promoted `viewforum` query pages are unreachable; the recovered URL-backed forum indexes are already in the reachable set from `BB/index.html`.

## Forum Grouping For Topic Pages

Topic grouping should use recovered page evidence in this order: visible phpBB breadcrumb links (`a.nav`), `<link rel="up/chapter/forum" title="...">`, selected jumpbox forum, then `Unknown/Recovered orphan pages`. Do not use repeated jumpbox option lists alone as membership evidence.

| Inferred forum/group | Unreachable pages |
| --- | ---: |
| lollercade | 1,096 |
| Games | 488 |
| Movies/Television/Books | 306 |
| Music | 283 |
| Sports | 79 |
| Unknown/Recovered orphan pages | 21 |

## Date Grouping

Date grouping is extractable from visible phpBB post/date strings on many pages. The archive should provide a date facet by year where a year can be parsed, with an `Unknown date` bucket for pages without reliable visible dates.

| Year/date bucket | Unreachable pages |
| --- | ---: |
| 2004 | 2,186 |
| 2005 | 67 |
| Unknown date | 20 |

## Required Metadata Extraction

For each indexed page, extract and store these fields in the generated archive listing data:

- `path`: local site-relative path, e.g. `BB/viewtopic__q_0019df6c/index.html`.
- `page_type`: route/class such as `viewtopic query page`, `viewforum query page`, `profile dynamic/query page`, or `generic alias/error page`.
- `page_title`: `a.maintitle` text first, falling back to `<title>` with `PWNED ::` removed.
- `forum_label`: breadcrumb/`rel=up`/selected-forum label, or `Unknown/Recovered orphan pages`.
- `topic_title`: same as `page_title` for `viewtopic` pages; blank for non-topic pages unless a topic title is visibly present.
- `post_anchors`: numeric `a[name]`/element IDs present on the page, used for post-level deep links.
- `source_original_url`: from `site.manifest.jsonl` `source_url`, falling back to inventory URL fields if needed.
- `source_timestamp`: from `site.manifest.jsonl` `timestamp`, falling back to inventory alias timestamp if needed.

Metadata mapping caveat: `0` unreachable files did not have a direct source row by `output_path`/normalized inventory hint during this pass.

## Archive Section Specification

Create these pages under `BB/archive-index/`:

- `index.html`: overview, counts, caveat that entries are recovered static pages, and links to forum/type/date indexes.
- `forums/index.html`: groups pages by inferred forum label, including `Unknown/Recovered orphan pages`.
- `forums/<slug>/index.html`: one listing per inferred forum/group; topic pages first, then forum pages, then dynamic/other pages.
- `types/index.html`: groups pages by page type/route (`viewtopic`, `viewforum`, `profile`, `login`, `search`, etc.).
- `types/<route>/index.html`: one listing per route family.
- `dates/index.html`: groups by parsed year/date bucket.
- `dates/<year>/index.html` and `dates/unknown/index.html`: date-bucket listings.

Each listing row should include title, forum/group, page type, first visible date if any, source timestamp, source original URL, local link, and first few post anchors for topic pages. Listing pages should be static HTML generated from recovered files only.

## Link Placement

- Add one visible link from `BB/index.html` near the main forum table/top navigation to `archive-index/index.html` with text like `Recovered forum archive index` and a short note that it lists recovered pages not linked by the original forum navigation.
- Add a backlink block to every currently unreachable promoted HTML page: `Recovered archive: Archive index | Forum/group listing | Page-type listing | Date listing`.
- For pages with inferred forum labels matching a recovered visible forum, include a `Nearest recovered forum` link to the existing `viewforum__q_.../index.html` forum index where available.
- For topic pages, add the forum/group backlink based on the inferred label, not on repeated jumpbox options.
- For `Unknown/Recovered orphan pages`, link only to the archive index, Unknown forum/group listing, page-type listing, and date/unknown bucket.
- Do not add links to non-recovered forum IDs `2`, `3`, `7`, `8`, or `12` as if they were recovered forum pages.

## Existing Tool Fit

`tools/fix_forum_navigation.py` already indexes forum/topic titles and repairs collapsed generic phpBB links where title/anchor evidence is enough. The archive-index work should be implemented as a separate generator or a new mode, because it creates discovery pages and backlinks rather than repairing generic `viewtopic`/`viewforum` hrefs in place.

Recommended implementation shape:

- Reuse the script's `norm_text`, `route_name`, `page_title`, post-anchor extraction, and relative-link helpers.
- Add a dry-run default that reports counts before writing.
- Generate archive pages from parsed metadata in memory.
- When backlinks are enabled, insert a small phpBB-styled table/block after the opening body/main forum container, preserving original content below it.
- Keep all generated text explicit that this is a recovered archive navigation layer.

## Samples By Class

### generic alias/error page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic/index.html |  | Unknown/Recovered orphan pages | 20040903202452 | http://kyledurepos.com:80/BB/viewtopic.php |  |

### login dynamic/query page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/login__q_644adadf/index.html | Log in | Unknown/Recovered orphan pages | 20050321203821 | http://www.kyledurepos.com:80/BB/login.php?sid=96dae49138432887261f64cd58556454 |  |

### posting dynamic/query page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/posting__q_10e01dd0/index.html |  | Unknown/Recovered orphan pages | 20040616220826 | http://kyledurepos.com:80/BB/posting.php?mode=quote&amp;amp |  |
| BB/posting__q_154487fd/index.html |  | Unknown/Recovered orphan pages | 20040616221038 | http://kyledurepos.com:80/BB/posting.php?mode=reply&amp;amp |  |
| BB/posting__q_5719dd89/index.html |  | Unknown/Recovered orphan pages | 20040616220743 | http://kyledurepos.com:80/BB/posting.php?mode=newtopic&amp;amp |  |

### profile dynamic/query page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/profile__q_cb9c23f4/index.html |  | Unknown/Recovered orphan pages | 20040228212518 | http://kyledurepos.com:80/BB/profile.php?mode=sendpassword&amp;amp |  |
| BB/profile__q_d333bbfe/index.html |  | Unknown/Recovered orphan pages | 20040406185521 | http://kyledurepos.com:80/BB/profile.php?mode=email&amp;amp |  |
| BB/profile__q_d9a2c922/index.html |  | Unknown/Recovered orphan pages | 20040616163532 | http://kyledurepos.com:80/BB/profile.php?mode=viewprofile&amp;amp |  |

### search dynamic/query page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/search__q_3e07e477/index.html | Search | Unknown/Recovered orphan pages | 20040616163804 | http://kyledurepos.com:80/BB/search.php?search_id=unanswered&amp;amp |  |
| BB/search__q_644adadf/index.html | Search | Unknown/Recovered orphan pages | 20050321204021 | http://www.kyledurepos.com:80/BB/search.php?sid=96dae49138432887261f64cd58556454 |  |

### viewtopic query page

| Path | Title | Forum/group | Source timestamp | Source URL | Anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_0019df6c/index.html | DEAR DANGER FAGGOTS | lollercade | 20041228191347 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=4937&amp;amp | 4934, 4936, 4937, 4938, 4939 |
| BB/viewtopic__q_00cb1272/index.html | Actually BUYING music?! | Music | 20041222105151 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=3230&amp;amp | 2922, 2936, 2939, 2946, 2947 |
| BB/viewtopic__q_00fccda3/index.html |  | Unknown/Recovered orphan pages | 20040530014827 | http://kyledurepos.com:80/BB/viewtopic.php?p=931&amp;amp |  |
| BB/viewtopic__q_0179b920/index.html | NCAA 05 | Games | 20041212041235 | http://www.kyledurepos.com:80/BB/viewtopic.php?t=365&amp;amp | 4713, 4714, 4716, 4719, 4720 |
| BB/viewtopic__q_01a7a413/index.html | new recommendations | Music | 20041217212952 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=4582&amp;amp | 4514, 4555, 4558, 4569, 4582 |
| BB/viewtopic__q_01d2520f/index.html | American Dad | Movies/Television/Books | 20050321184803 | http://www.kyledurepos.com:80/BB/viewtopic.php?t=383&amp;amp | 4820 |
| BB/viewtopic__q_03172d2e/index.html | Post Your Favorite lyrics | Music | 20050213175254 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=2803&amp;amp | 2803, 3320, 3338, 3339, 3509 |
| BB/viewtopic__q_0331903f/index.html | Sports forum? | lollercade | 20040509024112 | http://kyledurepos.com:80/BB/viewtopic.php?p=1302&amp;amp | 1299, 1302, 1303, 1307, 1309 |

## Topic Samples By Inferred Forum

### Games

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_0179b920/index.html | NCAA 05 | Jul 14, 2004, Jul 14, 2004 | 20041212041235 | http://www.kyledurepos.com:80/BB/viewtopic.php?t=365&amp;amp | 4713, 4714, 4716, 4719, 4720, 4721 |
| BB/viewtopic__q_05861a93/index.html | Metal Gear Soild 3: Snake Eater | Nov 30, 2004, Nov 30, 2004 | 20050215080633 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5274&amp;amp | 5271, 5273, 5274, 5275, 5276, 5300, 5315 |
| BB/viewtopic__q_05872c8c/index.html | Battlefield Vietnam | Mar 17, 2004, Mar 17, 2004 | 20040602053539 | http://kyledurepos.com:80/BB/viewtopic.php?p=1970&amp;amp | 1741, 1743, 1748, 1766, 1957, 1959, 1961, 1970 |
| BB/viewtopic__q_07d1a3bc/index.html | Gaming Nights? | Feb 26, 2004, Feb 26, 2004 | 20040308035724 | http://kyledurepos.com:80/BB/viewtopic.php?p=105&amp;amp | 76, 80, 81, 84, 87, 88, 92, 105 |
| BB/viewtopic__q_093838d9/index.html | Halo 2 (sticky?) | Apr 11, 2004, Apr 11, 2004 | 20050216144859 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=3351&amp;amp | 3248, 3249, 3254, 3350, 3351, 3352, 3353, 3364 |

### Movies/Television/Books

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_01d2520f/index.html | American Dad | Aug 03, 2004 | 20050321184803 | http://www.kyledurepos.com:80/BB/viewtopic.php?t=383&amp;amp | 4820 |
| BB/viewtopic__q_05044c97/index.html | Chronicles of Riddick | May 07, 2004, May 07, 2004 | 20040625080143 | http://kyledurepos.com:80/BB/viewtopic.php?p=3984&amp;amp | 3982, 3983, 3984, 4011, 4020, 4030, 4034, 4035 |
| BB/viewtopic__q_051b91de/index.html | Saved! | Jun 18, 2004, Jun 18, 2004 | 20050209133021 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=4580&amp;amp | 4577, 4578, 4579, 4580 |
| BB/viewtopic__q_0548f102/index.html | Aliens versus Predator | Apr 07, 2004, Apr 07, 2004 | 20040625080317 | http://kyledurepos.com:80/BB/viewtopic.php?p=2870&amp;amp | 2870, 2892, 2894, 2906, 3026, 3035 |
| BB/viewtopic__q_058d6a8f/index.html | Chronicles of Riddick | May 07, 2004, May 07, 2004 | 20040616220104 | http://kyledurepos.com:80/BB/viewtopic.php?t=278&amp;amp | 3982, 3983, 3984, 4011, 4020, 4030, 4034, 4035 |

### Music

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_00cb1272/index.html | Actually BUYING music?! | Apr 07, 2004, Apr 08, 2004 | 20041222105151 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=3230&amp;amp | 2922, 2936, 2939, 2946, 2947, 2959, 2970, 2980 |
| BB/viewtopic__q_01a7a413/index.html | new recommendations | Jun 11, 2004, Jun 14, 2004 | 20041217212952 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=4582&amp;amp | 4514, 4555, 4558, 4569, 4582, 4585, 4586, 4588 |
| BB/viewtopic__q_03172d2e/index.html | Post Your Favorite lyrics | Apr 06, 2004, Apr 13, 2004 | 20050213175254 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=2803&amp;amp | 2803, 3320, 3338, 3339, 3509, 3515, 3520, 3527 |
| BB/viewtopic__q_06048a66/index.html | My new toy.... | Apr 19, 2004, Apr 19, 2004 | 20050218165328 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=3490&amp;amp | 3481, 3483, 3490, 3491, 3492, 3495, 3497, 3499 |
| BB/viewtopic__q_07f81fc6/index.html | . | Feb 26, 2004, Feb 26, 2004 | 20040228170244 | http://kyledurepos.com:80/BB/viewtopic.php?p=203&amp;amp | 174, 202, 203 |

### Sports

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_0914b40f/index.html | I am watching the superbowl | Feb 07, 2005, Feb 07, 2005 | 20050215075843 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5430&amp;amp | 5429, 5430, 5431, 5432, 5433, 5434, 5435, 5436 |
| BB/viewtopic__q_0ede4553/index.html | screw it im blogging about the superbowl | Feb 05, 2005, Feb 05, 2005 | 20050215075924 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5422&amp;amp | 5422, 5423, 5426 |
| BB/viewtopic__q_11958ad4/index.html | I am watching the superbowl | Feb 07, 2005, Feb 07, 2005 | 20050215080142 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5429&amp;amp | 5429, 5430, 5431, 5432, 5433, 5434, 5435, 5436 |
| BB/viewtopic__q_11a30de8/index.html | my nba playoff diary | May 11, 2004, May 11, 2004 | 20040625081818 | http://kyledurepos.com:80/BB/viewtopic.php?p=4201&amp;amp | 4047, 4053, 4055, 4056, 4057, 4058, 4093, 4094 |
| BB/viewtopic__q_221153fa/index.html | screw it im blogging about the superbowl | Feb 05, 2005, Feb 05, 2005 | 20050209135330 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5426&amp;amp | 5422, 5423, 5426 |

### Unknown/Recovered orphan pages

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_00fccda3/index.html |  |  | 20040530014827 | http://kyledurepos.com:80/BB/viewtopic.php?p=931&amp;amp |  |
| BB/viewtopic__q_071d5bab/index.html |  |  | 20040530185038 | http://kyledurepos.com:80/BB/viewtopic.php?p=444&amp;amp |  |
| BB/viewtopic__q_293f7cf2/index.html |  |  | 20040530173416 | http://kyledurepos.com:80/BB/viewtopic.php?p=286&amp;amp |  |
| BB/viewtopic__q_2b4728c1/index.html |  |  | 20040530014346 | http://kyledurepos.com:80/BB/viewtopic.php?p=924&amp;amp |  |
| BB/viewtopic__q_32ae848c/index.html |  |  | 20040530172943 | http://kyledurepos.com:80/BB/viewtopic.php?p=283&amp;amp |  |

### lollercade

| Path | Topic title | Dates | Source timestamp | Source URL | Post anchors |
| --- | --- | --- | --- | --- | --- |
| BB/viewtopic__q_0019df6c/index.html | DEAR DANGER FAGGOTS | Aug 28, 2004, Aug 28, 2004 | 20041228191347 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=4937&amp;amp | 4934, 4936, 4937, 4938, 4939, 4941, 4943, 4944 |
| BB/viewtopic__q_0331903f/index.html | Sports forum? | Mar 11, 2004, Mar 11, 2004 | 20040509024112 | http://kyledurepos.com:80/BB/viewtopic.php?p=1302&amp;amp | 1299, 1302, 1303, 1307, 1309, 1312, 1317 |
| BB/viewtopic__q_03bde879/index.html | question | Sep 28, 2004, Sep 28, 2004 | 20050209134733 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5127&amp;amp | 5122, 5123, 5124, 5127 |
| BB/viewtopic__q_03f84266/index.html | POST PICTURES OF YOURSELF! | Mar 25, 2004, Mar 25, 2004 | 20040506133013 | http://kyledurepos.com:80/BB/viewtopic.php?p=2645&amp;amp | 2061, 2065, 2067, 2084, 2096, 2103, 2117, 2134 |
| BB/viewtopic__q_05840335/index.html | forums dot something awful dot com | Sep 10, 2004, Sep 10, 2004 | 20050214200601 | http://www.kyledurepos.com:80/BB/viewtopic.php?p=5064&amp;amp | 5050, 5051, 5052, 5053, 5056, 5058, 5064, 5065 |

## Viewforum Query Samples

| Path | Title | Forum/group | Source timestamp | Source URL |
| --- | --- | --- | --- | --- |

## Caveats

- The archive index should improve discoverability of recovered pages, not claim original phpBB navigation relationships that are not evidenced in recovered HTML or manifests.
- `Pr0n` and other jumpbox-only forum names should be mentioned as historical labels seen in recovered markup, but not treated as recovered forums.
- Repeated `rel="chapter forum"` labels can be stale or generic; use `rel="up"`, visible breadcrumbs, selected jumpbox state, and URL-backed forum indexes preferentially.
- Date extraction from rendered text is useful for grouping but not authoritative capture time; keep `source_timestamp` separate from visible post dates.
