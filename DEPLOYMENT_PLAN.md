# Render.com 部署规划

## 项目结构

```
music_mix/ (根目录)
├── deploy/
│   ├── app.py           # Flask 应用入口（用于生产）
│   ├── requirements.txt # 依赖列表
│   └── render.yaml      # Render 配置文件
├── demo/
│   └── index.html       # 前端静态页面
├── mixer_core/           # 核心算法
├── .gitignore           # Git 忽略文件
└── README.md            # 项目说明
```

---

## 部署步骤

### 步骤 1：本地测试（必做）

```bash
# 1. 安装依赖
pip install -r deploy/requirements.txt

# 2. 测试 Flask 应用
cd deploy
python app.py

# 3. 访问 http://localhost:5000
# 确认页面正常加载，API 可用
```

**如果本地测试失败**：
- 检查依赖是否正确安装
- 确认 `demo/` 目录和 `mixer_core/` 在正确位置
- 查看错误日志

---

### 步骤 2：提交代码到 Git

```bash
# 1. 切换到项目根目录
cd /Users/mi/Desktop/auto_mix/music_mix

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "准备部署：添加 Render.com 配置文件"

# 4. 推送到 GitHub
git push -u origin main
```

**如果推送失败**：
- 确认远程仓库已添加：`git remote -v`
- 如果没有，添加：`git remote add origin https://github.com/mileszhang001-boom/ai-mix.git`
- 检查 GitHub 仓库是否有写入权限

---

### 步骤 3：在 Render.com 创建服务

#### 3.1 登录并创建

1. 访问：https://dashboard.render.com
2. 登录 GitHub 账户（如未登录）
3. 点击：**New +** → **Web Service**

#### 3.2 连接 GitHub 仓库

1. 在 "Build and deploy from Git" 下：
   - 找到 "ai-mix" 仓库
   - 点击 **Connect**

#### 3.3 配置服务

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Name** | `music-mix` | 服务名称 |
| **Region** | `Oregon (US West)` | 选择最近的区域 |
| **Branch** | `main` | 分支名称 |
| **Root Directory** | `.` | 项目根目录 |
| **Runtime** | `Python 3` | 运行环境 |
| **Build Command** | `pip install -r deploy/requirements.txt && pip install -e .` | 安装依赖 |
| **Start Command** | `gunicorn deploy.app:app --workers 2 --timeout 120` | 启动命令 |

#### 3.4 配置环境变量（在 Advanced 部分）

| 变量名 | 值 | 必需 |
|----------|-----|------|
| `PYTHON_VERSION` | `3.11.6` | 否 |
| `PORT` | `5000` | 否（Render 自动设置） |
| `MAX_CONTENT_LENGTH` | `52428800` | 否 |
| `UPLOAD_FOLDER` | `/tmp/music-mix-uploads` | 否 |
| `OUTPUT_FOLDER` | `/tmp/music-mix-outputs` | 否 |

#### 3.5 配置磁盘（Disk Storage）

1. 在服务页面找到 **Disk Storage**
2. 点击 **Add Disk**
3. 配置：
   - **Mount Path**: `/tmp`
   - **Size**: `1 GB`
   - **Name**: `music-mix-storage`

#### 3.6 点击 **Create Web Service**

---

### 步骤 4：等待部署

- 首次部署：**5-10 分钟**（需要安装 librosa 等大依赖）
- 后续部署：**2-3 分钟**
- 实时日志：在 Render 控制台查看

**部署成功标志**：
- 状态变为 **"Live"**
- 得到一个 URL，例如：`https://music-mix.onrender.com`

---

### 步骤 5：测试部署

```bash
# 1. 访问 URL
open https://你的服务名.onrender.com

# 2. 测试前端
- 页面是否正常加载
- 上传歌曲按钮是否可用

# 3. 测试 API
- 上传两首歌曲
- 确认混音功能正常
- 播放混音结果
```

---

## 可能遇到的问题

### 问题 1：部署超时

**现象**：
- 部署一直卡在 "Building" 状态
- 15 分钟后超时失败

**原因**：
- librosa 编译时间过长（包含 C 扩展）

**解决方案**：
```yaml
# 在 render.yaml 中配置更长的超时时间
services:
  - name: music-mix-api
    type: web
    runtime: python
    timeout: 900  # 15 分钟
```

---

### 问题 2：依赖安装失败

**现象**：
```
ERROR: Failed building wheel for librosa
```

**原因**：
- 系统缺少 ffmpeg（librosa 的依赖）

**解决方案**：
在 `render.yaml` 中预安装系统依赖：

```yaml
services:
  - name: music-mix-api
    type: web
    envVars:
      - key: APT_INSTALL_CMD
        value: "apt-get update && apt-get install -y ffmpeg"
    buildCommand: "$APT_INSTALL_CMD && pip install -r deploy/requirements.txt && pip install -e ."
```

---

### 问题 3：磁盘空间不足

**现象**：
- 混音时上传/输出失败
- 日志显示 "No space left on device"

**原因**：
- 免费层磁盘空间小（512MB - 1GB）

**解决方案**：
1. **添加 Disk Storage**（已在步骤 3.5 配置）
2. **增加磁盘大小到 2GB**
3. **定期清理临时文件**

---

### 问题 4：内存不足

**现象**：
- 混音时服务崩溃
- 日志显示 "Out of memory"

**原因**：
- librosa 加载大音频占用大量内存
- 免费层内存限制：512MB

**解决方案**：
1. **降低采样率**（已在 mixer_core 默认 22050）
2. **限制音频时长**（提示用户上传 < 5 分钟）
3. **升级到付费层**（512MB → 2GB）

---

### 问题 5：CORS 错误

**现象**：
- 前端调用 API 失败
- 浏览器控制台：`CORS policy: No 'Access-Control-Allow-Origin'`

**原因**：
- Flask 未配置 CORS

**解决方案**：
在 `deploy/app.py` 中添加：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求
```

需要安装 `flask-cors`：

```txt
# deploy/requirements.txt
flask-cors>=4.0.0
```

---

### 问题 6：静态文件 404

**现象**：
- 前端页面加载，但 CSS/JS 资源 404

**原因**：
- Flask static_folder 路径配置错误

**解决方案**：
已在 `deploy/app.py` 中修复：
```python
app = Flask(__name__, static_folder="demo", static_url_path="")
```

---

### 问题 7：混音超时

**现象**：
- 上传大文件后等待很久
- 最终超时失败

**原因**：
- Gunicorn 默认超时 30 秒

**解决方案**：
已在 render.yaml 中配置：
```yaml
startCommand: "gunicorn deploy.app:app --workers 2 --timeout 120"
```

---

## 部署后优化

### 1. 添加健康检查端点

Render 会定期调用 `/health` 确认服务存活：

```python
@app.route("/health")
def health():
    return {"status": "ok"}
```

### 2. 配置自动重试

混音失败时，前端自动重试：

```javascript
async function retryMix(attempts = 3) {
    for (let i = 0; i < attempts; i++) {
        try {
            await fetch('/api/mix', ...);
            return;
        } catch (err) {
            if (i === attempts - 1) throw err;
            await sleep(1000);
        }
    }
}
```

### 3. 添加监控

使用 Render 内置日志：
- 在控制台实时查看日志
- 搜索关键字：`ERROR`, `WARNING`, `Exception`

---

## 费用预估

### 免费层

| 资源 | 限制 | 说明 |
|--------|------|------|
| 运行时间 | 750 小时/月 | 约 25 天/月 |
| 内存 | 512 MB | 可能需要升级 |
| 磁盘 | 1 GB | 需额外配置 |
| 带宽 | 100 GB/月 | 足够测试 |

### 付费层（如需升级）

| 资源 | Starter ($7/月) | Standard ($25/月) |
|--------|------------------|-------------------|
| 运行时间 | 无限 | 无限 |
| 内存 | 2 GB | 8 GB |
| CPU | 1 核 | 2 核 |
| 磁盘 | 10 GB | 100 GB |
| 带宽 | 500 GB | 2000 GB |

---

## 回滚方案

如果部署失败或遇到问题：

### 选项 1：恢复本地运行

```bash
# 直接运行本地 demo
cd demo
python server.py
```

### 选项 2：切换到 Netlify 前端 + Render 后端

参考 `DEPLOY.md` 中的方案 B。

---

## 检查清单

部署前：
- [ ] 本地测试通过（`python deploy/app.py`）
- [ ] 所有文件已提交到 Git
- [ ] 代码已推送到 GitHub
- [ ] README.md 已更新（添加部署说明）

部署时：
- [ ] Render 服务已创建
- [ ] 环境变量已配置
- [ ] 磁盘存储已添加
- [ ] Build Command 正确
- [ ] Start Command 正确

部署后：
- [ ] 服务状态为 "Live"
- [ ] URL 可访问
- [ ] 前端页面正常加载
- [ ] 上传歌曲功能正常
- [ ] 混音功能正常
- [ ] 输出音频可播放
