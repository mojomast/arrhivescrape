# Hidden/Unlinked Forum Audit

Run ID: `20260622T194955Z-latest-good`

## Finding

This independent audit supports the likely first-audit answer that the recovered forum navigation is incomplete: `/BB/index.html` visibly links only 5 forums, while recovered phpBB forum metadata and jumpboxes list 10 forums. The unlinked/missing forum names are `the DANGERZONE`, `Pr0n`, `Clipsey's House of Debauchery`, `Alcohol`, and `Technology`.

Important qualification: I did not find recovered topic pages whose actual current forum breadcrumb (`rel="up"`) is `Pr0n`/pron. The `Pr0n` references are forum-list/jumpbox metadata repeated across pages, not proof that recovered topic HTML belongs to a recovered `Pr0n` forum. The archive appears to have selected/recovered only forum index pages for `f=1`, `f=6`, `f=9`, `f=10`, and `f=11`.

## Reachability Counts

Local-only crawl rules used: start at `site/BB/index.html`; follow local hrefs only to `BB/*.html` and `BB/**/index.html`; do not leave the filesystem.

- Total `BB` HTML files on disk: 2,481
- Reachable under the local crawl: 208
- Unreachable under the local crawl: 2,273
- Recovered forum index pages visible from `/BB/index.html`: 5
- Forum names listed by phpBB jumpboxes/metadata: 10
- Manifest `source_url` rows under `/BB/`: 2,497
- Manifest HTML-ish `/BB/` rows: 2,484
- Manifest `viewforum.php?f=` rows: 5

## Current `/BB/` Navigation

`site/BB/index.html` contains only these visible forum links:

- `site/BB/index.html:258` links `viewforum__q_3047a972/index.html` as `lollercade`
- `site/BB/index.html:267` links `viewforum__q_a3f54d0a/index.html` as `Games`
- `site/BB/index.html:276` links `viewforum__q_71d676ee/index.html` as `Music`
- `site/BB/index.html:285` links `viewforum__q_a490e64f/index.html` as `Movies/Television/Books`
- `site/BB/index.html:294` links `viewforum__q_99d5528a/index.html` as `Sports`

No visible `forumlink` entry for `Pr0n`, `the DANGERZONE`, `Clipsey's House of Debauchery`, `Alcohol`, or `Technology` was present in `/BB/index.html`.

## Evidence For Unlinked/Missing Forums

Recovered pages repeatedly list additional forums in phpBB jumpboxes. Example:

- `site/BB/viewforum__q_3047a972/index.html:749` contains jumpbox options for `lollercade`, `the DANGERZONE`, `Pr0n`, `Games`, `Music`, `Movies/Television/Books`, `Sports`, `Clipsey's House of Debauchery`, `Alcohol`, and `Technology`.
- `site/BB/viewtopic__q_fff9bba5/index.html:16` contains `<link href="../viewforum/index.html" rel="chapter forum" title="Pr0n"/>`.
- `site/BB/viewtopic__q_fff9bba5/index.html:21-23` likewise lists `Clipsey's House of Debauchery`, `Alcohol`, and `Technology` with the same generic `../viewforum/index.html` target.
- `site/BB/viewforum/index.html:252` says `The forum you selected does not exist.`, which is the local target used by the unlinked chapter-forum entries.

Manifest evidence agrees that only five `viewforum.php?f=` pages were selected/recovered:

- `site.manifest.jsonl:30` source `http://kyledurepos.com:80/BB/viewforum.php?f=1&amp` -> `BB/viewforum__q_3047a972/index.html`
- `site.manifest.jsonl:31` source `http://kyledurepos.com:80/BB/viewforum.php?f=9&amp` -> `BB/viewforum__q_71d676ee/index.html`
- `site.manifest.jsonl:32` source `http://kyledurepos.com:80/BB/viewforum.php?f=11&amp` -> `BB/viewforum__q_99d5528a/index.html`
- `site.manifest.jsonl:33` source `http://kyledurepos.com:80/BB/viewforum.php?f=6&amp` -> `BB/viewforum__q_a3f54d0a/index.html`
- `site.manifest.jsonl:34` source `http://kyledurepos.com:80/BB/viewforum.php?f=10&amp` -> `BB/viewforum__q_a490e64f/index.html`

No selected `site.manifest.jsonl` `viewforum.php?f=` source was found for the jumpbox-listed forum ids `2`, `3`, `7`, `8`, or `12`.

## Topic/File Classification

Using each topic page's `<link rel="up" title="...">` as the best local indication of actual forum membership, recovered topic pages classify only into visible forums:

- `lollercade`: 1,182 files, 86 reachable
- `Games`: 528 files, 40 reachable
- `Movies/Television/Books`: 341 files, 35 reachable
- `Music`: 307 files, 24 reachable
- `Sports`: 89 files, 10 reachable
- Other/no forum marker: 34 files, 13 reachable

No recovered topic page had actual `rel="up" title="Pr0n"`, `the DANGERZONE`, `Clipsey's House of Debauchery`, `Alcohol`, or `Technology`.

## Pattern Search Notes

Search terms requested: `pr0n`, `pron`, `porn`, `private`, `hidden`, `adult`, `nsfw`, `moderator`, `admin`, `forum=`, `viewforum.php?f=`, `viewtopic.php?t=`, `viewtopic.php?p=`.

- `Pr0n` appears frequently in repeated forum-list metadata and jumpboxes, e.g. `site/BB/viewtopic__q_fff9bba5/index.html:16` and `site/BB/viewforum__q_3047a972/index.html:749`.
- `porn` appears in ordinary topic text/title evidence, e.g. `site/BB/viewforum__q_3047a972/index.html:431` topic title `Trapped by pornography? Have no fear!`; this is not evidence of a recovered porn/pr0n forum section.
- `private`, `moderator`, and `admin` are common phpBB UI/user-role strings, e.g. private-message links and `Site Admin`/`Moderator` labels; they did not identify an additional navigable hidden forum page.
- Manifest URL patterns are dominated by `viewtopic.php?p=` and `viewtopic.php?t=` records plus the five visible `viewforum.php?f=` records listed above.

## Conclusion

The recovered `/BB/` navigation is missing/unlinking forum sections that phpBB metadata says existed, especially `Pr0n` (`f=3`) and four other forums (`f=2`, `f=7`, `f=8`, `f=12`). However, the recovered HTML on disk does not contain actual `Pr0n` forum index/topic pages under the tested membership signal; it contains references to those forums without corresponding recovered `viewforum.php?f=` outputs.
