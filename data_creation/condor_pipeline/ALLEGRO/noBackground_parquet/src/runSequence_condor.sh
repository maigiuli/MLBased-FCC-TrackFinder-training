#!/bin/bash

TRAIN_OR_TEST="$1"
SEED="$2"
KEY4HEP_VERSION="$3"

WORK_DIR="/eos/user/g/gimainer/MLBased-FCC-TrackFinder-training"
OUTDIR="/eos/user/g/gimainer/MLBased-FCC-TrackFinder-training/output"

exec "$WORK_DIR/data_creation/condor_pipeline/ALLEGRO/noBackground_parquet/src/runSequence.sh" \
    "$OUTDIR" \
    "$TRAIN_OR_TEST" \
    "$SEED" \
    "$WORK_DIR" \
    "$KEY4HEP_VERSION"
