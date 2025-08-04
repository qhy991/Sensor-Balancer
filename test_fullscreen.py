#!/usr/bin/env python3
"""
测试窗口全屏功能
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from weight_measurement_tool import WeightMeasurementInterface
    print("✅ 成功导入WeightMeasurementInterface")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

class TestFullscreenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全屏测试窗口")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        try:
            # 创建WeightMeasurementInterface实例
            self.weight_interface = WeightMeasurementInterface()
            layout.addWidget(self.weight_interface)
            print("✅ WeightMeasurementInterface 创建成功")
            
            # 添加全屏测试按钮
            self.fullscreen_btn = QPushButton("切换全屏")
            self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
            layout.addWidget(self.fullscreen_btn)
            
            # 检查窗口大小设置
            print(f"✅ 窗口最小大小: {self.weight_interface.minimumSize()}")
            print(f"✅ 窗口当前大小: {self.weight_interface.size()}")
            print(f"✅ 窗口是否可调整大小: {not self.weight_interface.isFixedSize()}")
            
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
    window = TestFullscreenWindow()
    window.show()
    
    print("✅ 测试窗口已显示")
    print("点击'切换全屏'按钮测试全屏功能")
    print("如果窗口可以全屏显示，说明修复成功！")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 