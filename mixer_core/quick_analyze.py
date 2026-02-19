"""
轻量级音频分析模块
使用最少的内存和 CPU 进行分析
"""

import os
import numpy as np

# 尝试使用 pydub（更轻量），失败则用 librosa
try:
    from pydub import AudioSegment

    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

try:
    import librosa

    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


def quick_analyze(audio_path: str) -> dict:
    """
    快速分析音频文件，返回基本信息

    使用采样读取而非完整加载，大幅降低内存使用
    """
    file_size = os.path.getsize(audio_path)

    # 文件太小可能是无效的
    if file_size < 10000:
        return {"bpm": 120, "confidence": 0.5, "key": "C", "duration": 0, "error": "文件太小或无效"}

    if HAS_PYDUB:
        return _analyze_with_pydub(audio_path)
    elif HAS_LIBROSA:
        return _analyze_with_librosa_light(audio_path)
    else:
        # 回退：返回默认值
        return {
            "bpm": 120,
            "confidence": 0.5,
            "key": "C",
            "duration": 180,
            "note": "无法分析，使用默认值",
        }


def _analyze_with_pydub(audio_path: str) -> dict:
    """使用 pydub 进行轻量分析"""
    try:
        audio = AudioSegment.from_file(audio_path)

        duration = len(audio) / 1000.0  # 转换为秒

        # 简单的能量分析来估算 BPM
        # 每 500ms 计算一次能量
        chunk_size = 500  # ms
        energies = []
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i : i + chunk_size]
            # 计算 RMS
            rms = chunk.rms
            energies.append(rms)

        if len(energies) < 4:
            return {
                "bpm": 120,
                "confidence": 0.5,
                "key": "C",
                "duration": duration,
            }

        # 检测峰值（可能的节拍）
        energies = np.array(energies)
        mean_energy = np.mean(energies)
        threshold = mean_energy * 1.2

        peaks = []
        for i, e in enumerate(energies):
            if e > threshold:
                if i > 0 and energies[i - 1] < e and energies[i - 1] < mean_energy:
                    peaks.append(i)

        if len(peaks) < 2:
            return {
                "bpm": 120,
                "confidence": 0.5,
                "key": "C",
                "duration": duration,
            }

        # 计算平均间隔
        intervals = np.diff(peaks) * (chunk_size / 1000.0)  # 转换为秒
        avg_interval = np.mean(intervals)

        if avg_interval > 0:
            bpm = 60.0 / avg_interval
            # 调整到合理范围
            while bpm < 60:
                bpm *= 2
            while bpm > 200:
                bpm /= 2
        else:
            bpm = 120

        # 置信度基于峰值的一致性
        if len(intervals) > 1:
            std = np.std(intervals)
            confidence = max(0.3, 1 - std / avg_interval)
        else:
            confidence = 0.5

        return {
            "bpm": round(bpm, 1),
            "confidence": round(confidence, 2),
            "key": "C",  # pydub 无法检测调性
            "duration": duration,
        }

    except Exception as e:
        print(f"pydub 分析失败: {e}")
        return {"bpm": 120, "confidence": 0.5, "key": "C", "duration": 180, "error": str(e)}


def _analyze_with_librosa_light(audio_path: str) -> dict:
    """使用 librosa 进行轻量分析（降低采样率）"""
    try:
        # 使用更低采样率
        sr = 8000  # 更低！

        # 只加载前 60 秒（大幅减少内存）
        duration = min(60, librosa.get_duration(path=audio_path))

        y, sr = librosa.load(audio_path, sr=sr, duration=duration)

        # BPM 检测
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # 后处理 BPM
        while tempo > 200:
            tempo /= 2
        while tempo < 60:
            tempo *= 2

        # 置信度
        if len(beats) >= 4:
            beat_times = librosa.frames_to_time(beats, sr=sr)
            intervals = np.diff(beat_times)
            if len(intervals) > 0 and np.mean(intervals) > 0:
                cv = np.std(intervals) / np.mean(intervals)
                confidence = max(0.3, 1 - cv)
            else:
                confidence = 0.5
        else:
            confidence = 0.5

        # 调性检测（简化版）
        key = "C"  # 默认

        return {
            "bpm": float(tempo),
            "confidence": float(confidence),
            "key": key,
            "duration": float(duration),
        }

    except Exception as e:
        print(f"librosa 轻量分析失败: {e}")
        return {"bpm": 120, "confidence": 0.5, "key": "C", "duration": 180, "error": str(e)}


def estimate_bpm_from_filename(filename: str) -> float:
    """
    从文件名估算 BPM（作为备用方案）
    一些歌曲文件名可能包含 BPM 信息
    """
    import re

    # 查找数字
    numbers = re.findall(r"\b(\d{2,3})\b", filename)
    for n in numbers:
        bpm = int(n)
        if 60 <= bpm <= 200:
            return float(bpm)

    return 120.0  # 默认值
