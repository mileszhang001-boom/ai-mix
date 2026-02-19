"""
混音引擎模块
"""

import logging
from pathlib import Path

import librosa
import numpy as np

from mixer_core.transition import TransitionFactory
from mixer_core.transition.beat_sync import stretch_to_target_bpm
from mixer_core.segment_detector import detect_segments, find_optimal_transition_point
from mixer_core.compatibility import TrackAnalyzer, CompatibilityEvaluator

logger = logging.getLogger(__name__)


class Mixer:
    """混音引擎"""

    def __init__(self):
        self.sr = 16000  # 降低采样率以提高速度
        self.track_analyzer = TrackAnalyzer(self.sr)
        self.compatibility_evaluator = CompatibilityEvaluator(self.sr)

    def mix(
        self,
        track_a_path: str,
        track_b_path: str,
        strategy: str = "crossfade",
        output_path: str | None = None,
        transition_duration: float = 10.0,
    ) -> dict:
        """
        混音两首歌曲

        Args:
            track_a_path: 第一首歌曲路径
            track_b_path: 第二首歌曲路径
            strategy: 过渡策略 (crossfade, beat_sync)
            output_path: 输出路径（可选）
            transition_duration: 过渡持续时间（秒）

        Returns:
            dict: 混音结果信息
        """
        logger.info(f"开始混音: {track_a_path} -> {track_b_path}, 策略: {strategy}")

        # 加载音频
        y_a, sr_a = librosa.load(track_a_path, sr=self.sr)
        y_b, sr_b = librosa.load(track_b_path, sr=self.sr)

        # 检测 BPM 和节拍
        bpm_a, beats_a = self._detect_bpm_and_beats(track_a_path)
        bpm_b, beats_b = self._detect_bpm_and_beats(track_b_path)

        logger.info(f"检测到 BPM: {track_a_path} = {bpm_a:.1f}, {track_b_path} = {bpm_b:.1f}")

        # 兼容性评估
        compatibility_result = self.evaluate_compatibility(track_a_path, track_b_path)

        # 检测歌曲结构（前奏/尾奏）
        seg_a = detect_segments(track_a_path, self.sr)
        seg_b = detect_segments(track_b_path, self.sr)

        logger.info(
            f"歌曲A结构: 前奏结束={seg_a['intro_end']:.1f}s, 尾奏开始={seg_a['outro_start']:.1f}s"
        )
        logger.info(
            f"歌曲B结构: 前奏结束={seg_b['intro_end']:.1f}s, 尾奏开始={seg_b['outro_start']:.1f}s"
        )

        # Beat-sync 策略：检查是否可以应用时间拉伸
        actual_strategy = strategy
        if strategy == "beat_sync":
            can_apply, stretch_ratio = self._can_beat_sync(bpm_a, bpm_b)
            if not can_apply:
                logger.warning(
                    f"BPM 差异过大 ({bpm_a:.1f} vs {bpm_b:.1f}, 拉伸比例 {stretch_ratio:.2f})，"
                    f"超出 ±15% 限制，fallback 到 Crossfade"
                )
                actual_strategy = "crossfade"
            else:
                # 执行时间拉伸
                logger.info(f"执行 Beat-sync: BPM {bpm_b:.1f} -> {bpm_a:.1f}")
                y_b, actual_ratio = stretch_to_target_bpm(y_b, self.sr, bpm_b, bpm_a)
                logger.info(f"时间拉伸完成，实际拉伸比例: {actual_ratio:.3f}")

        # ========== 自适应过渡时长 ==========
        # BPM 差异越大，过渡时间越长
        bpm_diff_ratio = abs(bpm_a - bpm_b) / max(bpm_a, bpm_b)

        if bpm_diff_ratio < 0.05:
            # BPM 几乎相同，使用较短过渡
            base_transition = 8.0
        elif bpm_diff_ratio < 0.10:
            base_transition = 10.0
        elif bpm_diff_ratio < 0.15:
            base_transition = 12.0
        else:
            # BPM 差异大，需要更长过渡
            base_transition = 15.0

        # 创建过渡策略
        strategy_obj = TransitionFactory.create(
            actual_strategy,
            fade_duration=base_transition,
            curve_type="equal_power",
            align_to_beat=True,
        )

        # ========== 计算过渡点 - Downbeat 对齐 + 能量匹配 ==========
        duration_a = len(y_a) / self.sr
        duration_b = len(y_b) / self.sr

        # 歌曲A：从 Outro 区域更早开始过渡
        # 直接使用 outro_start 位置（能量下降点），不再用 downbeat
        outro_point_a = seg_a["outro_start"]
        transition_point_a = outro_point_a

        # 确保过渡点不会太早（至少在 55% 位置之后）
        min_transition_point = duration_a * 0.55
        transition_point_a = max(transition_point_a, min_transition_point)

        # 歌曲B：从 Intro 后的第一个 Downbeat 开始（跳过前奏）
        # 优先使用 Intro Downbeat
        intro_point_b = seg_b.get("intro_downbeat", seg_b["intro_end"])
        transition_point_b = intro_point_b

        # 限制跳过前奏的最大时间 - 更激进
        max_intro_skip = min(duration_b * 0.08, 8)  # 最多跳过 8% 或 8 秒
        transition_point_b = min(transition_point_b, max_intro_skip)

        # 如果计算出的 intro_point_b 为 0，使用一个更合理的值
        if transition_point_b < 1.0:
            transition_point_b = 3.0  # 至少跳过前 3 秒

        transition_point = int(transition_point_a * self.sr)

        logger.info(
            f"计算过渡点(Downbeat对齐+自适应时长): 歌曲A={transition_point_a:.1f}s (总时长{duration_a:.1f}s), "
            f"歌曲B从={transition_point_b:.1f}s开始, 过渡时长={base_transition:.1f}s"
        )

        # 应用过渡策略（传入节拍信息用于对齐，以及歌曲B的起始位置）
        y_mixed = strategy_obj.apply(
            y_a,
            y_b,
            self.sr,
            transition_point,
            beats_a=beats_a,
            beats_b=beats_b,
            transition_point_b=transition_point_b,
        )

        # 归一化避免爆音
        y_mixed = self._normalize(y_mixed)

        # 保存结果
        if output_path:
            self._save(y_mixed, self.sr, output_path)
            logger.info(f"混音结果已保存: {output_path}")

        result = {
            "strategy": actual_strategy,
            "original_strategy": strategy,
            "bpm_a": bpm_a,
            "bpm_b": bpm_b,
            "track_a": track_a_path,
            "track_b": track_b_path,
            "transition_point": float(transition_point / self.sr),
            "transition_point_b": float(transition_point_b),
            "transition_duration": base_transition,
            "duration": float(len(y_mixed) / self.sr),
            "output": output_path,
            "segment_a": {
                "intro_end": seg_a["intro_end"],
                "outro_start": seg_a["outro_start"],
                "outro_downbeat": seg_a.get("outro_downbeat", seg_a["outro_start"]),
            },
            "segment_b": {
                "intro_end": seg_b["intro_end"],
                "intro_downbeat": seg_b.get("intro_downbeat", seg_b["intro_end"]),
            },
            "compatibility": compatibility_result,
        }

        return result

    def evaluate_compatibility(self, track_a_path: str, track_b_path: str) -> dict:
        """
        评估两首歌曲的兼容性

        Args:
            track_a_path: 第一首歌曲路径
            track_b_path: 第二首歌曲路径

        Returns:
            dict: 兼容性评估结果
        """
        logger.info(f"评估兼容性: {track_a_path} <-> {track_b_path}")

        # 分析两首歌曲
        info_a = self.track_analyzer.analyze(track_a_path)
        info_b = self.track_analyzer.analyze(track_b_path)

        # 评估兼容性
        result = self.compatibility_evaluator.evaluate(info_a, info_b)

        # 添加BPM信息
        result["bpm_a"] = info_a["bpm"]
        result["bpm_b"] = info_b["bpm"]

        return result

    def _detect_bpm_and_beats(self, audio_path: str) -> tuple[float, list[float]]:
        """检测音频 BPM 和节拍位置"""
        y, sr = librosa.load(audio_path, sr=self.sr)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

        # 后处理：处理 2x/0.5x 问题
        while tempo > 200:
            tempo /= 2
        while tempo < 60:
            tempo *= 2

        # 转换为时间（秒）
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        return float(tempo), beat_times.tolist()

    def _detect_bpm(self, audio_path: str) -> float:
        """检测音频 BPM（兼容旧接口）"""
        bpm, _ = self._detect_bpm_and_beats(audio_path)
        return bpm

    def _can_beat_sync(
        self, bpm_a: float, bpm_b: float, max_stretch: float = 0.15
    ) -> tuple[bool, float]:
        """
        检查是否可以应用 Beat-sync

        Args:
            bpm_a: 第一首歌曲 BPM
            bpm_b: 第二首歌曲 BPM
            max_stretch: 最大拉伸比例

        Returns:
            (是否可以应用, 需要的拉伸比例)
        """
        if bpm_a == 0 or bpm_b == 0:
            return False, 0.0

        stretch_ratio = bpm_b / bpm_a

        # 检查是否在允许范围内
        if 1.0 - max_stretch <= stretch_ratio <= 1.0 + max_stretch:
            return True, stretch_ratio

        return False, stretch_ratio

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """归一化音频，避免爆音"""
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val * 0.95
        return audio

    def _save(self, audio: np.ndarray, sr: int, output_path: str):
        """保存音频文件"""
        # 转换 float32 到 int16
        audio_int16 = (audio * 32767).astype(np.int16)

        # 使用 pydub 保存
        from pydub import AudioSegment

        audio_segment = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=1,
        )
        audio_segment.export(output_path, format="mp3")
