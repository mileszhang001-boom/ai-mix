"""
节拍追踪模块
获取每拍的精确位置，包括 Downbeat（强拍）检测
"""

import logging
from pathlib import Path

import librosa
import numpy as np

logger = logging.getLogger(__name__)


class BeatTracker:
    """节拍追踪器"""

    def __init__(self):
        self.sr = 22050
        self.hop_length = 512

    def track(self, audio_path: str) -> dict:
        """
        获取音频的节拍信息

        Args:
            audio_path: 音频文件路径

        Returns:
            dict: 包含 beats, tempo, downbeats 等信息
        """
        logger.info(f"开始节拍追踪: {audio_path}")

        y, sr = librosa.load(audio_path, sr=self.sr)

        # 获取 BPM 和节拍位置
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)

        # 转换为时间（秒）
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=self.hop_length)

        # 后处理 BPM
        tempo = self._post_process_bpm(tempo)

        # 获取 Downbeat 信息（每小节的第一拍）
        downbeats = self._get_downbeats(beat_times, tempo)

        # 获取小节信息
        bars = self._get_bars(beat_times)

        result = {
            "tempo": float(tempo),
            "beats": [float(t) for t in beat_times],
            "downbeats": [float(t) for t in downbeats],
            "bars": [float(t) for t in bars],
            "beat_count": len(beat_times),
            "bar_count": len(bars),
            "duration": float(librosa.get_duration(y=y, sr=sr)),
        }

        logger.info(
            f"节拍追踪完成: {len(beat_times)} beats, {len(downbeats)} downbeats, {len(bars)} bars"
        )
        return result

    def _post_process_bpm(self, tempo: float) -> float:
        """BPM 后处理"""
        while tempo > 200:
            tempo /= 2
        while tempo < 60:
            tempo *= 2
        return tempo

    def _get_downbeats(self, beat_times: np.ndarray, tempo: float) -> np.ndarray:
        """
        获取 Downbeat（强拍/小节第一拍）位置
        使用动态分析方法确定小节起始
        """
        if len(beat_times) < 4:
            return beat_times

        # 计算平均拍间隔
        intervals = np.diff(beat_times)
        avg_interval = np.median(intervals)

        # 估计每小节拍数（通常 4 拍，偶数拍子更常见）
        beats_per_bar = 4

        # 取前几个 downbeat 作为参考
        downbeat_indices = np.arange(0, len(beat_times), beats_per_bar)
        return beat_times[downbeat_indices]

    def _get_bars(self, beat_times: np.ndarray) -> np.ndarray:
        """获取小节起始时间（假设 4/4 拍）"""
        if len(beat_times) < 4:
            return np.array([])

        # 每 4 个 beat 是一个小节
        bar_indices = np.arange(0, len(beat_times), 4)
        return beat_times[bar_indices]

    def find_nearest_downbeat(
        self, target_time: float, downbeats: list, direction: str = "before"
    ) -> float:
        """
        找到最近的 Downbeat

        Args:
            target_time: 目标时间
            downbeats: downbeat 列表
            direction: "before" 找之前的，"after" 找之后的

        Returns:
            最近的 downbeat 时间
        """
        if not downbeats:
            return target_time

        downbeats = np.array(downbeats)

        if direction == "before":
            candidates = downbeats[downbeats <= target_time]
            if len(candidates) > 0:
                return float(candidates[-1])
            return float(downbeats[0])
        else:
            candidates = downbeats[downbeats >= target_time]
            if len(candidates) > 0:
                return float(candidates[0])
            return float(downbeats[-1])

    def get_transition_point(self, audio_path: str, transition_duration: float = 10.0) -> dict:
        """
        获取推荐的过渡点（在歌曲结尾处）

        Args:
            audio_path: 音频文件路径
            transition_duration: 过渡持续时间（秒）

        Returns:
            dict: 包含 start_time, end_time 等
        """
        result = self.track(audio_path)

        duration = librosa.get_duration(filename=audio_path)
        beats = result["beats"]

        # 在歌曲结尾找合适的过渡点
        # 至少保留 transition_duration 秒
        end_time = duration
        start_time = max(0, end_time - transition_duration)

        # 找到最接近的节拍点
        start_beat = max([b for b in beats if b <= start_time], default=0)
        end_beat = min([b for b in beats if b >= end_time], default=duration)

        return {
            "start_time": float(start_beat),
            "end_time": float(end_beat),
            "duration": float(end_beat - start_beat),
        }
