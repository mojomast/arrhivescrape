# Forum Image Audit

Run ID: `20260622T194955Z-latest-good`
Scope: `/BB/**/*.html` plus inline CSS `url()` / `background` references. No site files were mutated.

## Summary

| Metric | Count |
| --- | ---: |
| HTML files parsed | 2494 |
| Image/CSS URL references found | 275939 |
| Unique image/CSS URL references found | 391 |
| Missing local or first-party references | 246829 |
| Unique missing local or first-party references | 111 |

## Counts By Class

| Class | Total refs | Missing local/first-party refs | Unique missing refs |
| --- | ---: | ---: | ---: |
| forum UI chrome | 231984 | 231984 | 33 |
| smilies/emoticons | 3195 | 3195 | 24 |
| avatars/uploads | 8775 | 3212 | 24 |
| post content images | 9709 | 8438 | 30 |
| external/third-party | 22276 | 0 | 0 |

## Counts By Scope And Extractor

| Scope | Count |
| --- | ---: |
| first-party | 239403 |
| local | 14260 |
| third-party | 22276 |

| Extractor | Count |
| --- | ---: |
| css-background | 7443 |
| img | 268496 |

## Top Missing Forum UI Chrome Assets

| Refs | Missing URL | Promoted same-basename candidates | Inventory evidence | Recommendation |
| ---: | --- | --- | --- | --- |
| 30356 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_minipost.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 30345 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_pm.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 30337 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_quote.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 30337 | `http://kyledurepos.com/BB/templates/subSilver/images/spacer.gif` | `spacer.gif`<br>`mt-static/images/spacer.gif` | exact raw/canonical: 0/0; basename raw/canonical: 11/33; selected exact: no | copy existing same-basename file into requested `/BB/templates/subSilver/images/...` path, preserving requested filename |
| 30295 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_profile.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 23203 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_aim.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 6980 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_www.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 6454 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_email.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 5166 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_yim.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 4906 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/post.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 4854 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/reply.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 3383 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_msnm.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2681 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_icq_add.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_faq.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_groups.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_login.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_members.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_message.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_profile.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_register.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_search.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/logo_phpBB.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 157 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_latest_reply.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 139 | `http://kyledurepos.com/BB/templates/subSilver/images/folder.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 14 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_hot.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 11 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_sticky.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 8 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_lock.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 7 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_announce.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 6 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_new.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |
| 5 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_big.gif` | none found | exact raw/canonical: 0/0; basename raw/canonical: 0/0; selected exact: no | generate neutral phpBB-style placeholder for chrome asset |

## Top Missing Smilies/Emoticons

| Refs | Missing URL | Same-basename candidates | Inventory evidence | Recommendation |
| ---: | --- | --- | --- | --- |
| 472 | `http://kyledurepos.com/BB/images/smiles/icon_eek.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 414 | `http://kyledurepos.com/images/smiles/icon_sad.gif` | `BB/images/smiles/icon_sad.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 387 | `http://kyledurepos.com/BB/images/smiles/lol.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 256 | `http://kyledurepos.com/images/smiles/inlove.gif` | `BB/images/smiles/inlove.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 211 | `http://kyledurepos.com/images/smiles/icon_rolleyes.gif` | `BB/images/smiles/icon_rolleyes.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 206 | `http://kyledurepos.com/images/smiles/icon_smile.gif` | `BB/images/smiles/icon_smile.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 172 | `http://kyledurepos.com/images/smiles/icon_biggrin.gif` | `BB/images/smiles/icon_biggrin.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 149 | `http://kyledurepos.com/images/smiles/icon_cool.gif` | `BB/images/smiles/icon_cool.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 147 | `http://kyledurepos.com/BB/images/smiles/icon_wink.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 107 | `http://kyledurepos.com/BB/images/smiles/icon_confused.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 88 | `http://kyledurepos.com/images/smiles/icon_razz.gif` | `BB/images/smiles/icon_razz.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 87 | `http://kyledurepos.com/BB/images/smiles/icon_twisted.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 85 | `http://kyledurepos.com/images/smiles/icon_mad.gif` | `BB/images/smiles/icon_mad.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 75 | `http://kyledurepos.com/images/smiles/icon_lol.gif` | `BB/images/smiles/icon_lol.gif` | exact raw/canonical: 0/0; selected exact: no | copy existing same-basename smiley if visually plausible |
| 68 | `http://kyledurepos.com/BB/images/smiles/icon_cry.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 57 | `http://kyledurepos.com/BB/images/smiles/emot-sax.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 52 | `http://kyledurepos.com/BB/images/smiles/emot-q.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 51 | `http://kyledurepos.com/BB/images/smiles/icon_redface.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 35 | `http://kyledurepos.com/BB/images/smiles/emot-crying.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 31 | `http://kyledurepos.com/BB/images/smiles/emot-eng101.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 19 | `http://kyledurepos.com/BB/images/smiles/icon_evil.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 12 | `http://kyledurepos.com/BB/images/smiles/emot-nyd.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 8 | `http://kyledurepos.com/BB/images/smiles/icon_exclaim.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |
| 6 | `http://kyledurepos.com/BB/images/smiles/emot-nws.gif` | none found | exact raw/canonical: 0/0; selected exact: no | generate neutral tiny smiley/emoticon placeholder or leave if nonessential post expression |

## Missing Assets By Class

### forum UI chrome

| Refs | URL |
| ---: | --- |
| 30356 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_minipost.gif` |
| 30345 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_pm.gif` |
| 30337 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_quote.gif` |
| 30337 | `http://kyledurepos.com/BB/templates/subSilver/images/spacer.gif` |
| 30295 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_profile.gif` |
| 23203 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_aim.gif` |
| 6980 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_www.gif` |
| 6454 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_email.gif` |
| 5166 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_yim.gif` |
| 4906 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/post.gif` |
| 4854 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/reply.gif` |
| 3383 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_msnm.gif` |
| 2681 | `http://kyledurepos.com/BB/templates/subSilver/images/lang_english/icon_icq_add.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_faq.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_groups.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_login.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_members.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_message.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_profile.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_register.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_mini_search.gif` |
| 2481 | `http://kyledurepos.com/BB/templates/subSilver/images/logo_phpBB.gif` |
| 157 | `http://kyledurepos.com/BB/templates/subSilver/images/icon_latest_reply.gif` |
| 139 | `http://kyledurepos.com/BB/templates/subSilver/images/folder.gif` |
| 14 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_hot.gif` |
| 11 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_sticky.gif` |
| 8 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_lock.gif` |
| 7 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_announce.gif` |
| 6 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_new.gif` |
| 5 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_big.gif` |
| 5 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_lock_new.gif` |
| 5 | `http://kyledurepos.com/BB/templates/subSilver/images/folder_new_hot.gif` |
| 1 | `http://kyledurepos.com/BB/templates/subSilver/images/whosonline.gif` |

### smilies/emoticons

| Refs | URL |
| ---: | --- |
| 472 | `http://kyledurepos.com/BB/images/smiles/icon_eek.gif` |
| 414 | `http://kyledurepos.com/images/smiles/icon_sad.gif` |
| 387 | `http://kyledurepos.com/BB/images/smiles/lol.gif` |
| 256 | `http://kyledurepos.com/images/smiles/inlove.gif` |
| 211 | `http://kyledurepos.com/images/smiles/icon_rolleyes.gif` |
| 206 | `http://kyledurepos.com/images/smiles/icon_smile.gif` |
| 172 | `http://kyledurepos.com/images/smiles/icon_biggrin.gif` |
| 149 | `http://kyledurepos.com/images/smiles/icon_cool.gif` |
| 147 | `http://kyledurepos.com/BB/images/smiles/icon_wink.gif` |
| 107 | `http://kyledurepos.com/BB/images/smiles/icon_confused.gif` |
| 88 | `http://kyledurepos.com/images/smiles/icon_razz.gif` |
| 87 | `http://kyledurepos.com/BB/images/smiles/icon_twisted.gif` |
| 85 | `http://kyledurepos.com/images/smiles/icon_mad.gif` |
| 75 | `http://kyledurepos.com/images/smiles/icon_lol.gif` |
| 68 | `http://kyledurepos.com/BB/images/smiles/icon_cry.gif` |
| 57 | `http://kyledurepos.com/BB/images/smiles/emot-sax.gif` |
| 52 | `http://kyledurepos.com/BB/images/smiles/emot-q.gif` |
| 51 | `http://kyledurepos.com/BB/images/smiles/icon_redface.gif` |
| 35 | `http://kyledurepos.com/BB/images/smiles/emot-crying.gif` |
| 31 | `http://kyledurepos.com/BB/images/smiles/emot-eng101.gif` |
| 19 | `http://kyledurepos.com/BB/images/smiles/icon_evil.gif` |
| 12 | `http://kyledurepos.com/BB/images/smiles/emot-nyd.gif` |
| 8 | `http://kyledurepos.com/BB/images/smiles/icon_exclaim.gif` |
| 6 | `http://kyledurepos.com/BB/images/smiles/emot-nws.gif` |

### avatars/uploads

| Refs | URL |
| ---: | --- |
| 1095 | `http://kyledurepos.com//upload_files/wolf copy.gif` |
| 1051 | `http://kyledurepos.com//upload_files/hope avatar1.gif` |
| 449 | `http://kyledurepos.com//upload_files/mattandgirl22.jpg` |
| 112 | `http://kyledurepos.com//upload_files/cyphermatrix2.gif` |
| 106 | `http://kyledurepos.com//upload_files/HomoAvatar.jpg` |
| 95 | `http://kyledurepos.com//upload_files/GHOUl.gif` |
| 45 | `http://kyledurepos.com//upload_files/meavatar.bmp` |
| 40 | `http://kyledurepos.com/vitis/upload_files/orionsmomaward.jpg` |
| 24 | `http://kyledurepos.com//upload_files/Alex Avatar.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/KOH&VV.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/VV&DRAB.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/VV-1.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/VitisDJHombre.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/mojomasta.jpg` |
| 21 | `http://kyledurepos.com/vitis/upload_files/wakeupmojo.jpg` |
| 18 | `http://kyledurepos.com/vitis/upload_files/cyber.jpg` |
| 17 | `http://kyledurepos.com/vitis/upload_files/Blues%20029.jpg` |
| 10 | `http://kyledurepos.com//upload_files/Brad3.jpg` |
| 10 | `http://kyledurepos.com/vitis/upload_files/DSC02168.JPG` |
| 8 | `http://kyledurepos.com/vitis/upload_files/fuck-you-crackaVitis.jpg` |
| 3 | `http://kyledurepos.com//upload_files/stonecold.jpg` |
| 1 | `http://kyledurepos.com//upload_files/,yg,t.JPG` |
| 1 | `http://kyledurepos.com//upload_files/rochesingle22.jpg` |
| 1 | `http://kyledurepos.com//upload_files/untitled.bmp` |

### post content images

| Refs | URL |
| ---: | --- |
| 2481 | `templates/subSilver/images/cellpic1.gif` |
| 2481 | `templates/subSilver/images/cellpic2.jpg` |
| 2481 | `templates/subSilver/images/cellpic3.gif` |
| 200 | `http://kyledurepos.com/templates/subSilver/images/vote_lcap.gif` |
| 200 | `http://kyledurepos.com/templates/subSilver/images/vote_rcap.gif` |
| 200 | `http://kyledurepos.com/templates/subSilver/images/voting_bar.gif` |
| 107 | `http://kyledurepos.com/images/eclipse_girl2.gif` |
| 42 | `http://kyledurepos.com/templates/subSilver/images/lang_english/reply-locked.gif` |
| 21 | `http://kyledurepos.com/bitchtits/hi.jpg` |
| 21 | `http://kyledurepos.com/bitchtits/iviewcapture_date_11_03_2004_time_21_36_12.jpg` |
| 21 | `http://kyledurepos.com/bitchtits/iviewcapture_date_14_03_2004_time_18_48_21.jpg` |
| 21 | `http://kyledurepos.com/shangified/0047.jpg` |
| 19 | `http://kyledurepos.com/bitchtits/kotor/iviewcapture_date_04_04_2004_time_23_45_45.jpg` |
| 17 | `http://kyledurepos.com/eclipse/Images/Other/Shannon3.jpg` |
| 17 | `http://kyledurepos.com/eclipse/Images/Other/Shannon4.jpg` |
| 17 | `http://kyledurepos.com/shangified/mojolol.jpg` |
| 15 | `http://kyledurepos.com/bitchtits/sh_04.jpg` |
| 10 | `http://kyledurepos.com/bitchtits/MVC-013F.jpg` |
| 10 | `http://kyledurepos.com/shangified/0055.jpg` |
| 7 | `http://kyledurepos.com/shangified/adrian2.jpg` |
| 7 | `http://kyledurepos.com/shangified/adrian3.jpg` |
| 7 | `http://kyledurepos.com/shangified/adrian4.jpg` |
| 7 | `http://kyledurepos.com/shangified/adrian5.jpg` |
| 7 | `http://kyledurepos.com/shangified/adrian6.jpg` |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic1.gif` |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic2.gif` |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic3.gif` |
| 4 | `http://kyledurepos.com/images/glenn.jpg` |
| 3 | `http://kyledurepos.com/eclipse/Images/Other/stfu_n00b.jpg` |
| 3 | `http://kyledurepos.com/eclipse/Images/Other/wonder.jpg` |

## Manifest Findings

- `site.manifest.jsonl` contains selected/recovered phpBB smilies such as `icon_biggrin.gif`, `icon_cool.gif`, `icon_lol.gif`, `icon_mad.gif`, and `icon_razz.gif`, but the missing smiley filenames listed above are not selected at their exact `/BB/images/smiles/...` URLs.
- The focused `inventory.dependencies.feedback-2` pass queried the listed `/BB/images/smiles/...` and `/BB/templates/subSilver/images/...` high-value dependencies and reported them as unresolved, so the main issue is unavailable CDX evidence for the exact requested URLs rather than a selection omission.
- Some phpBB chrome basenames exist elsewhere in the promoted tree, especially under `dgclan/modules/Forums/templates/subSilver/images/...`; these are the best copy sources for neutral UI chrome repair when exact `/BB/templates/subSilver/images/...` captures are absent.

## Recommended Implementation Plan

1. For missing `/BB/templates/subSilver/images/...` chrome, copy same-basename assets from promoted phpBB/subSilver paths when present, preferring `dgclan/modules/Forums/templates/subSilver/images/...` over unrelated locations. Do not symlink in the served tree.
2. For missing chrome with no promoted same-basename source, generate small neutral phpBB-style GIF/PNG placeholders matching the filename role, such as folder, mini icon, post/reply, spacer, or whosonline.
3. For missing `/BB/images/smiles/...`, copy same-basename recovered smilies only when an exact basename exists; otherwise generate neutral 15x15 to 20x20 placeholders for high-frequency emoticons.
4. Leave third-party/external images and unrecovered post-content images broken unless there is explicit content value or a known local candidate. They are content recovery gaps, not forum chrome blockers.
5. After any repair pass, rerun the same audit and static validation to confirm missing UI chrome and smilie counts fall to zero or to documented intentional waivers.

