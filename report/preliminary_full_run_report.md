# Preliminary Full-Run Report (Pre-Upgrade)

Date: 2026-02-20
Run ID: ds007056_v1_1_1_final_refined_2026_02_20

## Scope
- Indexed EEG files: 286
- Processed EEG files: 285
- Skipped EEG files: 1
- Subjects in modeling CV: 285
- Feature rows: 58,963

## Baseline Model Performance (Before Upgrade)
- Mean balanced accuracy (model): 0.5781067472214015
- Mean balanced accuracy (baseline): 0.5
- Balanced accuracy lift: +0.07810674722140154
- ROC AUC: 0.6082288207341247
- Fold balanced accuracy range: 0.570075 to 0.586547

## Confusion Matrix
- TN: 26,337
- FP: 20,834
- FN: 4,742
- TP: 7,050

## Interpretation
- The model is above chance on subject-wise CV, but false positives are high for Rare_Target calls.
- Highest-impact next step: tune decision threshold per fold while preserving subject-wise GroupKFold and class-balanced training.
