"""
Flask API Server for music-mix (Minimal Version)
直接运行，不使用 gunicorn
"""

import os
import sys

# 设置项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 50)
print("开始启动应用...")
print(f"项目目录: {project_root}")

# 导入依赖
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

print("✓ Flask 加载成功")

# 延迟导入 Mixer（避免启动时崩溃）
mixer = None


def get_mixer():
    global mixer
    if mixer is None:
        from mixer_core.mixer import Mixer

        mixer = Mixer()
        print("✓ Mixer 初始化成功")
    return mixer


# 创建 Flask 应用
app = Flask(__name__)

# 配置
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "/tmp/music-mix-uploads"
app.config["OUTPUT_FOLDER"] = "/tmp/music-mix-outputs"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

CORS(app)

print("✓ 应用配置完成")


# 路由
@app.route("/")
def index():
    index_path = os.path.join(project_root, "demo", "index.html")
    print(f"尝试加载: {index_path}")
    print(f"文件存在: {os.path.exists(index_path)}")
    if os.path.exists(index_path):
        return send_from_directory(os.path.join(project_root, "demo"), "index.html")
    return jsonify({"error": "index.html not found"}), 404


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/test", methods=["POST"])
def test():
    print(f"\n[/api/test] 收到测试请求")
    return jsonify({"status": "ok", "message": "API is working"})


@app.route("/favicon.ico")
def favicon():
    return "", 204  # 返回空响应，忽略 favicon 请求


@app.route("/api/mix", methods=["POST"])
def mix():
    import uuid

    try:
        if "track_a" not in request.files or "track_b" not in request.files:
            return jsonify({"error": "Missing files"}), 400

        m = get_mixer()

        track_a = request.files["track_a"]
        track_b = request.files["track_b"]
        strategy = request.form.get("strategy", "crossfade")

        track_a_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        track_a.save(track_a_path)
        track_b.save(track_b_path)

        output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        result = m.mix(track_a_path, track_b_path, strategy=strategy, output_path=output_path)

        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except:
            pass

        return jsonify(
            {
                "success": True,
                "strategy": result["strategy"],
                "bpm_a": result["bpm_a"],
                "bpm_b": result["bpm_b"],
                "duration": result["duration"],
                "transition_point": result["transition_point"],
                "output_url": f"/api/output/{output_filename}",
            }
        )
    except Exception as e:
        print(f"Mix error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/output/<filename>")
def get_output(filename):
    path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    if os.path.exists(path):
        return send_from_directory(app.config["OUTPUT_FOLDER"], filename, mimetype="audio/mpeg")
    return jsonify({"error": "Not found"}), 404


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    import uuid
    import time

    start_time = time.time()

    print(f"\n{'=' * 60}")
    print(f"[{time.strftime('%H:%M:%S')}] 收到 /api/evaluate 请求")
    print(f"Content-Type: {request.content_type}")
    print(f"Content-Length: {request.content_length}")

    try:
        if "track_a" not in request.files or "track_b" not in request.files:
            print("错误: 缺少文件")
            return jsonify({"error": "Missing files"}), 400

        track_a = request.files["track_a"]
        track_b = request.files["track_b"]

        print(f"Track A: {track_a.filename}, size: {request.content_length}")
        print(f"Track B: {track_b.filename}")

        track_a_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        print(f"保存文件到: {track_a_path}")
        track_a.save(track_a_path)
        track_b.save(track_b_path)
        print(f"文件保存完成, 耗时: {time.time() - start_time:.2f}s")

        print("开始初始化 Mixer...")
        t1 = time.time()
        m = get_mixer()
        print(f"Mixer 初始化完成, 耗时: {time.time() - t1:.2f}s")

        print("开始分析音频...")
        t2 = time.time()
        result = m.evaluate_compatibility(track_a_path, track_b_path)
        print(f"分析完成, 耗时: {time.time() - t2:.2f}s")
        print(f"评估结果: {result}")

        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except:
            pass

        total_time = time.time() - start_time
        print(f"总耗时: {total_time:.2f}s")
        print("=" * 60)

        return jsonify(
            {
                "success": True,
                "score": result["score"],
                "bpm_score": result.get("bpm_score", 0),
                "key_score": result.get("key_score", 0),
                "beat_score": result.get("beat_score", 0),
                "recommendation": result["recommendation"],
                "recommendation_name": {
                    "crossfade": "Crossfade",
                    "beat_sync": "Beat-sync",
                    "echo_fade": "Echo",
                    "harmonic": "Harmonic",
                }.get(result["recommendation"], result["recommendation"]),
                "reason": result["reason"],
                "bpm_a": result["bpm_a"],
                "bpm_b": result["bpm_b"],
            }
        )

    except Exception as e:
        print(f"评估错误: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# 启动
if __name__ == "__main__":
    print("=" * 50)
    print("Render 启动检查")
    print("=" * 50)
    print(f"PORT 环境变量: {os.environ.get('PORT', 'NOT SET')}")
    print(f"环境变量数量: {len(os.environ)}")

    print("检查系统依赖...")
    import subprocess

    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        print(f"✓ ffmpeg: {result.stdout.split(chr(10))[0] if result.stdout else 'not found'}")
    except Exception as e:
        print(f"✗ ffmpeg: {e}")

    try:
        import soundfile

        print(f"✓ soundfile: {soundfile.__version__}")
    except Exception as e:
        print(f"✗ soundfile: {e}")

    try:
        import librosa

        print(f"✓ librosa: {librosa.__version__}")
    except Exception as e:
        print(f"✗ librosa: {e}")

    port_str = os.environ.get("PORT")
    if port_str:
        port = int(port_str)
        print(f"✓ PORT: {port} (来自环境变量)")
    else:
        port = 5000
        print(f"⚠ PORT 未设置，使用默认端口 {port}")

    print(f"✓ 启动服务器在端口 {port}")
    print("=" * 50)

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
