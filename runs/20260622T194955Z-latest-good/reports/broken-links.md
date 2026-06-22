# Broken Links Report

Run ID: `20260622T194955Z-latest-good`  
Generated: `2026-06-22T23:04:25Z`  
Stage: `validate.feedback-1`  
Gate impact: `none`

## Summary

| Item | Count |
| --- | ---: |
| HTML files parsed | 2716 |
| HTML/CSS references checked | 606746 |
| Broken local staged references | 0 |
| Missing CSS dependencies in staged CSS | 0 |
| Preserved external absolute first-party URLs | 943 |
| External third-party absolute/protocol-relative URLs ignored as local refs | 6033 |
| Unresolved first-party recovery coverage gaps | 87481 |
| High-value missing dependencies after feedback-2 | 454 |

## Result

- No broken local staged HTML/CSS references were found. This verifies the normalize.feedback-1 reduction from the previous 514456 broken staged refs to 0 in this validation pass.

## Preserved First-Party Absolute URLs

- Remaining absolute first-party URLs are classified as unresolved recovery coverage gaps, not static-serving broken local refs, unless they are homepage/top-level/CSS/JS/critical images and recoverable.
- Focused dependency inventory feedback-2 queried high-value candidates; unresolved/unsupported assets are warning or waiver candidates for private-tailnet serving when they do not block render/static smoke.

## Sample Preserved First-Party URLs
- `http://hellslayer.kyledurepos.com/blog`
- `http://hellslayer.kyledurepos.com/blog/index.php`
- `http://hellslayer.kyledurepos.com/blog/wp-admin`
- `http://hellslayer.kyledurepos.com/blog/wp-content/plugins/Calendar/images/arrow_left.gif`
- `http://hellslayer.kyledurepos.com/blog/wp-content/plugins/Calendar/images/arrow_right.gif`
- `http://hellslayer.kyledurepos.com/blog/wp-content/plugins/Calendar/images/dot.gif`
- `http://hellslayer.kyledurepos.com/blog/wp-content/themes/corporatefk-10/fader.swf`
- `http://hellslayer.kyledurepos.com/blog/wp-login.php`
- `http://hellslayer.kyledurepos.com/blog/xmlrpc.php`
- `http://hellslayer.kyledurepos.com/blog/xmlrpc.php?rsd=`
- `http://hellslayer.kyledurepos.com/podcast`
- `http://hellslayer.kyledurepos.com/podcast/index.php?paged=2`
- `http://hellslayer.kyledurepos.com/podcast/wp-content/plugins/coolplayer/coolplayer.css`
- `http://hellslayer.kyledurepos.com/podcast/wp-content/plugins/coolplayer/coolplayer.js`
- `http://hellslayer.kyledurepos.com/podcast/wp-content/plugins/coolplayer/phprpc_client.js`
- `http://hellslayer.kyledurepos.com/podcast/wp-content/themes/orange-subway-10/style.css`
- `http://hellslayer.kyledurepos.com/podcast/wp-login.php`
- `http://hellslayer.kyledurepos.com/podcast/wp-login.php?action=register`
- `http://hellslayer.kyledurepos.com/podcast/xmlrpc.php`
- `http://hellslayer.kyledurepos.com/podcast/xmlrpc.php?rsd=`
- `http://kyledurepos.com//upload_files/,yg,t.JPG`
- `http://kyledurepos.com//upload_files/Alex Avatar.jpg`
- `http://kyledurepos.com//upload_files/Brad3.jpg`
- `http://kyledurepos.com//upload_files/GHOUl.gif`
- `http://kyledurepos.com//upload_files/HomoAvatar.jpg`
- `http://kyledurepos.com//upload_files/cyphermatrix2.gif`
- `http://kyledurepos.com//upload_files/hope avatar1.gif`
- `http://kyledurepos.com//upload_files/mattandgirl22.jpg`
- `http://kyledurepos.com//upload_files/meavatar.bmp`
- `http://kyledurepos.com//upload_files/rochesingle22.jpg`
- `http://kyledurepos.com//upload_files/stonecold.jpg`
- `http://kyledurepos.com//upload_files/untitled.bmp`
- `http://kyledurepos.com//upload_files/wolf copy.gif`
- `http://kyledurepos.com/000007/index.html`
- `http://kyledurepos.com/000008/index.html`
- `http://kyledurepos.com/000009/index.html`
- `http://kyledurepos.com/000010/index.html`
- `http://kyledurepos.com/000011/index.html`
- `http://kyledurepos.com/000012/index.html`
- `http://kyledurepos.com/000016/index.html`
