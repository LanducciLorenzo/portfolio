# False memories and cognitive style: a reproducible reanalysis of my MSc thesis

**Lorenzo Landucci** · MSc thesis, University of Florence (2026) · supervisor Prof. Stefania Righi

The thesis tested whether **presentation modality** (pictures, concrete words, abstract words) and **visual-verbal
cognitive style** (Paivio's Individual Differences Questionnaire) affect false memories in the
Deese-Roediger-McDermott (DRM) paradigm (N = 130). The original analyses were run in SPSS.
This repository redoes them in Python as a reproducible pipeline and extends them.

## What the pipeline does
1. **Replication** – 3 (condition, within) × 2 (high vs low visualisers, between) mixed ANOVAs on recall and
   recognition (hits, critical lures, false alarms), Greenhouse-Geisser correction, Bonferroni follow-ups:
   the same analyses as the thesis.
2. **Extension: signal detection.** The thesis interpreted the lower false recognition of pictures in high
   visualisers as a *stricter decision criterion*. Signal detection separates sensitivity (d′) from response
   criterion (c), so this interpretation can be tested directly.
3. **Extension: continuous cognitive style.** Correlations with the Paivio visual score avoid the information
   lost by a median split.

## Why a custom ANOVA implementation
The mixed ANOVA is written in NumPy/SciPy with the contrast (multivariate) approach used by SPSS GLM,
giving Type III sums of squares also with unequal group sizes. It is checked in `tests/test_stats.py` against:
an independent regression model, textbook formulas, t-tests in the cases where they are equivalent,
known signal-detection values, and simulations of real effects and of the false positive rate.

## Use
```
pip install numpy pandas scipy matplotlib openpyxl      # + pyreadstat for SPSS .sav files
python tests/test_stats.py                              # checks
python run_analysis.py --demo                           # pipeline on simulated data
python run_analysis.py data/thesis_data.csv             # real data (.csv, .xlsx or .sav)
```
Data format: one row per participant, see `data/data_template.csv` and `config.py`.
Results: `output/results.md` (APA-style report), `output/anova_table.csv`, figures.

## Data
The original data are not included (participants' privacy). `simulate_thesis_data.py` creates a fake dataset
with the same structure, used only to test the pipeline: its results have no scientific value.
