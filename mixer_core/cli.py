"""
CLI 模块
"""

import json
import logging
import sys
from pathlib import Path

import click
from tqdm import tqdm

from mixer_core import BPMDetector, BeatTracker, Mixer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """music-mix: Automix 实现音乐间的丝滑过渡"""
    pass


@cli.command()
@click.argument("folder_path", type=click.Path(exists=True))
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]))
@click.option("--recursive", is_flag=True, help="递归扫描子目录")
def scan(folder_path: str, output_format: str, recursive: bool):
    """扫描音乐文件夹，检测所有 mp3 文件的 BPM"""

    detector = BPMDetector()

    # 查找所有 mp3 文件
    path = Path(folder_path)
    if recursive:
        mp3_files = list(path.rglob("*.mp3"))
    else:
        mp3_files = list(path.glob("*.mp3"))

    if not mp3_files:
        click.echo("未找到 mp3 文件", err=True)
        return

    # 检测每首歌曲的 BPM
    results = []
    for mp3_file in tqdm(mp3_files, desc="检测 BPM"):
        try:
            result = detector.detect(str(mp3_file))
            result["file"] = mp3_file.name
            result["path"] = str(mp3_file)
            results.append(result)
        except Exception as e:
            logger.error(f"检测失败 {mp3_file}: {e}")
            results.append({"file": mp3_file.name, "path": str(mp3_file), "error": str(e)})

    # 输出结果
    if output_format == "json":
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            if "error" in r:
                click.echo(f"❌ {r['file']}: {r['error']}")
            else:
                click.echo(f"✓ {r['file']}: BPM={r['bpm']:.1f} (置信度: {r['confidence']:.0%})")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]))
def analyze(file_path: str, output_format: str):
    """分析单首歌曲的详细信息"""

    detector = BPMDetector()
    beat_tracker = BeatTracker()

    try:
        # BPM 检测
        bpm_result = detector.detect(file_path)

        # 节拍追踪
        beat_result = beat_tracker.track(file_path)

        result = {
            "file": Path(file_path).name,
            "bpm": bpm_result["bpm"],
            "confidence": bpm_result["confidence"],
            "duration": bpm_result["duration"],
            "beat_count": beat_result["beat_count"],
            "bar_count": beat_result["bar_count"],
        }

        if output_format == "json":
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            click.echo(f"文件: {result['file']}")
            click.echo(f"BPM: {result['bpm']:.1f}")
            click.echo(f"置信度: {result['confidence']:.0%}")
            click.echo(f"时长: {result['duration']:.1f} 秒")
            click.echo(f"节拍数: {result['beat_count']}")
            click.echo(f"小节数: {result['bar_count']}")

    except Exception as e:
        click.echo(f"分析失败: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("track_a", type=click.Path(exists=True))
@click.argument("track_b", type=click.Path(exists=True))
@click.option(
    "--strategy",
    default="crossfade",
    type=click.Choice(["crossfade", "beat_sync", "echo_fade", "harmonic"]),
)
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
@click.option("--duration", default=5.0, type=float, help="过渡持续时间（秒）")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]))
def mix(
    track_a: str, track_b: str, strategy: str, output: str, duration: float, output_format: str
):
    """混音两首歌曲"""

    mixer = Mixer()

    try:
        result = mixer.mix(
            track_a, track_b, strategy=strategy, output_path=output, transition_duration=duration
        )

        if output_format == "json":
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            click.echo(f"✓ 混音完成")
            click.echo(f"  策略: {result['strategy']}")
            click.echo(f"  过渡点: {result['transition_point']:.1f}秒")
            click.echo(f"  总时长: {result['duration']:.1f}秒")
            if output:
                click.echo(f"  输出: {output}")

    except Exception as e:
        click.echo(f"混音失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("folder_path", type=click.Path(exists=True))
@click.option(
    "--strategy",
    default="crossfade",
    type=click.Choice(["crossfade", "beat_sync", "echo_fade", "harmonic"]),
)
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
@click.option("--duration", default=5.0, type=float, help="过渡持续时间（秒）")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]))
def playlist(folder_path: str, strategy: str, output: str, duration: float, output_format: str):
    """混音文件夹中的所有歌曲（按文件名排序）"""
    from pathlib import Path

    # 获取所有 mp3 文件
    path = Path(folder_path)
    mp3_files = sorted(path.glob("*.mp3"))

    if not mp3_files:
        click.echo("未找到 mp3 文件", err=True)
        return

    click.echo(f"找到 {len(mp3_files)} 首歌曲")

    if len(mp3_files) == 1:
        click.echo("只有一首歌曲，直接复制")
        if output:
            import shutil

            shutil.copy(str(mp3_files[0]), output)
        return

    mixer = Mixer()

    try:
        # 依次混音每两首歌曲
        current_output = output or "/tmp/playlist_output.mp3"

        # 先混音前两首
        click.echo(f"混音: {mp3_files[0].name} -> {mp3_files[1].name}")
        result = mixer.mix(
            str(mp3_files[0]),
            str(mp3_files[1]),
            strategy=strategy,
            output_path=current_output,
            transition_duration=duration,
        )

        # 依次添加后续歌曲
        for i in range(2, len(mp3_files)):
            temp_output = f"/tmp/playlist_temp_{i}.mp3"
            click.echo(f"混音: 已有结果 -> {mp3_files[i].name}")

            # 混音当前结果和下一首
            result = mixer.mix(
                current_output,
                str(mp3_files[i]),
                strategy=strategy,
                output_path=temp_output,
                transition_duration=duration,
            )

            # 替换
            import os

            os.replace(temp_output, current_output)

        click.echo(f"✓ 播放列表混音完成")
        click.echo(f"  歌曲数: {len(mp3_files)}")
        click.echo(f"  总时长: {result['duration']:.1f}秒")
        click.echo(f"  输出: {current_output}")

    except Exception as e:
        click.echo(f"播放列表混音失败: {e}", err=True)
        sys.exit(1)


def main():
    """入口函数"""
    cli()


if __name__ == "__main__":
    main()
