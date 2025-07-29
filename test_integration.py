#!/usr/bin/env python3
"""
测试简化校正系统整合的脚本
"""

import sys
import os
from PyQt5 import QtWidgets

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_integration():
    """测试简化校正系统的整合"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 导入主界面
    from simple_sensor_interface import SimpleSensorInterface
    
    # 创建主窗口
    window = SimpleSensorInterface()
    window.show()
    
    print("✅ 主界面已打开")
    print("请检查:")
    print("1. 是否显示了3个标签页：一致性评估、校正系统、简化校正")
    print("2. 简化校正标签页是否包含使用说明和所有控件")
    print("3. 点击'快速校正'菜单是否弹出选择对话框")
    print("4. 传感器连接后是否可以正常使用简化校正功能")
    
    return app.exec_()

if __name__ == "__main__":
    test_integration() 