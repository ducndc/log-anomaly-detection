# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Research/tooling repo for anomaly detection on Wi-Fi device syslogs (EasyMesh `logmesh` and `messages` logs from AP/ONT devices: APw6, ONTw6, XGSPONw6, ONTw5, APw5). It holds several independent sub-projects, each representing a different generation of technique. They share no build system or test suite. There are no automated tests or linters. Scripts named `test_*.py` are pipeline entry points, not unit tests.

| Directory | Technique | Origin |
|---|---|---|
| `log-parser/` | Drain / LogCluster log template parsing | adapted from logpai/logparser |
| `loganalysis/` | Classical ML: PCA, InvariantsMiner, LogClustering | adapted from logpai/loglizer (He et al., ISSRE'16, cited in README) |
| `deeploganalysis/` | DL: LSTM, CNN, Transformer, Autoencoder | vendored logpai/deep-loglizer |
| `LogLLM/` | BERT + Llama-3-8B with LoRA adapters | vendored official LogLLM implementation |
| `app/DetectAnomalLog/` | Qt6/QML C++ port of the parse + PCA pipeline (uses Eigen) | in-house |
| `tools/` | Wi-Fi scan helpers (`iw scan` → `wifi_analyzer.py`), not part of the anomaly pipeline | in-house |

## Main pipeline (Wi-Fi logs, classical PCA)

`detect_anomal_log.sh <archive.tar>` runs the end-to-end flow. `test_ui.py` is a PySide6 front end that just shells out to this script with the selected file and writes the output to `debug_output_<device>.log`.

1. It extracts the archive in `data/original_log/` (create this directory first; it is not tracked), concatenates `logmesh.old + logmesh` and `messages.old + messages`, and copies the results to `data/input_log/`.
2. `cd log-parser && python parse_log_with_drain.py` runs Drain on `data/input_log/logmesh` and writes `data/result/logmesh_structured.csv` and `logmesh_templates.csv`.
3. `cd loganalysis && python test_PCA_without_label.py` treats each log line as a single-event session (`dataloader.load_wifi_log`). It runs a TF-IDF and zero-mean `FeatureExtractor`, fits PCA on the first 70% of lines, predicts on the remaining 30%, and writes `loganalysis/results/anomalies_detected.csv` and `anomalous_events_with_templates.csv` (anomalies joined with their templates).

Notes on these scripts:
- Every script uses paths relative to its own directory and `sys.path.append('../')`, so run each one from inside its directory.
- `parse_log_with_drain.py` imports `from logparser.Drain import LogParser`. The local directory is `log-parser` (hyphenated), so it cannot be imported as `logparser`. The import only works if a `logparser` package is installed (for example `pip install logparser3`) or the directory is made available under that name.
- The Drain `log_format` (`<Day> <Month> <Date> <Time> <Year> <Level> <Component>: <Line> <Content>`) and the masking `regex` list are tuned for the device logs. The C++ app hard-codes the same format in `LogAnalyzer.cpp`, so a change to one should be mirrored in the other.

Setup: `bash setup.sh` creates `myenv/` with PySide6 and `log-parser/requirements.txt`.

## C++ Qt app (`app/DetectAnomalLog`)

This is a native reimplementation of the parse + PCA pipeline. It needs Qt ≥ 6.8 (Quick) and Eigen at `/usr/include/eigen3`.

```bash
cmake -S app/DetectAnomalLog -B build && cmake --build build
```

Flow: `Main.qml` → `LogAnalyzer` (registered in QML as `Backend.LogAnalyzer`). `LogAnalyzer::analyze()` extracts `.tar`/`.tgz` input into `./tmp/extracted_log` (`FileUtils` looks for `logmesh`, then `logmesh.old`, then any `.log`/`.txt`). It then calls `ParseLog` (a Drain port that writes `_structured.csv` and `_templates.csv` to `./tmp/analyzed_result`), then `PCA::run()`, which reports back through the `detectionFinished` and `detectionError` signals.

## deeploganalysis (deep-loglizer)

The demos in `demo/` are argparse-driven and run from `demo/`:
```bash
cd deeploganalysis/demo
python lstm_demo.py --label_type next_log --feature_type sequentials --topk 10 --dataset HDFS --data_dir ../data/processed/HDFS_100k/hdfs_0.0_tar
```
`benchmarks/{w,wo}_semantics/*.sh` hold the reference invocations. Their default `--data_dir` points at `HDFS/...`, but only `data/processed/HDFS_100k/` is checked in. `data_preprocess/preprocess_{hdfs,bgl}.py` generate `session_train.pkl`/`session_test.pkl`; the `hdfs_<ratio>_tar` suffix is the train anomaly ratio. Each run writes into `demo/experiment_records/<hash>/`. All models subclass `deeploglizer/models/base_model.py`.

## LogLLM

This needs a CUDA GPU, a local Meta-Llama-3-8B, and bert-base-uncased. `train.py`, `eval.py`, and `prepareData/{sliding_window,session_window}.py` take no CLI arguments. You configure them by editing module-level variables (`dataset_name`, `data_path`, `Bert_path`, `Llama_path`, `data_dir`, `log_name`, `start_line`/`end_line`), which currently hold absolute `/mnt/public/gw/...` paths from the upstream authors. Run them from `LogLLM/`. Use `session_window` for HDFS and `sliding_window` for BGL, Thunderbird, and Liberty.

`DATASET_NAME`, `DATA_DIR`, `BERT_PATH`, `LLAMA_PATH`, and `MIN_SAMPLES` environment variables override those variables in `train.py` and `eval.py`. Hugging Face hub IDs work as model paths.

Wi-Fi logs (`DATASET_NAME=Wifi`): `prepareData/wifi_window.py` reads `data/input_log/{logmesh,messages}` directly, without Drain, and writes `data/llm/Wifi/{train,test}.csv` (windows of 20 lines with a step of 10, split 80/20 per log). The device logs have no ground truth, so labels come from `data/llm/Wifi/template_labels.csv`, one 0/1 label per masked template. The first run seeds that file from keyword heuristics. It is meant to be corrected by hand, then the script is rerun. Severity can't be used as a label because mapd logs nearly everything at `daemon.err`. `run_wifi.sh [install|prep|train|eval|all]` is the cloud-GPU runbook. `detect.py <logfile>...` runs a trained model on new unlabeled logs.

The model (`model.py`) encodes each log message with BERT (LoRA), projects the encoding into Llama's embedding space (`projector.pt`), and has Llama (LoRA, 4-bit) generate "The sequence is normal/anomalous." Training proceeds in staged phases (`n_epochs_1`, `n_epochs_2_1`, `n_epochs_2_2`, `n_epochs_3`) that unfreeze different parts. The fine-tuned adapters for each dataset are committed under `ft_model_<dataset>/`.
