# Compositing: one block = scenes + one camera take + burned captions

`node video/render/compose_block.mjs <n>` does all of this. The commands below are what it runs, for doing it by hand or debugging. Run them from `video/`; `compose_block` uses that folder as its working directory, so filter paths need no Windows escaping.

The film has one layout, and the speaker sits in one fixed picture-in-picture (PiP) slot for the whole film (`Kit.GRID.camera`):

| Element | x, y | Size | Drawn by |
|---|---|---|---|
| PiP | 1416, 748 | 384 × 216 | camera take, overlaid by ffmpeg |
| PiP hairline | 1415, 747 | 386 × 218 (1 px outside) | the scene render (kit) |
| Name tag | 1416, 656 | 384 × 84 | the scene render (kit) |
| Caption zone | 96, 872 | 1272 × 116 | libass (`subtitles/block_<n>.ass`) |

Each member records one continuous take, so a block gets exactly **one overlay at fixed coordinates**. There is no per-scene offset, no alpha render, and no drawbox.

Notation:
- `n=2` is the block (1 = scenes 01–07, 2 = 08–13, 3 = 14–19, 4 = 20–26);
- `DUR=134` is the block length (the sum of its scene durations in `timeline/timeline.json`);
- `OFF=2.4` is the second in the take where the block starts.

## 1 · Concatenate the block's scene renders

```bash
# out/list_block_2.txt, in timeline order
file 's08_missing_codes.mp4'
file 's09_erased_positives.mp4'
...
ffmpeg -f concat -safe 0 -i out/list_block_2.txt -c copy out/scenes_block_2.mp4
```

All scene renders share the same codec settings (H.264, yuv420p, 30 fps, BT.709), so the concat is a stream copy.

## 2 · Overlay the take, burn the captions, encode

```bash
ffmpeg -i out/scenes_block_2.mp4 -ss $OFF -t $DUR -i takes/block_2.mp4 -filter_complex "\
  [1:v]fps=30,scale=384:216:force_original_aspect_ratio=increase,crop=384:216,setsar=1,setpts=PTS-STARTPTS[cam];\
  [0:v][cam]overlay=x=1416:y=748:eof_action=pass,\
  ass=subtitles/block_2.ass:fontsdir=out/fonts,format=yuv420p[v]" \
  -map "[v]" -map 1:a:0 -t $DUR -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart out/block_2.mp4
```

- The take is scaled to cover 384 × 216 and centre-cropped, so frame it as a chest-up shot.
- `eof_action=pass` shows the grey slot if the take is shorter than the block.
- The take's audio is the narration. Captions are burned last, so they sit above everything.

**No take yet (placeholder).** Use a neutral grey 384 × 216 with a small "camera" label and silent audio. The name tag is already in the scene render.

```bash
ffmpeg -i out/scenes_block_2.mp4 -f lavfi -t $DUR -i color=c=0xC9CFD5:s=384x216:r=30 \
  -f lavfi -t $DUR -i anullsrc=r=48000:cl=stereo -filter_complex "\
  [1:v]drawtext=fontfile=out/fonts/IBMPlexSans-400.ttf:text=camera:fontsize=24:fontcolor=0x15202B@0.6:x=(w-tw)/2:y=(h-th)/2,setsar=1[cam];\
  [0:v][cam]overlay=x=1416:y=748:eof_action=pass,ass=subtitles/block_2.ass:fontsdir=out/fonts,format=yuv420p[v]" \
  -map "[v]" -map 2:a:0 -t $DUR -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 out/block_2.mp4
```

`out/fonts/` holds IBM Plex Sans TTFs made by `render/fonts.mjs` from the `@fontsource/ibm-plex-sans` npm package. libass needs local font files; the scenes themselves load the fonts from Google Fonts in Chrome.

## 3 · The film

```bash
# out/list_film.txt: block_1.mp4 … block_4.mp4
ffmpeg -f concat -safe 0 -i out/list_film.txt -c:v copy -af loudnorm=I=-16:TP=-1:LRA=11 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart out/film.mp4
```

This is `node video/render/compose_film.mjs`. It also copies `subtitles/full.srt` to `out/film.srt` for YouTube. The film has three cuts between members, at the block boundaries.

## After recording

1. Put each take at `video/takes/block_<n>.mp4`, and its start offset in `video/subtitles/overrides.json` → `takes`.
2. Put the measured scene durations into `video/timeline/timeline.json`, and set the speaking windows or caption times per scene in `overrides.json` → `scenes`.
3. Re-render the scenes. Their cues come from the same word clock, so they move with the captions. Then run `compose_block.mjs` for each block and `compose_film.mjs`.
