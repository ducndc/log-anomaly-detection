import subprocess
import re
import sys

def scan_bss(interface='wlan0'):
    try:
        # Gọi lệnh iw để quét mạng Wi-Fi
        result = subprocess.check_output(
            ['sudo', 'iw', 'dev', interface, 'scan'],
            stderr=subprocess.DEVNULL  # Ẩn lỗi nếu không tìm thấy gì
        ).decode('utf-8')

        # Tìm tất cả dòng bắt đầu với "BSS <MAC>"
        bss_list = re.findall(r'^BSS ([0-9a-f:]{17})', result, re.MULTILINE)

        print(f"Phát hiện {len(bss_list)} BSS trên interface '{interface}':")
        for idx, bss in enumerate(bss_list, 1):
            print(f"{idx:2}. {bss}")

    except subprocess.CalledProcessError:
        print("❌ Không thể quét mạng. Hãy kiểm tra interface hoặc quyền sudo.")
    except FileNotFoundError:
        print("❌ Lệnh 'iw' không tìm thấy. Hãy cài đặt bằng: sudo apt install iw")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        iface = sys.argv[1]
    else:
        iface = "wlan0"

    scan_bss(iface)

