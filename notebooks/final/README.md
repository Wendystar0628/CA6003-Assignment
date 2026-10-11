# notebooks/final – assembled deliverable (Stage S11a)

`CA6003_NHANES_Diabetes.ipynb` is the **only graded code artefact**. It is generated, never edited by hand:

```bash
# build only (no outputs; wording says "run top to bottom", default FAST)
.venv/Scripts/python tools/build_final.py

# build + execute in a fresh temporary directory (never in the checkout) and store the outputs
.venv/Scripts/python tools/build_final.py --execute               # FAST  (default, target <= 5 min)
.venv/Scripts/python tools/build_final.py --execute --mode FINAL  # FINAL (5x5 CV, B = 1000, 100 permutations)

# validate an existing notebook only (schema, absolute paths, execution counts, size, code-cell SHA-256,
# front-matter word counts, remaining [TEAM TO FILL] entries - reported as a warning, not a failure)
.venv/Scripts/python tools/build_final.py --validate-only notebooks/final/CA6003_NHANES_Diabetes.ipynb

# team entries: edit notebooks/final/team.json, then update the committed notebook in place
# (only the group/contribution/GenAI cells and the "Section lead" lines change; code cells and outputs are kept)
.venv/Scripts/python tools/build_final.py --fill-team notebooks/final/CA6003_NHANES_Diabetes.ipynb

# replace the opening (front matter) of an existing notebook with the current layout and text from the builder and team.json;
# code cells and outputs are kept (use this after editing CHECKLIST, MARKERS_PATH or the front-matter functions)
.venv/Scripts/python tools/build_final.py --refresh-front notebooks/final/CA6003_NHANES_Diabetes.ipynb

# refresh the FINAL reference numbers (after a FINAL execution has updated results/metrics_*.json)
.venv/Scripts/python tools/build_final.py --make-final-ref

# development helpers
.venv/Scripts/python tools/build_final.py --out some/dir/x.ipynb --sections 00,01,02 --workdir some/run_dir
.venv/Scripts/python tools/build_final.py --execute --download    # test the CDC download path instead of the local raw files
```

An executed build also appends a line to `notebooks/final/runtime_log.md` (mode, total, seconds per section).

## Incremental release (`--assemble`) or full run (`--execute`)

A full FINAL `--execute` takes about 26 min (§7 about 11 min, §9 about 13 min). Each section starts from `new_section()`, re-loads the data and reads upstream results from `results/`, so a change confined to a few sections can be released without re-running the rest:

```bash
# 1. re-run the changed sections in the release mode, in file order (writes results/ and notebooks/executed/<file>.ipynb
#    with a run record: mode, seconds, SHA-256 of the section and of src/*.py, config and governance inputs)
.venv/Scripts/python tools/run_section.py notebooks/sections/06_experiments.py notebooks/sections/07_fairness.py \
    notebooks/sections/08_robustness.py notebooks/sections/09_synthesis.py --mode FINAL
# 2. if reference numbers moved: refresh final_ref.json (A.5)
.venv/Scripts/python tools/build_final.py --make-final-ref
# 3. assemble: current sources; outputs from those runs and, for every other section, from the previous release
.venv/Scripts/python tools/build_final.py --assemble --from-executed 06,07,08,09
```

`--assemble` builds the notebook from the current sources exactly like the build-only path and then fills the outputs. **Sections in `--from-executed`** take them from `notebooks/executed/<file>.ipynb`; **all others** from `--base` (default: the committed release, which must hold FINAL outputs). It fails, naming the section and cell, when a section's code cells are not token-identical to the source of their outputs (comments and blank lines may differ), when an executed notebook has no run record or a different mode, when a module or governance input the section uses changed after its run, or when a section taken from the base uses an inlined file that changed (for example `governance/genai_log.csv` for §0 and §10). Changed or new `src/*.py` and governance file cells get their standard output (`Writing <path>`, or the returned path). The appendix cells are executed in a temp workspace against the current `results/` (A.1 register, A.5 FINAL_REF check). Execution counts are renumbered and absolute paths scrubbed; the title table says which sections were re-run and when; `build_record.json` records `procedure: "assembled"`, the source of every section and the executed-notebook hashes.

Use **`--execute`** for a clean-room run from an empty folder: after changes to §0–§6 or `src/` modules that most sections use, before the final submission if time allows, and as the FAST reproducibility check. Limitation of `--assemble`: re-run sections are executed in the repository (not in a fresh workspace), and a section taken from the base is not checked for reading results that a re-run section changed (re-run all downstream sections; the tool warns when a base section follows a re-run one).

## What the builder does

| Step | Content |
|---|---|
| Front matter | six cells before §0: (1) title with a facts table (group, members, video, data, models, stored run); (2) **Summary** (≤ 250 words; every number read from `results/final_metrics.json` and re-asserted in A.5; the build fails above 250 words); (3) brief requirements → § links; (4) **Team and contributions** from `team.json` (roles, leads and reviewers, video segments, decisions, checks, how the work was shared; open entries shown as **[TEAM TO FILL: …]**); (5) short GenAI declaration; (6) how to read and run (8-item marker's path, conventions, section-level contents). Per-section runtimes are kept in `build_record.json` and `runtime_log.md` |
| § links | front-matter and appendix text writes `@@H:<n>/<title prefix>@@` (resolved to `[§n.m](#anchor)` by heading title, so renumbering is harmless) and `@@A:<exact heading>~<label>@@`; an unresolved link is a build PROBLEM |
| §0.0 Self-contained workspace | creates `ca6003_workspace/` next to the notebook (override: `CA6003_WORKSPACE`), `chdir`s into it and writes the repository files with collapsed cells: `src/*.py` (`%%writefile`), `config/variable_spec.csv`, `requirements.txt`, the governance inputs the sections read or hash-check (`hypotheses.md`, `label_freeze.md`, `S1_scope.md`, `genai_log.csv`, ...), all `governance/register/S*.csv`, the SHA-256 manifest, the 16 CDC codebooks (zip + base64, hash-checked) and the stored records of events a single notebook cannot reproduce (`SEED_RESULTS` in the builder): the pre-registration lock (`results/S6/prereg_lock.json`), the exp-freeze record (`results/S9/exp_freeze_record.json`) and the one-shot hold-out run (`results/S9/holdout_log.json`, `holdout_metrics.csv`, `holdout_pairs.csv`). Then the single global bootstrap (`from src import config as C, plots, results_io as R`, `ROOT`, `new_section()`), then the data cell (local `data/nhanes_2021_2023/raw` above the notebook, or `CA6003_DATA_SRC`, else download from CDC; all 16 files verified against the inlined manifest, mismatches are warnings) |
| Sections | `notebooks/sections/NN_*.py` in file order. The five-line bootstrap of every section is removed; each section after the first starts with `new_section()` (clears the namespace, closes figures) so it runs exactly as it did standalone and no variable can leak between sections. In the first cell a "(Stage Sk)" suffix of the `# §N` heading is dropped and a `**Section lead:**` line (from `team.json`) is added under it. Cell order and content are otherwise untouched |
| Heading scheme | `# §N Title` is taken from the section file; `##` items become `N.M` and `###` items `N.M.k`. An explicit local number is kept (so prose such as "§6.5" or "§4.10" stays valid), unnumbered headings continue after the highest number used in that section. The generated setup is `0.0`. Section numbers must be consecutive (§0…§10; the build fails on a gap). `SPLITS` splits a file that holds two stages into two sections: `02_profiling.py` becomes §2 (Stage S2 checks, item 2.1) and §3 (Stage S3 audit, items 3.1–3.10), with no `new_section()` between them |
| Appendix A | A.1 merged decision register (all `governance/register/S*.csv`, saved as `governance/decision_register.csv` inside the workspace), A.2 locked pre-registration text shown verbatim with SHA-256 and a glossary of the internal names it contains, A.3 pointer to the §10 scoreboard (no duplicate), A.4 references (only works cited somewhere in the notebook; the build reports citations without a reference and references never cited), A.5 reference check (`FINAL_REF`: headline and Summary numbers of the FINAL run from `final_ref.json`, asserted within a FAST/FINAL tolerance in every run), A.6 build record (commit and file hashes), A.7 GenAI use log (`governance/genai_log.csv`) |
| Execution (`--execute`) | `nbclient` with the Windows selector event-loop policy, kernel working directory = a fresh temp dir, `NB_MODE` from `--mode`, local raw files offered through `CA6003_DATA_SRC`. Outputs are scrubbed of absolute paths, per-section runtimes are computed from cell timings |
| Validation | `nbformat.validate`; no absolute path in any source cell or output; `execution_count` sequential 1..n and no error outputs (executed builds); size report (total / images / cell counts); SHA-256 of all code cells (S12: after the video link is added to §0 only markdown may change); `tools/check_repo.py` on the result |

## Contract for section authors

* First cell: markdown `# §N Title` (a "(Stage Sx)" suffix is allowed and dropped by the builder); the numbers of the assembled sections must be consecutive (a split file counts twice, see `SPLITS`).
* Headings that the front matter links to (`CHECKLIST`, `MARKERS_PATH`, `@@H:` tokens in the builder) are found by title prefix: renumbering is free, renaming one of them needs a change in the builder.
* Cite as "Author (Year)", "Author & Author Year" or "Author et al. Year"; every cited work needs an entry in `REFERENCES`.
* The standard bootstrap lines must be present verbatim (they are stripped); any other import in that cell is kept.
* A section may only rely on (a) files created by earlier sections, (b) the inlined inputs listed in `TEXT_INPUTS` / `REGISTER_GLOB` / `SEED_RESULTS` in `tools/build_final.py`, (c) the raw data. If a section reads another repository file before it is created, tell `assembly` (or add the file to the lists) – a fresh run starts from an empty folder.
* Sub-headings: `## Title` or `## k Title` (local number kept) / `### Title`. Use `§N.M` for cross-references.
* No `__file__`, no `git` calls without a fallback, no absolute paths (the builder fails on them).

## Testing protocol

Never execute in the shared checkout. Build and run from a clean export:

```bash
git archive HEAD | tar -x -C <tmp>/copy          # + copy the working-tree tools/build_final.py if it is not committed yet
export CA6003_SOURCE_COMMIT=$(git rev-parse HEAD)   # the export has no .git; recorded in Appendix A.6
cd <tmp>/copy && <repo>/.venv/Scripts/python tools/build_final.py --execute --workdir <tmp>/run
```

The execution directory holds only the notebook-created workspace, so anything a fresh reader would lack shows up as a failure.

## Files

* `CA6003_NHANES_Diabetes.ipynb` – the assembled notebook (stored outputs from a FINAL execution of a clean `git archive` export).
* `build_record.json` – how the committed notebook was produced (`procedure`: full run or `assembled`, with the source of each section's outputs): source commit, mode of the stored outputs, FAST and FINAL runtimes per section, code-cell SHA-256 (S12 markdown-only check), file SHA-256, validation and FINAL_REF results.
* `final_ref.json` – reference values (`REF_SPECS` in the builder, including the numbers quoted in the Summary) for the appendix check; regenerate with `--make-final-ref` after the FINAL run.
* `team.json` – group number, video link, A-D responsibilities, evidence-linked verification records, role-specific AI use, shared human-AI workflow and section leads. Group/matric/video entries remain to be supplied; members confirm their individual participation.
* `runtime_log.md` – one line per executed build.
* `README.md` – this file.

## Team-record update (12 October 2026)

Team entries, the governance README and the GenAI log (seven entries) were updated without re-running the analysis: the embedded copies of the two governance files and the two printed log counts (§0, §10) were synchronised; all analytical code and numerical outputs are unchanged (see `build_record.json`). `governance/team_verification.json` holds 28 automated evidence checks; each member still confirms their own checks.
