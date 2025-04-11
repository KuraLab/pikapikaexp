% CSVファイルの読み込み（例: phase_diff_agent_2.csv）
% CSVファイルのヘッダーが "time (s)" と "phase_diff (radians)" になっているとします。
data = readtable('phase_diff_agent_2.csv');

% 各列のデータを取り出す
time_data = data{:, 1};       % 1列目：相対時刻
phase_diff = data{:, 2};      % 2列目：位相差

% プロット（NaNが含まれている場合は線が途切れる）
figure;
%plot(time_data, phase_diff);
plot(phase_diff);
xlabel('Time (s)');
ylabel('Phase Difference (radians)');
title('Phase Difference from Agent 2');
grid on;

figure
hold on
sp = 5514;
ep = 6454;
h3 = plot(time_data(sp:ep)-time_data(sp), phase_diff(sp:ep), 'DisplayName', '$$d = 50$$');
sp = 6772;
ep = 7702;
h2 = plot(time_data(sp:ep)-time_data(sp), phase_diff(sp:ep), 'DisplayName', '$$d = 100$$');
sp = 1075;
ep = 2078;
h1 = plot(time_data(sp:ep)-time_data(sp), phase_diff(sp:ep), 'DisplayName', '$$d = 200$$');
set(gca, 'XGrid', 'off', 'YGrid', 'on');
legend('show')
ylabel("$$\phi_1-\phi_2$$")
xlabel("Time $$t$$")
ylim([-0.5,pi])
xlim([0,20])
tuneFigure;