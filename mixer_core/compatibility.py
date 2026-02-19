"""
混音兼容性评估模块
评估两首歌曲是否适合混音，并推荐最佳策略
"""

import logging

import librosa
import numpy as np

logger = logging.getLogger(__name__)

# 五度圈映射
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

# 评分权重 - 调整后
WEIGHTS = {
    "bpm": 0.45,
    "key": 0.35,
    "beat": 0.20,
}

# 策略推荐规则 - 基于综合评分和具体特征
# 格式: (最小分数, 最大分数, BPM差异阈值, 策略, 原因)
RECOMMENDATION_RULES = [
    # Beat-sync: BPM差异小于15%时才推荐
    (60, 100, 0.15, "beat_sync", "BPM接近，可做节拍对齐"),
    # Harmonic: 调性匹配（距离<=2）且分数足够
    (55, 100, 0.30, "harmonic", "调性和谐，推荐调性匹配"),
    # Echo: BPM差异大但分数中等
    (40, 60, 0.40, "echo_fade", "差异较大，用回声效果更自然"),
    # Crossfade: 默认选项
    (30, 100, 1.0, "crossfade", "使用平滑过渡"),
    # Echo: 分数太低
    (0, 35, 1.0, "echo_fade", "建议更换歌曲"),
]


def recommend_strategy(
    score: float, bpm_score: float, key_score: float, bpm_a: float, bpm_b: float
) -> tuple[str, str]:
    """基于综合评分和各维度评分推荐策略"""

    # 计算实际 BPM 差异率
    bpm_diff_ratio = abs(bpm_a - bpm_b) / max(bpm_a, bpm_b) if bpm_a > 0 and bpm_b > 0 else 1.0

    # 规则1: BPM差异太大，不适合beat_sync
    if bpm_diff_ratio > 0.20:
        if score >= 50:
            return "crossfade", "BPM差异较大，使用简单过渡"
        else:
            return "echo_fade", "差异较大，用回声效果掩盖"

    # 规则2: BPM接近，优先beat_sync
    if bpm_diff_ratio <= 0.15 and bpm_score >= 55:
        return "beat_sync", "BPM接近，节拍对齐更丝滑"

    # 规则3: 调性匹配，harmonic
    if key_score >= 65:
        return "harmonic", "调性匹配，和声过渡更和谐"

    # 规则4: 中等分数，crossfade
    if score >= 45:
        return "crossfade", "使用平滑过渡"

    # 规则5: 低分，echo
    return "echo_fade", "差异较大，用回声效果掩盖"


class TrackAnalyzer:
    """单曲分析器 - 轻量版"""

    def __init__(self, sr: int = 16000):
        self.sr = sr
        # 尝试使用轻量分析
        try:
            from mixer_core.quick_analyze import quick_analyze

            self.use_quick = True
        except ImportError:
            self.use_quick = False

    def analyze(self, audio_path: str) -> dict:
        """分析单曲，返回特征字典"""

        if self.use_quick:
            # 使用轻量分析
            try:
                from mixer_core.quick_analyze import quick_analyze

                result = quick_analyze(audio_path)

                # 兼容原接口
                return {
                    "bpm": result.get("bpm", 120),
                    "confidence": result.get("confidence", 0.5),
                    "key": result.get("key", "C"),
                    "key_confidence": 0.5,
                    "duration": result.get("duration", 180),
                }
            except Exception as e:
                print(f"轻量分析失败，回退到标准方法: {e}")

        # 标准方法（完整加载）
        y, sr = librosa.load(audio_path, sr=self.sr, duration=60)  # 最多加载60秒

        # BPM和节拍
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        tempo = self._post_process_bpm(tempo)
        confidence = self._calculate_beat_confidence(y, beats)

        # 调性
        key, key_confidence = self._detect_key(y, sr)

        return {
            "bpm": float(tempo),
            "confidence": float(confidence),
            "key": key,
            "key_confidence": float(key_confidence),
            "duration": float(librosa.get_duration(y=y, sr=sr)),
        }

    def _post_process_bpm(self, tempo: float) -> float:
        """BPM后处理"""
        while tempo > 200:
            tempo /= 2
        while tempo < 60:
            tempo *= 2
        return tempo

    def _calculate_beat_confidence(self, y: np.ndarray, beats: np.ndarray) -> float:
        """计算节拍置信度"""
        if len(beats) < 4:
            return 0.0
        beat_times = librosa.frames_to_time(beats, sr=self.sr)
        intervals = np.diff(beat_times)
        if len(intervals) == 0:
            return 0.0
        cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else 1.0
        return max(0, 1 - cv)

    def _detect_key(self, y: np.ndarray, sr: int) -> tuple[str, float]:
        """检测调性"""
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        major_pattern = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
        minor_pattern = np.array([1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0])

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

        best_key = "C"
        best_score = 0

        for key in keys:
            is_minor = "m" in key
            pattern = minor_pattern if is_minor else major_pattern
            score = np.dot(chroma_mean, pattern)
            if score > best_score:
                best_score = score
                best_key = key

        return best_key, float(best_score)


class CompatibilityEvaluator:
    """兼容性评估器"""

    def __init__(self, sr: int = 22050):
        self.analyzer = TrackAnalyzer(sr)

    def evaluate(self, track_a_info: dict, track_b_info: dict) -> dict:
        """
        评估两首歌的兼容性

        Args:
            track_a_info: 歌曲A的特征 dict (包含 bpm, confidence, key 等)
            track_b_info: 歌曲B的特征 dict

        Returns:
            兼容性评估结果
        """
        # BPM评分
        bpm_score = self._score_bpm(track_a_info.get("bpm", 0), track_b_info.get("bpm", 0))

        # 调性评分
        key_score = self._score_key(track_a_info.get("key", "C"), track_b_info.get("key", "C"))

        # 节拍评分
        beat_score = self._score_beat(
            track_a_info.get("confidence", 0), track_b_info.get("confidence", 0)
        )

        # 综合评分
        score = (
            bpm_score * WEIGHTS["bpm"] + key_score * WEIGHTS["key"] + beat_score * WEIGHTS["beat"]
        )

        # 推荐策略 - 传入BPM用于判断是否适合beat_sync
        bpm_a = track_a_info.get("bpm", 0)
        bpm_b = track_b_info.get("bpm", 0)
        recommendation, reason = self._recommend_strategy(score, bpm_score, key_score, bpm_a, bpm_b)

        result = {
            "score": round(score),
            "bpm_score": round(bpm_score),
            "key_score": round(key_score),
            "beat_score": round(beat_score),
            "recommendation": recommendation,
            "reason": reason,
        }

        logger.info(f"兼容性评估: {result}")
        return result

    def _score_bpm(self, bpm_a: float, bpm_b: float) -> float:
        """BPM兼容性评分 - 平滑曲线，范围20-90"""
        if bpm_a == 0 or bpm_b == 0:
            return 50.0

        diff_ratio = abs(bpm_a - bpm_b) / max(bpm_a, bpm_b)

        # 平滑曲线：差异越小分数越高
        # 0%差异=90分，25%差异=40分，50%差异=20分
        score = 90 - (diff_ratio * 140)
        return max(20, min(90, score))

    def _score_key(self, key_a: str, key_b: str) -> float:
        """调性兼容性评分 - 范围30-90"""
        pos_a = CIRCLE_OF_FIFTHS.get(key_a.replace("#", "").replace("b", ""), 0)
        pos_b = CIRCLE_OF_FIFTHS.get(key_b.replace("#", "").replace("b", ""), 0)

        distance = abs(pos_a - pos_b)
        distance = min(distance, 12 - distance)

        # 调性距离评分
        if distance == 0:
            return 90  # 完全相同
        elif distance == 1:
            return 80  # 相邻调性（五度关系）
        elif distance == 2:
            return 65  # 两个半音
        elif distance == 3:
            return 50  # 三个半音
        elif distance == 4:
            return 40  # 四个半音
        else:
            return 30  # 较远关系

    def _score_beat(self, conf_a: float, conf_b: float) -> float:
        """节拍稳定性评分 - 范围30-85"""
        avg_conf = (conf_a + conf_b) / 2
        # 压缩到30-85范围
        return 30 + avg_conf * 55

    def _recommend_strategy(
        self, score: float, bpm_score: float, key_score: float, bpm_a: float = 0, bpm_b: float = 0
    ) -> tuple[str, str]:
        """推荐策略并生成原因 - 基于综合评分和各维度特征"""
        return recommend_strategy(score, bpm_score, key_score, bpm_a, bpm_b)


def evaluate_tracks(track_a_path: str, track_b_path: str) -> dict:
    """
    便捷函数：直接评估两个音频文件

    Args:
        track_a_path: 歌曲A路径
        track_b_path: 歌曲B路径

    Returns:
        兼容性评估结果
    """
    evaluator = CompatibilityEvaluator()

    analyzer = TrackAnalyzer()
    info_a = analyzer.analyze(track_a_path)
    info_b = analyzer.analyze(track_b_path)

    return evaluator.evaluate(info_a, info_b)
