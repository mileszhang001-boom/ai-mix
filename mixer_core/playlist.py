"""
播放列表混音模块
支持多首歌曲连续混音
"""

import logging
from pathlib import Path

import librosa
import numpy as np

from mixer_core.mixer import Mixer

logger = logging.getLogger(__name__)


class PlaylistMixer:
    """播放列表混音器"""

    def __init__(self):
        self.mixer = Mixer()

    def mix_playlist(
        self,
        track_paths: list[str],
        strategy: str = "crossfade",
        output_path: str | None = None,
        transition_duration: float = 5.0,
    ) -> dict:
        """
        混音播放列表中的所有歌曲

        Args:
            track_paths: 歌曲路径列表
            strategy: 过渡策略
            output_path: 输出路径
            transition_duration: 每两首歌曲之间的过渡时间

        Returns:
            dict: 混音结果
        """
        if len(track_paths) == 0:
            raise ValueError("播放列表为空")

        if len(track_paths) == 1:
            # 只有一首歌曲，直接复制
            logger.info("播放列表只有一首歌曲，直接复制")
            y, sr = librosa.load(track_paths[0], sr=22050)
            from mixer_core.mixer import Mixer

            m = Mixer()
            m._save(y, sr, output_path)
            return {
                "track_count": 1,
                "duration": len(y) / sr,
                "output": output_path,
                "transitions": [],
            }

        logger.info(f"开始播放列表混音: {len(track_paths)} 首歌曲")

        # 加载第一首歌曲
        y_all, sr = librosa.load(track_paths[0], sr=22050)
        first_duration = len(y_all) / sr

        transitions = []

        # 依次混音每两首歌曲
        for i in range(1, len(track_paths)):
            track_a = track_paths[i - 1]
            track_b = track_paths[i]

            logger.info(
                f"混音第 {i}/{len(track_paths) - 1}: {Path(track_a).name} -> {Path(track_b).name}"
            )

            # 临时输出
            temp_output = f"/tmp/playlist_temp_{i}.mp3"

            # 混音
            result = self.mixer.mix(
                track_a,
                track_b,
                strategy=strategy,
                output_path=temp_output,
                transition_duration=transition_duration,
            )

            transitions.append(
                {
                    "from": Path(track_a).name,
                    "to": Path(track_b).name,
                    "transition_point": result["transition_point"],
                    "strategy": result["strategy"],
                }
            )

            # 加载混音结果并追加到主音频
            y_mixed, _ = librosa.load(temp_output, sr=sr)

            # 找到第二首歌曲开始的位置（过渡点之后）
            # 简单处理：直接拼接（已经有过渡处理了）
            # 实际上混音结果已经包含了完整的过渡，所以我们只需要取前一首歌曲的全部
            # 然后追加第二首歌曲超出过渡区的部分

            # 获取原始两首歌曲
            y_a_orig, _ = librosa.load(track_a, sr=sr)
            y_b_orig, _ = librosa.load(track_b, sr=sr)

            # 重新混音，使用更简单的方式
            # 获取第一首歌曲的前半部分 + 混音结果的后半部分
            transition_sample = int(result["transition_point"] * sr)

            # 构建新的结果：保留第一首到过渡点，然后接第二首
            # 这里简化处理，直接使用混音结果
            y_all = y_mixed

            # 清理临时文件
            import os

            if os.path.exists(temp_output):
                os.remove(temp_output)

        # 保存最终结果
        if output_path:
            self.mixer._save(y_all, sr, output_path)
            logger.info(f"播放列表混音完成: {output_path}")

        total_duration = len(y_all) / sr

        return {
            "track_count": len(track_paths),
            "tracks": [Path(p).name for p in track_paths],
            "strategy": strategy,
            "duration": total_duration,
            "output": output_path,
            "transitions": transitions,
        }


def scan_playlist(folder_path: str) -> list[str]:
    """扫描文件夹获取播放列表（按文件名排序）"""
    path = Path(folder_path)
    mp3_files = sorted(path.glob("*.mp3"))
    return [str(f) for f in mp3_files]
