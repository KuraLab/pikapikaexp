import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from ParamBroadcast import udp_param_server_thread
from display_utils import update_display

# グローバル辞書: agent_data[agent_id] = (phi, ts)
agent_data = {}

def udp_server_thread(port=5000):
    """
    指定したポートでUDPを待ち受け、受信したデータをagent_dataに格納する。
    フォーマット例: "ID=1,PHI=0.123,TS=1739844864.0,V=3.300000,Vbat=3.300000"
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"[INFO] UDP server listening on port {port}")

    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode(errors='ignore').strip()
        try:
            # 例: "ID=1,PHI=0.123,TS=1739844864.0,V=3.300000,Vbat=3.300000" を分解
            items = msg.split(',')
            id_str   = items[0].split('=')[1]
            phi_str  = items[1].split('=')[1]
            ts_str   = items[2].split('=')[1]
            v_str    = items[3].split('=')[1]
            vbat_str = items[4].split('=')[1]

            agent_id = int(id_str)
            phi_val  = float(phi_str)
            ts_val   = float(ts_str)
            sensor_v = float(v_str)
            battery_v = float(vbat_str)

            # agent_dataに更新（各エージェントの最新の(phi, ts, sensor_v, battery_v)を保持）
            agent_data[agent_id] = (phi_val, ts_val, sensor_v, battery_v)
        except Exception as e:
            print(f"[WARN] Parse error: {e}, msg={msg}")

def main():
    # UDPサーバをデーモンスレッドで起動
    server_thread = threading.Thread(target=udp_server_thread, args=(5000,), daemon=True)
    server_thread.start()

    # UDPパラメータサーバの起動
    param_server_thread = threading.Thread(target=udp_param_server_thread, args=(5001,), daemon=True)
    param_server_thread.start()

    # tkinter ウィンドウ作成
    global root, text_box
    root = tk.Tk()
    root.title("UDP Phase Monitor")

    # スクロール付きテキストボックスの作成
    text_box = scrolledtext.ScrolledText(root, width=90, height=20)
    text_box.pack(padx=10, pady=10)

    # 表示更新を開始
    root.after(0, lambda: update_display(root, text_box, agent_data))

    # メインループ開始
    root.mainloop()

if __name__ == "__main__":
    main()