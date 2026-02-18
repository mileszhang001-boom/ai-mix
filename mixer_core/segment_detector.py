"""
歌曲结构分析模块
检测前奏(Intro)、主歌(Verse)、副歌(Chorus)、尾奏(Outro)
支持 Downbeat 对齐和能量匹配
"""

import logging

import librosa
import numpy as np

logger = logging.getLogger(__name__)


def detect_segments(audio_path: str, sr: int = 22050) -> dict:
    """
    检测歌曲结构：前奏、主歌、副歌、尾奏

    Returns:
        dict: 包含 intro_start, intro_end, verse_start, chorus_start, outro_start, outro_end, energy_curve 等
    """
    logger.info(f"开始歌曲结构分析: {audio_path}")

    y, sr = librosa.load(audio_path, sr=sr)
    duration = len(y) / sr

    # 方法1：基于能量的段落检测
    energy_curve = compute_energy_curve(y, sr)
    energy_times = np.linspace(0, duration, len(energy_curve))

    # 检测前奏结束位置（能量开始上升的点）
    intro_end = detect_intro_end(energy_curve, sr)

    # 检测尾奏开始位置（能量开始持续下降的点）
    outro_start = detect_outro_start(energy_curve, sr, duration)

    # 获取节拍信息用于 downbeat 对齐
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # 获取 downbeats（每小节第一拍）
    downbeats = beat_times[::4] if len(beat_times) >= 4 else beat_times

    # 在尾奏区域找最近的 downbeat
    outro_downbeat = find_nearest_downbeat_before(outro_start, downbeats)

    # 在前奏结束后找第一个 downbeat
    intro_downbeat = find_nearest_downbeat_after(intro_end, downbeats)

    # 激进版：前奏最多 5%，尾奏最多 20%
    intro_end = min(intro_end, duration * 0.05)
    outro_start = max(outro_start, duration * 0.80)

    # 计算能量统计
    energy_mean = np.mean(energy_curve)
    energy_std = np.std(energy_curve)

    # 在过渡区域找到能量匹配的点
    transition_energy_point = find_energy_matching_point(
        energy_curve, energy_times, outro_start, duration, energy_mean
    )

    result = {
        "duration": duration,
        "intro_end": intro_end,
        "outro_start": outro_start,
        "main_body_start": intro_end,
        "main_body_end": outro_start,
        "downbeats": downbeats.tolist() if hasattr(downbeats, "tolist") else list(downbeats),
        "outro_downbeat": float(outro_downbeat) if outro_downbeat else float(outro_start),
        "intro_downbeat": float(intro_downbeat) if intro_downbeat else float(intro_end),
        "energy_mean": float(energy_mean),
        "energy_std": float(energy_std),
    }

    logger.info(
        f"歌曲结构分析完成: 前奏结束={intro_end:.1f}s, 尾奏开始={outro_start:.1f}s, 尾奏downbeat={outro_downbeat:.1f}s"
    )
    return result


def find_nearest_downbeat_before(target_time: float, downbeats: np.ndarray) -> float:
    """找到目标时间之前的最近 downbeat"""
    if len(downbeats) == 0:
        return target_time
    candidates = downbeats[downbeats <= target_time]
    if len(candidates) > 0:
        return float(candidates[-1])
    return float(downbeats[0])


def find_nearest_downbeat_after(target_time: float, downbeats: np.ndarray) -> float:
    """找到目标时间之后的最近 downbeat"""
    if len(downbeats) == 0:
        return target_time
    candidates = downbeats[downbeats >= target_time]
    if len(candidates) > 0:
        return float(candidates[0])
    return float(downbeats[-1])


def find_energy_matching_point(
    energy_curve: np.ndarray,
    energy_times: np.ndarray,
    start_time: float,
    end_time: float,
    target_energy: float,
) -> float:
    """
    在能量曲线上找到与目标能量最接近的点
    用于找到两首歌能量相近的过渡点
    """
    # 只在指定区间搜索
    mask = (energy_times >= start_time) & (energy_times <= end_time)
    if not np.any(mask):
        return start_time

    region_energy = energy_curve[mask]
    region_times = energy_times[mask]

    # 找到能量最接近目标的点
    diff = np.abs(region_energy - target_energy)
    idx = np.argmin(diff)

    return float(region_times[idx])


def compute_energy_curve(
    y: np.ndarray, sr: int, frame_length: int = 2048, hop_length: int = 512
) -> np.ndarray:
    """计算音频能量曲线"""
    energy = np.array(
        [np.sum(y[i : i + frame_length] ** 2) for i in range(0, len(y) - frame_length, hop_length)]
    )
    # 归一化
    energy = energy / (energy.max() + 1e-10)
    return energy


def detect_intro_end(energy: np.ndarray, sr: int, threshold: float = 0.25) -> float:
    """
    检测前奏结束位置
    原理：前奏能量较低，当能量持续上升超过阈值时，认为前奏结束
    """
    if len(energy) < 10:
        return 0.0

    # 计算能量的移动平均
    window = min(50, len(energy) // 10)
    energy_smooth = np.convolve(energy, np.ones(window) / window, mode="valid")

    # 找到能量首次持续超过阈值的位置
    hop_length = 512
    for i in range(len(energy_smooth)):
        if energy_smooth[i] > threshold:
            # 检查是否持续
            if i + 10 < len(energy_smooth):
                if np.mean(energy_smooth[i : i + 10]) > threshold:
                    return (i + window) * hop_length / sr

    return 0.0


def detect_outro_start(
    energy: np.ndarray, sr: int, duration: float, threshold: float = 0.25
) -> float:
    """
    检测尾奏开始位置
    原理：尾奏能量持续下降，当能量持续低于阈值时，认为尾奏开始
    """
    if len(energy) < 10:
        return duration

    # 计算能量的移动平均
    window = min(50, len(energy) // 10)
    energy_smooth = np.convolve(energy, np.ones(window) / window, mode="valid")

    # 从后往前找能量首次持续低于阈值的位置
    for i in range(len(energy_smooth) - 1, -1, -1):
        if energy_smooth[i] < threshold:
            # 检查是否持续
            if i - 10 >= 0:
                if np.mean(energy_smooth[i - 10 : i]) < threshold:
                    hop_length = 512
                    return min((i + window) * hop_length / sr, duration)

    return duration


def find_optimal_transition_point(
    audio_a_path: str, audio_b_path: str, transition_duration: float = 5.0, sr: int = 22050
) -> tuple[float, float]:
    """
    找到最佳过渡点（带 Downbeat 对齐）

    Returns:
        (transition_point_a, transition_point_b): 两首歌的最佳过渡时间（秒）
    """
    # 分析歌曲A：找到尾奏开始时间
    seg_a = detect_segments(audio_a_path, sr)

    # 使用 Outro 的 Downbeat 作为过渡点
    transition_a = seg_a.get("outro_downbeat", seg_a["outro_start"] - transition_duration)

    # 确保不过早
    transition_a = max(transition_a, seg_a["main_body_start"])

    # 分析歌曲B：找到前奏结束后的第一个 Downbeat
    seg_b = detect_segments(audio_b_path, sr)
    transition_b = seg_b.get("intro_downbeat", seg_b["intro_end"])

    logger.info(f"最佳过渡点(Downbeat对齐): 歌曲A={transition_a:.1f}s, 歌曲B={transition_b:.1f}s")

    return transition_a, transition_b
