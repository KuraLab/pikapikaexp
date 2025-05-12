import socket
import threading
import math
import time
import os
import csv
import datetime
import numpy as np
import tkinter as tk
from tkinter import scrolledtext
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from ParamBroadcast import udp_param_server_thread
from display_utils import update_display

# -------------------------
# 受信データの保管（各エージェント毎に (補正済みタイムスタンプ, 位相) のリスト）
# -------------------------
agent_history = {}  # agent_history[agent_id] = [(corrected_ts, phi), ...]
MAX_POINTS = 100000   # 各エージェントごとに保持する最大データ数

# 各エージェントの offset（サーバ受信時刻 - エージェントタイムスタンプ）の履歴
agent_offset_history = {}  # agent_offset_history[agent_id] = [offset, ...]
# オフセット平均を求める際に使用する過去データの件数（MAX_POINTSより少ない値に設定）
OFFSET_AVG_POINTS = 500

# プロット用の履歴（各エージェントの位相差を時系列に保存）
time_history = []           # 最新時刻が0となる相対時間の履歴
pairs_diff_history = {}     # pairs_diff_history[agent_id] = [phase_diff, ...]
pairs_lines = {}            # matplotlib の Line2D オブジェクトを保持

# 参照エージェント（最初に受信したエージェントを使用）
reference_agent = None

# サーバ側のタイムステップ管理用（前回 update() 実行時刻）
last_update_time = None

# -------------------------
# UDPサーバ（データ受信スレッド）
# -------------------------
def udp_server_thread(port=5000):
    """
    "ID=1,PHI=0.123456,TS=1690000000.123456,V=3.300000,Vbat=3.300000" の形式で受信し、
    各エージェントの履歴に、補正済みのタイムスタンプ、位相、光センサ電圧、バッテリー電圧を記録する。
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"[INFO] UDP server listening on port {port}")
    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode(errors='ignore').strip()
        try:
            parts = msg.split(',')
            # 各フィールドを抽出
            id_str    = parts[0].split('=')[1]
            phi_str   = parts[1].split('=')[1]
            ts_str    = parts[2].split('=')[1]
            sensor_str = parts[3].split('=')[1]   # 光センサ電圧 V
            vbat_str  = parts[4].split('=')[1]      # バッテリー電圧 Vbat

            agent_id = int(id_str)
            phi_val  = float(phi_str)
            ts_val   = float(ts_str)
            sensor_v = float(sensor_str)
            battery_v= float(vbat_str)
            
            # サーバ側でメッセージを受信した時刻
            recv_time = time.time()
            # 現在のオフセット = (受信時刻 - エージェントのタイムスタンプ)
            offset = recv_time - ts_val

            # 各エージェントごとにオフセットの履歴を更新
            if agent_id not in agent_offset_history:
                agent_offset_history[agent_id] = []
            agent_offset_history[agent_id].append(offset)
            if len(agent_offset_history[agent_id]) > MAX_POINTS:
                agent_offset_history[agent_id].pop(0)

            # 直近 OFFSET_AVG_POINTS 件で平均を算出
            recent_offsets = agent_offset_history[agent_id][-OFFSET_AVG_POINTS:]
            avg_offset = sum(recent_offsets) / len(recent_offsets)
            # 補正済みタイムスタンプ
            corrected_ts = ts_val + avg_offset

            # 履歴に追加（タプルに補正済みタイムスタンプ, 位相, 光センサ電圧, バッテリー電圧を含める）
            if agent_id not in agent_history:
                agent_history[agent_id] = []
            agent_history[agent_id].append((corrected_ts, phi_val, sensor_v, battery_v))
            if len(agent_history[agent_id]) > MAX_POINTS:
                agent_history[agent_id].pop(0)
        except Exception as e:
            print(f"[WARN] Parse error: {e}, msg={msg}")


def export_plot_data():
    """
    現在プロットに使用している位相差の時系列データを、
    タイムスタンプと各エージェントの位相差を横並びにして1つの CSV ファイルへエクスポートする関数
    （エージェントが n 個なら、タイムスタンプ＋各エージェントで n+1 列となる）
    """
    # 各エージェントのデータ数の最大値を求める
    max_points = max(len(phase_diffs) for phase_diffs in pairs_diff_history.values())
    # 全体のタイムスタンプは最新が先頭なので、上位 max_points 個を取り、古い順に並べる
    times = time_history[:max_points][::-1]

    # CSVのヘッダー：最初の列がタイムスタンプ、残りは各エージェントの位相差
    # エージェントID順にソートしておく
    agent_ids = sorted(pairs_diff_history.keys())
    header = ["time (s)"] + [f"phase_diff_agent_{agent_id}" for agent_id in agent_ids]

    # 保存先フォルダを指定し、存在しなければ作成
    save_dir = "exported_data"
    os.makedirs(save_dir, exist_ok=True)
    
    # 日時情報をファイル名に付加（例: 20250220_143205）
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"phase_diff_all_agents_{now_str}.csv")
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        # 各行はタイムスタンプと、各エージェントの位相差を対応付けて出力
        for i in range(max_points):
            row = [times[i]]
            for agent_id in agent_ids:
                phase_diffs = pairs_diff_history[agent_id]
                # 各エージェントのデータ数が max_points に満たない場合、先頭を空欄にする
                missing = max_points - len(phase_diffs)
                if i < missing:
                    row.append("")
                else:
                    # phase_diffs は最新が先頭なので、古い順にするため反転して対応する値を取得
                    row.append(phase_diffs[::-1][i - missing])
            writer.writerow(row)
    print(f"[INFO] Exported all data to {filename}")



def on_key(event):
    if event.key.lower() == "e":
        print("[INFO] Exporting plotted phase difference data...")
        export_plot_data()



# -------------------------
# 位相ラップ関数：-π < angle <= π
# -------------------------
def wrap_angle(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi

# -------------------------
# matplotlib の設定
# -------------------------
fig, ax = plt.subplots()
ax.set_title("Phase Differences (Interpolated at Server Time)")
ax.set_xlabel("Time (seconds, latest = 0)")
ax.set_ylabel("Phase Difference (radians)")
ax.set_ylim(-math.pi, math.pi)
ax.set_xlim(-30, 0)  # 過去30秒分を表示（必要に応じて変更）
ax.grid(True, axis='y', linestyle='--', alpha=0.7)

# -------------------------
# アニメーション初期化関数
# -------------------------
def init():
    return []

# -------------------------
# アニメーション更新関数（サーバ側のタイムステップ毎に呼ばれる）
# -------------------------
def update(frame):
    global last_update_time, reference_agent, time_history

    current_time = time.time()

    if last_update_time is None:
        last_update_time = current_time
        return []

    dt = current_time - last_update_time
    last_update_time = current_time

    # 相対時刻の履歴を更新：最新データは 0、既存は dt だけシフト（古いほど負の値）
    time_history = [t - dt for t in time_history]
    time_history.insert(0, 0)
    if len(time_history) > MAX_POINTS:
        time_history.pop()

    # 受信済みエージェントのIDリスト
    sorted_ids = sorted(agent_history.keys())
    if not sorted_ids:
        return []
    if reference_agent is None:
        reference_agent = sorted_ids[0]
    if reference_agent not in agent_history or len(agent_history[reference_agent]) < 2:
        return []

    # 補完に使うデータ点数（変数化）
    n_points_for_interp = 100

    # 参照エージェントの直近 n_points_for_interp 個のデータを取得
    recent_ref = (agent_history[reference_agent][-n_points_for_interp:]
                  if len(agent_history[reference_agent]) >= n_points_for_interp
                  else agent_history[reference_agent])
    ref_times = np.array([pt[0] for pt in recent_ref])
    ref_phis  = np.array([pt[1] for pt in recent_ref])

    # 各エージェントについて
    for agent_id in sorted_ids:
        if agent_id == reference_agent:
            continue
        if len(agent_history[agent_id]) < 2:
            continue

        # 対象エージェントの直近 n_points_for_interp 個のデータを取得
        recent_agent = (agent_history[agent_id][-n_points_for_interp:]
                        if len(agent_history[agent_id]) >= n_points_for_interp
                        else agent_history[agent_id])
        agent_times = np.array([pt[0] for pt in recent_agent])
        agent_phis  = np.array([pt[1] for pt in recent_agent])

        # それぞれのデータのタイムスタンプが覆う範囲の重なりを計算
        overlap_start = max(ref_times[0], agent_times[0])
        overlap_end   = min(ref_times[-1], agent_times[-1])
        if overlap_start >= overlap_end:
            # 重なりがない場合は current_time を採用（もしくはスキップ）
            mid_time = current_time
            #print("no overlap")
        else:
            mid_time = (overlap_start + overlap_end) / 2.0

        # mid_time での補間を行う
        ref_phase_mid = np.interp(mid_time, ref_times, ref_phis)
        agent_phase_mid = np.interp(mid_time, agent_times, agent_phis)
        phase_diff = wrap_angle(agent_phase_mid - ref_phase_mid)

        # 補完結果の履歴に追加（最新を先頭に）
        if agent_id not in pairs_diff_history:
            pairs_diff_history[agent_id] = []
        pairs_diff_history[agent_id].insert(0, phase_diff)
        if len(pairs_diff_history[agent_id]) > MAX_POINTS:
            pairs_diff_history[agent_id].pop()

        # プロット用 Line2D オブジェクトの作成／更新
        if agent_id not in pairs_lines:
            line, = ax.plot([], [], label=f"Ref-{reference_agent} vs {agent_id}")
            pairs_lines[agent_id] = line
        n_points = len(pairs_diff_history[agent_id])
        x_data = time_history[:n_points]  # 最新の n_points 分の相対時刻
        y_data = pairs_diff_history[agent_id]

        # 位相差の連続性チェック：前後の差が pi を超える場合、途中に NaN を挟む
        new_x_data = []
        new_y_data = []
        prev_y = None
        for x, y in zip(x_data, y_data):
            if prev_y is not None and abs(y - prev_y) > math.pi:
                new_x_data.append(x)  # NaN を挟む位置の x 値（任意ですがそのままで可）
                new_y_data.append(np.nan)
            new_x_data.append(x)
            new_y_data.append(y)
            prev_y = y

        pairs_lines[agent_id].set_data(new_x_data, new_y_data)


    ax.legend(loc='upper right')
    return list(pairs_lines.values())


# matplotlib の図にキーイベントを登録
fig.canvas.mpl_connect("key_press_event", on_key)

# -------------------------
# メイン処理
# -------------------------
def main():
    # UDP受信スレッドの開始
    t = threading.Thread(target=udp_server_thread, args=(5000,), daemon=True)
    t.start()

    # UDPパラメータサーバの起動
    param_server_thread = threading.Thread(target=udp_param_server_thread, args=(5001,), daemon=True)
    param_server_thread.start()
    
    # matplotlib のアニメーション開始（10ms間隔で更新）
    ani = animation.FuncAnimation(fig, update, init_func=init, interval=10, blit=False, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    main()
