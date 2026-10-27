#!/bin/bash
# Fine-tune and evaluate LogLLM on the Wi-Fi device logs. Run on a CUDA GPU
# machine (>= 24 GB VRAM) from the LogLLM directory:
#   export HF_TOKEN=...   # account with access to meta-llama/Meta-Llama-3-8B
#   bash run_wifi.sh [install|prep|train|eval|all]
set -e
cd "$(dirname "$0")"

export DATASET_NAME=Wifi
export DATA_DIR=${DATA_DIR:-$(realpath ../data/llm/Wifi)}
export BERT_PATH=${BERT_PATH:-google-bert/bert-base-uncased}
export LLAMA_PATH=${LLAMA_PATH:-meta-llama/Meta-Llama-3-8B}
export MIN_SAMPLES=${MIN_SAMPLES:-10000}

step=${1:-all}

if [[ $step == install || $step == all ]]; then
    pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121
    pip install transformers datasets peft accelerate bitsandbytes safetensors scikit-learn pandas tqdm
fi

if [[ $step == prep || $step == all ]]; then
    python prepareData/wifi_window.py
fi

if [[ $step == train || $step == all ]]; then
    python train.py
fi

if [[ $step == eval || $step == all ]]; then
    python eval.py
fi
