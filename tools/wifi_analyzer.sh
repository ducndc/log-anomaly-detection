#!/bin/bash

# Interface Wi-Fi (bạn có thể sửa thành interface của bạn)
IFACE="wlxd0374542d42e"

# File log sẽ được lưu tại đây
LOGFILE="scan.log"

echo "📡 Đang quét mạng Wi-Fi trên interface: $IFACE ..."
sudo iw dev $IFACE scan > "$LOGFILE"

if [ $? -ne 0 ]; then
    echo "❌ Lỗi khi thực hiện quét Wi-Fi. Kiểm tra interface và quyền sudo."
    exit 1
fi

echo "✅ Đã lưu kết quả scan vào: $LOGFILE"
echo "🚀 Đang phân tích bằng tool Python..."

# Gọi tool Python
python3 wifi_analyzer.py "$LOGFILE"

