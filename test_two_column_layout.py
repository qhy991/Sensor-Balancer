#!/usr/bin/env python3
"""
测试两栏布局效果
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from weight_measurement_tool import WeightMeasurementInterface
    print("✅ 成功导入WeightMeasurementInterface")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

class TwoColumnLayoutTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("两栏布局测试")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 添加说明标签
        info_label = QLabel("两栏布局测试\n左侧：传感器控制和监控\n右侧：称重组件")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; margin: 20px; background-color: #f8f9fa; padding: 20px; border: 2px solid #dee2e6; border-radius: 8px;")
        layout.addWidget(info_label)
        
        try:
            # 创建WeightMeasurementInterface实例
            self.weight_interface = WeightMeasurementInterface()
            layout.addWidget(self.weight_interface)
            print("✅ WeightMeasurementInterface 创建成功")
            
            # 检查布局信息
            print(f"✅ 窗口标题: {self.weight_interface.windowTitle()}")
            print(f"✅ 窗口最小大小: {self.weight_interface.minimumSize()}")
            print(f"✅ 窗口当前大小: {self.weight_interface.size()}")
            
            # 添加全屏测试按钮
            self.fullscreen_btn = QPushButton("切换全屏")
            self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
            self.fullscreen_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #007bff; color: white;")
            layout.addWidget(self.fullscreen_btn)
            
        except Exception as e:
            print(f"❌ 创建WeightMeasurementInterface失败: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("切换全屏")
            print("✅ 退出全屏模式")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")
            print("✅ 进入全屏模式")

def main():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TwoColumnLayoutTest()
    window.show()
    
    print("✅ 两栏布局测试窗口已显示")
    print("左侧栏包含：传感器控制、压力信息、热力图、校准信息")
    print("右侧栏包含：称重组件（校准参数、归零控制、重量显示、测量控制、历史记录）")
    print("如果看到两栏布局且功能正常，说明修改成功！")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 