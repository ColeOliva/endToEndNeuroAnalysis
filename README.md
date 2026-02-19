# End-to-End EEG Analysis Pipeline (Open Dataset)

## Project Summary
This repository is a planning-first, end-to-end cognitive neuroscience project using an open BIDS-formatted EEG dataset.

**Working title:** Decoding stimulus category from EEG using machine learning

The goal is to demonstrate a full neuroscience workflow equivalent to MSc-level independent work: data access, preprocessing, feature extraction, statistical/ML modeling, and clear scientific reporting.

## Research Question
Can stimulus category be decoded from task EEG signals above chance level using interpretable features derived from standard preprocessing and epoch-based analysis?

## Hypothesis
After BIDS-compliant preprocessing and epoch extraction, EEG-derived features (time-domain and/or frequency-domain) will enable classification of stimulus categories at performance significantly above chance under cross-validation.

## Dataset Choice (BIDS)
**Primary source:** OpenNeuro (BIDS-formatted EEG dataset)

### Why this choice
- OpenNeuro datasets are already organized in BIDS, reducing data-friction.
- Public accessibility and reproducibility are strong for admissions and portfolio review.
- Multiple EEG task paradigms (e.g., oddball, motor imagery, visual category tasks) support classification questions.

### Dataset selection criteria (final pick)
1. BIDS-compliant EEG with clear event labels (`events.tsv`).
2. Sufficient number of trials per class for balanced modeling.
3. Moderate size (fast local iteration on a personal machine).
4. Metadata completeness (sampling rate, channel info, task description).

## Planned End-to-End Pipeline

### 1) Data Loading (BIDS)
- Parse BIDS dataset structure (subjects/sessions/runs).
- Read EEG recordings and events with MNE-BIDS workflow.
- Build analysis table linking trial labels, subject IDs, and run info.

### 2) Preprocessing
- Re-reference strategy (common average or task-appropriate reference).
- Band-pass filtering (task-appropriate range).
- Line-noise handling (notch if needed).
- Artifact handling (bad channel marking, ICA/SSP if justified).
- Epoching around stimulus events with baseline correction.
- Quality checks and exclusion criteria tracked in logs.

### 3) Feature Engineering + Analysis
- Feature options:
  - ERP/time-window means across selected channels
  - Band-power features (e.g., theta/alpha/beta)
  - Optional connectivity/complexity features (if scope allows)
- Model options:
  - Baseline: logistic regression (interpretable)
  - Optional comparison: SVM / random forest
- Validation:
  - Subject-wise or stratified cross-validation (final scheme declared before running)
  - Primary metric: balanced accuracy or ROC-AUC
  - Null/chance comparison and confidence intervals where possible

### 4) Visualization
- Data quality plots: trial counts, rejected epochs, channel diagnostics
- Neuro plots: evoked responses/topomaps or band-power maps
- ML plots: confusion matrix, ROC, feature importance coefficients
- Summary figure set suitable for 3–5 page report

### 5) Reporting
- Short paper-style report (3–5 pages):
  1. Question + hypothesis
  2. Dataset + preprocessing methods
  3. Analysis + validation strategy
  4. Results + visualizations
  5. Limitations + future work

## Tech Stack
- Python
- `numpy`, `pandas`
- `mne` (+ `mne-bids`)
- `scikit-learn`
- `matplotlib`, `seaborn`
- Optional: `nilearn` (if extending to fMRI later)

## Proposed Repository Structure

```text
endToEndNeuroAnalysis/
├─ README.md
├─ report/
│  ├─ outline.md
│  └─ figures/
├─ data/
│  ├─ raw/                # not committed (BIDS dataset)
│  └─ derivatives/        # preprocessing outputs
├─ notebooks/
│  ├─ 01_dataset_qc.ipynb
│  ├─ 02_preprocessing.ipynb
│  ├─ 03_feature_engineering.ipynb
│  └─ 04_modeling_and_results.ipynb
├─ src/
│  ├─ config.py
│  ├─ io_bids.py
│  ├─ preprocess.py
│  ├─ features.py
│  ├─ modeling.py
│  └─ visualization.py
├─ outputs/
│  ├─ tables/
│  ├─ figures/
│  └─ metrics/
├─ requirements.txt
└─ .gitignore
```

## Scope Guardrails (Planning Phase)
- Start with **one** dataset, **one** primary question, **one** baseline model.
- Add complexity only after baseline reproducibility is achieved.
- Predefine preprocessing and validation decisions before running final analyses.

## Milestone Plan (High-Level)
1. Finalize dataset ID and class labels.
2. Implement data loading + QC summary.
3. Implement preprocessing and epoch pipeline.
4. Implement features + baseline model + CV.
5. Generate final figures and complete 3–5 page report.

## Definition of Success
- Reproducible pipeline from BIDS input to final figures/metrics.
- Classification performance above chance with transparent validation.
- Clear write-up of methods, results, limitations, and next steps.
