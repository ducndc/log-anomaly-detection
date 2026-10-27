"""Run a fine-tuned LogLLM on new, unlabeled Wi-Fi device logs.

Usage (from the LogLLM directory):
    DATASET_NAME=Wifi python detect.py /path/to/logmesh [/path/to/messages ...]

Each log is cut into the same fixed-size windows used for training
(prepareData/wifi_window.py); windows the model calls anomalous are written,
with their line range and raw lines, to `detect_<dataset>.csv`.
"""
import os
import re
import sys
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from model import LogLLM
from customDataset import CustomCollator, replace_patterns

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prepareData'))
from wifi_window import read_log, window_size, step_size, spliter

max_content_len = 100
max_seq_len = 128
batch_size = 32
dataset_name = os.environ.get('DATASET_NAME', 'Wifi')

Bert_path = os.environ.get('BERT_PATH', r"/mnt/public/gw/LLM_model/bert-base-uncased")
Llama_path = os.environ.get('LLAMA_PATH', r"/mnt/public/gw/LLM_model/Meta-Llama-3-8B")

ROOT_DIR = Path(__file__).parent
ft_path = os.path.join(ROOT_DIR, r"ft_model_{}".format(dataset_name))
output_path = os.environ.get('DETECT_OUT', os.path.join(ROOT_DIR, 'detect_{}.csv'.format(dataset_name)))

device = torch.device("cuda:0")


class WindowDataset(Dataset):
    def __init__(self, windows):
        self.sequences = [[replace_patterns(line) for line in w.split(spliter)] for w in windows]

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], 0  # label unused at inference


def build_windows(path):
    df = read_log(path, os.path.basename(path))
    df['Content'] = df['Component'].str.replace(r'\[\d+\]', '', regex=True) + ': ' + df['Content']
    rows = []
    for i in range(0, max(len(df) - window_size, 0) + 1, step_size):
        window = df.iloc[i:i + window_size]
        first, last = window.iloc[0], window.iloc[-1]
        rows.append({
            'Source': os.path.basename(path),
            'StartLine': i + 1,
            'EndLine': i + len(window),
            'StartTime': f"{first['Month']} {first['Date']} {first['Time']}",
            'EndTime': f"{last['Month']} {last['Date']} {last['Time']}",
            'Content': spliter.join(window['Content']),
        })
    return pd.DataFrame(rows)


def predict(model, dataloader):
    model.eval()
    preds = []
    with torch.no_grad():
        for batch in tqdm(dataloader):
            outputs_ids = model(batch['inputs'].to(device), batch['seq_positions'])
            for text in model.Llama_tokenizer.batch_decode(outputs_ids):
                match = re.search(r'normal|anomalous', text, re.IGNORECASE)
                preds.append(int(bool(match) and match.group().lower() == 'anomalous'))
    return preds


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    windows = pd.concat([build_windows(p) for p in sys.argv[1:]], ignore_index=True)

    model = LogLLM(Bert_path, Llama_path, ft_path=ft_path, is_train_mode=False, device=device,
                   max_content_len=max_content_len, max_seq_len=max_seq_len)
    collator = CustomCollator(model.Bert_tokenizer, max_seq_len=max_seq_len, max_content_len=max_content_len)
    dataloader = DataLoader(WindowDataset(windows['Content']), batch_size=batch_size, collate_fn=collator,
                            shuffle=False, drop_last=False)

    windows['Anomaly'] = predict(model, dataloader)
    anomalies = windows[windows['Anomaly'] == 1].copy()
    anomalies['Content'] = anomalies['Content'].str.replace(spliter, '\n', regex=False)
    anomalies.to_csv(output_path, index=False)
    print(f'{len(anomalies)} / {len(windows)} windows anomalous -> {output_path}')
