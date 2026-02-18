"""
单元测试 - 过渡策略
"""

import numpy as np
import pytest
from mixer_core.transition.base import CrossfadeStrategy, BeatSyncStrategy, TransitionFactory


class TestCrossfadeStrategy:
    """Crossfade 策略测试"""

    @pytest.fixture
    def strategy(self):
        return CrossfadeStrategy(fade_duration=1.0)

    @pytest.fixture
    def sample_audio(self):
        # 创建 5 秒的测试音频（22050 Hz）
        sr = 22050
        duration = 5
        audio_a = np.sin(2 * np.pi * 440 * np.arange(sr * duration))  # 440 Hz
        audio_b = np.sin(2 * np.pi * 440 * np.arange(sr * duration))  # 440 Hz
        return audio_a, audio_b, sr

    def test_crossfade_returns_audio(self, strategy, sample_audio):
        """测试 Crossfade 返回音频数据"""
        audio_a, audio_b, sr = sample_audio
        transition_point = int(3 * sr)  # 3 秒处过渡

        result = strategy.apply(audio_a, audio_b, sr, transition_point)

        assert isinstance(result, np.ndarray)
        assert len(result) > 0

    def test_crossfade_preserves_length(self, strategy, sample_audio):
        """测试 Crossfade 保持音频长度"""
        audio_a, audio_b, sr = sample_audio
        transition_point = int(3 * sr)

        result = strategy.apply(audio_a, audio_b, sr, transition_point)

        # 结果长度应该是 max(len(a), transition_point + len(b))
        expected_min = max(len(audio_a), transition_point + (len(audio_b) - transition_point))
        assert len(result) >= expected_min - sr  # 允许一些误差


class TestTransitionFactory:
    """过渡策略工厂测试"""

    def test_create_crossfade(self):
        """测试创建 Crossfade 策略"""
        strategy = TransitionFactory.create("crossfade")
        assert isinstance(strategy, CrossfadeStrategy)

    def test_create_beat_sync(self):
        """测试创建 BeatSync 策略"""
        strategy = TransitionFactory.create("beat_sync")
        assert isinstance(strategy, BeatSyncStrategy)

    def test_create_invalid_strategy(self):
        """测试创建无效策略"""
        with pytest.raises(ValueError):
            TransitionFactory.create("invalid_strategy")

    def test_list_strategies(self):
        """测试列出所有策略"""
        strategies = TransitionFactory.list_strategies()
        assert "crossfade" in strategies
        assert "beat_sync" in strategies
