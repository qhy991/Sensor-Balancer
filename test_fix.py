#!/usr/bin/env python3
"""
测试WeightMeasurementWidget修复
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from weight_measurement_tool import WeightMeasurementWidget
    print("✅ 成功导入WeightMeasurementWidget")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WeightMeasurementWidget 测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        try:
            # 创建WeightMeasurementWidget实例
            self.weight_widget = WeightMeasurementWidget()
            layout.addWidget(self.weight_widget)
            print("✅ WeightMeasurementWidget 创建成功")
            
            # 测试一些基本属性
            print(f"✅ 校准系数: {self.weight_widget.calibration_coefficient}")
            print(f"✅ 校准偏置: {self.weight_widget.calibration_bias}")
            print(f"✅ 归零压力: {self.weight_widget.zero_pressure}")
            print(f"✅ 是否已归零: {self.weight_widget.is_zeroed}")
            
        except Exception as e:
            print(f"❌ 创建WeightMeasurementWidget失败: {e}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("✅ 测试窗口已显示")
    print("如果看到窗口且没有错误信息，说明修复成功！")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 