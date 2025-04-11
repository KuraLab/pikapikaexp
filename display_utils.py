# display_utils.py

import tkinter as tk
import math

def wrap_angle(angle):
    """
    与えられた角度を -pi < angle <= pi にラップする。
    """
    return (angle + math.pi) % (2 * math.pi) - math.pi

def update_display(root, text_box, agent_data):
    """
    定期的にagent_dataの内容をテキストボックスに表示更新する。
    """
    text_box.delete('1.0', tk.END)  # テキストボックスをクリア

    if agent_data:
        sorted_ids = sorted(agent_data.keys())
        text_box.insert(tk.END, "=== Current Agent Data ===\n")
        for aid in sorted_ids:
            phi_val, ts_val, sensor_v, battery_v = agent_data[aid]
            text_box.insert(
                tk.END,
                f"Agent {aid}: TS = {ts_val:.5f}, phi = {phi_val:.5f}, "
                f"sensorV = {sensor_v:.5f}, batteryV = {battery_v:.5f}\n"
            )

        if len(sorted_ids) >= 2:
            text_box.insert(tk.END, "\n--- Phase Differences (wrapped) ---\n")
            for i in range(len(sorted_ids)):
                for j in range(i+1, len(sorted_ids)):
                    id_i = sorted_ids[i]
                    id_j = sorted_ids[j]
                    phi_i = agent_data[id_i][0]
                    phi_j = agent_data[id_j][0]
                    diff_raw = phi_i - phi_j
                    diff_wrapped = wrap_angle(diff_raw)
                    text_box.insert(
                        tk.END,
                        f"Agent {id_i} - Agent {id_j}: diff = {diff_wrapped:.5f}\n"
                    )
    else:
        text_box.insert(tk.END, "No data yet...\n")

    # 再度10ms後にこの関数を呼び出す
    root.after(10, lambda: update_display(root, text_box, agent_data))