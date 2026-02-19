"""
BPM 检测模块
使用 librosa 进行音频节奏分析
"""

import logging
from pathlib import Path

import librosa
import numpy as np

logger = logging.getLogger(__name__)


class BPMDetector:
    """BPM 检测器"""

    def __init__(self):
        self.sr = 16000  # 降低采样率以提高速度  # 采样率
        self.hop_length = 512  # 帧移

    def detect(self, audio_path: str) -> dict:
        """
        检测音频文件的 BPM

        Args:
            audio_path: 音频文件路径

        Returns:
            dict: 包含 bpm, confidence 等信息
        """
        logger.info(f"开始 BPM 检测: {audio_path}")

        # 加载音频
        y, sr = librosa.load(audio_path, sr=self.sr)

        # BPM 检测 - 使用动态规划
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)

        # 后处理：处理 2x/0.5x 问题
        tempo = self._post_process(tempo)

        # 计算置信度（基于节拍的清晰度）
        confidence = self._calculate_confidence(y, beats)

        result = {
            "bpm": float(tempo),
            "confidence": float(confidence),
            "beat_count": len(beats),
            "duration": float(librosa.get_duration(y=y, sr=sr)),
        }

        logger.info(f"BPM 检测完成: {result}")
        return result

    def _post_process(self, tempo: float) -> float:
        """后处理：处理 BPM 2x/0.5x 问题"""
        # 人类音乐的 BPM 范围通常是 60-200
        # 如果检测到 > 200，可能是实际 BPM 的 2 倍
        while tempo > 200:
            tempo /= 2
        # 如果检测到 < 60，可能是实际 BPM 的一半
        while tempo < 60:
            tempo *= 2
        return tempo

    def _calculate_confidence(self, y: np.ndarray, beats: np.ndarray) -> float:
        """计算检测置信度"""
        if len(beats) < 4:
            return 0.0

        # 计算节拍间隔的变异系数
        beat_times = librosa.frames_to_time(beats, sr=self.sr, hop_length=self.hop_length)
        intervals = np.diff(beat_times)

        if len(intervals) == 0:
            return 0.0

        # CV = std / mean，越小说明节拍越稳定
        cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else 1.0

        # 转换为置信度 (0-1)
        confidence = max(0, 1 - cv)
        return confidence

    def detect_batch(self, audio_paths: list[str]) -> list[dict]:
        """批量检测多个音频文件的 BPM"""
        results = []
        for path in audio_paths:
            try:
                result = self.detect(path)
                result["file"] = path
                results.append(result)
            except Exception as e:
                logger.error(f"BPM 检测失败 {path}: {e}")
                results.append({"file": path, "error": str(e)})
        return results
