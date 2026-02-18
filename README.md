# music-mix

Automix: 实现音乐间的丝滑过渡

## 安装

```bash
pip install -e .
```

## 使用

### 扫描音乐库

```bash
music-mix scan ./music --format json
```

### 分析单首歌曲

```bash
music-mix analyze song.mp3
```

### 混音两首歌曲

```bash
music-mix mix song_a.mp3 song_b.mp3 --strategy crossfade --output output.mp3
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```
