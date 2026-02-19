"""
Vercel API Handler for music-mix
"""

import os
import sys
import uuid

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.utils import secure_filename

# 初始化 Mixer（延迟）
mixer = None


def get_mixer():
    global mixer
    if mixer is None:
        from mixer_core.mixer import Mixer

        mixer = Mixer()
    return mixer


# 配置
UPLOAD_FOLDER = "/tmp/music-mix-uploads"
OUTPUT_FOLDER = "/tmp/music-mix-outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def api_evaluate(request):
    """评估 API"""
    if request.method != "POST":
        return {"error": "Method not allowed"}, 405

    try:
        files = request.files
        if "track_a" not in files or "track_b" not in files:
            return {"error": "Missing files"}, 400

        track_a = files["track_a"]
        track_b = files["track_b"]

        # 保存文件
        track_a_path = os.path.join(
            UPLOAD_FOLDER, f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            UPLOAD_FOLDER, f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        track_a.save(track_a_path)
        track_b.save(track_b_path)

        # 评估
        m = get_mixer()
        result = m.evaluate_compatibility(track_a_path, track_b_path)

        # 清理
        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except:
            pass

        return {
            "success": True,
            "score": result["score"],
            "recommendation": result["recommendation"],
            "reason": result["reason"],
            "bpm_a": result["bpm_a"],
            "bpm_b": result["bpm_b"],
        }

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}, 500


def api_mix(request):
    """混音 API"""
    if request.method != "POST":
        return {"error": "Method not allowed"}, 405

    try:
        files = request.files
        if "track_a" not in files or "track_b" not in files:
            return {"error": "Missing files"}, 400

        track_a = files["track_a"]
        track_b = files["track_b"]
        strategy = request.form.get("strategy", "crossfade")

        # 保存文件
        track_a_path = os.path.join(
            UPLOAD_FOLDER, f"{uuid.uuid4()}_{secure_filename(track_a.filename)}"
        )
        track_b_path = os.path.join(
            UPLOAD_FOLDER, f"{uuid.uuid4()}_{secure_filename(track_b.filename)}"
        )

        track_a.save(track_a_path)
        track_b.save(track_b_path)

        # 混音
        m = get_mixer()
        output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        result = m.mix(track_a_path, track_b_path, strategy=strategy, output_path=output_path)

        # 清理
        try:
            os.remove(track_a_path)
            os.remove(track_b_path)
        except:
            pass

        return {
            "success": True,
            "strategy": result["strategy"],
            "bpm_a": result["bpm_a"],
            "bpm_b": result["bpm_b"],
            "duration": result["duration"],
            "transition_point": result["transition_point"],
            "output_url": f"/api/output/{output_filename}",
        }

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}, 500


def api_output(request, filename):
    """获取输出文件"""
    path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read(), 200, {"Content-Type": "audio/mpeg"}
    return {"error": "Not found"}, 404


def handler(request):
    """主处理函数"""
    path = request.path

    if path == "/api/evaluate":
        return api_evaluate(request)
    elif path == "/api/mix":
        return api_mix(request)
    elif path.startswith("/api/output/"):
        filename = path.split("/api/output/")[1]
        return api_output(request, filename)
    elif path == "/health":
        return {"status": "ok"}
    else:
        # 返回 index.html（前端）
        index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return f.read(), 200, {"Content-Type": "text/html"}
        return {"error": "Not found"}, 404
