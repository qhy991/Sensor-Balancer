#!/usr/bin/env python3
"""
测试引导功能是否正常工作
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from sensor_sensitivity_calibration import SensitivityCalibrationInterface

def test_guide_function():
    """测试引导功能"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("引导功能测试")
    main_window.resize(1400, 900)
    
    # 创建主界面
    interface = SensitivityCalibrationInterface()
    main_window.setCentralWidget(interface)
    
    # 显示窗口
    main_window.show()
    
    print("🎉 引导功能测试已启动！")
    print("\n📋 测试步骤:")
    print("1. 在右侧标签页中选择 '局部灵敏度检验'")
    print("2. 选择一个预定义区域（如：中心区域）")
    print("3. 设置测试参数（微小变化范围、位置数量等）")
    print("4. 点击 '生成微调位置' 生成测试位置")
    print("5. 点击 '开始引导式测试' 启动可视化引导 ⭐")
    print("6. 观察是否出现引导窗口")
    print("7. 检查手动控制按钮是否启用")
    print("\n🔍 需要验证的功能:")
    print("• 引导窗口是否正常显示")
    print("• 红色标记是否显示当前按压位置")
    print("• 手动控制按钮是否启用")
    print("• 状态显示是否更新")
    
    # 延迟显示提示
    QTimer.singleShot(2000, lambda: QMessageBox.information(
        main_window, 
        "测试提示", 
        "请按照控制台中的步骤进行测试：\n\n"
        "1. 选择'局部灵敏度检验'标签页\n"
        "2. 选择测试区域并生成位置\n"
        "3. 点击'开始引导式测试'按钮\n"
        "4. 观察引导窗口和按钮状态"
    ))
    
    return app.exec_()

if __name__ == "__main__":
    from PyQt5.QtCore import QTimer
    test_guide_function() 