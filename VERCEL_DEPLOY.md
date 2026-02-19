# Vercel 部署指南

## 快速部署

### 1. 安装 Vercel CLI（如果还没有）

```bash
npm i -g vercel
```

### 2. 部署

```bash
vercel
```

### 3. 按照提示操作

- Set up and deploy? **Y**
- Which scope? **你的用户名**
- Want to link to existing project? **N**
- What's your project's name? **ai-mix** (或你喜欢的名字)
- In which directory is your code located? **./**

### 4. 部署完成

Vercel 会给你一个 URL，例如：`https://ai-mix.vercel.app`

---

## ⚠️ 重要限制

### Vercel 免费层限制

| 限制 | 值 |
|------|-----|
| 带宽 | 100GB/月 |
| 函数执行时间 | 10 秒 |
| 请求大小 | 4.5MB |

### 问题

1. **音频文件太大**：免费层只支持 4.5MB 以内的文件
2. **处理时间太长**：librosa 分析可能超过 10 秒

### 解决方案

1. **使用短音频**：建议使用 1-3 分钟的音频文件
2. **压缩音频**：上传前先压缩音频文件
3. **升级付费层**：如果需要处理更长文件

---

## 📁 项目结构

```
ai-mix/
├── api/
│   └── index.py       # Vercel API 处理函数
├── demo/
│   └── index.html     # 前端页面
├── mixer_core/        # 核心算法
├── vercel.json        # Vercel 配置
└── deploy/
    └── requirements.txt  # Python 依赖
```

---

## 🔧 本地开发

```bash
# 安装依赖
pip install -r deploy/requirements.txt

# 本地运行
vercel dev
```

---

## 🎯 测试建议

1. 使用**短音频文件**（1-2分钟）
2. 先测试**评估功能**（/api/evaluate）
3. 再测试**混音功能**（/api/mix）

---

## 💡 如果遇到问题

1. **超时**：Vercel 免费层限制 10 秒，可能不够
2. **文件太大**：免费层只支持 4.5MB 以内

如果需要处理更长/更大的音频，建议：
- 升级到 Vercel Pro
- 或使用 Render 付费层
