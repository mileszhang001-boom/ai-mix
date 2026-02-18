"""
Beat-sync 过渡策略
通过时间拉伸让两首歌 BPM 一致
"""

import logging

import librosa
import numpy as np

from mixer_core.transition.base import CrossfadeStrategy

logger = logging.getLogger(__name__)


class BeatSyncStrategy:
    """Beat-sync 节拍对齐策略"""

    def __init__(self, max_stretch: float = 0.15, fade_duration: float = 5.0):
        """
        初始化 Beat-sync 策略

        Args:
            max_stretch: 最大拉伸比例（默认 15%）
            fade_duration: 淡入淡出持续时间（秒）
        """
        self._max_stretch = max_stretch
        self._fade_duration = fade_duration

    @property
    def name(self) -> str:
        return "beat_sync"

    @property
    def name_cn(self) -> str:
        return "节拍对齐"

    @property
    def description(self) -> str:
        return "通过时间拉伸让两首歌 BPM 一致，实现节奏对齐"

    def apply(
        self, audio_a: np.ndarray, audio_b: np.ndarray, sr: int, transition_point: int
    ) -> np.ndarray:
        """
        应用 Beat-sync 过渡

        Args:
            audio_a: 第一首音频数据
            audio_b: 第二首音频数据
            sr: 采样率
            transition_point: 过渡点（样本索引）

        Returns:
            混合后的音频数据
        """
        # 获取音频 B 的 BPM（需要从外部传入或重新检测）
        # 这里简化处理，假设 BPM 已知
        # 实际实现中需要先分析两首歌曲的 BPM

        # 使用 Crossfade 作为基础实现
        # TODO: 实现真正的时间拉伸
        return CrossfadeStrategy(self._fade_duration).apply(audio_a, audio_b, sr, transition_point)

    def can_apply(self, bpm_a: float, bpm_b: float) -> tuple[bool, float]:
        """
        检查是否可以应用 Beat-sync

        Args:
            bpm_a: 第一首歌曲 BPM
            bpm_b: 第二首歌曲 BPM

        Returns:
            (是否可以应用, 需要的拉伸比例)
        """
        if bpm_a == 0 or bpm_b == 0:
            return False, 0.0

        stretch_ratio = bpm_b / bpm_a

        # 检查是否在允许范围内
        if 1.0 - self._max_stretch <= stretch_ratio <= 1.0 + self._max_stretch:
            return True, stretch_ratio

        return False, stretch_ratio


def time_stretch(audio: np.ndarray, sr: int, target_duration: float) -> np.ndarray:
    """
    时间拉伸音频到目标时长

    Args:
        audio: 音频数据
        sr: 采样率
        target_duration: 目标时长（秒）

    Returns:
        拉伸后的音频
    """
    current_duration = len(audio) / sr
    rate = current_duration / target_duration

    logger.info(f"时间拉伸: {current_duration:.1f}s -> {target_duration:.1f}s, rate={rate:.3f}")

    # 使用 librosa 的时间拉伸
    # 注意：过大的拉伸会有失真
    stretched = librosa.effects.time_stretch(audio, rate=rate)

    return stretched


def stretch_to_target_bpm(
    audio: np.ndarray, sr: int, current_bpm: float, target_bpm: float
) -> tuple[np.ndarray, float]:
    """
    将音频拉伸到目标 BPM

    Args:
        audio: 音频数据
        sr: 采样率
        current_bpm: 当前 BPM
        target_bpm: 目标 BPM

    Returns:
        (拉伸后的音频, 实际拉伸比例)
    """
    if abs(current_bpm - target_bpm) < 0.1:
        return audio, 1.0

    # 计算需要的拉伸比例
    stretch_ratio = current_bpm / target_bpm

    # 检查是否在允许范围内
    max_stretch = 0.15  # 15%
    if abs(stretch_ratio - 1.0) > max_stretch:
        logger.warning(f"拉伸比例 {stretch_ratio:.3f} 超过限制 {max_stretch}，使用最大允许拉伸")
        stretch_ratio = 1.0 + max_stretch if stretch_ratio > 1.0 else 1.0 - max_stretch

    # 计算目标时长
    current_duration = len(audio) / sr
    target_duration = current_duration * stretch_ratio

    # 执行拉伸
    stretched = librosa.effects.time_stretch(audio, rate=stretch_ratio)

    logger.info(
        f"BPM {current_bpm:.1f} -> {target_bpm:.1f}, "
        f"时长 {current_duration:.1f}s -> {len(stretched) / sr:.1f}s"
    )

    return stretched, stretch_ratio
