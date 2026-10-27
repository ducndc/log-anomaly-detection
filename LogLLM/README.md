# LogLLM: Log-based Anomaly Detection Using Large Language Models #

Official Implementation of "LogLLM: Log-based Anomaly Detection Using Large Language Models"
![framework.png](framework.png)

## Datasets

The statistics of datasets used in the experiments.

|             |                    |                     |    Training Data    |  Training Data  |   Training Data   |    Testing Data     |  Testing Data   |   Testing Data    |
|:-----------:|:------------------:|:-------------------:|:-------------------:|:---------------:|:-----------------:|:-------------------:|:---------------:|:-----------------:|
|             | **# Log Messages** | **# Log Sequences** | **# Log Sequences** | **# Anomalies** | **Anomaly Ratio** | **# Log Sequences** | **# Anomalies** | **Anomaly Ratio** |
|    HDFS     |     11,175,629     |       575,061       |       460,048       |      13497      |       2.93%       |       115013        |      3341       |       2.90%       |
|     BGL     |     4,747,963      |       47,135        |       37,708        |      4009       |      10.63%       |        9427         |       817       |       8.67%       |
|   Liberty   |     5,000,000      |       50,000        |        40000        |      34144      |      85.36%       |        10000        |       651       |       6.51%       |
| Thunderbird |     10,000,000     |       99,997        |       79,997        |       837       |       1.05%       |        20000        |       29        |       0.15%       |

## Experiment Results

Experimental Results on HDFS, BGL, Liberty, and Thunderbird datasets. The best results are indicated using bold
typeface.

|            |                |   HDFS    |   HDFS    |   HDFS    |    BGL    |    BGL    |    BGL    |  Liberty  |  Liberty  |  Liberty  | Thunderbird | Thunderbird | Thunderbird |             |
|:----------:|:--------------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:-----------:|:-----------:|:-----------:|:-----------:|
|            | **Log Parser** | **Prec.** | **Rec.**  |  **F1**   | **Prec.** | **Rec.**  |  **F1**   | **Prec.** | **Rec.**  |  **F1**   |  **Prec.**  |  **Rec.**   |   **F1**    | **Avg. F1** |
|  DeepLog   |    &#10004;    |   0.835   |   0.994   |   0.908   |   0.166   |   0.988   |   0.285   |   0.751   |   0.855   |   0.800   |    0.017    |    0.966    |    0.033    |    0.506    |
| LogAnomaly |    &#10004;    |   0.886   |   0.893   |   0.966   |   0.176   |   0.985   |   0.299   |   0.684   |   0.876   |   0.768   |    0.025    |    0.966    |    0.050    |    0.521    |
|   PLELog   |    &#10004;    |   0.893   |   0.979   |   0.934   |   0.595   |   0.880   |   0.710   |   0.795   |   0.874   |   0.832   |    0.808    |    0.724    |    0.764    |    0.810    |
| FastLogAD  |    &#10004;    |   0.721   |   0.893   |   0.798   |   0.167   | **1.000** |   0.287   |   0.151   | **0.999** |   0.263   |    0.008    |    0.931    |    0.017    |    0.341    |
|  LogBERT   |    &#10004;    |   0.989   |   0.614   |   0.758   |   0.165   |   0.989   |   0.283   |   0.902   |   0.633   |   0.744   |    0.022    |    0.172    |    0.039    |    0.456    |
| LogRobust  |    &#10004;    |   0.961   |   1.000   |   0.980   |   0.696   |   0.968   |   0.810   |   0.695   |   0.979   |   0.813   |    0.318    |  **1.000**  |    0.482    |    0.771    |
|    CNN     |    &#10004;    |   0.966   |   1.000   |   0.982   |   0.698   |   0.965   |   0.810   |   0.580   |   0.914   |   0.709   |    0.870    |    0.690    |    0.769    |    0.818    |
| NeuralLog  |    &#10008;    |   0.971   |   0.988   |   0.979   |   0.792   |   0.884   |   0.835   |   0.875   |   0.926   |   0.900   |    0.794    |    0.931    |    0.857    |    0.893    |
|   RAPID    |    &#10008;    | **1.000** |   0.859   |   0.924   | **0.874** |   0.399   |   0.548   |   0.911   |   0.611   |   0.732   |    0.200    |    0.207    |    0.203    |    0.602    |
|   LogLLM   |    &#10008;    |   0.994   | **1.000** | **0.997** |   0.861   |   0.979   | **0.916** | **0.992** |   0.926   | **0.958** |  **0.966**  |    0.966    |  **0.966**  |  **0.959**  |

## Using Our Code to Reproduce the Results
### 1. Set Up the Environment.
- **Software Requirements**:
  - Python: 3.8.20
  - CUDA: 12.1

- **Choose one of the following methods to install dependencies**:
 
--- Option 1: Install from ```requirements.txt```
```
 conda install --yes --file requirements.txt # You may need to downgrade the torch using pip to match the CUDA version
```

--- Option 2: Install packages individually
```
conda create -n logllm python=3.8
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets peft accelerate bitsandbytes safetensors
pip install scikit-learn
pip install tqdm
```


### 2. Download open-source LLM [Meta-Llama-3-8B](https://huggingface.co/meta-llama/Meta-Llama-3-8B/tree/main), and Bert [bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased).

```
   ├── Meta-Llama-3-8B
   │ ├── config.json
   │ ├── generation_config.json
   │ ├── LICENSE
   │ ├── model-00001-of-00004.safetensors
   │ ├── model-00002-of-00004.safetensors
   │ ├── model-00003-of-00004.safetensors
   │ ├── model-00004-of-00004.safetensors
   │ ├── model.safetensors.index.json
   │ ├── special_tokens_map.json
   │ ├── tokenizer.json
   │ └── tokenizer_config.json
```

```
   ├── bert-base-uncased
   │ ├── config.json
   │ ├── model.safetensors
   │ ├── tokenizer.json
   │ ├── tokenizer_config.json
   │ └── vocab.txt
```

### 3. Prepare training and testing data

- Download BGL/HDFS_v1/Thunderbird dataset from [here](https://github.com/logpai/loghub). Download Liberty dataset
  from [here](http://0b4af6cdc2f0c5998459-c0245c5c937c5dedcca3f1764ecc9b2f.r43.cf2.rackcdn.com/hpc4/liberty2.gz).
- For **BGL**, **Thunderbird** and **Liberty**, set the following variations in **sliding_window.py** under *
  *prepareData**
  directory:
   ```
   data_dir =  # i.e. r'/mnt/public/gw/SyslogData/BGL'
   log_name =  # i.e. 'BGL.log'
   ```

  For  **Liberty**, you should activate
  ```
  start_line = 40000000
  end_line = 45000000
  ```

  For  **Thunderbird**, you should activate
  ```
  start_line = 160000000
  end_line = 170000000
  ```

  Run ```python prepareData.sliding_window.py```  from the root directory to generate training and testing data.
  Training and testing data will be saved in {data_dir}.

- For **HDFS**, set the following directories in **session_window.py** under **prepareData**
  directory:
   ```
   data_dir =  # i.e. r'/mnt/public/gw/SyslogData/HDFS_v1'
   log_name =  # i.e. 'HDFS.log'
   ```
  Run ```python prepareData.session_window.py```  from the root directory to generate training and testing data.
  Training and testing data will be saved in {data_dir}

### 4. Train our proposed deep model. This step can be skipped by directly using our fine-tuned model (ft_model_[dataset_name])

- Set the following variables in **train.py**, or override them with environment variables
  (`BERT_PATH`, `LLAMA_PATH`, `DATASET_NAME`, `DATA_DIR`; Hugging Face hub IDs also work as model paths):
   ```
   Bert_path = # i.e., r"/mnt/public/gw/LLM_model/bert-base-uncased"
   Llama_path = # i.e., r"/mnt/public/gw/LLM_model/Meta-Llama-3-8B"
   dataset_name = # i.e., 'Liberty'
   data_dir =  # i.e., r'/mnt/public/gw/SyslogData/{dataset_name}'  (reads {data_dir}/train.csv)
   ```
  `MIN_SAMPLES` (default 50000) sets how many samples are drawn per epoch in training phases 2-3.
- Run ```python train.py``` from the root directory to get fine-tuned model.

### 5. Evaluate on test dataset.

- Set the same variables in **eval.py** (or the same environment variables). It reads `{data_dir}/test.csv`.
- We have provided the test file for the BGL and Liberty dataset, which can be accessed
  at [here (BGL test file)](https://drive.google.com/file/d/1aMKzhrLklnk5RX78UBc3Zx3voIIGnQzo/view?usp=sharing), and [here (Liberty test file)](https://drive.google.com/file/d/1-Z2FrsRSm8ojfOW1555obNyU6B_aRDTH/view?usp=sharing)
- Run ```python eval.py``` from the root directory. 

## Wi-Fi device logs

This fork adds support for the EasyMesh `logmesh` / `messages` syslogs in `../data/input_log/`
(format `<Day> <Month> <Date> <Time> <Year> <Level> <Component>: <Content>`).

| File | Purpose |
|---|---|
| `prepareData/wifi_window.py` | Builds `../data/llm/Wifi/{train,test}.csv` and seeds `template_labels.csv` |
| `run_wifi.sh` | Runs install, prep, train, and eval on a GPU machine |
| `detect.py` | Runs a trained model on new, unlabeled logs |

### Labels

The device logs have no anomaly labels, so `wifi_window.py` assigns them per log template:

1. Each line is reduced to a template by masking MACs, IPs, hex IDs, and words that contain digits.
2. Labels are read from `../data/llm/Wifi/template_labels.csv` (`Template, Source, Level, Occurrences, Label, Reason`).
   If the file does not exist, it is seeded with these heuristics:
   - `Label=1` if the template contains a failure keyword (fail, error, timeout, invalid, refused, drop, ...) or the level is crit/alert/emerg.
   - Keyword templates that make up ≥ 5% of their log are treated as background chatter: they get `Label=0` and a `REVIEW` reason.
     For example, `invalid radio_idx!` is about 40% of `logmesh`.
   - Severity alone is not used, because `mapd` logs almost everything at `daemon.err`.
3. **Review the `Label` column by hand**, then rerun the script. Templates that are missing from the file are treated as normal.
4. Each log is split 80/20 in time order into fixed windows of 20 lines with a step of 10. A window is anomalous if any line in it is.

The model learns these labels, and `eval.py` scores against them. Precision and recall therefore measure agreement with
`template_labels.csv`, not with real incidents.

### Run

```bash
python prepareData/wifi_window.py      # locally; review template_labels.csv and rerun
export HF_TOKEN=...                    # GPU machine, >= 24 GB VRAM, access to meta-llama/Meta-Llama-3-8B
bash run_wifi.sh all                   # or one step: install | prep | train | eval
DATASET_NAME=Wifi python detect.py /path/to/logmesh /path/to/messages
```

`run_wifi.sh` sets `DATASET_NAME=Wifi`, `DATA_DIR=../data/llm/Wifi`, `BERT_PATH=google-bert/bert-base-uncased`,
`LLAMA_PATH=meta-llama/Meta-Llama-3-8B`, and `MIN_SAMPLES=10000`. Any of these can be overridden by exporting the variable first.
The adapters are saved to `ft_model_Wifi/`.

`detect.py` writes the windows predicted as anomalous to `detect_Wifi.csv`, with source file, line range, time range,
and raw lines. Set `DETECT_OUT` to change the output path. Window size and step come from `wifi_window.py`, so detection
uses the same windowing as training.
