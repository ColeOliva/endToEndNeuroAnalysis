# Final Report Draft: End-to-End EEG Oddball Decoding

## Title
End-to-End EEG-Based Decoding of Visual Oddball Stimulus Class Using Subject-Wise Cross-Validation

## Abstract
We built and evaluated an end-to-end EEG analysis pipeline on OpenNeuro dataset ds007056 (PURSUE P300 Visual Oddball). The finalized run processed 285 EEG recordings (286 event files total; 1 EEG file skipped due to read/processing failure) and produced 58,963 trial-level feature rows. Using subject-wise GroupKFold (5 folds) and a class-weighted logistic regression model with subject-normalized feature expansion and fold-wise threshold optimization, the model achieved mean balanced accuracy of 0.6081 (baseline: 0.5000) and ROC AUC of 0.6467. Compared with the pre-upgrade baseline, post-upgrade performance improved by +0.0300 balanced-accuracy points and +0.0385 ROC AUC, with substantial false-positive reduction.

## 1. Introduction
### 1.1 Research Question
Can EEG-derived event-locked and spectral features decode target vs non-target stimulus classes above chance under strict subject-wise validation?

### 1.2 Hypothesis
A lightweight EEG feature set (ERP windows + waveform descriptors + bandpower), augmented by subject-wise feature normalization, should provide reliable above-chance decoding under GroupKFold.

## 2. Data
### 2.1 Dataset
- Source: OpenNeuro
- Accession: ds007056 (v1.1.1)
- Task: VisualOddball
- Labels: Frequent_NonTarget, Rare_Target
- Label field: value (mapped via `task-VisualOddball_events.json`)

### 2.2 Cohort and Coverage
- Event files processed: 286
- EEG files processed: 285
- EEG files skipped: 1
- Subjects in CV: 285
- Trial rows: 58,963
- Class counts: Frequent_NonTarget = 47,171; Rare_Target = 11,792

## 3. Methods
### 3.1 Pipeline
1. BIDS indexing and integrity checks
2. EEG preprocessing (bandpass and baseline handling in feature extraction workflow)
3. Event-locked feature extraction
4. Subject-wise cross-validated modeling
5. Figure and report generation

### 3.2 Features
- ERP window means: N1, P2, P3
- Waveform features: peak positive, peak negative, peak-to-peak, mean absolute amplitude, standard deviation, absolute AUC
- Bandpower features: theta, alpha, beta (+ relative bandpower)
- Subject normalization: enabled (z-transformed counterparts for each base feature group)
- Feature groups: 15 base + 15 z-normalized

### 3.3 Modeling
- Model: Logistic Regression (`class_weight=balanced`)
- Validation: GroupKFold (n=5), grouped by subject
- Threshold strategy: `train_balanced_optimal` per fold
- Primary metric: balanced accuracy
- Secondary metric: ROC AUC
- Baseline comparator: majority class (balanced accuracy = 0.5)

## 4. Results
### 4.1 Primary Outcomes
- Mean balanced accuracy (model): 0.6081258625383577
- Mean balanced accuracy (baseline): 0.5
- Lift over baseline: +0.10812586253835765
- ROC AUC: 0.6467288195979253

### 4.2 Fold Stability
Fold-wise model balanced accuracy range: 0.598020 to 0.618041.

### 4.3 Confusion Matrix (OOF)
- TN: 29,058
- FP: 18,113
- FN: 4,714
- TP: 7,078

### 4.4 Upgrade Impact
Relative to pre-upgrade baseline:
- Balanced accuracy: +0.0300191153169562
- ROC AUC: +0.0384999988638006
- TP: +28, FN: -28, FP: -2721, TN: +2721

## 5. Discussion
The finalized pipeline demonstrates stable above-chance decoding on a large multi-subject cohort under subject-wise validation. Subject-normalized feature expansion materially improved separability, and threshold optimization provided additional calibration gains. The largest practical gain is the reduction in false positives while maintaining/improving target sensitivity.

## 6. Limitations
- One EEG file was skipped, leaving 285 modeled subjects.
- Linear model and handcrafted features may underfit nonlinear structure.
- Single-dataset evaluation; external generalization is not yet tested.

## 7. Conclusion
The project now has a reproducible end-to-end baseline with meaningful decoding performance improvements after feature and threshold upgrades. This constitutes a strong foundation for manuscript-ready iteration and future model/feature expansion.

## 8. Reproducibility Artifacts
- Main summary: `report/results.md`
- Preliminary baseline summary: `report/preliminary_full_run_report.md`
- Upgrade deltas: `report/upgrade_impact_report.md`
- Final run stamp: `outputs/metrics/final_run_stamp.json`
- Model metrics: `outputs/metrics/modeling_baseline_metrics.json`

## 9. Figures to Include
- `outputs/figures/class_balance.png`
- `outputs/figures/fold_balanced_accuracy.png`
- `outputs/figures/mean_balanced_accuracy.png`
- `outputs/figures/confusion_matrix.png`
- `outputs/figures/roc_curve.png`

## 10. Next Revisions Checklist
- Add brief clinical/neuroscience context for oddball decoding motivation.
- Expand methods detail on preprocessing and event alignment assumptions.
- Add error analysis by subject and class.
- Add table formatting for publication style.
