# log anomaly detection

Anomaly detection for Wi-Fi device syslogs (EasyMesh `logmesh` and `messages` logs from AP/ONT devices: APw6, ONTw6, XGSPONw6, ONTw5, APw5).

The repository holds several independent approaches, from classical machine learning to large language models:

| Directory | Approach | Based on |
|---|---|---|
| [`log-parser/`](log-parser) | Log template parsing (Drain, LogCluster) | [logpai/logparser](https://github.com/logpai/logparser) |
| [`loganalysis/`](loganalysis) | Classical ML: PCA, Invariants Mining, Log Clustering | [logpai/loglizer](https://github.com/logpai/loglizer) |
| [`deeploganalysis/`](deeploganalysis) | Deep learning: LSTM, CNN, Transformer, Autoencoder | [logpai/deep-loglizer](https://github.com/logpai/deep-loglizer) |
| [`LogLLM/`](LogLLM) | LLM: BERT + Llama-3-8B fine-tuned with LoRA | [LogLLM](LogLLM/README.md) |
| [`app/DetectAnomalLog/`](app/DetectAnomalLog) | Qt6/QML desktop app (C++ port of parsing + PCA) | — |
| [`tools/`](tools) | Wi-Fi scan helpers (`iw scan` analyzer) | — |

The papers behind each approach are in [`documents/`](documents).

## Library

- Eigen
- PySide6 (for UI)
- Pandas
- Numpy
- PyTorch, Transformers, PEFT, bitsandbytes (for LogLLM; needs a CUDA GPU)

## 1. PCA pipeline (Drain + PCA)

```bash
bash setup.sh                        # creates myenv/ with PySide6 + log-parser requirements
source myenv/bin/activate
mkdir -p data/original_log
cp <device_log>.tar data/original_log/
./detect_anomal_log.sh <device_log>.tar
```

The script:

1. Extracts the archive and merges `logmesh.old + logmesh` and `messages.old + messages` into `data/input_log/`.
2. Parses `logmesh` with Drain (`log-parser/parse_log_with_drain.py`) into `data/result/logmesh_structured.csv` and `logmesh_templates.csv`.
3. Fits PCA on the first 70% of lines and flags anomalies in the remaining 30% (`loganalysis/test_PCA_without_label.py`).
4. Writes `loganalysis/results/anomalous_events_with_templates.csv` and opens it in LibreOffice Calc.

`python test_ui.py` gives a PySide6 GUI that selects the device type and log archive, then runs the same script.

Notes:

- Run each Python script from its own directory, because they use relative paths.
- `parse_log_with_drain.py` imports `logparser.Drain`, so a `logparser` package must be importable (e.g. `pip install logparser3`). The local folder is named `log-parser` and cannot be imported under that name.
- The Drain log format `<Day> <Month> <Date> <Time> <Year> <Level> <Component>: <Line> <Content>` and its masking regexes are tuned for these devices. The Qt app hard-codes the same format.

## 2. Desktop app (Qt6 + Eigen)

Requires Qt ≥ 6.8 (Quick) and Eigen at `/usr/include/eigen3`.

```bash
cmake -S app/DetectAnomalLog -B build && cmake --build build
./build/appDetectAnomalLog
```

It accepts a log file or a `.tar`/`.tar.gz`/`.tgz` archive. It parses the log with a C++ Drain port, runs PCA, and writes results under `./tmp/analyzed_result`.

## 3. Deep learning models (deep-loglizer)

```bash
cd deeploganalysis
pip install -r requirement.txt
cd demo
python lstm_demo.py --label_type next_log --feature_type sequentials --topk 10 \
    --dataset HDFS --data_dir ../data/processed/HDFS_100k/hdfs_0.0_tar
```

Reference commands for every model are in `deeploganalysis/benchmarks/`. Only the HDFS 100k sample dataset is included.

## 4. LLM-based detection (LogLLM)

LogLLM encodes each log line with BERT, projects the result into Llama-3-8B, and has Llama answer "The sequence is normal/anomalous." Training needs a CUDA GPU with at least 24 GB of memory (Llama is loaded in 4-bit) and access to [meta-llama/Meta-Llama-3-8B](https://huggingface.co/meta-llama/Meta-Llama-3-8B).

For the Wi-Fi logs:

```bash
cd LogLLM
python prepareData/wifi_window.py   # 1. build data/llm/Wifi/{train,test}.csv and seed template labels
#                                      2. review data/llm/Wifi/template_labels.csv, then rerun step 1
export HF_TOKEN=...                 # on the GPU machine
bash run_wifi.sh all                # 3. install, prep, train, eval -> ft_model_Wifi/
DATASET_NAME=Wifi python detect.py /path/to/logmesh /path/to/messages   # 4. detect on new logs
```

> **Labels:** the device logs have no ground truth. Training labels come from `template_labels.csv`, which has one normal/anomalous label per log template. It is seeded from keyword heuristics ("fail", "timeout", "invalid", crit/alert levels) and **should be reviewed by hand**. The model learns those labels, and `eval.py` scores against them, so label quality limits detection quality.

See [`LogLLM/README.md`](LogLLM/README.md#wi-fi-device-logs) for details and for reproducing the paper results on HDFS, BGL, Liberty, and Thunderbird.

## Data layout

| Path | Content |
|---|---|
| `data/original_log/` | Raw device archives (not tracked; create it) |
| `data/input_log/` | Merged `logmesh` / `messages` logs |
| `data/result/` | Drain output: `*_structured.csv`, `*_templates.csv` |
| `data/llm/Wifi/` | LogLLM dataset: `train.csv`, `test.csv`, `template_labels.csv` |
| `loganalysis/results/` | PCA anomaly reports |

## Citation

If you use this project, please cite the following paper:

> Shilin He, Jieming Zhu, Pinjia He, Michael R. Lyu.  
> **Experience Report: System Log Analysis for Anomaly Detection**  
> 2016 IEEE 27th International Symposium on Software Reliability Engineering.  
> [IEEE Link](https://ieeexplore.ieee.org/document/7774521)

BibTeX:
```bibtex
@INPROCEEDINGS{7774521,
  author={He, Shilin and Zhu, Jieming and He, Pinjia and Lyu, Michael R.},
  booktitle={2016 IEEE 27th International Symposium on Software Reliability Engineering (ISSRE)}, 
  title={Experience Report: System Log Analysis for Anomaly Detection}, 
  year={2016},
  volume={},
  number={},
  pages={207-218},
  keywords={Feature extraction;Open source software;Runtime;Industries;Manuals;Inspection;Large-scale systems},
  doi={10.1109/ISSRE.2016.21}}
```
