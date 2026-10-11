# notebooks/final – assembled deliverable (Stage S11a)

`CA6003_NHANES_Diabetes.ipynb` is the **only graded code artefact**. It is generated, never edited by hand:

```bash
# build only (no outputs; wording says "run top to bottom", default FAST)
.venv/Scripts/python tools/build_final.py

# build + execute in a fresh temporary directory (never in the checkout) and store the outputs
.venv/Scripts/python tools/build_final.py --execute               # FAST  (default, target <= 5 min)
.venv/Scripts/python tools/build_final.py --execute --mode FINAL  # FINAL (5x5 CV, B = 1000, 100 permutations)

# validate an existing notebook only (schema, absolute paths, execution counts, size, code-cell SHA-256)
.venv/Scripts/python tools/build_final.py --validate-only notebooks/final/CA6003_NHANES_Diabetes.ipynb

# refresh the FINAL reference numbers (after a FINAL execution has updated results/metrics_*.json)
.venv/Scripts/python tools/build_final.py --make-final-ref

# development helpers
.venv/Scripts/python tools/build_final.py --out some/dir/x.ipynb --sections 00,01,02 --workdir some/run_dir
.venv/Scripts/python tools/build_final.py --execute --download    # test the CDC download path instead of the local raw files
```

An executed build also appends a line to `notebooks/final/runtime_log.md` (mode, total, seconds per section).

## What the builder does

| Step | Content |
|---|---|
| Front matter | title, group / members / video placeholders (`[TODO: ...]`), contribution-table template, GenAI declaration (table rendered from `governance/genai_log.csv` + the statement that no LLM or complex model is in the pipeline), reading guide, run-mode and runtime note (runtime table filled in after execution), generated contents list |
| §0.0 Self-contained workspace | creates `ca6003_workspace/` next to the notebook (override: `CA6003_WORKSPACE`), `chdir`s into it and writes the repository files with collapsed cells: `src/*.py` (`%%writefile`), `config/variable_spec.csv`, `requirements.txt`, the governance inputs the sections read or hash-check (`hypotheses.md`, `label_freeze.md`, `S1_scope.md`, `genai_log.csv`, ...), all `governance/register/S*.csv`, the SHA-256 manifest, the 16 CDC codebooks (zip + base64, hash-checked) and the stored records of events a single notebook cannot reproduce (`SEED_RESULTS` in the builder): the pre-registration lock (`results/S6/prereg_lock.json`), the exp-freeze record (`results/S9/exp_freeze_record.json`) and the one-shot hold-out run (`results/S9/holdout_log.json`, `holdout_metrics.csv`, `holdout_pairs.csv`). Then the single global bootstrap (`from src import config as C, plots, results_io as R`, `ROOT`, `new_section()`), then the data cell (local `data/nhanes_2021_2023/raw` above the notebook, or `CA6003_DATA_SRC`, else download from CDC; all 16 files verified against the inlined manifest, mismatches are warnings) |
| Sections | `notebooks/sections/NN_*.py` in file order. The five-line bootstrap of every section is removed; each section after the first starts with `new_section()` (clears the namespace, closes figures) so it runs exactly as it did standalone and no variable can leak between sections. Cell order and content are otherwise untouched |
| Heading scheme | `# §N Title` is taken from the section file; `##` items become `N.M` and `###` items `N.M.k`. An explicit local number is kept (so prose such as "§6.5" or "§4.10" stays valid), unnumbered headings continue after the highest number used in that section. The generated setup is `0.0` |
| Appendix A | A.1 merged decision register (all `governance/register/S*.csv`, saved as `governance/decision_register.csv` inside the workspace), A.2 pre-registration text with SHA-256, A.3 hypothesis scoreboard (S10 file if present, else S7), A.4 references, A.5 reference check (`FINAL_REF`: headline numbers of the FINAL run from `final_ref.json`, asserted within a FAST/FINAL tolerance in every run), A.6 build record (commit and file hashes) |
| Execution (`--execute`) | `nbclient` with the Windows selector event-loop policy, kernel working directory = a fresh temp dir, `NB_MODE` from `--mode`, local raw files offered through `CA6003_DATA_SRC`. Outputs are scrubbed of absolute paths, per-section runtimes are computed from cell timings |
| Validation | `nbformat.validate`; no absolute path in any source cell or output; `execution_count` sequential 1..n and no error outputs (executed builds); size report (total / images / cell counts); SHA-256 of all code cells (S12: after the video link is added to §0 only markdown may change); `tools/check_repo.py` on the result |

## Contract for section authors

* First cell: markdown `# §N Title (Stage Sx)` with `N` strictly increasing over the section files.
* The standard bootstrap lines must be present verbatim (they are stripped); any other import in that cell is kept.
* A section may only rely on (a) files created by earlier sections, (b) the inlined inputs listed in `TEXT_INPUTS` / `REGISTER_GLOB` / `SEED_RESULTS` in `tools/build_final.py`, (c) the raw data. If a section reads another repository file before it is created, tell `assembly` (or add the file to the lists) – a fresh run starts from an empty folder.
* Sub-headings: `## Title` or `## k Title` (local number kept) / `### Title`. Use `§N.M` for cross-references.
* No `__file__`, no `git` calls without a fallback, no absolute paths (the builder fails on them).

## Testing protocol

Never execute in the shared checkout. Build and run from a clean export:

```bash
git archive HEAD | tar -x -C <tmp>/copy          # + copy the working-tree tools/build_final.py if it is not committed yet
cd <tmp>/copy && <repo>/.venv/Scripts/python tools/build_final.py --execute --workdir <tmp>/run
```

The execution directory holds only the notebook-created workspace, so anything a fresh reader would lack shows up as a failure.

## Files

* `CA6003_NHANES_Diabetes.ipynb` – the assembled notebook (committed by the lead once executed with FINAL outputs).
* `final_ref.json` – reference values (`REF_SPECS` in the builder) for the appendix check; regenerate with `--make-final-ref` after the FINAL run.
* `runtime_log.md` – one line per executed build.
* `README.md` – this file.
