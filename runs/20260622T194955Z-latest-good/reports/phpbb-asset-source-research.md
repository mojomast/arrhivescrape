# phpBB 2.0.6 Asset Source Research

Run ID: `20260622T194955Z-latest-good`
Site root reviewed: `/home/mojo/projects/archivebackup/recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site`
Inputs reviewed: `tools/fix_forum_images.py`, `runs/20260622T194955Z-latest-good/reports/forum-image-fix-report.md`

## Summary

- Placeholder assets currently created by `tools/fix_forum_images.py`: 50.
- Verified replaceable from phpBB 2.0.6 official package sources: 43.
- Not found in phpBB 2.0.6 official package sources: 7 custom/non-core smilies.
- Site files were not modified for this research.

## Recommended Sources

1. SourceForge phpBB project `OldFiles` full package: `https://sourceforge.net/projects/phpbb/files/OldFiles/phpBB-2.0.6.zip/download`
2. SourceForge browsable directory: `https://sourceforge.net/projects/phpbb/files/OldFiles/`
3. GitHub official phpBB repository tag: `https://github.com/phpbb/phpbb/releases/tag/release-2.0.6`
4. GitHub tag archive API: `https://api.github.com/repos/phpbb/phpbb/zipball/refs/tags/release-2.0.6`

SourceForge is the preferred source because it is the historical phpBB release file mirror and its `phpBB-2.0.6.zip` archive has the expected phpBB 2 distribution layout. The GitHub tag is a strong independent cross-check from the official `phpbb/phpbb` repository, but its archive layout is a repository snapshot rather than the released zip layout.

## Source Archive Details

| Source | Archive Filename | Observed Size | Observed MD5 | Notes |
| --- | --- | ---: | --- | --- |
| SourceForge `OldFiles` | `phpBB-2.0.6.zip` | 679,907 bytes | `c9b37721c2ec214b5acdd3f1c5da79b9` | Downloaded from `OldFiles`; SourceForge listing shows `phpBB-2.0.6.zip`, date `2004-03-01`, displayed size `679.9 kB`. |
| GitHub official tag | `phpbb-release-2.0.6-github.zip` | 3,838,172 bytes | `aece8975e6dc7d08f1cdcac41aa591ff` | GitHub generated zipball for tag `release-2.0.6`, commit `c183ce616d000d5465fb339f8d79ae9d981e234f`. |

## Expected Package Paths

The recovered site uses `BB/` as the phpBB root. The phpBB 2.0.6 SourceForge release archive uses `phpBB2/` as its internal root. Therefore replacements should map as follows:

- Recovered `BB/templates/subSilver/images/...` => SourceForge `phpBB2/templates/subSilver/images/...`
- Recovered `BB/templates/subSilver/images/lang_english/...` => SourceForge `phpBB2/templates/subSilver/images/lang_english/...`
- Recovered `BB/images/smiles/...` => SourceForge `phpBB2/images/smiles/...`

The GitHub tag archive uses a generated root directory and then `phpBB/`, for example `phpbb-phpbb-c183ce6/phpBB/templates/subSilver/images/...`.

## Placeholder Mapping

| Placeholder Path | Recommended Archive | Expected Internal Path | Available |
| --- | --- | --- | --- |
| `BB/images/smiles/emot-crying.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/emot-eng101.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/emot-nws.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/emot-nyd.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/emot-q.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/emot-sax.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/images/smiles/icon_confused.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_confused.gif` | yes |
| `BB/images/smiles/icon_cry.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_cry.gif` | yes |
| `BB/images/smiles/icon_eek.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_eek.gif` | yes |
| `BB/images/smiles/icon_evil.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_evil.gif` | yes |
| `BB/images/smiles/icon_exclaim.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_exclaim.gif` | yes |
| `BB/images/smiles/icon_redface.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_redface.gif` | yes |
| `BB/images/smiles/icon_twisted.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_twisted.gif` | yes |
| `BB/images/smiles/icon_wink.gif` | `phpBB-2.0.6.zip` | `phpBB2/images/smiles/icon_wink.gif` | yes |
| `BB/images/smiles/lol.gif` | none verified | n/a | no - custom/non-core smilie |
| `BB/templates/subSilver/images/cellpic1.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/cellpic1.gif` | yes |
| `BB/templates/subSilver/images/cellpic2.jpg` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/cellpic2.jpg` | yes |
| `BB/templates/subSilver/images/cellpic3.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/cellpic3.gif` | yes |
| `BB/templates/subSilver/images/folder.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder.gif` | yes |
| `BB/templates/subSilver/images/folder_announce.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_announce.gif` | yes |
| `BB/templates/subSilver/images/folder_big.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_big.gif` | yes |
| `BB/templates/subSilver/images/folder_hot.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_hot.gif` | yes |
| `BB/templates/subSilver/images/folder_lock.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_lock.gif` | yes |
| `BB/templates/subSilver/images/folder_lock_new.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_lock_new.gif` | yes |
| `BB/templates/subSilver/images/folder_new.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_new.gif` | yes |
| `BB/templates/subSilver/images/folder_new_hot.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_new_hot.gif` | yes |
| `BB/templates/subSilver/images/folder_sticky.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/folder_sticky.gif` | yes |
| `BB/templates/subSilver/images/icon_latest_reply.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_latest_reply.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_faq.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_faq.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_groups.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_groups.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_login.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_login.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_members.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_members.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_message.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_message.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_profile.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_profile.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_register.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_register.gif` | yes |
| `BB/templates/subSilver/images/icon_mini_search.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_mini_search.gif` | yes |
| `BB/templates/subSilver/images/icon_minipost.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/icon_minipost.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_aim.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_aim.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_email.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_email.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_icq_add.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_icq_add.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_msnm.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_msnm.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_pm.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_pm.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_profile.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_profile.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_quote.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_quote.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_www.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_www.gif` | yes |
| `BB/templates/subSilver/images/lang_english/icon_yim.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/icon_yim.gif` | yes |
| `BB/templates/subSilver/images/lang_english/post.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/post.gif` | yes |
| `BB/templates/subSilver/images/lang_english/reply.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/lang_english/reply.gif` | yes |
| `BB/templates/subSilver/images/logo_phpBB.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/logo_phpBB.gif` | yes |
| `BB/templates/subSilver/images/whosonline.gif` | `phpBB-2.0.6.zip` | `phpBB2/templates/subSilver/images/whosonline.gif` | yes |

## Unavailable In Verified phpBB 2.0.6 Sources

These seven placeholders were not present in either SourceForge `phpBB-2.0.6.zip` or the GitHub `release-2.0.6` tag archive:

- `BB/images/smiles/emot-crying.gif`
- `BB/images/smiles/emot-eng101.gif`
- `BB/images/smiles/emot-nws.gif`
- `BB/images/smiles/emot-nyd.gif`
- `BB/images/smiles/emot-q.gif`
- `BB/images/smiles/emot-sax.gif`
- `BB/images/smiles/lol.gif`

These appear to be site-specific or third-party smilies, not stock phpBB 2.0.6 assets. They should not be replaced from the core phpBB package unless a separate reliable smilie-pack source or original site capture is found.

## Confidence

High for the 43 stock phpBB replacements: they were present in both the SourceForge 2.0.6 release archive and the official GitHub `release-2.0.6` tag snapshot.

Medium-high for the seven unavailable smilies: absence from both verified official sources strongly indicates they are custom/non-core, but they may exist in third-party smilie packs or original site backups.
