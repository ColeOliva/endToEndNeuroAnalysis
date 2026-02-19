# Data Manifest

Purpose: record exactly which dataset version was used so analyses are reproducible.

## Dataset Record Template
- Dataset source:
- Dataset accession/identifier:
- Download URL:
- Date downloaded:
- Local BIDS root:
- Version/tag/release (if available):
- Subject inclusion criteria:
- Subject exclusions and reasons:
- Run/session exclusions and reasons:
- Label column used for decoding (for example: trial_type):
- Final classes included:
- Notes on known issues:

## Integrity Checks
- dataset_description.json present:
- participants.tsv present:
- events.tsv present for all included runs:
- channels.tsv/electrodes.tsv present where expected:

## Provenance Log
- 2026-02-19: Initialized manifest template.
