# Results Summary

## Run Metadata
- Final run ID: ds007056_v1_1_1_final_2026_02_20
- Run stamp: ../outputs/metrics/final_run_stamp.json

## Dataset and Features
- Event files processed: 17
- EEG files processed: 16
- EEG files skipped: 1
- Trial rows in feature table: 2855
- Class counts: {'Frequent_NonTarget': 2286, 'Rare_Target': 569}

## Modeling
- Subjects in CV: 16
- CV folds: 5
- Mean balanced accuracy (model): 0.5753737567805867
- Mean balanced accuracy (baseline): 0.5
- ROC AUC: 0.6175090372051473
- Confusion matrix (TN, FP, FN, TP): (1160, 1126, 202, 367)

## Figures
- Class balance: ../outputs/figures/class_balance.png
- Fold balanced accuracy: ../outputs/figures/fold_balanced_accuracy.png
- Mean balanced accuracy: ../outputs/figures/mean_balanced_accuracy.png
- Confusion matrix: ../outputs/figures/confusion_matrix.png
- ROC curve: ../outputs/figures/roc_curve.png

## Interpretation
- Model minus baseline (balanced accuracy): 0.07537375678058666
- Current signal-feature pipeline shows above-chance decoding on subject-wise CV.
