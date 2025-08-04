#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试传感器模式切换功能
"""

import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# 尝试导入传感器接口
try:
    from simple_sensor_interface import SensorInterface
    DATA_HANDLER_AVAILABLE = True
    print("✅ 传感器接口可用")
except ImportError:
    print("⚠️ 传感器接口不可用，将使用模拟数据")
    DATA_HANDLER_AVAILABLE = False

class SensorModeTest(QWidget):
    """传感器模式测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.data_handler = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("传感器模式测试")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 传感器选择
        sensor_group = QGroupBox("传感器选择")
        sensor_layout = QVBoxLayout()
        
        self.sensor_combo = QComboBox()
        self.sensor_combo.addItems(["模拟传感器", "真实传感器"])
        self.sensor_combo.currentTextChanged.connect(self.on_sensor_changed)
        
        self.status_label = QLabel("状态: 未初始化")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        sensor_layout.addWidget(QLabel("选择传感器类型:"))
        sensor_layout.addWidget(self.sensor_combo)
        sensor_layout.addWidget(self.status_label)
        
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
        # 测试按钮
        test_group = QGroupBox("测试功能")
        test_layout = QVBoxLayout()
        
        self.test_btn = QPushButton("测试数据获取")
        self.test_btn.clicked.connect(self.test_data_acquisition)
        self.test_btn.setEnabled(False)
        
        self.result_label = QLabel("测试结果: 未测试")
        self.result_label.setStyleSheet("font-family: monospace; background-color: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.result_label)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 信息显示
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()
        
        info_text = f"传感器接口可用: {'是' if DATA_HANDLER_AVAILABLE else '否'}\n"
        info_text += f"当前模式: 未选择\n"
        info_text += f"数据处理器: 未初始化"
        
        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-family: monospace; background-color: #e9ecef; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        info_layout.addWidget(self.info_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)
        
        # 初始化传感器
        self.init_sensor()
    
    def init_sensor(self):
        """初始化传感器"""
        try:
            if DATA_HANDLER_AVAILABLE:
                self.data_handler = SensorInterface()
                print("✅ 传感器接口初始化成功")
            else:
                print("⚠️ 使用模拟传感器")
                self.data_handler = None
        except Exception as e:
            print(f"⚠️ 传感器初始化失败: {e}")
            self.data_handler = None
    
    def on_sensor_changed(self, sensor_text):
        """传感器选择变化时的处理函数"""
        try:
            if sensor_text == "模拟传感器":
                sensor_id = 0
                self.data_handler = None
                mode = "模拟模式"
                print("✅ 切换到模拟传感器模式")
            elif sensor_text == "真实传感器":
                sensor_id = 1
                if DATA_HANDLER_AVAILABLE:
                    self.data_handler = SensorInterface()
                    mode = "真实传感器模式"
                    print("✅ 切换到真实传感器模式")
                else:
                    self.data_handler = None
                    mode = "模拟模式（真实传感器不可用）"
                    print("⚠️ 真实传感器不可用，使用模拟模式")
            else:
                sensor_id = 0
                self.data_handler = None
                mode = "未知模式"
            
            self.status_label.setText(f"状态: {mode}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # 更新信息显示
            info_text = f"传感器接口可用: {'是' if DATA_HANDLER_AVAILABLE else '否'}\n"
            info_text += f"当前模式: {mode}\n"
            info_text += f"数据处理器: {'已初始化' if self.data_handler else '未初始化'}"
            self.info_label.setText(info_text)
            
            # 启用测试按钮
            self.test_btn.setEnabled(True)
            
        except Exception as e:
            print(f"⚠️ 传感器模式切换失败: {e}")
            self.status_label.setText("状态: 切换失败")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def test_data_acquisition(self):
        """测试数据获取"""
        try:
            if self.data_handler:
                # 真实传感器数据
                self.data_handler.trigger()
                with self.data_handler.lock:
                    if not self.data_handler.value:
                        result = "真实传感器: 无数据"
                    else:
                        data = np.array(self.data_handler.value[-1])
                        result = f"真实传感器: 数据形状 {data.shape}, 总和 {np.sum(data):.4f}"
            else:
                # 模拟数据
                data = np.random.rand(64, 64) * 0.01
                center_x, center_y = 32, 32
                for i in range(64):
                    for j in range(64):
                        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                        if distance < 15:
                            weight = 2.0 + np.random.rand() * 3.0
                            data[i, j] += weight * np.exp(-distance / 8)
                
                result = f"模拟传感器: 数据形状 {data.shape}, 总和 {np.sum(data):.4f}"
            
            self.result_label.setText(f"测试结果: {result}")
            print(f"✅ 数据获取测试成功: {result}")
            
        except Exception as e:
            error_msg = f"数据获取测试失败: {e}"
            self.result_label.setText(f"测试结果: {error_msg}")
            print(f"❌ {error_msg}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 创建测试窗口
    window = SensorModeTest()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 