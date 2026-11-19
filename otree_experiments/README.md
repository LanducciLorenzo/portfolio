# Online experiments in oTree – Lorenzo Landucci

One oTree project with two experiments and Python analysis scripts.
Built with the help of AI coding tools, which I use to learn Python and oTree; the research questions and design choices are my own.

| Folder | Contents |
|---|---|
| `pgg_inequality/` | Experiment 1: public goods game (inequality and cooperation) |
| `drm_intro/`, `drm_study/`, `drm_distractor/`, `drm_test/`, `drm_questionnaire/` | Experiment 2: false memories in the DRM paradigm, in 5 parts |
| `drm_common/` | Word lists, DRM logic and questionnaire (file to be filled in) |
| `analysis/` | Python analysis scripts and simulated data to test them |
| `tests/` | Automated tests of the DRM logic |
| `_static/drm_pictures/` | Pictures for the "pictures" condition (to be added) |

---

## Experiment 1 – Public goods game

**Question:** does inequality in initial endowments reduce cooperation?

**2×2 design:**
- **Equal** endowments (20, 20, 20, 20) or **unequal** endowments (10, 10, 30, 30). The group total is always 80.
- **Fixed** groups for all rounds (partner) or **new** groups every round (stranger).

Groups of 4, 10 rounds, multiplier 1.6, other members' endowments visible. Each player keeps the same endowment in every round, also when the group changes.

**Hypotheses**
1. With unequal endowments, average cooperation (share of the endowment contributed) is lower.
2. Players with a high endowment contribute a lower share of their endowment.
3. With fixed groups, cooperation declines less over the rounds.

**Features**
- Comprehension questions before starting: wrong answers must be corrected before continuing.
- 120-second limit per decision: a player who does not decide contributes 0 and is flagged (`timed_out`), so the group is never stuck.
- History of previous rounds on the results page.
- Final questionnaire (age, gender, strategy) and a payment page with total earnings in euros.
- Variable `is_high_endowment` to compare high- and low-endowment players directly.
- Points have 2 decimals, so the project share is not rounded (e.g. 13 × 1.6 / 4 = 5.2, not 5).

---

## Experiment 2 – False memories (online DRM)

**Question:** do false memories change with presentation modality (written words, spoken words, pictures) and with visual-verbal cognitive style?

**Procedure (about 20 minutes)**
1. Consent, demographics and, for the auditory condition only, an audio check.
2. **Study:** 6 lists of 12 items, one every 2 seconds (1.5 s presentation + 0.5 s blank). The participant presses Start, then the list runs by itself.
3. **Free recall** after each list (60 seconds), with automatic scoring: correct words and intrusion of the critical lure.
4. **Distractor:** 2 minutes of arithmetic, checked on the server.
5. **Recognition test:** 48 words, each judged old/new (F/J keys) with confidence from 1 to 4 and response time.
6. Visual-verbal questionnaire, attention check, awareness questions and debriefing.

**Materials and counterbalancing**
- 12 classic DRM lists (Roediger & McDermott, 1995), to be checked against published norms (Stadler et al., 1999) before a real study.
- Each participant studies 6 lists (set A or B, alternated). The other 6 serve as controls: their critical lures measure baseline false alarms.
- List order and test-item order randomised for each participant.
- Modality assigned in a balanced way: each modality × list-set combination is filled equally.

**Main measures (computed automatically)**
- `p_old_studied`: correct recognitions
- `p_old_critical_lure`: **false memories**
- `p_old_control_lure`: baseline
- `false_memory_corrected` = false memories − baseline
- `visual_minus_verbal`: cognitive-style index from the questionnaire

**Robustness**
- Every test answer is saved on the server at once: if the page reloads, the test resumes from the right word without losing data.
- Double clicks and late answers are ignored.
- The number of times the participant switches tab during the lists is recorded (`page_hidden_count`).
- "Long" export (one row per answer) from Data → Custom export of `drm_test`.

**Before a real study:**
1. Insert the questionnaire items in `drm_common/questionnaire_items.py` (currently placeholders), only with permission to use them.
2. For the "pictures" condition, add one picture per word to `_static/drm_pictures/`, named after the word (e.g. `bed.png`). If a picture is missing, the written word is shown.
3. Replace the consent and debriefing texts with those approved for the study.
4. The auditory condition uses the browser's speech synthesis (works well in Chrome, Edge and Safari on desktop). For a real study, recorded audio files are better.

---

## How to run it

Requires **Python 3.10, 3.11 or 3.12**.
```
pip install otree
otree devserver
```
Then open **http://localhost:8000** and choose a demo session.

**Automated tests with bots:**
```
otree test pgg_unequal_stranger
otree test drm_memory
python tests/test_logic.py
```

## Python analysis

Try the scripts on simulated data:
```
pip install pandas scipy matplotlib
python analysis/simulate_data.py
python analysis/drm_analysis.py --demo
python analysis/pgg_analysis.py --demo
```
With real data, download the exports from the oTree Data page:
```
python analysis/drm_analysis.py drm_test_custom_export.csv all_apps_wide.csv
python analysis/pgg_analysis.py pgg_inequality.csv
```
Figures and tables are saved in `analysis/output/`. The data in `analysis/demo_data/` are **simulated** and only serve to test the scripts.

## What has been checked
- Checked: the logic of both experiments (condition assignment, payoffs, scoring, saving and resuming the test), the pages' JavaScript in a simulated browser, the analysis scripts.
- **Not yet checked:** running inside a live oTree server and the visual layout of the pages (requires `otree devserver` on a local machine).

(An Italian version of this file is in `LEGGIMI.md`.)
