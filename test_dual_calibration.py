#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试双重校准数据加载功能
- 传感器校准映射（.npy文件）
- 压力-质量转换参数（JSON文件）
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

class DualCalibrationTest(QWidget):
    """双重校准测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.calibration_loader = CalibrationDataLoader()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("双重校准测试")
        self.setGeometry(100, 100, 700, 600)
        
        layout = QVBoxLayout()
        
        # 测试按钮组
        test_group = QGroupBox("测试功能")
        test_layout = QVBoxLayout()
        
        # 加载传感器校准映射按钮
        self.load_sensor_cal_btn = QPushButton("加载传感器校准映射 (.npy)")
        self.load_sensor_cal_btn.clicked.connect(self.load_sensor_calibration)
        
        # 加载压力-质量转换参数按钮
        self.load_pressure_cal_btn = QPushButton("加载压力-质量转换参数 (.json)")
        self.load_pressure_cal_btn.clicked.connect(self.load_pressure_calibration)
        
        # 自动加载所有校准数据按钮
        self.auto_load_btn = QPushButton("自动加载所有校准数据")
        self.auto_load_btn.clicked.connect(self.auto_load_all_calibration)
        
        # 显示校准信息按钮
        self.show_info_btn = QPushButton("显示完整校准信息")
        self.show_info_btn.clicked.connect(self.show_calibration_info)
        
        # 测试校准应用按钮
        self.test_apply_btn = QPushButton("测试完整校准流程")
        self.test_apply_btn.clicked.connect(self.test_complete_calibration)
        
        test_layout.addWidget(self.load_sensor_cal_btn)
        test_layout.addWidget(self.load_pressure_cal_btn)
        test_layout.addWidget(self.auto_load_btn)
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
        self.log("✅ 双重校准测试工具已启动")
        self.log("请先加载传感器校准映射，然后加载压力-质量转换参数")
    
    def log(self, message):
        """添加日志信息"""
        self.result_text.append(f"[{QTime.currentTime().toString('HH:mm:ss')}] {message}")
        print(message)
    
    def load_sensor_calibration(self):
        """加载传感器校准映射"""
        try:
            # 指定传感器校准文件路径
            sensor_file = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\校正数据-200帧.npy"
            
            if os.path.exists(sensor_file):
                self.log(f"🔍 加载传感器校准映射: {sensor_file}")
                if self.calibration_loader.load_calibration_data(sensor_file):
                    self.log("✅ 传感器校准映射加载成功")
                    
                    # 显示传感器校准信息
                    cal_data = self.calibration_loader.calibration_data
                    if 'calibration_map' in cal_data:
                        cal_map = cal_data['calibration_map']
                        self.log(f"   校准映射形状: {cal_map.shape}")
                        self.log(f"   校准映射统计:")
                        self.log(f"     均值: {np.mean(cal_map):.6f}")
                        self.log(f"     标准差: {np.std(cal_map):.6f}")
                        self.log(f"     最小值: {np.min(cal_map):.6f}")
                        self.log(f"     最大值: {np.max(cal_map):.6f}")
                else:
                    self.log("❌ 传感器校准映射加载失败")
            else:
                self.log(f"❌ 传感器校准文件不存在: {sensor_file}")
                
        except Exception as e:
            self.log(f"❌ 加载传感器校准映射时出错: {e}")
    
    def load_pressure_calibration(self):
        """加载压力-质量转换参数"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择压力-质量转换参数文件", "", 
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if filename:
                self.log(f"🔍 加载压力-质量转换参数: {filename}")
                if self.calibration_loader.load_calibration_data(filename):
                    self.log("✅ 压力-质量转换参数加载成功")
                    
                    # 显示压力-质量转换参数信息
                    cal_data = self.calibration_loader.calibration_data
                    self.log(f"   压力-质量转换参数:")
                    self.log(f"     系数: {cal_data.get('coefficient', 'N/A')}")
                    self.log(f"     偏置: {cal_data.get('bias', 'N/A')}")
                    self.log(f"     归零压力: {cal_data.get('zero_pressure', 'N/A')}")
                    self.log(f"     已归零: {cal_data.get('is_zeroed', 'N/A')}")
                else:
                    self.log("❌ 压力-质量转换参数加载失败")
            else:
                self.log("⚠️ 未选择文件")
                
        except Exception as e:
            self.log(f"❌ 加载压力-质量转换参数时出错: {e}")
    
    def auto_load_all_calibration(self):
        """自动加载所有校准数据"""
        try:
            self.log("🔄 开始自动加载所有校准数据...")
            
            # 加载传感器校准映射
            sensor_file = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\校正数据-200帧.npy"
            if os.path.exists(sensor_file):
                self.log(f"🔍 自动加载传感器校准映射: {sensor_file}")
                self.calibration_loader.load_calibration_data(sensor_file)
            
            # 加载压力-质量转换参数
            pressure_files = [
                r"C:\Users\84672\Documents\Research\balance-sensor\position_calibration_data.json",
                "config/calibration_config.json",
                "../config/calibration_config.json"
            ]
            
            for file_path in pressure_files:
                if os.path.exists(file_path):
                    self.log(f"🔍 自动加载压力-质量转换参数: {file_path}")
                    if self.calibration_loader.load_calibration_data(file_path):
                        break
            
            self.log("✅ 自动加载完成")
            self.show_calibration_info()
            
        except Exception as e:
            self.log(f"❌ 自动加载校准数据时出错: {e}")
    
    def show_calibration_info(self):
        """显示完整校准信息"""
        try:
            if not self.calibration_loader.calibration_data:
                self.log("⚠️ 没有加载的校准数据")
                return
            
            cal_data = self.calibration_loader.calibration_data
            self.log("📋 完整校准信息:")
            
            # 传感器校准信息
            if cal_data.get('sensor_calibration_loaded'):
                self.log(f"   传感器校准: 已加载")
                self.log(f"   传感器校准文件: {cal_data.get('sensor_calibration_file', 'N/A')}")
                if 'calibration_map' in cal_data:
                    cal_map = cal_data['calibration_map']
                    self.log(f"   传感器校准映射形状: {cal_map.shape}")
                    self.log(f"   传感器校准映射统计: 均值={np.mean(cal_map):.6f}, 标准差={np.std(cal_map):.6f}")
            else:
                self.log(f"   传感器校准: 未加载")
            
            # 压力-质量转换信息
            if cal_data.get('pressure_calibration_loaded'):
                self.log(f"   压力-质量转换: 已加载")
                self.log(f"   压力-质量转换文件: {cal_data.get('pressure_calibration_file', 'N/A')}")
                self.log(f"   压力-质量转换系数: {cal_data.get('coefficient', 'N/A')}")
                self.log(f"   压力-质量转换偏置: {cal_data.get('bias', 'N/A')}")
                self.log(f"   归零压力: {cal_data.get('zero_pressure', 'N/A')}")
                self.log(f"   已归零: {cal_data.get('is_zeroed', 'N/A')}")
            else:
                self.log(f"   压力-质量转换: 未加载")
            
            # 其他信息
            if cal_data.get('timestamp'):
                self.log(f"   时间戳: {cal_data['timestamp']}")
            if cal_data.get('description'):
                self.log(f"   描述: {cal_data['description']}")
                
        except Exception as e:
            self.log(f"❌ 显示校准信息时出错: {e}")
    
    def test_complete_calibration(self):
        """测试完整校准流程"""
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
            
            self.log("🧪 测试完整校准流程:")
            self.log(f"   原始数据总和: {np.sum(test_data):.6f}")
            
            # 步骤1: 应用传感器校准映射
            calibrated_data = self.calibration_loader.apply_calibration_map(test_data)
            
            if calibrated_data is not test_data:
                self.log(f"   传感器校准后数据总和: {np.sum(calibrated_data):.6f}")
                self.log(f"   传感器校准变化量: {np.sum(calibrated_data) - np.sum(test_data):.6f}")
                self.log("✅ 传感器校准映射已应用")
            else:
                self.log("⚠️ 传感器校准映射未生效")
            
            # 步骤2: 应用压力-质量转换
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
            
            self.log(f"   最终计算重量: {weight:.6f} g")
            self.log(f"   使用的转换参数:")
            self.log(f"     系数: {coefficient}")
            self.log(f"     偏置: {bias}")
            self.log(f"     归零压力: {zero_pressure}")
            self.log(f"     已归零: {is_zeroed}")
            
        except Exception as e:
            self.log(f"❌ 测试完整校准流程时出错: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 创建测试窗口
    window = DualCalibrationTest()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 