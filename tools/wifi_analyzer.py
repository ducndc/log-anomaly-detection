import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_scan_log(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    bss_entries = []
    current = {}

    for line in lines:
        line = line.strip()

        bss_match = re.match(r'^BSS ([0-9a-f:]{17})', line)
        if bss_match:
            if current:
                bss_entries.append(current)
                current = {}
            current['BSSID'] = bss_match.group(1)
            continue

        if line.startswith('SSID:'):
            current['SSID'] = line.split('SSID: ')[1]

        if line.startswith('freq:'):
            freq_str = line.split('freq: ')[1]
            try:
                freq = int(float(freq_str))
                current['Frequency'] = freq
                if 2400 <= freq <= 2500:
                    current['Band'] = '2.4GHz'
                elif 5000 <= freq <= 5900:
                    current['Band'] = '5GHz'
                else:
                    current['Band'] = 'Other'
            except ValueError:
                print(f"")

        if line.startswith('signal:'):
            current['Signal (dBm)'] = float(line.split('signal: ')[1].split()[0])

    if current:
        bss_entries.append(current)

    return pd.DataFrame(bss_entries)


def export_data(df, csv_path='wifi_scan.csv', excel_path='wifi_scan.xlsx'):
    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False)
    print(f"Exported to: {csv_path}, {excel_path}")


def plot_heatmap(df):
    if 'SSID' not in df.columns or 'Signal (dBm)' not in df.columns:
        print("Không có đủ dữ liệu để vẽ heatmap.")
        return

    # Lọc bỏ SSID rỗng
    df = df[df['SSID'].notna() & (df['SSID'] != '')]

    plt.figure(figsize=(12, 6))
    sns.boxplot(x='SSID', y='Signal (dBm)', data=df)
    plt.title('Signal Strength Distribution per SSID')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else input("Enter scan file").strip() 

    df = parse_scan_log(file_path)
    print(f"\nTổng số BSS phát hiện: {len(df)}")
    print(df['Band'].value_counts())
    print(df.head())

    export_data(df)
    plot_heatmap(df)

