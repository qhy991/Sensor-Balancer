#!/usr/bin/env python3
"""
测试校正系统修复的脚本
"""

import sys
import os
from PyQt5 import QtWidgets

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_calibration_widget():
    """测试校正组件的基本功能"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 导入校正组件
    from calibration_system import CalibrationWidget
    
    # 创建一个测试窗口
    test_window = QtWidgets.QWidget()
    test_window.setWindowTitle("校正组件测试")
    test_window.setGeometry(100, 100, 800, 600)
    
    # 创建校正组件
    calibration_widget = CalibrationWidget(test_window)
    
    # 设置布局
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(calibration_widget)
    test_window.setLayout(layout)
    
    # 显示窗口
    test_window.show()
    
    print("✅ 校正组件测试窗口已打开")
    print("请检查:")
    print("1. 校正组件是否正确显示")
    print("2. 点击'调试状态'按钮是否正常工作")
    print("3. 标签页是否正常切换")
    
    return app.exec_()

if __name__ == "__main__":
    test_calibration_widget() 