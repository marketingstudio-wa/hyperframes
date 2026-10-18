# WA Video Studio

Automated editing pipeline for **WA Construct** and **Home Estimator** videos. Drop in raw footage
or a screen recording, get back finished, branded videos for every platform.

```
raw.mp4 ──► normalize ──► transcribe ──► cut ──► frame + captions ──► cards ──► music + loudness ──► QA
           (30 fps CFR)   (Parakeet,      (fillers,   (16:9 / 9:16 / 1:1,   (intro +     (−14 LUFS,          (contact sheet,
                           local, free)    stutters,   logo, word-by-word    CTA outro)   share copy < 30 MB)  report.json)
                                           long pauses) captions, name strap)
```

## Quick start

```bash
./setup.sh                                   # once per session
cp jobs/TEMPLATE.yaml jobs/my-video.yaml     # edit brand, source, title, formats
python3 vstudio.py jobs/my-video.yaml        # all formats in the job
python3 vstudio.py jobs/my-video.yaml --only vertical
```

Outputs land in `jobs/out/<name>/`:

| File | What it is |
|---|---|
| `<name>_landscape.mp4` / `_vertical.mp4` / `_square.mp4` | Masters (YouTube, Reels/Shorts/TikTok, feed) |
| `*_share.mp4` | Same video under 30 MB, for chat or email |
| `*.srt` | Caption file for platform upload (timed to the finished video) |
| `*_contact.png` | 12-frame contact sheet for a quick visual check |
| `transcript.txt` | What's said in the finished cut |
| `edit_plan.json` | Kept spans and dropped words, in source time — tweak `trim.remove` and re-run |
| `report.json` | Duration, loudness, true peak, black gaps, size, and any warnings |

Re-runs reuse the cached transcription (`work/words.json`), so tweaking a job is fast.

## What it does

- **Trim:** cuts "um / uh / er" fillers and stutters ("the the"), and tightens any pause over
  `silence_max` (0.7 s for HEAI) to a ~0.5 s gap. Joins get 10 ms audio fades so they never click.
  Manual cuts: `trim.remove: [[12.4, 15.0]]` in source seconds. For b-roll with no talking,
  set `trim.mode: none`.
- **Captions and branding:** word-by-word burned-in captions, with the active word in the brand
  accent. Also an optional name strap (`lower_third`), a corner logo (per brand), and intro and
  CTA cards in brand colors and type.
- **Formats:** 16:9, 9:16 and 1:1 from one source. Footage of a different shape is fitted
  per brand: `blur` (blurred fill), `brand` (solid brand color, the HEAI reel layout) or `crop`
  (`crop_x` picks the side).
- **Audio:** an optional music bed, either under the cards only (the HEAI demo rule) or under
  everything at `bed_db`. Two-pass loudness normalization to −14 LUFS, true peak ≤ −1.5 dBTP.

## Brands

Brand profiles live in `brands/*.yaml`; a job can override any key with `brand_overrides:`.

- `heai.yaml` follows the Home Estimator house style: navy `#1a1a2e`, gold `#d4af37`, sand
  `#c9a96e`, Inter, the original logo, no corner logo on full-bleed demos, music under cards only,
  and the approved CTA.
- `waconstruct.yaml` holds **placeholder** colors and CTA. Replace them with the real brand
  values and add `brands/assets/waconstruct-logo.png`. Until the logo exists, a text wordmark
  is used.

## When to use the HyperFrames workflow instead

This pipeline is the fast lane: minutes per video, no hand animation. For a Home Estimator demo
re-edit with a re-voiced presenter, gold highlight boxes, chapter subtitles or name patches, or a
from-scratch motion promo, use the `heai-videos` / `heai-motion-promo` skills (HyperFrames).
You can feed this pipeline's trimmed cut and transcript into them.
