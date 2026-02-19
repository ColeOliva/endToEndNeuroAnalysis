# Methods (Pre-Registered Style Draft)

## 1) Study Aim
We test whether stimulus category can be decoded from task EEG data above chance with a reproducible BIDS-based pipeline.

## 2) Hypothesis
After standard EEG preprocessing and event-locked epoching, model performance on held-out data will be above chance.

## 3) Dataset and Participants
- Source: OpenNeuro EEG dataset (final accession to be filled in).
- Inclusion: participants/runs with complete EEG and event annotations.
- Exclusion: runs with missing critical metadata or unusable signal quality.

## 4) Data Format and Loading
- Input format: BIDS.
- Core files: dataset_description.json, participants.tsv, EEG recordings, events.tsv.
- Data indexing outputs: subject, session, run, trial label, and quality flags.

## 5) Preprocessing Plan
- Re-reference: common average (unless dataset-specific standard differs).
- Filtering: task-appropriate band-pass; notch only if line noise is evident.
- Artifact handling: bad-channel handling plus optional ICA/SSP if justified.
- Epoching: event-locked windows with baseline correction.
- Quality control: trial counts, rejected epochs, and exclusion log.

## 6) Feature Engineering Plan
- Primary feature family: time-window and/or band-power features.
- Label target: stimulus category field from events annotations.
- Feature standardization applied inside cross-validation folds only.

## 7) Modeling and Validation Plan
- Baseline model: logistic regression.
- Optional comparison model: SVM.
- Validation: stratified cross-validation (default 5 folds).
- Primary metric: balanced accuracy.
- Secondary metrics: confusion matrix-derived statistics and ROC-AUC where applicable.
- Baseline comparison: majority-class chance baseline.

## 8) Visualization Plan
- Data quality: class balance and rejection summary plots.
- Neuro figures: ERP/topomap or band-power map.
- ML figures: confusion matrix and ROC curve.

## 9) Reproducibility Rules
- Freeze dataset choice and class mapping before final runs.
- Record all exclusions in data manifest.
- Keep config-driven parameters in configs/default.yaml.
- Store generated outputs under outputs/ with run identifiers.

## 10) Planned Limitations
- Potential class imbalance and inter-subject variability.
- Limited model complexity in initial baseline phase.
- Results depend on quality and consistency of event annotations.
