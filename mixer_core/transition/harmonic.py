"""
调性匹配策略 (Harmonic Mix)
基于五度圈理论进行调性匹配
"""

import logging

import librosa
import numpy as np

from mixer_core.transition.base import CrossfadeStrategy

logger = logging.getLogger(__name__)

# 五度圈映射
# C -> G -> D -> A -> E -> B -> F# -> Db -> Ab -> Eb -> Bb -> F -> C
CIRCLE_OF_FIFTHS = {
    "C": 0,
    "G": 1,
    "D": 2,
    "A": 3,
    "E": 4,
    "B": 5,
    "F#": 6,
    "Db": 7,
    "Ab": 8,
    "Eb": 9,
    "Bb": 10,
    "F": 11,
    "Am": 0,
    "Em": 1,
    "Bm": 2,
    "F#m": 3,
    "C#m": 4,
    "G#m": 5,
    "Ebm": 6,
    "Bbm": 7,
    "Fm": 8,
    "Cm": 9,
    "Gm": 10,
    "Dm": 11,
}

# 和谐调性对（距离 0-2 或 10-11）
HARMONIC_COMPATIBLE = {
    0: [0, 1, 2, 7, 8, 9, 10, 11],  # C 大调
    1: [0, 1, 2, 3, 8, 9, 10],  # G 大调
    2: [0, 1, 2, 3, 4, 9, 10],  # D 大调
    # ... 更多
}


def detect_key(audio_path: str, sr: int = 16000) -> tuple[str, int]:
    """
    检测歌曲调性

    Returns:
        (key_name, key_number): 如 ("C", 0) 或 ("Am", 0)
    """
    y, sr = librosa.load(audio_path, sr=sr)

    # 使用色度特征检测调性
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    # 平均色度
    chroma_mean = np.mean(chroma, axis=1)

    # 简化的调性检测
    # C 大调: C, D, E, F, G, A, B
    # 对应 chroma 索引: 0, 2, 4, 5, 7, 9, 11
    major_pattern = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])  # C major
    minor_pattern = np.array([1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0])  # A minor

    # 尝试每个调
    best_key = "C"
    best_score = 0

    keys = [
        "C",
        "G",
        "D",
        "A",
        "E",
        "B",
        "F#",
        "Db",
        "Ab",
        "Eb",
        "Bb",
        "F",
        "Am",
        "Em",
        "Bm",
        "F#m",
        "C#m",
        "G#m",
        "Ebm",
        "Bbm",
        "Fm",
        "Cm",
        "Gm",
        "Dm",
    ]

    for key in keys:
        is_minor = "m" in key
        root = key.replace("m", "")
        if root not in [
            "C",
            "C#",
            "Db",
            "D",
            "D#",
            "Eb",
            "E",
            "F",
            "F#",
            "Gb",
            "G",
            "G#",
            "Ab",
            "A",
            "A#",
            "Bb",
            "B",
        ]:
            continue

        # 旋转模式
        pattern = minor_pattern if is_minor else major_pattern
        score = np.dot(chroma_mean, pattern)

        if score > best_score:
            best_score = score
            best_key = key

    key_number = CIRCLE_OF_FIFTHS.get(best_key, 0)

    logger.info(f"检测到调性: {best_key} (五度圈位置: {key_number})")

    return best_key, key_number


def calculate_harmonic_distance(key1: int, key2: int) -> int:
    """计算两个调性在五度圈上的距离"""
    distance = abs(key1 - key2)
    return min(distance, 12 - distance)


def is_harmonic_compatible(key1: int, key2: int) -> bool:
    """检查两个调性是否和谐"""
    distance = calculate_harmonic_distance(key1, key2)
    # 距离 0-2 或 10-12 是和谐的
    return distance <= 2 or distance >= 10


class HarmonicMixStrategy(CrossfadeStrategy):
    """Harmonic Mix 调性匹配策略"""

    def __init__(
        self,
        fade_duration: float = 10.0,
        prefer_harmonic: bool = True,
        curve_type: str = "equal_power",
        align_to_beat: bool = True,
        skip_silence: bool = True,
    ):
        super().__init__(fade_duration, curve_type, align_to_beat, skip_silence)
        self._prefer_harmonic = prefer_harmonic

    @property
    def name(self) -> str:
        return "harmonic"

    @property
    def name_cn(self) -> str:
        return "调性匹配"

    @property
    def description(self) -> str:
        return "基于五度圈理论，调性和谐时深度重叠，不和谐时缩短过渡"

    def apply(
        self,
        audio_a: np.ndarray,
        audio_b: np.ndarray,
        sr: int,
        transition_point: int,
        beats_a=None,
        beats_b=None,
        transition_point_b: float = 0,
        key_a: str = None,
        key_b: str = None,
    ) -> np.ndarray:
        if not key_a or not key_b:
            logger.warning("未提供调性信息，使用基础 Crossfade")
            return super().apply(
                audio_a,
                audio_b,
                sr,
                transition_point,
                beats_a=beats_a,
                beats_b=beats_b,
                transition_point_b=transition_point_b,
            )

        key_a_num = CIRCLE_OF_FIFTHS.get(key_a.replace("#", "").replace("b", ""), 0)
        key_b_num = CIRCLE_OF_FIFTHS.get(key_b.replace("#", "").replace("b", ""), 0)
        distance = calculate_harmonic_distance(key_a_num, key_b_num)

        if is_harmonic_compatible(key_a_num, key_b_num):
            logger.info(f"调性和谐 (距离: {distance})，使用深度重叠")
            adjusted_duration = self._fade_duration * 1.5
        else:
            logger.info(f"调性不和谐 (距离: {distance})，缩短过渡")
            adjusted_duration = self._fade_duration * 0.5

        adjusted_strategy = CrossfadeStrategy(
            fade_duration=adjusted_duration,
            curve_type=self._curve_type,
            align_to_beat=self._align_to_beat,
            skip_silence=self._skip_silence,
        )

        return adjusted_strategy.apply(
            audio_a,
            audio_b,
            sr,
            transition_point,
            beats_a=beats_a,
            beats_b=beats_b,
            transition_point_b=transition_point_b,
        )
