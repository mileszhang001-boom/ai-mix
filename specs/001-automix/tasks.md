# Tasks: music-mix Automix

**Branch**: `001-automix` | **Generated**: 2026-02-17

---

## Phase 1: 基础设施与核心算法

### P1.1 项目初始化

- [ ] **T1.1.1** 创建项目目录结构 `music_mix/`
- [ ] **T1.1.2** 创建 `pyproject.toml` 配置 Python 包
- [ ] **T1.1.3** 配置虚拟环境，安装依赖：librosa, pydub, click/typer, numpy, scipy
- [ ] **T1.1.4** 初始化 Git 仓库（如需要）
- [ ] **T1.1.5** 创建 `README.md` 简要说明

**交付物**: 项目骨架可运行 `pip install -e .`

---

### P1.2 BPM 检测算法

- [ ] **T1.2.1** 实现 `mixer_core/bpm_detector.py`：使用 librosa 实现 BPM 检测
- [ ] **T1.2.2** 实现 BPM 后处理：处理 2x/0.5x 歧义
- [ ] **T1.2.3** 添加日志输出：检测到的 BPM、置信度

**代码示例**:
```python
import librosa

def detect_bpm(audio_path: str) -> float:
    y, sr = librosa.load(audio_path)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)
```

**交付物**: `mixer_core.bpm_detector.detect_bpm()`

---

### P1.3 节拍追踪

- [ ] **T1.3.1** 实现 `mixer_core/beat_tracker.py`：获取每拍的帧位置
- [ ] **T1.3.2** 计算节拍之间的时间间隔
- [ ] **T1.3.3** 集成 BPM 检测与节拍追踪

**交付物**: `mixer_core.beat_tracker.BeatTracker`

---

### P1.4 CLI 基础功能

- [ ] **T1.4.1** 实现 `music-mix scan <folder>` 命令：扫描文件夹获取所有 mp3 的 BPM
- [ ] **T1.4.2** 实现 `music-mix analyze <file>` 命令：分析单首歌曲
- [ ] **T1.4.3** 支持 `--format json` 输出格式
- [ ] **T1.4.4** 添加帮助信息和错误处理

**CLI 示例**:
```bash
music-mix scan ./music --format json
# Output: [{"file": "song1.mp3", "bpm": 128.5}, ...]
```

**交付物**: CLI 可用，响应 < 5 秒

---

### P1.5 单元测试

- [ ] **T1.5.1** 创建测试音频 fixtures（3-5 首不同 BPM 的 mp3）
- [ ] **T1.5.2** 编写 BPM 检测单元测试
- [ ] **T1.5.3** 验证 BPM 检测准确率 > 90%
- [ ] **T1.5.4** 添加 CI 测试（如需要）

**测试验证**: 使用已知 BPM 的测试音频，验证检测准确率

**交付物**: 测试覆盖率 > 80%

---

## Phase 2: 混音引擎与基础过渡策略

*待 Phase 1 完成后生成*

---

## Phase 3: 前端 Demo

*待 Phase 2 完成后生成*

---

## Phase 3.5: 兼容性评估

### P3.5.1 兼容性评估模块

- [ ] **T3.5.1.1** 创建 `mixer_core/compatibility.py`
- [ ] **T3.5.1.2** 实现 BPM 兼容性评分函数
- [ ] **T3.5.1.3** 实现调性检测（五度圈）
- [ ] **T3.5.1.4** 实现节拍稳定性评估
- [ ] **T3.5.1.5** 实现综合评分算法

**代码接口**:
```python
from mixer_core.compatibility import CompatibilityEvaluator

evaluator = CompatibilityEvaluator()
result = evaluator.evaluate(track_a, track_b)
# result = {
#     "score": 85,
#     "bpm_score": 90,
#     "key_score": 80,
#     "beat_score": 85,
#     "recommendation": "beat_sync",
#     "reason": "BPM接近，节拍清晰"
# }
```

**交付物**: `mixer_core.compatibility.CompatibilityEvaluator`

---

### P3.5.2 调性检测与匹配

- [ ] **T3.5.2.1** 实现基于色度特征的调性检测
- [ ] **T3.5.2.2** 实现五度圈距离计算
- [ ] **T3.5.2.3** 集成调性评分到综合评估

**交付物**: 调性兼容性评分功能

---

### P3.5.3 策略推荐

- [ ] **T3.5.3.1** 基于评分选择最佳策略
- [ ] **T3.5.3.2** 生成一句话推荐原因
- [ ] **T3.5.3.3** API 集成兼容性评估

**一句话原因示例**:
- "BPM接近，推荐使用节拍对齐"
- "调性和谐，适合调性匹配"
- "差异较大，建议简单过渡"

**交付物**: 策略推荐与原因生成

---

### P3.5.4 前端展示

- [ ] **T3.5.4.1** 后端 API 返回兼容性数据
- [ ] **T3.5.4.2** 前端显示兼容性评分（进度条/数字）
- [ ] **T3.5.4.3** 前端显示推荐策略与原因

**前端展示**:
```
兼容性: 85分  ✓ 推荐策略: Beat-sync
原因: BPM接近，节拍清晰
```

---

## Phase 4: 播放列表与集成

*待 Phase 3 完成后生成*

---

## Phase 5: 高级策略（可选）

*待 Phase 4 完成后生成*

---

## 任务清单统计

| Phase | 任务数 | 状态 |
|-------|--------|------|
| Phase 1 | 5 个子阶段 | 待开始 |
| Phase 2 | - | 待生成 |
| Phase 3 | - | 待生成 |
| Phase 4 | - | 待生成 |
| Phase 5 | - | 待生成 |

---

## 依赖关系

```
P1.1 → P1.2 → P1.3 → P1.4 → P1.5
                              ↓
                         Phase 2
```

---

## 备注

- 所有任务遵循 TDD 流程：先写测试 → 测试失败 → 实现 → 测试通过
- 每个子任务完成后需验证功能正常
- 遇到阻塞性问题及时记录和反馈
