# Preliminary Full-Run Report (Finalized Baseline)

Date: 2026-02-20
Run ID: ds007056_v1_1_1_final_refined_2026_02_20
Related analysis: see `report/upgrade_impact_report.md` for pre/post upgrade deltas.

## Scope
- Indexed EEG files: 286
- Processed EEG files: 285
- Skipped EEG files: 1
- Subjects in modeling CV: 285
- Feature rows: 58,963

## Baseline Model Performance (After Finalized Upgrade)
- Mean balanced accuracy (model): 0.6081258625383577
- Mean balanced accuracy (baseline): 0.5
- Balanced accuracy lift: +0.10812586253835765
- ROC AUC: 0.6467288195979253
- Fold balanced accuracy range: 0.598020 to 0.618041

## Confusion Matrix
- TN: 29,058
- FP: 18,113
- FN: 4,714
- TP: 7,078

## Interpretation
- The model is clearly above chance on subject-wise CV with stronger class separation than the pre-upgrade run.
- Current pipeline uses subject-normalized features and fold-wise threshold tuning as the default finalized baseline.
