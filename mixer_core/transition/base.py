"""
过渡策略模块
"""

from abc import ABC, abstractmethod

import librosa
import numpy as np


class TransitionStrategy(ABC):
    """过渡策略基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass

    @property
    @abstractmethod
    def name_cn(self) -> str:
        """中文名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass

    @abstractmethod
    def apply(
        self, audio_a: np.ndarray, audio_b: np.ndarray, sr: int, transition_point: int
    ) -> np.ndarray:
        """
        应用过渡策略

        Args:
            audio_a: 第一首音频数据
            audio_b: 第二首音频数据
            sr: 采样率
            transition_point: 过渡点（样本索引）

        Returns:
            混合后的音频数据
        """
        pass


def detect_silence(
    audio: np.ndarray, sr: int, threshold_db: float = -40.0
) -> list[tuple[int, int]]:
    """
    检测音频中的静音段

    Args:
        audio: 音频数据
        sr: 采样率
        threshold_db: 静音阈值（分贝）

    Returns:
        [(start_sample, end_sample), ...] 静音段列表
    """
    # 计算帧能量
    frame_length = 2048
    hop_length = 512
    energy = np.array(
        [
            np.sum(audio[i : i + frame_length] ** 2)
            for i in range(0, len(audio) - frame_length, hop_length)
        ]
    )

    # 转换为分贝
    energy_db = 10 * np.log10(energy + 1e-10)

    # 找出静音帧
    silent_frames = energy_db < threshold_db

    # 找出静音段的起始和结束
    silence_segments = []
    in_silence = False
    start_frame = 0

    for i, is_silent in enumerate(silent_frames):
        if is_silent and not in_silence:
            start_frame = i
            in_silence = True
        elif not is_silent and in_silence:
            start_sample = start_frame * hop_length
            end_sample = i * hop_length
            silence_segments.append((start_sample, end_sample))
            in_silence = False

    # 处理末尾的静音
    if in_silence:
        start_sample = start_frame * hop_length
        end_sample = len(audio)
        silence_segments.append((start_sample, end_sample))

    return silence_segments


def find_nearest_beat(transition_point: int, beats: list[float], sr: int) -> int:
    """
    找到最近的节拍点

    Args:
        transition_point: 目标过渡点（样本）
        beats: 节拍时间列表（秒）
        sr: 采样率

    Returns:
        调整后的过渡点（样本）
    """
    if not beats:
        return transition_point

    # 转换节拍时间为样本位置
    beat_samples = [int(b * sr) for b in beats]

    # 找到最近的节拍
    closest_beat = min(beat_samples, key=lambda b: abs(b - transition_point))

    # 确保在有效范围内
    if closest_beat < 0:
        closest_beat = beat_samples[0]
    if closest_beat > len(beats) * sr:
        closest_beat = beat_samples[-1]

    return closest_beat


def smooth_fade_curve(n_samples: int, curve_type: str = "sigmoid") -> np.ndarray:
    """
    生成平滑的淡入淡出曲线

    Args:
        n_samples: 样本数
        curve_type: 曲线类型 (linear, sigmoid, cosine, equal_power)

    Returns:
        淡入淡出曲线数组
    """
    t = np.linspace(0, 1, n_samples)

    if curve_type == "linear":
        return t
    elif curve_type == "cosine":
        return 0.5 - 0.5 * np.cos(2 * np.pi * t)
    elif curve_type == "sigmoid":
        # Sigmoid 曲线
        return 1 / (1 + np.exp(-10 * (t - 0.5)))
    elif curve_type == "equal_power":
        # 相等功率曲线（更自然的听感）
        return np.sin(t * np.pi / 2)
    else:
        return t


class CrossfadeStrategy(TransitionStrategy):
    """Crossfade 淡入淡出策略"""

    def __init__(
        self,
        fade_duration: float = 10.0,
        curve_type: str = "equal_power",
        align_to_beat: bool = True,
        skip_silence: bool = True,
    ):
        self._fade_duration = fade_duration
        self._curve_type = curve_type
        self._align_to_beat = align_to_beat
        self._skip_silence = skip_silence

    @property
    def name(self) -> str:
        return "crossfade"

    @property
    def name_cn(self) -> str:
        return "淡入淡出"

    @property
    def description(self) -> str:
        return "通过音量淡入淡出实现两首歌曲的平滑过渡"

    def apply(
        self,
        audio_a: np.ndarray,
        audio_b: np.ndarray,
        sr: int,
        transition_point: int,
        beats_a: list[float] | None = None,
        beats_b: list[float] | None = None,
        transition_point_b: float = 0,
    ) -> np.ndarray:
        fade_samples = int(self._fade_duration * sr)

        start_b = int(transition_point_b * sr) if transition_point_b > 0 else 0
        if start_b >= len(audio_b):
            start_b = 0

        if transition_point < fade_samples:
            fade_samples = transition_point

        if self._skip_silence:
            silence_segments = detect_silence(audio_a[transition_point - fade_samples :], sr)
            if silence_segments:
                fade_samples = min(fade_samples, len(audio_a) - transition_point)

        if self._align_to_beat and beats_a:
            transition_point = find_nearest_beat(transition_point, beats_a, sr)
            if transition_point < fade_samples:
                transition_point = fade_samples

        fade_samples = min(fade_samples, transition_point)

        fade_out_curve = smooth_fade_curve(fade_samples, self._curve_type)[::-1]
        fade_in_curve = smooth_fade_curve(fade_samples, self._curve_type)

        b_available = audio_b[start_b:]
        tail_b = max(0, len(b_available) - fade_samples)
        result_len = max(len(audio_a), transition_point) + tail_b
        result = np.zeros(result_len)

        copy_a = min(len(audio_a), transition_point - fade_samples)
        if copy_a > 0:
            result[:copy_a] = audio_a[:copy_a]

        a_fade_start = max(0, transition_point - fade_samples)
        a_fade_len = min(fade_samples, len(audio_a) - a_fade_start)
        if a_fade_len > 0:
            fade_out_data = audio_a[a_fade_start : a_fade_start + a_fade_len].copy()
            fade_out_data *= fade_out_curve[-a_fade_len:]
            result[a_fade_start : a_fade_start + a_fade_len] = fade_out_data

        b_fade_samples = min(fade_samples, len(b_available))
        b_fade_data = b_available[:b_fade_samples].copy()
        b_fade_data *= fade_in_curve[:b_fade_samples]

        overlap_start = a_fade_start
        overlap_len = min(b_fade_samples, result_len - overlap_start)
        result[overlap_start : overlap_start + overlap_len] += b_fade_data[:overlap_len]

        if b_fade_samples < len(b_available):
            b_remaining = b_available[b_fade_samples:]
            rem_start = overlap_start + overlap_len
            copy_len = min(len(b_remaining), result_len - rem_start)
            result[rem_start : rem_start + copy_len] = b_remaining[:copy_len]

        return result


class BeatSyncStrategy(TransitionStrategy):
    """Beat-sync 节拍对齐策略"""

    def __init__(
        self,
        max_stretch: float = 0.15,
        fade_duration: float = 10.0,
        curve_type: str = "equal_power",
        align_to_beat: bool = True,
    ):
        self._max_stretch = max_stretch
        self._fade_duration = fade_duration
        self._curve_type = curve_type
        self._align_to_beat = align_to_beat

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
        self,
        audio_a: np.ndarray,
        audio_b: np.ndarray,
        sr: int,
        transition_point: int,
        beats_a: list[float] | None = None,
        beats_b: list[float] | None = None,
        transition_point_b: float = 0,
    ) -> np.ndarray:
        # 使用优化的 Crossfade（带节拍对齐）
        crossfade = CrossfadeStrategy(
            fade_duration=self._fade_duration,
            curve_type=self._curve_type,
            align_to_beat=self._align_to_beat,
            skip_silence=True,
        )
        return crossfade.apply(
            audio_a, audio_b, sr, transition_point, beats_a, beats_b, transition_point_b
        )


# 策略工厂
class TransitionFactory:
    """过渡策略工厂"""

    _strategies = {
        "crossfade": CrossfadeStrategy,
        "beat_sync": BeatSyncStrategy,
    }

    @classmethod
    def _init_strategies(cls):
        """动态加载额外策略"""
        try:
            from mixer_core.transition.echo_fade import EchoFadeStrategy

            cls._strategies["echo_fade"] = EchoFadeStrategy
        except ImportError:
            pass

        try:
            from mixer_core.transition.harmonic import HarmonicMixStrategy

            cls._strategies["harmonic"] = HarmonicMixStrategy
        except ImportError:
            pass

    @classmethod
    def create(cls, strategy_name: str, **kwargs) -> TransitionStrategy:
        """创建策略实例"""
        cls._init_strategies()
        strategy_class = cls._strategies.get(strategy_name.lower())
        if strategy_class is None:
            raise ValueError(f"未知策略: {strategy_name}")
        return strategy_class(**kwargs)

    @classmethod
    def list_strategies(cls) -> list[str]:
        """列出所有可用策略"""
        cls._init_strategies()
        return list(cls._strategies.keys())
