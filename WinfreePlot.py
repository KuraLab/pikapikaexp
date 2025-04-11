import numpy as np
import matplotlib.pyplot as plt

# 変数の設定
phi = np.linspace(-np.pi, np.pi, 1000)
alpha = np.pi / 2  # 任意のalpha

# 上段：-sin
y1 = -np.sin(phi)

# 中段：cos(φ + α) > 0.9 で1、それ以外0
cos_val = np.cos(phi + alpha)
y2 = np.where(cos_val > 0.9, 1, 0)

# 下段：積
y3 = y1 * y2

# プロット
fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

# フォントサイズ設定
label_fontsize = 30
tick_fontsize = 20
plt.rcParams.update({'font.size': tick_fontsize})

# 目盛り設定（π単位）
xticks = [-np.pi, -np.pi/2, 0, np.pi/2, np.pi]
xtick_labels = [r'$-\pi$', r'$-\frac{\pi}{2}$', r'$0$', 
                r'$\frac{\pi}{2}$', r'$\pi$']

# 各軸にプロットとラベル
axs[0].plot(phi, y1)
axs[0].set_ylabel(r'$z(\phi_j)$', fontsize=label_fontsize)
axs[0].tick_params(axis='both', labelsize=tick_fontsize)
axs[0].grid(True)

axs[1].plot(phi, y2)
axs[1].set_ylabel(r'$s(t)$', fontsize=label_fontsize)
axs[1].tick_params(axis='both', labelsize=tick_fontsize)
axs[1].grid(True)

axs[2].plot(phi, y3)
axs[2].set_ylabel(r'$z(\phi_j) \cdot s(t)$', fontsize=label_fontsize)
axs[2].set_xlabel(r'$\phi_j$', fontsize=label_fontsize)
axs[2].set_xticks(xticks)
axs[2].set_xticklabels(xtick_labels, fontsize=tick_fontsize)
axs[2].tick_params(axis='both', labelsize=tick_fontsize)
axs[2].grid(True)

plt.tight_layout()
plt.show()
