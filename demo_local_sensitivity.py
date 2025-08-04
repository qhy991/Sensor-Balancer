#!/usr/bin/env python3
"""
LocalSensitivityWidget 集成演示 - 包含引导式测量功能
展示局部传感器灵敏度检验功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sensor_sensitivity_calibration import SensitivityCalibrationInterface

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("传感器敏感性标定系统 - 引导式测量功能演示")
    main_window.resize(1400, 900)
    
    # 创建主界面
    interface = SensitivityCalibrationInterface()
    main_window.setCentralWidget(interface)
    
    # 显示窗口
    main_window.show()
    
    print("🎉 LocalSensitivityWidget 引导式测量功能演示已启动！")
    print("\n📋 使用说明:")
    print("1. 在右侧标签页中选择 '局部灵敏度检验'")
    print("2. 选择一个预定义区域（如：中心区域）")
    print("3. 设置测试参数（微小变化范围、位置数量等）")
    print("4. 点击 '生成微调位置' 生成测试位置")
    print("5. 选择测试模式：")
    print("   • '开始灵敏度测试' - 自动测试模式")
    print("   • '开始引导式测试' - 可视化引导模式 ⭐")
    print("\n🔧 引导式测试功能特点:")
    print("• 64x64传感器网格可视化显示")
    print("• 红色大圆点标记当前按压位置")
    print("• 黄色闪烁圆圈增强视觉引导")
    print("• 手动控制按钮（下一个位置、上一个位置、记录数据）")
    print("• 实时状态显示和进度跟踪")
    print("• 位置完成提示和自动切换")
    print("\n🎯 引导式测试操作流程:")
    print("1. 点击'开始引导式测试'启动可视化引导")
    print("2. 观察引导窗口中的红色标记位置")
    print("3. 按照标记位置进行按压")
    print("4. 点击'记录数据'或'下一个位置'记录数据")
    print("5. 重复步骤3-4直到所有位置完成")
    print("6. 测试完成后进行数据分析和结果保存")
    
    return app.exec_()

if __name__ == "__main__":
    main() 