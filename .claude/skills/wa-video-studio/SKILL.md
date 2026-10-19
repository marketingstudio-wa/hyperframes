---
name: wa-video-studio
description: Fast automated editing for WA Construct and Home Estimator (HEAI) videos. Raw footage or a screen recording in; trimmed (fillers, stutters, long pauses), captioned, branded 16:9 / 9:16 / 1:1 videos out, at −14 LUFS with SRTs and a QA report. Use when the user uploads footage and asks to "edit", "clean up", "cut", "caption", "brand", or "make reels/shorts/YouTube versions" for either brand.
---

# WA Video Studio

The pipeline lives in `video-studio/` at the repo root (see `video-studio/README.md`). Run every command from that folder.

1. **Setup (once per session):** `./setup.sh`.
2. **Ask before rendering, in one round** (offer a recommended option first):
   - brand
   - which formats
   - intro headline/hook and CTA (HEAI: approved lines only, no "free" language, "HomeEstimator.ai" only in the CTA)
   - music (uploaded file or none)
   - name strap
   - whether the footage is talking (`trim.mode: speech`) or b-roll (`none`)
3. **Write the job:** copy uploads into `inbox/`, then write `jobs/<name>.yaml` from `jobs/TEMPLATE.yaml`.
4. **Run:** `python3 vstudio.py jobs/<name>.yaml`.
5. **Check before delivering:**
   - Read `report.json`. Fix any `warnings`.
   - Look at each `*_contact.png`, plus a frame from the intro, the body and the outro.
   - Read `transcript.txt` for ASR errors in the captions. Fix a wrong word by editing `work/words.json`, then re-run (the transcript is cached).
6. **Deliver:**
   - send the `*_share.mp4` files and the `.srt`
   - give the master paths
   - add one line on anything to double-check

## Rules

- **Brand:** `brands/waconstruct.yaml` follows the WA Construct Blog & Creative Context v1.0: Roboto, navy + white left-aligned cards with the white logo bottom-left, logo never boxed and never bare on footage (no corner logo), block-letter captions. WA Construct videos never mention pricing and never connect WA Construct to Home Estimator.
- **Not for HEAI demo re-edits:** a re-voiced presenter, highlight boxes, chapter subtitles or name patches go through the `heai-videos` skill (HyperFrames). This pipeline can produce the trimmed cut and transcript that feed it.
- **Large files:** keep media out of git (`inbox/`, `jobs/out/` and `models/` are gitignored).
