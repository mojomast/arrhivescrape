# Forum Coverage Audit

Run ID: `20260622T194955Z-latest-good`

Served site root audited: `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site`

No network fetches were used. The audit parsed the four requested manifests and crawled local `/BB` HTML links from `BB/index.html`.

## Summary

The recovered static site contains substantial phpBB content, but the current local navigation reaches only a small subset of the promoted `/BB` pages.

There is no URL-level evidence of a dedicated `Pr0n` forum capture such as `viewforum.php?f=3` in CDX inventory, selected captures, or promoted site metadata. However, the local promoted HTML repeatedly contains `Pr0n` in phpBB jumpboxes as forum ID `3`, and many promoted topic pages contain a `rel="chapter forum" title="Pr0n"` marker. That marker appears inconsistent with URL metadata and selected forum dropdowns, because URL-derived recovered forums are only `f=1`, `f=6`, `f=9`, `f=10`, and `f=11`.

## Counts

| Set | Forum IDs from URLs | Topic `t=` IDs | Post `p=` IDs | BB HTML / topic page count |
| --- | ---: | ---: | ---: | ---: |
| CDX inventory raw | 5 | 232 | 2,229 | 3,725 unique `/BB` HTML URLs |
| Canonical inventory | 5 | 232 | 2,229 | 25,590 forum-like rows |
| Selected captures | 5 | 232 | 2,229 | 2,487 unique `/BB` HTML URLs |
| Promoted site manifest | 5 | 232 | 2,226 | 2,481 promoted `/BB` HTML pages, 2,460 topic pages |
| Reachable from `BB/index.html` | 5 | 31 | 165 | 208 `/BB` HTML pages, 196 topic pages |

URL-derived forum IDs in inventory, selected captures, promoted metadata, and reachable metadata are all the same: `1`, `6`, `9`, `10`, `11`.

Local HTML jumpboxes expose additional forum labels not present as promoted URL captures: `1` lollercade, `2` the DANGERZONE, `3` Pr0n, `4` #FREEDOOM, `6` Games, `7` Clipsey's House of Debauchery, `8` Alcohol, `9` Music, `10` Movies/Television/Books, `11` Sports, `12` Technology, `13` Moderators. From the `BB/index.html` crawl, all except `13` were encountered in reachable pages as jumpbox labels, but only `1`, `6`, `9`, `10`, and `11` were selected current-forum values.

## Pr0n / Pron Evidence

| Location | Result |
| --- | --- |
| CDX inventory URL metadata | No `viewforum.php?f=3` URLs found. No URL-derived forum ID `3`. Keyword-like metadata hits exist, but not as a recoverable `f=3` forum page. |
| Selected captures | No selected `viewforum.php?f=3` URL. Selected URL forum IDs are `1`, `6`, `9`, `10`, `11`. |
| Promoted site manifest | No promoted `viewforum.php?f=3` URL. Promoted URL forum IDs are `1`, `6`, `9`, `10`, `11`. |
| Promoted local HTML | `Pr0n` appears in phpBB jumpboxes as forum ID `3`. 2,448 topic pages have `Pr0n` as selected/breadcrumb/chapter-style evidence, but this appears likely over-applied or stale because their URL metadata does not include `f=3`. |
| Reachable navigation | `Pr0n` appears as a jumpbox option on reachable pages. 196 reachable topic pages have the same `Pr0n` chapter/breadcrumb-style evidence. No reachable dedicated `Pr0n` forum landing page was found. |

Examples of local `Pr0n` evidence:

- `BB/viewforum__q_3047a972/index.html` contains jumpbox option `value="3">Pr0n`.
- `BB/viewtopic__q_fff9bba5/index.html` contains `<link href="../viewforum/index.html" rel="chapter forum" title="Pr0n"/>`.
- `BB/viewtopic__q_fff46dc4/index.html` contains the same `Pr0n` chapter marker while its jumpbox selected forum is `lollercade` (`f=1`).
- `BB/viewforum__q_3047a972/index.html` includes topic title `Trapped by pornography? Have no fear!`, which is a `pornography` keyword hit but not proof of a dedicated `Pr0n` forum capture.

No separate `pron` forum spelling was identified. `private` hits in local HTML are ordinary phpBB private-message navigation strings, not evidence of hidden/private forum recovery.

## Coverage Gaps

Promoted pages unreachable from `BB/index.html`: 2,273 of 2,481 promoted `/BB` HTML pages.

Examples of promoted but unreachable pages:

- `BB/login__q_644adadf/index.html`
- `BB/posting__q_10e01dd0/index.html`
- `BB/profile__q_cb9c23f4/index.html`
- `BB/search__q_3e07e477/index.html`
- `BB/viewtopic/index.html`
- `BB/viewtopic__q_0019df6c/index.html`
- `BB/viewtopic__q_00cb1272/index.html`
- `BB/viewtopic__q_00fccda3/index.html`
- `BB/viewtopic__q_0179b920/index.html`
- `BB/viewtopic__q_01a7a413/index.html`

Selected `/BB` HTML URLs not promoted locally: 6.

Examples:

- `http://kyledurepos.com/BB/?c=1&`
- `http://kyledurepos.com/BB/?mark=forums&`
- `http://kyledurepos.com/BB/?sid=96dae49138432887261f64cd58556454`
- `http://kyledurepos.com/BB/faq.php?sid=96dae49138432887261f64cd58556454`
- `http://kyledurepos.com/BB/groupcp.php?sid=96dae49138432887261f64cd58556454`
- `http://kyledurepos.com/BB/memberlist.php?sid=96dae49138432887261f64cd58556454`

CDX raw `/BB` HTML URL strings not represented as promoted local normalized URLs: 2,199. Many are aliases, `www` host variants, or unselected captures. Examples:

- `http://kyledurepos.com/BB/index.php`
- `http://kyledurepos.com/BB/index.php?c=1&`
- `http://kyledurepos.com/BB/index.php?mark=forums&`
- `http://www.kyledurepos.com/BB/viewforum.php?f=1&`
- `http://www.kyledurepos.com/BB/viewforum.php?f=6&`
- `http://www.kyledurepos.com/BB/viewforum.php?f=9&`
- `http://www.kyledurepos.com/BB/viewforum.php?f=10&`
- `http://www.kyledurepos.com/BB/viewforum.php?f=11&`
- `http://www.kyledurepos.com/BB/viewtopic.php?p=1001&`
- `http://www.kyledurepos.com/BB/viewtopic.php?p=1003&`

## Conclusion

The current static representation does not appear to be missing a recoverable `viewforum.php?f=3` Pr0n forum page from CDX or selection, because no such URL was present in the parsed inventory or promoted metadata. The site does contain `Pr0n` labels and topic-page chapter markers locally, but those labels are not backed by URL-level `f=3` captures and may be a navigation/title repair artifact.

The larger confirmed problem is reachability: most promoted forum pages are present on disk but not reachable by crawling local links from `BB/index.html`.
