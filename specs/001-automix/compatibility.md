# 混音兼容性评估与策略推荐

## 1. 需求背景

在用户选择两首歌曲进行混音时，系统应当能够：
1. **评估兼容性**：判断这两首歌是否适合混音，给出打分
2. **推荐策略**：基于分析结果，推荐最适合的混音策略

## 2. 技术可行性分析

### 2.1 可评估维度

| 维度 | 技术方案 | 准确度 | 复杂度 | 可行性 |
|------|----------|--------|--------|--------|
| **BPM差异** | 直接计算两首歌BPM的差异率 | 高 | 低 | ✅ 完全可行 |
| **调性匹配** | 使用librosa色度特征检测调性，基于五度圈计算距离 | 中 | 中 | ✅ 可行 |
| **能量匹配** | 分析两首歌的平均能量和动态范围 | 中 | 低 | ✅ 可行 |
| **节拍稳定性** | 检测BPM置信度，判断节拍是否清晰 | 中 | 中 | ✅ 可行 |
| **风格相似度** | 提取MFCC特征计算余弦相似度 | 低 | 高 | ⚠️ 需验证 |

### 2.2 各维度详细分析

#### BPM差异 (可行性: ✅ 高)
```
差异率 = |BPM_A - BPM_B| / max(BPM_A, BPM_B)

评分规则:
- 差异率 < 5%: 极高兼容性 (90-100分)
- 差异率 5-15%: 高兼容性 (70-90分) - 适合Beat-sync
- 差异率 15-30%: 中等兼容性 (50-70分) - 适合Crossfade
- 差异率 > 30%: 低兼容性 (30-50分) - 建议换歌
```

#### 调性匹配 (可行性: ✅ 中)
```
五度圈距离计算:
- 距离 0 (同调): 完全和谐 (100分)
- 距离 1-2 (相邻调): 高度和谐 (80-90分)
- 距离 3-6: 中等和谐 (50-70分)
- 距离 7-11: 不和谐 (30-50分)

适用策略:
- 高和谐度: 推荐 Harmonic
- 低和谐度: 推荐 Crossfade/Echo
```

#### 节拍稳定性 (可行性: ✅ 中)
```
计算BPM检测的置信度:
- 置信度 > 0.8: 节拍清晰，适合Beat-sync
- 置信度 0.5-0.8: 节拍一般，Beat-sync效果有限
- 置信度 < 0.5: 节拍模糊，建议Crossfade
```

#### 能量匹配 (可行性: ✅ 低)
```
分析方式:
- 计算两首歌的RMS能量均值
- 计算动态范围(峰值-均值)
- 评估能量差异对过渡的影响

评分权重较低，可作为辅助参考
```

### 2.3 综合评分算法

```python
def calculate_compatibility(track_a, track_b) -> dict:
    """
    计算两首歌的混音兼容性
    
    Returns:
    {
        "score": 85,              # 综合评分 0-100
        "bpm_score": 90,          # BPM兼容性
        "key_score": 80,         # 调性兼容性  
        "beat_score": 85,        # 节拍稳定性
        "recommendation": "beat_sync",  # 推荐策略
        "reason": "BPM接近，调性和谐"
    }
    """
    
    # BPM评分
    bpm_diff = abs(track_a.bpm - track_b.bpm) / max(track_a.bpm, track_b.bpm)
    if bpm_diff < 0.05: bpm_score = 100 - bpm_diff * 200
    elif bpm_diff < 0.15: bpm_score = 90 - (bpm_diff - 0.05) * 200
    else: bpm_score = 70 - (bpm_diff - 0.15) * 100
    
    # 调性评分
    key_distance = calculate_key_distance(track_a.key, track_b.key)
    key_score = max(0, 100 - key_distance * 10)
    
    # 节拍评分
    beat_score = (track_a.confidence + track_b.confidence) / 2 * 100
    
    # 综合评分 (加权平均)
    score = bpm_score * 0.4 + key_score * 0.3 + beat_score * 0.3
    
    # 推荐策略
    if score >= 80 and bpm_diff < 0.15:
        recommendation = "beat_sync"
    elif key_score >= 80:
        recommendation = "harmonic"
    elif bpm_diff > 0.25:
        recommendation = "echo_fade"
    else:
        recommendation = "crossfade"
    
    return {
        "score": round(score),
        "bpm_score": round(bpm_score),
        "key_score": round(key_score),
        "beat_score": round(beat_score),
        "recommendation": recommendation
    }
```

## 3. 推荐策略规则

| 评分 | 级别 | 推荐策略 | 说明 |
|------|------|----------|------|
| 80-100 | 极佳 | Beat-sync | BPM接近，节拍清晰，首选 |
| 70-80 | 优秀 | Beat-sync / Harmonic | 根据调性选择 |
| 50-70 | 一般 | Crossfade | 稳定可靠 |
| 30-50 | 较差 | Echo-fade | 用效果掩盖不协调 |
| <30 | 极差 | 警告 | 建议更换歌曲 |

## 4. 实现计划

### Phase 1: 基础评估 (1-2天)
- [x] BPM检测 (已实现)
- [ ] 调性检测 (基于现有色度特征)
- [ ] 兼容性评分算法
- [ ] 策略推荐逻辑

### Phase 2: 增强分析 (2-3天)
- [ ] 节拍置信度评估
- [ ] 能量分析
- [ ] 综合评分优化

### Phase 3: 前端展示 (1天)
- [ ] 显示兼容性评分
- [ ] 显示推荐策略及原因
- [ ] 各项维度评分可视化

## 5. 风险与限制

1. **BPM检测准确性**: 对古典、爵士等节奏自由的音乐可能不准确
2. **调性检测**: 对无调性音乐(电子、纯器乐)效果有限
3. **权重调优**: 评分权重需要通过大量测试调优

## 6. 结论

**可行性评估: ✅ 可行**

核心维度(BPM、调性、节拍)都有成熟的技术方案可以实现，准确度可控。建议优先实现BPM和调性分析，这两项对混音效果影响最大。
