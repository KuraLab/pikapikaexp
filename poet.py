import numpy as np
import simpleaudio as sa

# 二進数の詩
# 二進数の詩（新作）
binary_poem = (
    "01101001"
    "10010110"
    "11110000"
    "00001111"
    "01011010"
    "10100101"
    "11000011"
    "00111100"
    "00011110"
    "11100001"
    "01111000"
    "10000111"
    "10101010"
    "01010101"
    "11111111"
    "00000000"
)

# 再生設定
sampling_rate = 44100  # サンプリング周波数
note_duration = 0.2    # 1音の再生時間（秒）
frequency = 800        # 音の周波数（Hz）

# 音の生成
def generate_tone(frequency, duration, sampling_rate):
    t = np.linspace(0, duration, int(sampling_rate * duration), False)
    tone = np.sin(frequency * 2 * np.pi * t) * 0.3
    audio = tone * (2**15 - 1)
    return audio.astype(np.int16)

# 詩全体を音声データに変換
def poem_to_audio(poem, frequency, duration, sampling_rate):
    silence = np.zeros(int(sampling_rate * duration), dtype=np.int16)
    tone = generate_tone(frequency, duration, sampling_rate)

    audio_sequence = []
    for bit in poem:
        audio_sequence.append(tone if bit == '1' else silence)

    return np.concatenate(audio_sequence)

# 詩を再生
def play_binary_poem(poem, frequency, duration, sampling_rate):
    audio = poem_to_audio(poem, frequency, duration, sampling_rate)
    play_obj = sa.play_buffer(audio, 1, 2, sampling_rate)
    
    for i, bit in enumerate(poem, 1):
        print(f'再生中: {i}/{len(poem)}文字  [ {bit} ]', end='\r')
        sa.sleep(duration)

    play_obj.wait_done()
    print('\n再生終了')

if __name__ == '__main__':
    play_binary_poem(binary_poem, frequency, note_duration, sampling_rate)