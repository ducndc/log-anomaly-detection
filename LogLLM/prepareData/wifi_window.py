"""Build LogLLM train/test sets from the Wi-Fi device syslogs (logmesh, messages).

The device logs carry no anomaly labels, so labels are assigned per template:
  1. Every line is reduced to a template key (variables masked).
  2. Template labels are read from `template_labels.csv`. If that file does not
     exist it is generated with keyword heuristics (Label + Reason columns) and
     should be reviewed by hand: fix the Label column (0 normal / 1 anomalous)
     and run this script again.
  3. Lines inherit their template label; fixed-size windows of lines become
     LogLLM sequences, and a window is anomalous if any line in it is.

Run from the LogLLM directory:  python prepareData/wifi_window.py
"""
import os
import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
input_dir = os.environ.get('WIFI_LOG_DIR', str(ROOT_DIR / 'data' / 'input_log'))
log_names = os.environ.get('WIFI_LOG_NAMES', 'logmesh,messages').split(',')
output_dir = os.environ.get('WIFI_OUT_DIR', str(ROOT_DIR / 'data' / 'llm' / 'Wifi'))
template_label_file = os.path.join(output_dir, 'template_labels.csv')

window_size = 20
step_size = 10
train_ratio = 0.8
spliter = ' ;-; '

# <Day> <Month> <Date> <Time> <Year> <Level> <Component>: <Content>
line_regex = re.compile(
    r'^(?P<Day>\w{3})\s+(?P<Month>\w{3})\s+(?P<Date>\d{1,2})\s+(?P<Time>[\d:]{8})\s+(?P<Year>\d{4})\s+'
    r'(?P<Level>[\w-]+\.\w+)\s+(?P<Component>[^:]+?):\s?(?P<Content>.*)$'
)

mask_patterns = [
    r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}',                # MAC
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?',     # IP
    r'\b0x[0-9a-fA-F]+\b',                                # hex
    r'\b[0-9a-fA-F]{8,}\b',                               # ids / hashes
    r'[a-zA-Z\.\:\-\_]*\d[a-zA-Z0-9\.\:\-\_]*',           # word containing a digit
]
mask_regex = re.compile('|'.join(mask_patterns))

# Heuristics used only to seed template_labels.csv. Level is not used on its
# own: mapd logs almost everything at daemon.err.
anomaly_keywords = re.compile(
    r'\b(fail\w*|error\w*|timeout|timed out|invalid|crash\w*|panic|oops|segfault|unable|cannot|can\'t|'
    r'reject\w*|denied|refused|drop\w*|lost|abort\w*|overflow|exceed\w*|not found|wrong|watchdog|killed|'
    r'out of memory|oom|stuck|hang|corrupt\w*|mismatch|unexpected|illegal|deauth\w*|disassoc\w*|'
    r'reboot\w*|restart\w*)\b',
    re.IGNORECASE,
)
severe_levels = ('.crit', '.alert', '.emerg')
# Anomalies are assumed rare: a keyword template above this share of its log is
# treated as background chatter (still flagged in Reason for review).
frequent_share = 0.05


def template_key(component, content):
    component = re.sub(r'\[\d+\]', '', component)
    return component + ': ' + mask_regex.sub('<*>', content)


def read_log(path, source):
    rows = []
    with open(path, 'r', encoding='latin-1') as fin:
        for line in fin:
            match = line_regex.match(line.strip())
            if not match:
                continue
            row = match.groupdict()
            row['Source'] = source
            rows.append(row)
    df = pd.DataFrame(rows)
    df['Template'] = [template_key(c, m) for c, m in zip(df['Component'], df['Content'])]
    print(f'{source}: {len(df)} lines, {df["Template"].nunique()} templates')
    return df


def seed_template_labels(df):
    stats = df.groupby('Template').agg(Source=('Source', 'first'), Level=('Level', 'first'),
                                       Occurrences=('Template', 'size')).reset_index()
    source_sizes = df['Source'].value_counts()
    labels, reasons = [], []
    for template, level, source, count in zip(stats['Template'], stats['Level'], stats['Source'],
                                              stats['Occurrences']):
        keyword = anomaly_keywords.search(template)
        share = count / source_sizes[source]
        if keyword and share >= frequent_share:
            labels.append(0)
            reasons.append(f'REVIEW: keyword "{keyword.group()}" but frequent ({share:.0%} of {source})')
        elif level.endswith(severe_levels):
            labels.append(1)
            reasons.append(f'level {level}')
        elif keyword:
            labels.append(1)
            reasons.append(f'keyword "{keyword.group()}"')
        else:
            labels.append(0)
            reasons.append('')
    stats['Label'] = labels
    stats['Reason'] = reasons
    stats = stats.sort_values(['Label', 'Occurrences'], ascending=[False, False])
    stats.to_csv(template_label_file, index=False)
    print(f'Seeded {len(stats)} template labels ({sum(labels)} anomalous) -> {template_label_file}')
    print('Review the Label column, then run this script again.')
    return stats


def load_template_labels(df):
    if not os.path.exists(template_label_file):
        return seed_template_labels(df)
    stats = pd.read_csv(template_label_file)
    unseen = set(df['Template']) - set(stats['Template'])
    if unseen:
        print(f'Warning: {len(unseen)} templates missing from {template_label_file}; labelled normal.')
    return stats


def fixed_windows(df):
    rows = []
    for i in range(0, max(len(df) - window_size, 0) + 1, step_size):
        window = df.iloc[i:i + window_size]
        rows.append([spliter.join(window['Content']), int(window['Label'].max()),
                     window['Label'].tolist(), len(window)])
    return pd.DataFrame(rows, columns=['Content', 'Label', 'item_Label', 'session_length'])


if __name__ == '__main__':
    os.makedirs(output_dir, exist_ok=True)
    logs = [read_log(os.path.join(input_dir, name), name) for name in log_names]
    df_all = pd.concat(logs, ignore_index=True)

    stats = load_template_labels(df_all)
    label_map = dict(zip(stats['Template'], stats['Label']))

    train_parts, test_parts = [], []
    for df in logs:
        df['Label'] = df['Template'].map(label_map).fillna(0).astype(int)
        # Keep the component in the text so the model sees which daemon logged it.
        df['Content'] = df['Component'].str.replace(r'\[\d+\]', '', regex=True) + ': ' + df['Content']
        train_len = int(train_ratio * len(df))
        train_parts.append(fixed_windows(df[:train_len].reset_index(drop=True)))
        test_parts.append(fixed_windows(df[train_len:].reset_index(drop=True)))

    for name, parts in (('train', train_parts), ('test', test_parts)):
        session_df = pd.concat(parts, ignore_index=True)
        session_df.to_csv(os.path.join(output_dir, f'{name}.csv'), index=False)
        n_anomalous = session_df['Label'].sum()
        print(f'{name}: {len(session_df)} sequences, {n_anomalous} anomalous '
              f'({n_anomalous / max(len(session_df), 1):.1%}), mean length {session_df["session_length"].mean():.1f}')
