# Results Summary

## Run Metadata
- Final run ID: ds007056_v1_1_1_final_refined_2026_02_20
- Run stamp: ../outputs/metrics/final_run_stamp.json

## Dataset and Features
- Event files processed: 286
- EEG files processed: 285
- EEG files skipped: 1
- Trial rows in feature table: 58963
- Class counts: {'Frequent_NonTarget': 47171, 'Rare_Target': 11792}

## Modeling
- Subjects in CV: 285
- CV folds: 5
- Mean balanced accuracy (model): 0.5783009385900147
- Mean balanced accuracy (baseline): 0.5
- ROC AUC: 0.6082288207341247
- Confusion matrix (TN, FP, FN, TP): (26327, 20844, 4735, 7057)

## Figures
- Class balance: ../outputs/figures/class_balance.png
- Fold balanced accuracy: ../outputs/figures/fold_balanced_accuracy.png
- Mean balanced accuracy: ../outputs/figures/mean_balanced_accuracy.png
- Confusion matrix: ../outputs/figures/confusion_matrix.png
- ROC curve: ../outputs/figures/roc_curve.png

## Interpretation
- Model minus baseline (balanced accuracy): 0.07830093859001475
- Current signal-feature pipeline shows above-chance decoding on subject-wise CV.
