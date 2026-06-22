# Privacy & Legal Review

Run ID: `20260622T194955Z-latest-good`  
Stage: `privacy`  
Reviewed: `2026-06-22T21:25:53Z`  
Staged site: `runs/20260622T194955Z-latest-good/staging/normalized-site/`

## Publication Status

Recommendation: `approved-private-only`

Public promotion is not recommended without remediation. Private tailnet/internal publication is acceptable for archival QA because no live API key, client secret, access token, or hard-coded credential pattern was detected, but the staged site contains personal data and active-publication risks.

## Severity Summary

| Severity | Finding Groups |
| --- | ---: |
| Critical | 0 |
| High | 3 |
| Medium | 5 |
| Low | 2 |
| Info | 2 |

## Scan Summary

| Item | Count |
| --- | ---: |
| Site manifest entries | 2941 |
| Text-like files scanned | 2721 |
| Email occurrences | 765 |
| Unique email values | 164 |
| Candidate phone occurrences | 99 |
| Candidate street-address occurrences | 138 |
| `sid=` occurrences | 232682 |
| Unique `sid` values | 2516 |
| Sensitive query occurrences | 232692 |
| Form tags | 5075 |
| Archived dynamic form actions | 5035 |
| Absolute live form actions | 1 |
| Password inputs | 14 |
| Tracker occurrences | 20 |
| API key/secret/token candidates | 0 |

## Findings

### High

1. Archived forum/session IDs are present at large scale.

Evidence: 232682 `sid=` occurrences across 2489 files, with 2516 unique values. Examples include `BB__q_eaee3ce6/index.html`, `BB/viewtopic__q_fff9bba5/index.html`, and `dgclan/modules__q_f466c53c/index.html`.

Recommendation: do not promote publicly until session/query-bearing dynamic URLs are removed, canonicalized, or served in a non-interactive static mode.

2. Street-address-like personal data appears in forum content.

Evidence: repeated address lines in `BB/viewtopic__q_eb12253a/index.html` and duplicate captures, including `1744 Carmel Drive #308`, `356 El Pico Dr`, `2445 Montgomery RD APT 325`, and `11354 Deer Ridge Lane`.

Recommendation: owner review is required before any public publication. Private-only serving is acceptable for review.

3. Archived login/password forms are present.

Evidence: 14 password inputs across 13 files, including `squirrelmail/src/login/index.html`, `dgclan/modules__q_fd6d611c/index.html`, and phpBB login pages.

Recommendation: disable or neutralize forms before public promotion.

### Medium

1. Email addresses are exposed.

Evidence: 765 occurrences, 164 unique values, across 133 files. Examples include `kyledurepos@kyledurepos.com`, `steenoob@kyledurepos.com`, `dragonedge@kyledurepos.com`, `vitisvinifera@sbcglobal.net`, and `makewine@gmail.com`.

Recommendation: obtain owner approval or redact before public promotion.

2. Archived dynamic form actions are widespread.

Evidence: 5035 form tags target PHP/CGI/comment/forum/login-style paths. One absolute live form action points to `http://hellslayer.kyledurepos.com/podcast/`.

Recommendation: serve privately only unless forms are disabled or rewritten to inert local static endpoints.

3. Third-party tracker scripts, iframes, and pixels are present.

Evidence: 20 tracker occurrences across 4 files, including Tumblr analytics, Quantcast, comScore/ScorecardResearch, and Google Analytics code.

Recommendation: strip or neutralize trackers before public promotion.

4. Live external scripts/media remain in archived pages.

Evidence: many pages contain `http://` script, iframe, and image references to Tumblr, Google APIs, external webcam hosts, spam hosts, and old first-party hosts.

Recommendation: avoid public promotion until live external dependencies are statically captured, blocked, or legally reviewed.

5. Spam/pharma/casino comment content is present.

Evidence: forum and blog/comment archives include bulk external spam links and adult/pharma/casino content.

Recommendation: owner/legal review before public publication.

### Low / Informational

1. Candidate phone numbers were detected, but sampled matches were mostly Tumblr post IDs or spam artifacts.

Evidence: 99 candidate occurrences across 33 files.

Recommendation: sample further if public publication is reconsidered.

2. No API key, access token, client secret, or hard-coded credential pattern was detected.

Evidence: secret-pattern scan returned zero matches.

3. Archived JavaScript creates publication risk if served actively.

Recommendation: sandbox, strip, or review scripts before public promotion.

4. Adult/sensitive media paths exist.

Evidence: paths such as `images/pron/`, `images/muff/`, and `images/lemonparty.JPG`.

Recommendation: owner approval and context review before public promotion.

## Promotion Recommendation

Private-only promotion: approved.

Public promotion: not approved in current form. Required remediation includes owner review of personal addresses/emails, disabling forms/login/comment endpoints, removing or neutralizing trackers, and resolving live external script/media references.

## Blockers

No blocker for private-only archival review.

Public promotion blockers: personal address exposure, archived session IDs/sensitive query parameters, login/password forms, live/dynamic forms, trackers, and live external scripts/media.

approved-private-only
