#!/usr/bin/env python3
"""
传感器称重工具启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from weight_measurement_tool import main
    
    if __name__ == "__main__":
        print("🚀 启动传感器称重工具...")
        main()
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保所有依赖模块都已正确安装")
    print("需要的依赖:")
    print("- PyQt5")
    print("- pyqtgraph")
    print("- numpy")
    print("- usb")
    input("按回车键退出...")
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    input("按回车键退出...") 