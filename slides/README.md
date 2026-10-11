# Slides and video materials (S11b)

| File | Purpose |
|---|---|
| `storyboard.md` | 12-minute plan: slide ids, time budgets, titles, figures, one-line captions, speaker notes, declared numbers, cut order |
| `deck.md` | Marp slide deck (16:9) that implements the storyboard; one figure per slide, notes in HTML comments |
| `check_numbers.py` | Verifies every number in both files against `results/S10/numbers_on_slides.csv` |

Presenter assignment is decided by the team and is not planned in these files.

## Render

Figures are referenced as `../figures/<name>.png`, so keep `deck.md` inside `slides/`.

**VS Code.** Install the extension "Marp for VS Code", open `slides/deck.md`, use the preview, then the Marp icon in the editor title bar and "Export Slide Deck" (PDF, PPTX or HTML). Presenter notes are the HTML comments under each slide.

**Marp CLI** (needs Node.js; PDF, PPTX and PNG export need Chrome or Edge installed):

```bash
npx @marp-team/marp-cli slides/deck.md --html --allow-local-files -o slides/deck.html
npx @marp-team/marp-cli slides/deck.md --pdf --pdf-notes --allow-local-files -o slides/deck.pdf
npx @marp-team/marp-cli slides/deck.md --pptx --allow-local-files -o slides/deck.pptx
npx @marp-team/marp-cli slides/deck.md --images png --allow-local-files -o slides/png/s.png
```

`--allow-local-files` is required for the figures. Do not commit rendered files. The deck was rendered with Marp CLI to PNG and HTML to check layout (26 slides, 22 figures).

**Number check** (run before every rehearsal and after any change to results):

```bash
.venv/Scripts/python slides/check_numbers.py
```

It must print `OK`. If a number changes in `results/S10/numbers_on_slides.csv`, edit the same text in `storyboard.md` and `deck.md` (the check also requires the two files to stay identical in title, caption, footer, notes and figure).

## Timing

Target 11:20, cap 11:40, hard limit 12:00 for the upload.

| Segment | Window | Budget (s) | Slides |
|---|---|---|---|
| V1 Scope and design | 0:00–1:30 | 90 | V0, V1.1 to V1.4 |
| V2 Cost of naive cleaning | 1:30–2:15 | 45 | V2.1 |
| V3 Leakage gate | 2:15–3:30 | 75 | V3.1, V3.2 |
| V4 Redundancy and skewness | 3:30–4:30 | 60 | V4.1 to V4.3 |
| V5 Fallacies | 4:30–6:00 | 90 | V5.1, V5.2 |
| V6 Label and measurement bias | 6:00–8:30 | 150 | V6.1 to V6.5 |
| V7 Experiments synthesis | 8:30–10:15 | 105 | V7.1 to V7.5 |
| V8 Conclusions, limitations, GenAI | 10:15–11:20 | 65 | V8.1 to V8.3 |
| Total | 0:00–11:20 | 680 | 26 |

Per-slide budgets, with the clock at each slide start, are in `storyboard.md`. Speaker notes are written at about 2.2 words per second, so reading them at a normal pace fits the budget.

## Rehearsal loop (L6)

Start after content freeze. Rehearsal passes when the total is between 11:00 and 11:40 and every segment is within 10 percent of its budget. Two consecutive passes end the loop; at most two rounds.

1. Run the deck in presentation mode with a stopwatch; note the time at each segment boundary.
2. If a segment is over, shorten the notes first. If the total is still over 11:40, apply the cut list below in order and stop when it fits.
3. Re-run the number check after any wording change.

## Cut priority

| Order | Cut | Saves (s) | Slide |
|---|---|---|---|
| 1 | Asian standardisation clause shortened to one sentence | 10 | V5.1 |
| 2 | 68% blood-test annotation | 5 | V6.2 |
| 3 | ADA-lite sentence | 5 | V7.3 |
| 4 | Governance detail (response rates, availability-rule wording, NCHS decomposition) | 10 | V1.1, V1.3 |

Reserve cuts beyond the process document, only with team agreement: calibration sentence in V6.5 (5 s), robustness slide V7.5 folded into V7.4 (10 s).

Never cut: leakage gate (V3.1, V3.2), redundancy and skewness (V4.1 to V4.3), minimal versus systematic (V7.2), label bias (V6.1 to V6.4), contributions (V8.3).

## To fill in before recording

- Group number: `[N]` in the title-slide footer (`deck.md`, `storyboard.md` V0) and in the YouTube title.
- Contribution table and GenAI sentence on V8.3 (template). The GenAI sentence must match the declaration in notebook section 0 and `governance/genai_log.csv`.
- Segment-to-member assignment, decided by the team.

## Recording checklist

Rules from the assignment: one video, at most 12 minutes, all members on camera, public YouTube link with the group number.

1. Ask the lecturer whether several recorded parts joined by hard cuts count as a single continuous video. Decide before recording. If not allowed, record once (Zoom group recording with screen share, every member visible).
2. Each member appears on camera while presenting their segment; show a name caption when a member first speaks.
3. Export `deck.pdf` as a backup and present from the deck in full-screen at 1080p or higher. Keep presenter notes off the shared screen.
4. Check audio levels and background noise with a test clip. No copyrighted music.
5. Keep the final length between 11:00 and 11:40. Confirm the exported file is under 12:00.
6. Upload to YouTube as Public. Put the group number in title and description. Wait until processing finishes.
7. Open the link in a private window and on a second device; confirm it plays with sound and shows all members.
8. Record the link in notebook section 0 (markdown only) and in the submission record.

## Known gaps

- Plot text is small at slide size on tall figures (`S4_spearman_clustermap`, `S4_dag`, `S8_group_tpr`, `S4_binned_logodds`, right panel of `S7_coef_forest`). The slide caption carries the message; the presenter should point at the relevant part, or the figure owner can re-export larger fonts.
- There is no figure of the triglyceride distribution. The skewness slide (V4.3) uses the HbA1c outlier-fence figure and quotes the skewness values in the caption.
- Numbers not in `numbers_on_slides.csv` are not used on any slide (for example subgroup sizes, the 0.70 and 0.52 TPR of diagnosed and undiagnosed positives, the Asian observed-to-expected ratio of 1.35). Add them to the CSV first if the team wants them shown.
