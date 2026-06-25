# Forum External Media Recovery Report

Run ID: `20260622T194955Z-latest-good`

## Summary

- HTML files parsed: `2494`
- External image refs found: `22393`
- Unique external image URLs found: `250`
- Hosts found: `69`
- Candidate cap: `50`
- Attempted: `50`
- Recovered: `8`
- Failed: `42`
- HTML files rewritten: `1446`

## Top Hosts By Reference Count

| Refs | Host |
| ---: | --- |
| 5713 | `home.earthlink.net` |
| 2085 | `www.drunkwisdom.com` |
| 2068 | `img23.photobucket.com` |
| 1758 | `www.pie-hole.com` |
| 1577 | `internet.oit.edu` |
| 1575 | `www.nocturne.com` |
| 1155 | `www.pitt.edu` |
| 1080 | `www.neapolitanicecream.com` |
| 578 | `www.james-ramos.com` |
| 534 | `dramatica.250free.com` |
| 443 | `img.photobucket.com` |
| 421 | `img50.exs.cx` |
| 342 | `home.insightbb.com` |
| 328 | `www.yulitl.com` |
| 262 | `www.dark54555.com` |
| 246 | `www.skamunism.net` |
| 237 | `www.myimgs.com` |
| 234 | `home.comcast.net` |
| 223 | `www.simpsoncrazy.com` |
| 187 | `animatedgif.net` |

## Top Attempted URLs

| Refs | Host | URL | Result |
| ---: | --- | --- | --- |
| 1776 | `img23.photobucket.com` | `http://img23.photobucket.com/albums/v68/the_notorious/avatar03.jpg` | `failed` |
| 1329 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/images/avatar.jpg` | `failed` |
| 1145 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/avatar.jpg` | `failed` |
| 1062 | `home.earthlink.net` | `http://home.earthlink.net/~sdroden/images/weee2.gif` | `recovered` |
| 979 | `home.earthlink.net` | `http://home.earthlink.net/~eclipse26/images/DE1.jpg` | `recovered` |
| 495 | `home.earthlink.net` | `http://home.earthlink.net/~eclipse26/images/harleyquinn4.jpg` | `failed` |
| 488 | `dramatica.250free.com` | `http://dramatica.250free.com/Avatar.jpg` | `failed` |
| 421 | `img50.exs.cx` | `http://img50.exs.cx/img50/1563/38906961640bff4db92ce6.gif` | `failed` |
| 268 | `img.photobucket.com` | `http://img.photobucket.com/albums/v252/skamunism/avatar.jpg` | `recovered` |
| 230 | `home.earthlink.net` | `http://home.earthlink.net/~sdroden/images/senatepennywise.jpg` | `failed` |
| 141 | `img.photobucket.com` | `http://img.photobucket.com/albums/v68/the_notorious/06.jpg` | `failed` |
| 80 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/images/zom.jpg` | `failed` |
| 60 | `home.earthlink.net` | `http://home.earthlink.net/~zombiexp/images/rating.jpg` | `failed` |
| 42 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/images/alan.jpg` | `failed` |
| 36 | `dramatica.250free.com` | `http://dramatica.250free.com/syl2.jpg` | `failed` |
| 21 | `img23.photobucket.com` | `http://img23.photobucket.com/albums/v68/the_notorious/zack101.jpg` | `failed` |
| 21 | `img23.photobucket.com` | `http://img23.photobucket.com/albums/v68/the_notorious/zack100.jpg` | `failed` |
| 21 | `img23.photobucket.com` | `http://img23.photobucket.com/albums/v68/the_notorious/lerxst01.jpg` | `recovered` |
| 21 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/images/ursj.jpg` | `recovered` |
| 21 | `home.earthlink.net` | `http://home.earthlink.net/~zombie_poop/images/teaser.jpg` | `failed` |

## Recovered Examples

- `http://home.earthlink.net/~sdroden/images/weee2.gif` -> `BB/recovered-external/home.earthlink.net/weee2-22ba67b0a5f4.gif`
- `http://home.earthlink.net/~eclipse26/images/DE1.jpg` -> `BB/recovered-external/home.earthlink.net/DE1-e43107809bd3.jpg`
- `http://img.photobucket.com/albums/v252/skamunism/avatar.jpg` -> `BB/recovered-external/img.photobucket.com/avatar-631e2063001b.jpg`
- `http://img23.photobucket.com/albums/v68/the_notorious/lerxst01.jpg` -> `BB/recovered-external/img23.photobucket.com/lerxst01-a09b1a75f3c8.jpg`
- `http://home.earthlink.net/~zombie_poop/images/ursj.jpg` -> `BB/recovered-external/home.earthlink.net/ursj-c39241436b96.jpg`
- `http://home.earthlink.net/~zombie_poop/images/great.jpg` -> `BB/recovered-external/home.earthlink.net/great-4cd43966a080.jpg`
- `http://home.earthlink.net/~zombie_poop/images/DSC00508.JPG` -> `BB/recovered-external/home.earthlink.net/DSC00508-30eb5bd003d9.JPG`
- `http://img23.photobucket.com/albums/v68/the_notorious/004.jpg` -> `BB/recovered-external/img23.photobucket.com/004-1f6292ce6377.jpg`

## Failure Reasons

- `TimeoutError`: `22`
- `no-image-cdx-capture`: `17`
- `HTTPError`: `2`
- `URLError`: `1`

## Limitations

- CDX queries were exact URL lookups only; alternate schemes, host aliases, redirects, and resized thumbnail variants were not crawled.
- Only the top capped set was attempted, prioritizing high-frequency and historically recoverable image hosts.
- No placeholders were created for failed URLs.
