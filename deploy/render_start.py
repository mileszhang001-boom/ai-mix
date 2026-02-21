"""
Render 启动脚本 - 正确处理 PORT 环境变量
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("Render 启动脚本")
print("=" * 60)
print(f"当前工作目录: {os.getcwd()}")
print(
    f"所有环境变量: {[k for k in os.environ.keys() if k.startswith(('PORT', 'PYTHON', 'UPLOAD', 'OUTPUT'))]}"
)
print(f"PORT 值: {os.environ.get('PORT', 'NOT SET')}")
print("=" * 60)

# 导入 Flask 应用
try:
    from deploy.app_minimal import app

    print("✓ Flask 应用导入成功")
except ImportError as e:
    print(f"✗ Flask 应用导入失败: {e}")
    sys.exit(1)

# 获取端口
port = int(os.environ.get("PORT", 5000))
print(f"将启动在端口: {port}")
print("=" * 60)

# 启动应用
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
