# 快速部署指南

## ✅ 已完成

- [x] 代码已推送到 GitHub
- [x] 部署配置文件已创建
- [x] 本地代码整理完成

---

## 📋 下一步（需要你在 Render.com 操作）

### 1. 登录 Render.com

访问：https://dashboard.render.com

### 2. 创建 Web Service

点击：**New +** → **Web Service**

### 3. 连接 GitHub 仓库

1. 找到仓库：`ai-mix`
2. 点击 **Connect**

### 4. 配置服务

| 配置项 | 输入值 |
|----------|---------|
| Name | `music-mix` |
| Region | `Oregon (US West)` |
| Branch | `main` |
| Root Directory | `.` |
| Runtime | `Python 3` |
| Build Command | `pip install -r deploy/requirements.txt && pip install -e .` |
| Start Command | `gunicorn deploy.app:app --workers 2 --timeout 120` |

### 5. 配置 Advanced 设置

#### 环境变量（Environment）

在 "Advanced" → "Environment Variables" 添加：

| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.6` |
| `MAX_CONTENT_LENGTH` | `52428800` |
| `UPLOAD_FOLDER` | `/tmp/music-mix-uploads` |
| `OUTPUT_FOLDER` | `/tmp/music-mix-outputs` |

#### 磁盘存储（Disk Storage）

在 "Advanced" → "Disk Storage" 添加：

| Mount Path | Size | Name |
|-----------|------|------|
| `/tmp` | `1 GB` | `music-mix-storage` |

### 6. 点击 **Create Web Service**

---

## 🕐 部署时间

- 首次部署：**5-10 分钟**（librosa 需要编译）
- 后续部署：**2-3 分钟**

---

## ✅ 部署后验证

1. **访问服务 URL**
   - 例如：`https://music-mix.onrender.com`

2. **测试前端**
   - 页面是否加载
   - 上传按钮是否可用

3. **测试混音**
   - 上传两首歌曲
   - 选择策略
   - 生成混音
   - 播放结果

---

## 🐛 常见问题

| 问题 | 解决方案 |
|------|---------|
| 部署超时 | 查看 DEPLOYMENT_PLAN.md 问题 1 |
| 依赖安装失败 | 查看 DEPLOYMENT_PLAN.md 问题 2 |
| 磁盘空间不足 | 确保配置了 1GB 磁盘 |
| 内存不足 | 可能需要升级到付费层 |
| CORS 错误 | 已添加 flask-cors 支持 |
| 静态文件 404 | 已修复 static_folder 路径 |

详细问题排查：请查看 `DEPLOYMENT_PLAN.md`

---

## 📞 需要帮助？

部署过程中遇到问题，可以：
1. 查看日志：Render 控制台 → Logs
2. 检查构建：Render 控制台 → Events
3. 测试本地：`cd deploy && python app.py`

---

## 🎉 部署成功后

你的服务将可以通过以下方式访问：

- **Web**: https://music-mix.onrender.com
- **API Health**: https://music-mix.onrender.com/health
- **Mix API**: https://music-mix.onrender.com/api/mix
- **Evaluate API**: https://music-mix.onrender.com/api/evaluate

---

**祝部署顺利！** 🚀
