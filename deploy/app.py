"""
Flask API Server for music-mix (Production Version)
"""

import os
import sys
import uuid

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from flask import Flask, request, jsonify, send_from_directory, send_file
    from flask_cors import CORS
    from werkzeug.utils import secure_filename

    print("✓ Flask 依赖加载成功")
except ImportError as e:
    print(f"✗ Flask 依赖加载失败: {e}")
    sys.exit(1)

try:
    from mixer_core.mixer import Mixer

    print("✓ Mixer 模块导入成功")
except ImportError as e:
    print(f"✗ Mixer 模块导入失败: {e}")
    print(f"  Python 路径: {sys.path}")
    print(f"  当前目录: {os.getcwd()}")
    print(f"  文件所在: {os.path.dirname(os.path.abspath(__file__))}")
    sys.exit(1)

try:
    from mixer_core import Mixer

    print("✓ Mixer 模块导入成功")
except ImportError as e:
    print(f"✗ Mixer 模块导入失败: {e}")
    print("  请确保已安装 mixer_core: pip install -e .")
    sys.exit(1)

app = Flask(__name__, static_folder="demo", static_url_path="")
CORS(app)  # 启用跨域支持

# 配置
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "/tmp/music-mix-uploads")
app.config["OUTPUT_FOLDER"] = os.environ.get("OUTPUT_FOLDER", "/tmp/music-mix-outputs")

# 确保目录存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

mixer = Mixer()


@app.route("/")
def index():
    """前端页面"""
    return send_from_directory("demo", "index.html")


@app.route("/api/mix", methods=["POST"])
def mix():
    """混音接口"""
    try:
        if "track_a" not in request.files or "track_b" not in request.files:
            return jsonify({"error": "Missing track files"}), 400

        track_a = request.files["track_a"]
        track_b = request.files["track_b"]
        strategy = request.form.get("strategy", "crossfade")

        # 保存上传文件
        track_a_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        track_a.save(track_a_path)
        track_b.save(track_b_path)

        # 混音
        output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        result = mixer.mix(track_a_path, track_b_path, strategy=strategy, output_path=output_path)

        # 清理临时文件
        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except Exception:
            pass

        return jsonify(
            {
                "success": True,
                "strategy": result["strategy"],
                "bpm_a": result["bpm_a"],
                "bpm_b": result["bpm_b"],
                "duration": result["duration"],
                "transition_point": result["transition_point"],
                "transition_point_b": result.get("transition_point_b", 0),
                "transition_duration": result.get("transition_duration", 10),
                "output_url": f"/api/output/{output_filename}",
                "compatibility": result.get("compatibility", {}),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/output/<filename>")
def get_output(filename):
    """获取混音结果"""
    path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    if os.path.exists(path):
        return send_file(path, mimetype="audio/mpeg")
    return jsonify({"error": "File not found"}), 404


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """评估两首歌曲的兼容性"""
    try:
        if "track_a" not in request.files or "track_b" not in request.files:
            return jsonify({"error": "Missing track files"}), 400

        track_a = request.files["track_a"]
        track_b = request.files["track_b"]

        # 保存临时文件
        track_a_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        track_a.save(track_a_path)
        track_b.save(track_b_path)

        # 评估兼容性
        result = mixer.evaluate_compatibility(track_a_path, track_b_path)

        # 清理
        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except Exception:
            pass

        # 映射策略名称
        strategy_names = {
            "beat_sync": "Beat-sync",
            "crossfade": "Crossfade",
            "echo_fade": "Echo",
            "harmonic": "Harmonic",
        }

        return jsonify(
            {
                "success": True,
                "score": result["score"],
                "bpm_score": result.get("bpm_score"),
                "key_score": result.get("key_score"),
                "beat_score": result.get("beat_score"),
                "bpm_a": result["bpm_a"],
                "bpm_b": result["bpm_b"],
                "recommendation": result["recommendation"],
                "recommendation_name": strategy_names.get(
                    result["recommendation"], result["recommendation"]
                ),
                "reason": result["reason"],
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
