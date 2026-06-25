# Forum Missing Media Audit

Run ID: `20260622T194955Z-latest-good`
Site root: `/home/mojo/projects/archivebackup/recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site`
Scope: `/BB/**/*.html`; no site files were mutated and no network fetches were performed.

## Summary

| Metric | Count |
| --- | ---: |
| HTML files parsed | 2494 |
| Image/CSS URL refs scanned | 280871 |
| Missing refs | 25411 |
| Unique missing URLs | 284 |
| Unique missing with CDX evidence | 1 |

## Counts By Class

| Class | Missing refs | Unique URLs | Unique with CDX evidence |
| --- | ---: | ---: | ---: |
| avatars/uploads | 3212 | 24 | 1 |
| post content | 353 | 23 | 0 |
| smilies custom | 0 | 0 | 0 |
| external | 21846 | 237 | 0 |
| unknown | 0 | 0 | 0 |

## Manifest Match Status

| Status | Unique URLs |
| --- | ---: |
| external_not_searched | 237 |
| absent_from_inventory | 46 |
| raw_basename_match_only | 1 |

## Top Recoverable Candidates

| Rank | Refs | Class | URL | Match status | CDX examples |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 21 | avatars/uploads | `http://kyledurepos.com/vitis/upload_files/mojomasta.jpg` | raw_basename_match_only | 20030622145523 http://www.kyledurepos.com:80/blog/mojomasta.jpg<br>20031123182222 http://www.kyledurepos.com/blog/mojomasta.jpg |

## Top Missing By Class

### avatars/uploads

| Refs | URL | Status | Examples |
| ---: | --- | --- | --- |
| 1095 | `http://kyledurepos.com//upload_files/wolf copy.gif` | absent_from_inventory | BB/viewtopic__q_302f4ce2/index.html<br>BB/viewtopic__q_fc9a1438/index.html<br>BB/viewtopic__q_b2ccec10/index.html |
| 1051 | `http://kyledurepos.com//upload_files/hope avatar1.gif` | absent_from_inventory | BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_b8810e2c/index.html |
| 449 | `http://kyledurepos.com//upload_files/mattandgirl22.jpg` | absent_from_inventory | BB/viewtopic__q_f268c63d/index.html<br>BB/viewtopic__q_9288f10e/index.html<br>BB/viewtopic__q_4c8d3c2c/index.html |
| 112 | `http://kyledurepos.com//upload_files/cyphermatrix2.gif` | absent_from_inventory | BB/viewtopic__q_12b60f4d/index.html<br>BB/viewtopic__q_ad66b0cb/index.html<br>BB/viewtopic__q_c5839277/index.html |
| 106 | `http://kyledurepos.com//upload_files/HomoAvatar.jpg` | absent_from_inventory | BB/viewtopic__q_f81923a2/index.html<br>BB/viewtopic__q_209d7514/index.html<br>BB/viewtopic__q_209d7514/index.html |
| 95 | `http://kyledurepos.com//upload_files/GHOUl.gif` | absent_from_inventory | BB/viewtopic__q_fc9a1438/index.html<br>BB/viewtopic__q_0759536a/index.html<br>BB/viewtopic__q_9e695e28/index.html |
| 45 | `http://kyledurepos.com//upload_files/meavatar.bmp` | absent_from_inventory | BB/viewtopic__q_380dd108/index.html<br>BB/viewtopic__q_220cbbaa/index.html<br>BB/viewtopic__q_613305db/index.html |
| 40 | `http://kyledurepos.com/vitis/upload_files/orionsmomaward.jpg` | absent_from_inventory | BB/viewtopic__q_469182a0/index.html<br>BB/viewtopic__q_d2a6fdb5/index.html<br>BB/viewtopic__q_7126adcd/index.html |
| 24 | `http://kyledurepos.com//upload_files/Alex Avatar.jpg` | absent_from_inventory | BB/viewtopic__q_cc917535/index.html<br>BB/viewtopic__q_4d10039a/index.html<br>BB/viewtopic__q_a8819841/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/KOH&VV.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/mojomasta.jpg` | raw_basename_match_only | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/VitisDJHombre.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/VV&DRAB.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/VV-1.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 21 | `http://kyledurepos.com/vitis/upload_files/wakeupmojo.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 18 | `http://kyledurepos.com/vitis/upload_files/cyber.jpg` | absent_from_inventory | BB/viewtopic__q_5c9253c0/index.html<br>BB/viewtopic__q_8eeccd4f/index.html<br>BB/viewtopic__q_1b646aaf/index.html |
| 17 | `http://kyledurepos.com/vitis/upload_files/Blues%20029.jpg` | absent_from_inventory | BB/viewtopic__q_7a2deb9e/index.html<br>BB/viewtopic__q_cf701466/index.html<br>BB/viewtopic__q_8de5155d/index.html |
| 10 | `http://kyledurepos.com//upload_files/Brad3.jpg` | absent_from_inventory | BB/viewtopic__q_1be44adf/index.html<br>BB/viewtopic__q_3c059d7a/index.html<br>BB/viewtopic__q_2ed358b6/index.html |
| 10 | `http://kyledurepos.com/vitis/upload_files/DSC02168.JPG` | absent_from_inventory | BB/viewtopic__q_7d82b703/index.html<br>BB/viewtopic__q_8f279bc0/index.html<br>BB/viewtopic__q_d4859bd1/index.html |
| 8 | `http://kyledurepos.com/vitis/upload_files/fuck-you-crackaVitis.jpg` | absent_from_inventory | BB/viewtopic__q_2c032671/index.html<br>BB/viewtopic__q_0331903f/index.html<br>BB/viewtopic__q_0179462a/index.html |

### post content

| Refs | URL | Status | Examples |
| ---: | --- | --- | --- |
| 107 | `http://kyledurepos.com/images/eclipse_girl2.gif` | absent_from_inventory | BB/viewtopic__q_302f4ce2/index.html<br>BB/viewtopic__q_85cd91c5/index.html<br>BB/viewtopic__q_4b0faae0/index.html |
| 21 | `http://kyledurepos.com/bitchtits/hi.jpg` | absent_from_inventory | BB/viewtopic__q_b4e5b034/index.html<br>BB/viewtopic__q_533a3f8e/index.html<br>BB/viewtopic__q_9dfb531e/index.html |
| 21 | `http://kyledurepos.com/bitchtits/iviewcapture_date_11_03_2004_time_21_36_12.jpg` | absent_from_inventory | BB/viewtopic__q_06a6449e/index.html<br>BB/viewtopic__q_748fb5f6/index.html<br>BB/viewtopic__q_d79f920c/index.html |
| 21 | `http://kyledurepos.com/bitchtits/iviewcapture_date_14_03_2004_time_18_48_21.jpg` | absent_from_inventory | BB/viewtopic__q_06a6449e/index.html<br>BB/viewtopic__q_748fb5f6/index.html<br>BB/viewtopic__q_d79f920c/index.html |
| 21 | `http://kyledurepos.com/shangified/0047.jpg` | absent_from_inventory | BB/viewtopic__q_47514287/index.html<br>BB/viewtopic__q_bec4fae9/index.html<br>BB/viewtopic__q_32f18e68/index.html |
| 19 | `http://kyledurepos.com/bitchtits/kotor/iviewcapture_date_04_04_2004_time_23_45_45.jpg` | absent_from_inventory | BB/viewtopic__q_9b96553a/index.html<br>BB/viewtopic__q_28ce9e02/index.html<br>BB/viewtopic__q_fd155cc2/index.html |
| 17 | `http://kyledurepos.com/eclipse/Images/Other/Shannon3.jpg` | absent_from_inventory | BB/viewtopic__q_71799aaf/index.html<br>BB/viewtopic__q_6c4c6de5/index.html<br>BB/viewtopic__q_240996a2/index.html |
| 17 | `http://kyledurepos.com/eclipse/Images/Other/Shannon4.jpg` | absent_from_inventory | BB/viewtopic__q_71799aaf/index.html<br>BB/viewtopic__q_6c4c6de5/index.html<br>BB/viewtopic__q_240996a2/index.html |
| 17 | `http://kyledurepos.com/shangified/mojolol.jpg` | absent_from_inventory | BB/viewtopic__q_7a2deb9e/index.html<br>BB/viewtopic__q_cf701466/index.html<br>BB/viewtopic__q_8de5155d/index.html |
| 15 | `http://kyledurepos.com/bitchtits/sh_04.jpg` | absent_from_inventory | BB/viewtopic__q_d27137c6/index.html<br>BB/viewtopic__q_7cda3701/index.html<br>BB/viewtopic__q_57573e99/index.html |
| 10 | `http://kyledurepos.com/bitchtits/MVC-013F.jpg` | absent_from_inventory | BB/viewtopic__q_7d82b703/index.html<br>BB/viewtopic__q_8f279bc0/index.html<br>BB/viewtopic__q_d4859bd1/index.html |
| 10 | `http://kyledurepos.com/shangified/0055.jpg` | absent_from_inventory | BB/viewtopic__q_7d82b703/index.html<br>BB/viewtopic__q_8f279bc0/index.html<br>BB/viewtopic__q_d4859bd1/index.html |
| 7 | `http://kyledurepos.com/shangified/adrian2.jpg` | absent_from_inventory | BB/viewtopic__q_fcf8277d/index.html<br>BB/viewtopic__q_3e54214a/index.html<br>BB/viewtopic__q_5984805e/index.html |
| 7 | `http://kyledurepos.com/shangified/adrian3.jpg` | absent_from_inventory | BB/viewtopic__q_fcf8277d/index.html<br>BB/viewtopic__q_3e54214a/index.html<br>BB/viewtopic__q_5984805e/index.html |
| 7 | `http://kyledurepos.com/shangified/adrian4.jpg` | absent_from_inventory | BB/viewtopic__q_fcf8277d/index.html<br>BB/viewtopic__q_3e54214a/index.html<br>BB/viewtopic__q_5984805e/index.html |
| 7 | `http://kyledurepos.com/shangified/adrian5.jpg` | absent_from_inventory | BB/viewtopic__q_fcf8277d/index.html<br>BB/viewtopic__q_3e54214a/index.html<br>BB/viewtopic__q_5984805e/index.html |
| 7 | `http://kyledurepos.com/shangified/adrian6.jpg` | absent_from_inventory | BB/viewtopic__q_fcf8277d/index.html<br>BB/viewtopic__q_3e54214a/index.html<br>BB/viewtopic__q_5984805e/index.html |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic1.gif` | absent_from_inventory | BB/viewtopic__q_3055ffbf/index.html<br>BB/viewtopic__q_18f3e19a/index.html<br>BB/viewtopic__q_595145d6/index.html |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic2.gif` | absent_from_inventory | BB/viewtopic__q_3055ffbf/index.html<br>BB/viewtopic__q_18f3e19a/index.html<br>BB/viewtopic__q_595145d6/index.html |
| 4 | `http://kyledurepos.com/eclipse/Images/Other/pic3.gif` | absent_from_inventory | BB/viewtopic__q_3055ffbf/index.html<br>BB/viewtopic__q_18f3e19a/index.html<br>BB/viewtopic__q_595145d6/index.html |

### smilies custom

| Refs | URL | Status | Examples |
| ---: | --- | --- | --- |

### external

| Refs | URL | Status | Examples |
| ---: | --- | --- | --- |
| 1776 | `http://img23.photobucket.com/albums/v68/the_notorious/avatar03.jpg` | external_not_searched | BB/viewtopic__q_7b04533e/index.html<br>BB/viewtopic__q_7b04533e/index.html<br>BB/viewtopic__q_f268c63d/index.html |
| 1755 | `http://www.pie-hole.com/avatars/avatar.gif` | external_not_searched | BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_3f32506c/index.html |
| 1575 | `http://www.nocturne.com/images/shops/products/thumbs/baby/pirate_shag_sticker.jpg` | external_not_searched | BB/viewtopic__q_302f4ce2/index.html<br>BB/viewtopic__q_f268c63d/index.html<br>BB/viewtopic__q_fc9a1438/index.html |
| 1563 | `http://www.drunkwisdom.com/archive/cheney.jpg` | external_not_searched | BB/viewtopic__q_f44cca8a/index.html<br>BB/viewtopic__q_2cfc8f59/index.html<br>BB/viewtopic__q_2cfc8f59/index.html |
| 1329 | `http://home.earthlink.net/~zombie_poop/images/avatar.jpg` | external_not_searched | BB/viewtopic__q_b2ccec10/index.html<br>BB/viewtopic__q_b2ccec10/index.html<br>BB/viewtopic__q_b2ccec10/index.html |
| 1328 | `http://internet.oit.edu/~barberia/AvatarPics/avatar.gif` | external_not_searched | BB/viewtopic__q_f268c63d/index.html<br>BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_3f32506c/index.html |
| 1145 | `http://home.earthlink.net/~zombie_poop/avatar.jpg` | external_not_searched | BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_9288f10e/index.html<br>BB/viewtopic__q_9288f10e/index.html |
| 1104 | `http://www.pitt.edu/~das23/avat.jpg` | external_not_searched | BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_9b96553a/index.html |
| 1062 | `http://home.earthlink.net/~sdroden/images/weee2.gif` | external_not_searched | BB/viewtopic__q_fc9a1438/index.html<br>BB/viewtopic__q_9b96553a/index.html<br>BB/viewtopic__q_2cfc8f59/index.html |
| 1033 | `http://www.neapolitanicecream.com/iB_html/non-cgi/avatars/billy.jpg` | external_not_searched | BB/viewtopic__q_f81923a2/index.html<br>BB/viewtopic__q_4c8d3c2c/index.html<br>BB/viewtopic__q_4c8d3c2c/index.html |
| 979 | `http://home.earthlink.net/~eclipse26/images/DE1.jpg` | external_not_searched | BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_b8810e2c/index.html |
| 530 | `http://www.james-ramos.com/images/avatar.jpg` | external_not_searched | BB/viewtopic__q_f44cca8a/index.html<br>BB/viewtopic__q_3d6a5553/index.html<br>BB/viewtopic__q_d2a1f5cb/index.html |
| 495 | `http://home.earthlink.net/~eclipse26/images/harleyquinn4.jpg` | external_not_searched | BB/viewtopic__q_9b96553a/index.html<br>BB/viewtopic__q_9b96553a/index.html<br>BB/viewtopic__q_9b96553a/index.html |
| 488 | `http://dramatica.250free.com/Avatar.jpg` | external_not_searched | BB/viewtopic__q_7b04533e/index.html<br>BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_f5070e2f/index.html |
| 421 | `http://img50.exs.cx/img50/1563/38906961640bff4db92ce6.gif` | external_not_searched | BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_9b96553a/index.html |
| 342 | `http://home.insightbb.com/~e.mcdonald/cid3.jpg` | external_not_searched | BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_b8810e2c/index.html<br>BB/viewtopic__q_559f2164/index.html |
| 311 | `http://www.yulitl.com/robavatar.jpg` | external_not_searched | BB/viewtopic__q_c3fd6b16/index.html<br>BB/viewtopic__q_c3fd6b16/index.html<br>BB/viewtopic__q_c3fd6b16/index.html |
| 268 | `http://img.photobucket.com/albums/v252/skamunism/avatar.jpg` | external_not_searched | BB/viewtopic__q_abb27f77/index.html<br>BB/viewtopic__q_56c6accc/index.html<br>BB/viewtopic__q_b7498637/index.html |
| 247 | `http://www.dark54555.com/avatar.jpg` | external_not_searched | BB/viewtopic__q_3f32506c/index.html<br>BB/viewtopic__q_abb27f77/index.html<br>BB/viewtopic__q_4c8d3c2c/index.html |
| 230 | `http://home.earthlink.net/~sdroden/images/senatepennywise.jpg` | external_not_searched | BB/viewtopic__q_4c8d3c2c/index.html<br>BB/viewtopic__q_274fa0f3/index.html<br>BB/viewtopic__q_559f2164/index.html |

### unknown

| Refs | URL | Status | Examples |
| ---: | --- | --- | --- |

## Recommended Recovery Strategy

1. Prioritize first-party avatar/upload rows with `raw_exact_not_selected` or `raw_path_match_not_selected`; these can be selected/downloaded directly from CDX evidence without guessing content.
2. Next recover post-content rows with exact/path CDX matches, preserving original case, spaces, ampersands, and doubled-slash URL variants in lookup aliases while writing to normalized filesystem paths.
3. Treat basename-only matches as lower confidence; verify digest, MIME, dimensions, or surrounding page context before mapping them into forum posts.
4. Do not spend recovery effort on external third-party image URLs in this run unless a separate external-domain CDX inventory is created.
5. Existing generated phpBB UI and placeholder smilies are now local; any remaining first-party gaps in this audit are content media rather than forum chrome blockers.
