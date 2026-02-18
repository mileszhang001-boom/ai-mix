"""
Echo fade 过渡策略
"""

import numpy as np

from mixer_core.transition.base import CrossfadeStrategy


class EchoFadeStrategy(CrossfadeStrategy):
    """Echo fade 回声过渡策略"""

    def __init__(
        self,
        fade_duration: float = 10.0,
        echo_delay: float = 0.3,
        echo_decay: float = 0.5,
        echo_feedback: int = 3,
        curve_type: str = "equal_power",
        align_to_beat: bool = True,
        skip_silence: bool = True,
    ):
        super().__init__(fade_duration, curve_type, align_to_beat, skip_silence)
        self._echo_delay = echo_delay
        self._echo_decay = echo_decay
        self._echo_feedback = echo_feedback

    @property
    def name(self) -> str:
        return "echo_fade"

    @property
    def name_cn(self) -> str:
        return "回声淡入淡出"

    @property
    def description(self) -> str:
        return "在过渡段加入回声效果，适合空灵、Ambient 风格的音乐"

    def apply(
        self,
        audio_a: np.ndarray,
        audio_b: np.ndarray,
        sr: int,
        transition_point: int,
        beats_a=None,
        beats_b=None,
        transition_point_b: float = 0,
    ) -> np.ndarray:
        # 先应用基础淡入淡出
        result = super().apply(
            audio_a,
            audio_b,
            sr,
            transition_point,
            beats_a=beats_a,
            beats_b=beats_b,
            transition_point_b=transition_point_b,
        )

        # 在过渡区添加回声效果
        fade_samples = int(self._fade_duration * sr)
        delay_samples = int(self._echo_delay * sr)

        # 确保有足够的样本
        fade_start = max(0, transition_point - fade_samples)
        fade_end = min(len(result), transition_point + fade_samples + delay_samples)

        # 添加回声
        for i in range(self._echo_feedback):
            echo_offset = delay_samples * (i + 1)
            echo_gain = self._echo_decay ** (i + 1)

            # 回声叠加
            src_start = fade_start
            src_end = min(fade_end - echo_offset, len(result))
            dst_start = fade_start + echo_offset
            dst_end = dst_start + (src_end - src_start)

            if dst_end <= len(result) and src_end > src_start:
                result[dst_start:dst_end] += result[src_start:src_end] * echo_gain

        return result
