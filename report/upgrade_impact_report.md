# Upgrade Impact Report

Date: 2026-02-20
Upgrade: Subject-normalized feature expansion (base + z features) plus fold-wise decision-threshold tuning (`train_balanced_optimal`) on class-weighted logistic regression.

## Run Scope
- Event files processed: 286
- EEG files processed: 285
- EEG files skipped: 1
- Trial rows: 58,963
- Subjects in CV: 285
- Feature groups (base / z-normalized): 15 / 15

## Baseline (Pre-Upgrade)
- Mean balanced accuracy: 0.5781067472214015
- Baseline balanced accuracy: 0.5
- Model lift over baseline: +0.07810674722140154
- ROC AUC: 0.6082288207341247
- Confusion matrix: TN=26337, FP=20834, FN=4742, TP=7050

## Post-Upgrade
- Mean balanced accuracy: 0.6081258625383577
- Baseline balanced accuracy: 0.5
- Model lift over baseline: +0.10812586253835765
- ROC AUC: 0.6467288195979253
- Threshold strategy: train_balanced_optimal
- Mean applied threshold: 0.5
- Confusion matrix: TN=29058, FP=18113, FN=4714, TP=7078

## Delta (Post - Pre)
- Mean balanced accuracy: +0.0300191153169562
- ROC AUC: +0.0384999988638006
- True positives: +28
- False negatives: -28
- False positives: -2721
- True negatives: +2721

## Conclusion
- The combined feature + threshold upgrade produced a substantial improvement in both balanced accuracy and ROC AUC on the full cohort.
- Error profile improved in both classes simultaneously: far fewer false positives with slightly better target recall.
- This is now a stronger baseline for manuscript-style preliminary reporting.
