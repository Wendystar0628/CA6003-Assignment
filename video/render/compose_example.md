# Compositing: camera clips into the camera slot, then concatenation

The scenes reserve a camera slot at fixed coordinates (docs/video_plan.md §6.2, §6.3; `Kit.GRID.camera` in `video/kit/kit.js`):

| Layout | Slot (x, y, w × h) | Camera clip treatment |
|---|---|---|
| R (default) | 1344, 168, 480 × 270 | scale to 480 × 270 |
| X | 1344, 690, 480 × 270 | scale to 480 × 270 |
| S | 0, 0, 960 × 1080 | scale to height 1080, crop the centre 960 × 1080 (8:9) |
| F | 0, 0, 1920 × 1080 | scale to 1920 × 1080 |

Two ways to composite. Use **A** for R and X scenes, where nothing in the scene overlaps the slot. Use **B** for F and S scenes, because the lower-third sits on top of the portrait there. B also works for R and X.

Notation: `CAM=C_block_take2.mp4` is the member's continuous take (§9.6), and `OFF=312.4` is the second in that take where this scene starts (from the EDL or cue sheet, §8.3 step 5). Scene durations come from `SCENE.duration`; the leak gate is 34 s.

## A · Overlay the camera on the opaque scene render (R, X)

The scene mp4 has a flat white slot with a 1 px `#E3E7EC` hairline. Scale the camera, place it on the slot, then redraw the hairline over the clip.

```bash
ffmpeg -i video/out/s18_leak_gate.mp4 -ss $OFF -t 34 -i $CAM -filter_complex "\
  [1:v]fps=30,scale=480:270:force_original_aspect_ratio=increase,crop=480:270,setsar=1[cam];\
  [0:v][cam]overlay=x=1344:y=168:eof_action=pass,\
  drawbox=x=1344:y=168:w=480:h=270:color=0xE3E7EC:t=1,format=yuv420p[v]" \
  -map "[v]" -map 1:a -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -shortest video/out/comp_s18_leak_gate.mp4
```

For layout X, use `overlay=x=1344:y=690` and `drawbox=x=1344:y=690:...`.

## B · Camera underneath, scene with alpha on top (F, S, or any layout)

First render the scene with a transparent slot. This writes `video/out/<name>_alpha.mov` (PNG codec, RGBA):

```bash
node video/render/render.mjs video/scenes/<scene>.html --alpha
```

Then build a stage-coloured base, put the camera into the slot, and lay the scene over it. The slot hairline and the lower-third are part of the alpha render, so they end up on top of the portrait.

```bash
# S layout: portrait half, 8:9 centre crop
ffmpeg -ss $OFF -t $DUR -i $CAM -i video/out/<scene>_alpha.mov -filter_complex "\
  color=c=0xF6F7F9:s=1920x1080:r=30:d=$DUR[base];\
  [0:v]fps=30,scale=-2:1080,crop=960:1080,setsar=1[cam];\
  [base][cam]overlay=x=0:y=0[b];\
  [b][1:v]overlay=x=0:y=0:format=auto,format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 \
  video/out/comp_<scene>.mp4
```

For F, use `scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080` and `overlay=0:0`. For R, use `scale=480:270` and `overlay=1344:168`.

## Concatenate the composited scenes

The composited clips share codec, size, frame rate and audio settings, so the concat demuxer can join them without re-encoding:

```bash
# list.txt, in film order
file 'comp_15_simpson.mp4'
file 'comp_16_label.mp4'
file 'comp_17_screening.mp4'
file 'comp_s18_leak_gate.mp4'
...
ffmpeg -f concat -safe 0 -i video/out/list.txt -c copy video/out/block_C.mp4
```

If any clip differs in encoding settings, re-encode during the concat instead:

```bash
ffmpeg -f concat -safe 0 -i video/out/list.txt -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 video/out/block_C.mp4
```

The four blocks (A, B, C, D) are joined the same way. The film has only three cuts between members (§6.3). Final loudness (−16 LUFS, true peak ≤ −1 dBTP, §8.2) is set at the end, either in Resolve or with ffmpeg:

```bash
ffmpeg -i video/out/film.mp4 -c:v copy -af loudnorm=I=-16:TP=-1:LRA=11 -c:a aac -b:a 192k video/out/film_final.mp4
```
