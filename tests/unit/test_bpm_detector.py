"""
单元测试 - BPM 检测
"""

import pytest
from mixer_core.bpm_detector import BPMDetector


class TestBPMDetector:
    """BPM 检测器测试"""

    @pytest.fixture
    def detector(self):
        return BPMDetector()

    def test_bpm_detection_returns_valid_value(self, detector):
        """测试 BPM 返回有效值"""
        # 使用一个测试文件
        test_file = (
            "music-resource/流行乐/Ava Max - Ava Max - Don't Click Play (Official Audio).mp3"
        )

        result = detector.detect(test_file)

        assert "bpm" in result
        assert 30 < result["bpm"] < 300  # 人类音乐 BPM 范围
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_bpm_post_process(self, detector):
        """测试 BPM 后处理（2x/0.5x 校正）"""
        # 测试 2x 问题
        assert 60 <= detector._post_process(240) <= 200
        # 测试 0.5x 问题
        assert 60 <= detector._post_process(40) <= 200

    def test_confidence_calculation(self, detector):
        """测试置信度计算"""
        import numpy as np

        # 模拟稳定的节拍
        beats = np.array([0, 0.5, 1.0, 1.5, 2.0])
        y = np.random.randn(10000)

        confidence = detector._calculate_confidence(y, beats)

        assert 0 <= confidence <= 1
