#!/usr/bin/env python3
"""
测试引导式测量功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from sensor_sensitivity_calibration import SensitivityCalibrationInterface

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("引导式测量功能测试")
    main_window.resize(1400, 900)
    
    # 创建主界面
    interface = SensitivityCalibrationInterface()
    main_window.setCentralWidget(interface)
    
    # 显示窗口
    main_window.show()
    
    print("🎉 引导式测量功能测试已启动！")
    print("\n📋 测试步骤:")
    print("1. 在右侧标签页中选择 '局部灵敏度检验'")
    print("2. 选择一个预定义区域（如：中心区域）")
    print("3. 设置测试参数（微小变化范围、位置数量等）")
    print("4. 点击 '生成微调位置' 生成测试位置")
    print("5. 点击 '开始引导式测试' 启动可视化引导")
    print("6. 按照引导窗口中的红色标记进行按压")
    print("7. 使用手动控制按钮进行数据采集")
    print("\n🔧 新增功能:")
    print("• 可视化引导窗口显示按压位置")
    print("• 红色大圆点标记当前需要按压的位置")
    print("• 黄色闪烁圆圈增强视觉效果")
    print("• 手动控制按钮（下一个位置、上一个位置、记录数据）")
    print("• 实时状态显示和进度跟踪")
    print("• 位置完成提示和自动切换")
    
    return app.exec_()

if __name__ == "__main__":
    main() 