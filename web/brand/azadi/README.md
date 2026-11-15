# azadi.asia identity kit

Generated from map data by `build/build_azadi_brand.py` (marks, lockups) and `build/build_azadi_social.py` (social kit).
Palette: ink #0d0d0f, paper #f3eee2, red #a30f20. Type: Cormorant Garamond (headlines), Source Sans 3 (text),
Noto Nastaliq Urdu. All free fonts (Google Fonts, SIL OFL).

## Use
| File | Where | Size |
|---|---|---|
| social/profile-instagram.png | Instagram profile picture (circular crop safe) | 1080 x 1080 |
| social/profile-facebook.png | Facebook page profile picture | 720 x 720 |
| social/profile-reverse.png | dark variant | 1080 x 1080 |
| social/facebook-cover.png | Facebook page cover (content kept in the centre for phone crops) | 1640 x 624 |
| social/facebook-event-cover.png | Facebook event cover | 1920 x 1005 |
| social/post-template-ink.png, post-template-paper.png | Instagram/Facebook 4:5 posts | 1080 x 1350 |
| social/story-template.png | stories and reels covers | 1080 x 1920 |
| social/highlight-*.png | Instagram highlight covers: essays, kashmir, labour, climate, energy, air, solidarity, maps | 1080 x 1080 |
| azadi-world*, azadi-rivers*, azadi-star* | marks and lockups (SVG and PNG; light, paper, reverse, one colour) | 512 / 1700 x 512 |
| favicon.svg | site icon | 64 |

## New posts from text
Write `posts.json`: `[{"slug": "aac-committees", "kicker": "Kashmir", "headline": "...", "deck": "...", "source": "...", "theme": "ink"}]`
then `python build/build_azadi_social.py posts.json`; each post renders to `social/post-<slug>.png`.
The two template posts carry layout examples only; each real post's text should be its own.
