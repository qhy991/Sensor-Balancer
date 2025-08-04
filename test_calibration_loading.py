#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试校准参数加载和传递功能
"""

import sys
import os
import json
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# 导入校准加载器
from weight_measurement_tool import CalibrationDataLoader

class CalibrationTest(QWidget):
    """校准参数测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.calibration_loader = CalibrationDataLoader()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("校准参数测试")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # 测试按钮组
        test_group = QGroupBox("测试功能")
        test_layout = QVBoxLayout()
        
        # 创建测试校准文件按钮
        self.create_test_file_btn = QPushButton("创建测试校准文件")
        self.create_test_file_btn.clicked.connect(self.create_test_calibration_file)
        
        # 加载校准文件按钮
        self.load_calibration_btn = QPushButton("加载校准文件")
        self.load_calibration_btn.clicked.connect(self.load_calibration_file)
        
        # 显示校准信息按钮
        self.show_info_btn = QPushButton("显示校准信息")
        self.show_info_btn.clicked.connect(self.show_calibration_info)
        
        # 测试校准应用按钮
        self.test_apply_btn = QPushButton("测试校准应用")
        self.test_apply_btn.clicked.connect(self.test_calibration_application)
        
        test_layout.addWidget(self.create_test_file_btn)
        test_layout.addWidget(self.load_calibration_btn)
        test_layout.addWidget(self.show_info_btn)
        test_layout.addWidget(self.test_apply_btn)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 结果显示
        result_group = QGroupBox("测试结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #f8f9fa;")
        
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        self.setLayout(layout)
        
        # 初始化测试
        self.log("✅ 校准参数测试工具已启动")
        self.log("请先创建测试校准文件，然后加载并测试")
    
    def log(self, message):
        """添加日志信息"""
        self.result_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] {message}")
        print(message)
    
    def create_test_calibration_file(self):
        """创建测试校准文件"""
        try:
            # 创建测试校准数据
            test_calibration = {
                "calibration_params": {
                    "coefficient": 1730.6905,
                    "bias": 126.1741,
                    "zero_pressure": 0.05,
                    "is_zeroed": True
                },
                "calibration_map": {
                    "shape": [64, 64],
                    "type": "uniform",
                    "value": 1.0
                },
                "sensor_info": {
                    "type": "pressure_sensor",
                    "resolution": "64x64",
                    "unit": "N"
                },
                "measurement_settings": {
                    "update_frequency": 100,
                    "filter_enabled": True,
                    "auto_zero": False
                },
                "advanced_settings": {
                    "position_calibration": True,
                    "temperature_compensation": False,
                    "drift_correction": True
                },
                "metadata": {
                    "created_date": "2024-01-01 12:00:00",
                    "version": "1.0",
                    "description": "测试校准文件"
                }
            }
            
            # 保存到文件
            filename = "test_calibration_config.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_calibration, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ 已创建测试校准文件: {filename}")
            self.log(f"   系数: {test_calibration['calibration_params']['coefficient']}")
            self.log(f"   偏置: {test_calibration['calibration_params']['bias']}")
            self.log(f"   归零压力: {test_calibration['calibration_params']['zero_pressure']}")
            
        except Exception as e:
            self.log(f"❌ 创建测试校准文件失败: {e}")
    
    def load_calibration_file(self):
        """加载校准文件"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择校准文件", "", 
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if filename:
                if self.calibration_loader.load_calibration_data(filename):
                    self.log(f"✅ 成功加载校准文件: {filename}")
                    
                    # 显示校准信息
                    info = self.calibration_loader.get_calibration_info()
                    if info:
                        self.log(f"   系数: {info['coefficient']:.6f}")
                        self.log(f"   偏置: {info['bias']:.6f}")
                        self.log(f"   归零压力: {info['zero_pressure']:.6f}")
                        self.log(f"   已归零: {'是' if info['is_zeroed'] else '否'}")
                        if info.get('timestamp'):
                            self.log(f"   时间戳: {info['timestamp']}")
                        if info.get('description'):
                            self.log(f"   描述: {info['description']}")
                else:
                    self.log(f"❌ 加载校准文件失败: {filename}")
            else:
                self.log("⚠️ 未选择文件")
                
        except Exception as e:
            self.log(f"❌ 加载校准文件时出错: {e}")
    
    def show_calibration_info(self):
        """显示校准信息"""
        try:
            if not self.calibration_loader.calibration_data:
                self.log("⚠️ 没有加载的校准数据")
                return
            
            cal_data = self.calibration_loader.calibration_data
            self.log("📋 当前校准信息:")
            self.log(f"   文件: {self.calibration_loader.loaded_file}")
            self.log(f"   系数: {cal_data.get('coefficient', 'N/A')}")
            self.log(f"   偏置: {cal_data.get('bias', 'N/A')}")
            self.log(f"   归零压力: {cal_data.get('zero_pressure', 'N/A')}")
            self.log(f"   已归零: {cal_data.get('is_zeroed', 'N/A')}")
            self.log(f"   时间戳: {cal_data.get('timestamp', 'N/A')}")
            self.log(f"   描述: {cal_data.get('description', 'N/A')}")
            
            # 检查是否有校准映射
            if 'calibration_map' in cal_data and cal_data['calibration_map'] is not None:
                cal_map = cal_data['calibration_map']
                self.log(f"   校准映射形状: {cal_map.shape}")
                self.log(f"   校准映射类型: {type(cal_map)}")
                
                map_info = self.calibration_loader.get_calibration_map_info()
                if map_info:
                    self.log(f"   校准映射统计:")
                    self.log(f"     平均值: {map_info['mean']:.6f}")
                    self.log(f"     标准差: {map_info['std']:.6f}")
                    self.log(f"     最小值: {map_info['min']:.6f}")
                    self.log(f"     最大值: {map_info['max']:.6f}")
            else:
                self.log("   校准映射: 无")
                
        except Exception as e:
            self.log(f"❌ 显示校准信息时出错: {e}")
    
    def test_calibration_application(self):
        """测试校准应用"""
        try:
            if not self.calibration_loader.calibration_data:
                self.log("⚠️ 没有加载的校准数据，无法测试")
                return
            
            # 创建测试数据
            test_data = np.random.rand(64, 64) * 0.01
            center_x, center_y = 32, 32
            for i in range(64):
                for j in range(64):
                    distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if distance < 15:
                        weight = 2.0 + np.random.rand() * 3.0
                        test_data[i, j] += weight * np.exp(-distance / 8)
            
            self.log("🧪 测试校准应用:")
            self.log(f"   原始数据总和: {np.sum(test_data):.6f}")
            
            # 应用校准
            calibrated_data = self.calibration_loader.apply_calibration_map(test_data)
            
            if calibrated_data is not test_data:
                self.log(f"   校准后数据总和: {np.sum(calibrated_data):.6f}")
                self.log(f"   变化量: {np.sum(calibrated_data) - np.sum(test_data):.6f}")
                self.log("✅ 校准映射已应用")
            else:
                self.log("⚠️ 校准映射未生效（数据未改变）")
            
            # 测试重量计算
            cal_data = self.calibration_loader.calibration_data
            coefficient = cal_data.get('coefficient', 1.0)
            bias = cal_data.get('bias', 0.0)
            zero_pressure = cal_data.get('zero_pressure', 0.0)
            is_zeroed = cal_data.get('is_zeroed', False)
            
            total_pressure = np.sum(calibrated_data)
            
            if is_zeroed:
                weight = (total_pressure - zero_pressure) * coefficient
            else:
                weight = total_pressure * coefficient
            
            weight += bias
            
            self.log(f"   计算重量: {weight:.6f} g")
            self.log(f"   使用参数: 系数={coefficient}, 偏置={bias}, 归零压力={zero_pressure}")
            
        except Exception as e:
            self.log(f"❌ 测试校准应用时出错: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 创建测试窗口
    window = CalibrationTest()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 