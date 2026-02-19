# 部署指南

## 架构概览

```
┌─────────────────┐         ┌─────────────────────────────┐
│   Netlify       │  ───►   │   Render.com (Python/Flask) │
│   (静态前端)    │  API    │   (音频处理后端)            │
└─────────────────┘         └─────────────────────────────┘
```

## 部署步骤

### 第一步：部署后端 (Render.com)

1. **准备代码**
   ```bash
   cd music_mix
   # 确认 deploy 目录包含:
   # - app.py          # Flask 应用入口
   # - requirements.txt # 依赖
   # - render.yaml     # Render 配置
   ```

2. **推送到 GitHub**
   ```bash
   git add .
   git commit -m "Add production deployment files"
   git push origin main
   ```

3. **在 Render.com 创建服务**
   - 登录 https://dashboard.render.com
   - 点击 "New +" → "Web Service"
   - 连接你的 GitHub 仓库
   - 设置：
     - Name: `music-mix-api`
     - Region: `Oregon` (或最近区域)
     - Branch: `main`
     - Build Command: `pip install -r deploy/requirements.txt`
     - Start Command: `gunicorn deploy.app:app --workers 2 --timeout 120`
   - 点击 "Create Web Service"

4. **等待部署完成**
   - 首次部署需要 3-5 分钟
   - 完成后会得到一个 URL，例如：`https://music-mix-api.onrender.com`
   - 访问 `/health` 确认服务正常

### 第二步：部署前端 (Netlify)

1. **配置 API 地址**
   - 编辑 `demo/index.html`
   - 找到 `const API_BASE = '';`
   - 改为：`const API_BASE = 'https://你的-render-app.onrender.com';`

2. **推送代码**
   ```bash
   git add .
   git commit -m "Configure production API URL"
   git push origin main
   ```

3. **在 Netlify 创建站点**
   - 登录 https://app.netlify.com
   - 点击 "Add new site" → "Import an existing project"
   - 选择 GitHub 仓库
   - 配置：
     - Base directory: `music_mix`
     - Build command: `echo "Static site"`
     - Publish directory: `demo`
   - 点击 "Deploy site"

4. **配置重定向**
   - 项目中已有 `deploy/netlify.toml`
   - Netlify 会自动处理 SPA 重定向

### 第三步：验证

1. 访问 Netlify 提供的 URL
2. 上传两首歌曲测试混音功能
3. 确认 API 请求成功（检查浏览器开发者工具）

---

## 环境变量

### Render.com (后端)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PYTHON_VERSION` | 3.11 | Python 版本 |
| `MAX_CONTENT_LENGTH` | 52428800 | 最大上传 50MB |
| `UPLOAD_FOLDER` | /tmp/music-mix-uploads | 上传目录 |
| `OUTPUT_FOLDER` | /tmp/music-mix-outputs | 输出目录 |
| `PORT` | 5000 | 服务端口 |

### Netlify (前端)

| 变量 | 说明 |
|------|------|
| `API_BASE` | 后端 API 地址 |

---

## 费用

- **Render.com**: 免费层每月 750 小时（足够个人使用）
- **Netlify**: 免费层每月 100GB 流量

---

## 常见问题

### 1. 上传文件失败
- 检查 Render.com 的磁盘配置（见 render.yaml）
- 确保 /tmp 目录有足够空间

### 2. 混音时间过长
- 免费层有 30 秒请求超时
- 可升级到付费层或优化处理逻辑

### 3. CORS 错误
- 确保前端 API_BASE 正确指向 Render URL
- 检查 Render 日志确认请求是否到达
