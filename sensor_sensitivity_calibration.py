"""
传感器敏感性标定程序
使用不同质量的砝码对传感器进行敏感性标定
载入现有校准数据，计算压力总和，评估传感器敏感性
"""

import sys
import os
import numpy as np
import json
import csv
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QMessageBox, QVBoxLayout,
                            QGroupBox, QTextEdit, QFileDialog, QProgressBar, QTabWidget,
                            QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGridLayout, QSplitter, QDialog, QMainWindow, QApplication, QSizePolicy)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import random

# USB导入
try:
    from usb.core import USBError
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    print("⚠️ USB模块未找到，USB功能将不可用")

# PyQtGraph导入
try:
    import pyqtgraph as pg
    import pyqtgraph.exporters
    from pyqtgraph import ImageView, ColorMap, ColorBarItem
    PYQTGRAPH_AVAILABLE = True
    
    # 配置PyQtGraph
    pg.setConfigOption('background', 'w')  # 白色背景
    pg.setConfigOption('foreground', 'k')  # 黑色前景
    pg.setConfigOption('antialias', True)  # 抗锯齿
    pg.setConfigOption('useOpenGL', True)  # 使用OpenGL加速
    pg.setConfigOption('leftButtonPan', True)  # 左键平移
    
    print("✅ PyQtGraph模块导入成功")
except ImportError as e:
    print(f"⚠️ PyQtGraph未找到: {e}")
    PYQTGRAPH_AVAILABLE = False

# 导入数据处理器和USB驱动
try:
    from data_processing.data_handler import DataHandler
    from backends.usb_driver import LargeUsbSensorDriver
    DATA_HANDLER_AVAILABLE = True
    print("✅ 数据处理器模块导入成功")
except ImportError as e:
    print(f"⚠️ 数据处理器未找到: {e}")
    DATA_HANDLER_AVAILABLE = False

# 导入分离出的组件类
try:
    from SensitivityAnalysisWidget import SensitivityAnalysisWidget
    print("✅ SensitivityAnalysisWidget模块导入成功")
except ImportError as e:
    print(f"⚠️ SensitivityAnalysisWidget未找到: {e}")
    # 如果导入失败，定义一个空的占位类
    class SensitivityAnalysisWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setLayout(QVBoxLayout())
            label = QLabel("SensitivityAnalysisWidget模块未找到")
            self.layout().addWidget(label)

try:
    from PositionConsistencyWidget import PositionConsistencyWidget
    print("✅ PositionConsistencyWidget模块导入成功")
except ImportError as e:
    print(f"⚠️ PositionConsistencyWidget未找到: {e}")
    # 如果导入失败，定义一个空的占位类
    class PositionConsistencyWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setLayout(QVBoxLayout())
            label = QLabel("PositionConsistencyWidget模块未找到")
            self.layout().addWidget(label)

try:
    from LocalSensitivityWidget import LocalSensitivityWidget
    print("✅ LocalSensitivityWidget模块导入成功")
except ImportError as e:
    print(f"⚠️ LocalSensitivityWidget未找到: {e}")
    # 如果导入失败，定义完整的LocalSensitivityWidget类
    class LocalSensitivityWidget(QWidget):
        """局部传感器灵敏度检验组件"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            
            # 局部灵敏度检验相关属性
            self.predefined_regions = {}  # 存储预定义区域
            self.selected_region = None  # 当前选中的区域
            self.micro_positions = []  # 生成的微调位置
            self.sensitivity_data = {}  # 存储灵敏度数据
            self.current_position = None
            self.sensitivity_measurement_active = False
            self.measurement_count = 0
            self.current_frame = 0
            
            # 图表窗口引用，防止被垃圾回收
            self.current_sensitivity_plot_window = None
            self.current_sensitivity_main_window = None
            
            # 新增：引导窗口相关
            self.guide_window = None
            self.guide_plot = None
            self.current_position_index = 0
            self.guide_timer = QTimer()
            self.guide_timer.timeout.connect(self.update_guide_display)
            
            # 初始化UI
            self.init_ui()
            
            # 加载预定义区域
            self.load_predefined_regions()
            
            print("✅ 局部传感器灵敏度检验组件初始化完成")
        
        def load_predefined_regions(self):
            """加载9个预定义区域"""
            # 9个预定义区域，分布在传感器不同位置
            predefined_regions = [
                {"id": "center", "name": "中心区域", "x": 32, "y": 32, "description": "传感器中心区域"},
                {"id": "top_left", "name": "左上区域", "x": 16, "y": 16, "description": "左上角区域"},
                {"id": "top_right", "name": "右上区域", "x": 48, "y": 16, "description": "右上角区域"},
                {"id": "bottom_left", "name": "左下区域", "x": 16, "y": 48, "description": "左下角区域"},
                {"id": "bottom_right", "name": "右下区域", "x": 48, "y": 48, "description": "右下角区域"},
                {"id": "top_center", "name": "上中区域", "x": 32, "y": 16, "description": "上中区域"},
                {"id": "bottom_center", "name": "下中区域", "x": 32, "y": 48, "description": "下中区域"},
                {"id": "left_center", "name": "左中区域", "x": 16, "y": 32, "description": "左中区域"},
                {"id": "right_center", "name": "右中区域", "x": 48, "y": 32, "description": "右中区域"}
            ]
            
            for region in predefined_regions:
                self.predefined_regions[region["id"]] = {
                    "name": region["name"],
                    "x": region["x"],
                    "y": region["y"],
                    "description": region["description"]
                }
            
            # 更新UI显示
            self.update_region_table()
            self.update_region_selection()
            
            print(f"✅ 已加载 {len(predefined_regions)} 个预定义区域")
        
        def init_ui(self):
            """初始化UI"""
            layout = QVBoxLayout()
            
            # 预定义区域管理组
            region_group = QGroupBox("预定义区域管理")
            region_layout = QVBoxLayout()
            
            # 区域表格
            self.region_table = QTableWidget()
            self.region_table.setColumnCount(5)
            self.region_table.setHorizontalHeaderLabels(["区域ID", "名称", "X坐标", "Y坐标", "描述"])
            self.region_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.region_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.region_table.itemSelectionChanged.connect(self.on_region_selection_changed)
            
            region_layout.addWidget(self.region_table)
            region_group.setLayout(region_layout)
            
            # 局部灵敏度测试组
            sensitivity_group = QGroupBox("局部灵敏度测试")
            sensitivity_layout = QVBoxLayout()
            
            # 区域选择
            region_selection_layout = QHBoxLayout()
            self.region_selection_label = QLabel("选择测试区域:")
            self.region_combo = QComboBox()
            self.region_combo.setMinimumWidth(150)
            self.region_combo.currentTextChanged.connect(self.on_region_changed)
            
            region_selection_layout.addWidget(self.region_selection_label)
            region_selection_layout.addWidget(self.region_combo)
            region_selection_layout.addStretch()
            
            # 测试参数设置
            params_layout = QGridLayout()
            
            self.micro_variation_input = QSpinBox()
            self.micro_variation_input.setRange(1, 10)
            self.micro_variation_input.setValue(5)
            self.micro_variation_input.setSuffix(" 像素")
            self.micro_variation_input.setToolTip("微小变化范围（正负像素数）")
            
            self.micro_positions_count_input = QSpinBox()
            self.micro_positions_count_input.setRange(5, 20)
            self.micro_positions_count_input.setValue(10)
            self.micro_positions_count_input.setSuffix(" 个")
            self.micro_positions_count_input.setToolTip("生成的微调位置数量")
            
            self.frames_per_position_input = QSpinBox()
            self.frames_per_position_input.setRange(5, 100)
            self.frames_per_position_input.setValue(20)
            self.frames_per_position_input.setSuffix(" 帧")
            self.frames_per_position_input.setToolTip("每个位置采集的帧数")
            
            self.weight_id_input = QLineEdit()
            self.weight_id_input.setPlaceholderText("砝码ID (如: 1, 2, 3)")
            self.weight_id_input.setText("1")
            
            params_layout.addWidget(QLabel("微小变化范围:"), 0, 0)
            params_layout.addWidget(self.micro_variation_input, 0, 1)
            params_layout.addWidget(QLabel("微调位置数量:"), 0, 2)
            params_layout.addWidget(self.micro_positions_count_input, 0, 3)
            params_layout.addWidget(QLabel("每位置帧数:"), 1, 0)
            params_layout.addWidget(self.frames_per_position_input, 1, 1)
            params_layout.addWidget(QLabel("砝码ID:"), 1, 2)
            params_layout.addWidget(self.weight_id_input, 1, 3)
            
            # 测试控制
            control_layout = QHBoxLayout()
            
            self.generate_positions_btn = QPushButton("生成微调位置")
            self.generate_positions_btn.clicked.connect(self.generate_micro_positions)
            self.generate_positions_btn.setToolTip("根据选定区域生成微调位置")
            
            self.start_sensitivity_measurement_btn = QPushButton("开始灵敏度测试")
            self.start_sensitivity_measurement_btn.clicked.connect(self.start_sensitivity_measurement)
            self.start_sensitivity_measurement_btn.setEnabled(False)
            
            self.start_guided_measurement_btn = QPushButton("开始引导式测试")
            self.start_guided_measurement_btn.clicked.connect(self.start_guided_measurement)
            self.start_guided_measurement_btn.setEnabled(False)
            self.start_guided_measurement_btn.setToolTip("开始可视化引导的测试，会显示按压位置")
            
            self.stop_sensitivity_measurement_btn = QPushButton("停止灵敏度测试")
            self.stop_sensitivity_measurement_btn.clicked.connect(self.stop_sensitivity_measurement)
            self.stop_sensitivity_measurement_btn.setEnabled(False)
            
            self.sensitivity_progress_bar = QProgressBar()
            self.sensitivity_progress_bar.setVisible(False)
            
            # 测试状态显示
            self.sensitivity_status_label = QLabel("灵敏度测试状态: 未开始")
            self.sensitivity_status_label.setStyleSheet("color: gray; font-weight: bold;")
            
            control_layout.addWidget(self.generate_positions_btn)
            control_layout.addWidget(self.start_sensitivity_measurement_btn)
            control_layout.addWidget(self.start_guided_measurement_btn)
            control_layout.addWidget(self.stop_sensitivity_measurement_btn)
            control_layout.addWidget(self.sensitivity_progress_bar)
            control_layout.addWidget(self.sensitivity_status_label)
            control_layout.addStretch()
            
            # 手动控制按钮（用于引导式测试）
            manual_control_layout = QHBoxLayout()
            
            self.next_position_btn = QPushButton("下一个位置")
            self.next_position_btn.clicked.connect(self.next_position)
            self.next_position_btn.setEnabled(False)
            self.next_position_btn.setToolTip("手动切换到下一个测试位置")
            
            self.previous_position_btn = QPushButton("上一个位置")
            self.previous_position_btn.clicked.connect(self.previous_position)
            self.previous_position_btn.setEnabled(False)
            self.previous_position_btn.setToolTip("手动切换到上一个测试位置")
            
            self.record_data_btn = QPushButton("记录数据")
            self.record_data_btn.clicked.connect(self.record_position_data)
            self.record_data_btn.setEnabled(False)
            self.record_data_btn.setToolTip("手动记录当前位置的数据")
            
            manual_control_layout.addWidget(self.next_position_btn)
            manual_control_layout.addWidget(self.previous_position_btn)
            manual_control_layout.addWidget(self.record_data_btn)
            manual_control_layout.addStretch()
            
            # 组装灵敏度测试布局
            sensitivity_layout.addLayout(region_selection_layout)
            sensitivity_layout.addLayout(params_layout)
            sensitivity_layout.addLayout(control_layout)
            sensitivity_layout.addLayout(manual_control_layout)
            
            sensitivity_group.setLayout(sensitivity_layout)
            
            # 微调位置显示组
            positions_group = QGroupBox("微调位置")
            positions_layout = QVBoxLayout()
            
            self.positions_table = QTableWidget()
            self.positions_table.setColumnCount(4)
            self.positions_table.setHorizontalHeaderLabels(["位置ID", "X坐标", "Y坐标", "偏移量"])
            self.positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            positions_layout.addWidget(self.positions_table)
            positions_group.setLayout(positions_layout)
            
            # 灵敏度结果显示组
            results_group = QGroupBox("灵敏度分析结果")
            results_layout = QVBoxLayout()
            
            self.sensitivity_results_table = QTableWidget()
            self.sensitivity_results_table.setColumnCount(6)
            self.sensitivity_results_table.setHorizontalHeaderLabels([
                "位置ID", "X坐标", "Y坐标", "平均压力", "标准差", "变异系数"
            ])
            
            self.analyze_sensitivity_btn = QPushButton("分析局部灵敏度")
            self.analyze_sensitivity_btn.clicked.connect(self.analyze_local_sensitivity)
            self.analyze_sensitivity_btn.setEnabled(False)
            
            self.save_sensitivity_results_btn = QPushButton("保存灵敏度结果")
            self.save_sensitivity_results_btn.clicked.connect(self.save_sensitivity_results)
            self.save_sensitivity_results_btn.setEnabled(False)
            
            self.plot_sensitivity_btn = QPushButton("绘制灵敏度图表")
            self.plot_sensitivity_btn.clicked.connect(self.plot_sensitivity_analysis)
            self.plot_sensitivity_btn.setEnabled(False)
            
            results_buttons_layout = QHBoxLayout()
            results_buttons_layout.addWidget(self.analyze_sensitivity_btn)
            results_buttons_layout.addWidget(self.save_sensitivity_results_btn)
            results_buttons_layout.addWidget(self.plot_sensitivity_btn)
            results_buttons_layout.addStretch()
            
            results_layout.addWidget(self.sensitivity_results_table)
            results_layout.addLayout(results_buttons_layout)
            results_group.setLayout(results_layout)
            
            # 组装主布局
            layout.addWidget(region_group)
            layout.addWidget(sensitivity_group)
            layout.addWidget(positions_group)
            layout.addWidget(results_group)
            
            self.setLayout(layout)
            
            # 更新区域选择下拉框
            self.update_region_selection()
        
        def update_region_table(self):
            """更新区域表格"""
            self.region_table.setRowCount(len(self.predefined_regions))
            
            for row, (region_id, region_data) in enumerate(self.predefined_regions.items()):
                self.region_table.setItem(row, 0, QTableWidgetItem(region_id))
                self.region_table.setItem(row, 1, QTableWidgetItem(region_data['name']))
                self.region_table.setItem(row, 2, QTableWidgetItem(str(region_data['x'])))
                self.region_table.setItem(row, 3, QTableWidgetItem(str(region_data['y'])))
                self.region_table.setItem(row, 4, QTableWidgetItem(region_data['description']))
        
        def update_region_selection(self):
            """更新区域选择下拉框"""
            self.region_combo.clear()
            for region_id, region_data in self.predefined_regions.items():
                self.region_combo.addItem(f"{region_data['name']} ({region_id})", region_id)
        
        def on_region_selection_changed(self):
            """区域选择改变事件"""
            current_row = self.region_table.currentRow()
            if current_row >= 0:
                region_id = self.region_table.item(current_row, 0).text()
                self.selected_region = region_id
                # 更新下拉框选择
                index = self.region_combo.findData(region_id)
                if index >= 0:
                    self.region_combo.setCurrentIndex(index)
        
        def on_region_changed(self, text):
            """区域下拉框改变事件"""
            if text:
                region_id = self.region_combo.currentData()
                self.selected_region = region_id
                # 更新表格选择
                for row in range(self.region_table.rowCount()):
                    if self.region_table.item(row, 0).text() == region_id:
                        self.region_table.selectRow(row)
                        break
        
        def generate_micro_positions(self):
            """生成微调位置"""
            if not self.selected_region:
                QMessageBox.warning(self, "警告", "请先选择一个测试区域")
                return
            
            base_region = self.predefined_regions[self.selected_region]
            base_x, base_y = base_region['x'], base_region['y']
            variation = self.micro_variation_input.value()
            count = self.micro_positions_count_input.value()
            
            # 生成微调位置
            self.micro_positions = []
            used_positions = set()
            
            for i in range(count):
                attempts = 0
                while attempts < 100:  # 防止无限循环
                    # 在基准位置周围随机生成位置
                    offset_x = random.randint(-variation, variation)
                    offset_y = random.randint(-variation, variation)
                    
                    new_x = base_x + offset_x
                    new_y = base_y + offset_y
                    
                    # 确保位置在有效范围内
                    if 0 <= new_x <= 63 and 0 <= new_y <= 63:
                        position_key = (new_x, new_y)
                        if position_key not in used_positions:
                            used_positions.add(position_key)
                            self.micro_positions.append({
                                'id': f"pos_{i+1}",
                                'x': new_x,
                                'y': new_y,
                                'offset_x': offset_x,
                                'offset_y': offset_y,
                                'distance': np.sqrt(offset_x**2 + offset_y**2)
                            })
                            break
                    attempts += 1
            
            # 更新位置表格
            self.update_positions_table()
            
            # 启用测试按钮
            self.start_sensitivity_measurement_btn.setEnabled(True)
            self.start_guided_measurement_btn.setEnabled(True)
            
            print(f"✅ 已生成 {len(self.micro_positions)} 个微调位置")
            QMessageBox.information(self, "成功", f"已生成 {len(self.micro_positions)} 个微调位置\n\n现在可以选择：\n• '开始灵敏度测试' - 自动测试\n• '开始引导式测试' - 可视化引导测试")
        
        def update_positions_table(self):
            """更新位置表格"""
            self.positions_table.setRowCount(len(self.micro_positions))
            
            for row, position in enumerate(self.micro_positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(position['id']))
                self.positions_table.setItem(row, 1, QTableWidgetItem(str(position['x'])))
                self.positions_table.setItem(row, 2, QTableWidgetItem(str(position['y'])))
                offset_text = f"({position['offset_x']:+d}, {position['offset_y']:+d})"
                self.positions_table.setItem(row, 3, QTableWidgetItem(offset_text))
        
        def start_sensitivity_measurement(self):
            """开始灵敏度测试"""
            if not self.micro_positions:
                QMessageBox.warning(self, "警告", "请先生成微调位置")
                return
            
            weight_id = self.weight_id_input.text().strip()
            if not weight_id:
                QMessageBox.warning(self, "警告", "请输入砝码ID")
                return
            
            # 初始化测试数据
            self.sensitivity_data = {}
            self.current_position_index = 0
            self.current_frame = 0
            self.frames_per_position = self.frames_per_position_input.value()
            self.weight_id = weight_id
            
            # 更新UI状态
            self.sensitivity_measurement_active = True
            self.start_sensitivity_measurement_btn.setEnabled(False)
            self.stop_sensitivity_measurement_btn.setEnabled(True)
            self.generate_positions_btn.setEnabled(False)
            
            # 显示进度条
            total_frames = len(self.micro_positions) * self.frames_per_position
            self.sensitivity_progress_bar.setMaximum(total_frames)
            self.sensitivity_progress_bar.setValue(0)
            self.sensitivity_progress_bar.setVisible(True)
            
            # 更新状态
            self.sensitivity_status_label.setText(f"灵敏度测试状态: 正在测试位置 {self.current_position_index + 1}/{len(self.micro_positions)}")
            self.sensitivity_status_label.setStyleSheet("color: blue; font-weight: bold;")
            
            print(f"🚀 开始局部灵敏度测试")
            print(f"测试区域: {self.selected_region}")
            print(f"砝码ID: {weight_id}")
            print(f"位置数量: {len(self.micro_positions)}")
            print(f"每位置帧数: {self.frames_per_position}")
            
            # 开始数据采集
            self.start_data_collection()
        
        def start_data_collection(self):
            """开始数据采集"""
            if not self.sensitivity_measurement_active:
                return
            
            # 获取当前测试位置
            if self.current_position_index < len(self.micro_positions):
                current_pos = self.micro_positions[self.current_position_index]
                position_id = current_pos['id']
                
                # 初始化位置数据
                if position_id not in self.sensitivity_data:
                    self.sensitivity_data[position_id] = {
                        'x': current_pos['x'],
                        'y': current_pos['y'],
                        'offset_x': current_pos['offset_x'],
                        'offset_y': current_pos['offset_y'],
                        'distance': current_pos['distance'],
                        'pressure_sum': 0,
                        'frames': []
                    }
                
                # 模拟获取传感器数据（这里需要替换为实际的传感器数据获取）
                # 在实际应用中，这里应该调用传感器接口获取压力数据
                simulated_pressure = self.get_simulated_pressure_data(current_pos)
                
                # 记录数据
                self.sensitivity_data[position_id]['pressure_sum'] += simulated_pressure
                self.sensitivity_data[position_id]['frames'].append(simulated_pressure)
                
                self.current_frame += 1
                
                # 更新进度条
                self.sensitivity_progress_bar.setValue(self.current_frame)
                
                # 检查是否完成当前位置
                if self.current_frame % self.frames_per_position == 0:
                    self.current_position_index += 1
                    
                    # 更新状态
                    if self.current_position_index < len(self.micro_positions):
                        self.sensitivity_status_label.setText(
                            f"灵敏度测试状态: 正在测试位置 {self.current_position_index + 1}/{len(self.micro_positions)}"
                        )
                    else:
                        self.sensitivity_status_label.setText("灵敏度测试状态: 测试完成")
                        self.sensitivity_status_label.setStyleSheet("color: green; font-weight: bold;")
                        self.stop_sensitivity_measurement()
                        return
                
                # 继续下一帧
                QTimer.singleShot(100, self.start_data_collection)  # 100ms间隔
        
        def get_simulated_pressure_data(self, position):
            """获取模拟压力数据（实际应用中应替换为真实传感器数据）"""
            # 模拟压力数据，基于位置和随机噪声
            base_pressure = 1000  # 基础压力
            position_factor = 1.0 + (position['distance'] * 0.01)  # 位置影响因子
            noise = random.uniform(-50, 50)  # 随机噪声
            
            return base_pressure * position_factor + noise
        
        def stop_sensitivity_measurement(self):
            """停止灵敏度测试"""
            self.sensitivity_measurement_active = False
            self.start_sensitivity_measurement_btn.setEnabled(True)
            self.start_guided_measurement_btn.setEnabled(True)
            self.stop_sensitivity_measurement_btn.setEnabled(False)
            self.generate_positions_btn.setEnabled(True)
            self.sensitivity_progress_bar.setVisible(False)
            
            # 停止引导定时器
            self.guide_timer.stop()
            
            # 关闭引导窗口
            if self.guide_window:
                self.guide_window.close()
                self.guide_window = None
            
            # 禁用手动控制按钮
            self.next_position_btn.setEnabled(False)
            self.previous_position_btn.setEnabled(False)
            self.record_data_btn.setEnabled(False)
            
            # 启用分析按钮
            self.analyze_sensitivity_btn.setEnabled(True)
            self.save_sensitivity_results_btn.setEnabled(True)
            self.plot_sensitivity_btn.setEnabled(True)
            
            print(f"✅ 局部灵敏度测试完成")
            print(f"采集数据位置: {len(self.sensitivity_data)} 个")
        
        def analyze_local_sensitivity(self):
            """分析局部灵敏度"""
            if not self.sensitivity_data:
                QMessageBox.warning(self, "警告", "没有灵敏度测试数据")
                return
            
            print("\n🔍 开始局部灵敏度分析...")
            
            # 计算统计指标
            analysis_results = {}
            all_pressures = []
            
            for position_id, data in self.sensitivity_data.items():
                pressures = data['frames']
                avg_pressure = np.mean(pressures)
                std_pressure = np.std(pressures)
                cv_pressure = std_pressure / avg_pressure if avg_pressure > 0 else 0
                
                analysis_results[position_id] = {
                    'x': data['x'],
                    'y': data['y'],
                    'offset_x': data['offset_x'],
                    'offset_y': data['offset_y'],
                    'distance': data['distance'],
                    'avg_pressure': avg_pressure,
                    'std_pressure': std_pressure,
                    'cv_pressure': cv_pressure,
                    'pressure_sum': data['pressure_sum'],
                    'frames_count': len(pressures)
                }
                
                all_pressures.extend(pressures)
            
            # 计算整体统计
            overall_avg = np.mean(all_pressures)
            overall_std = np.std(all_pressures)
            overall_cv = overall_std / overall_avg if overall_avg > 0 else 0
            
            # 计算位置间变异系数
            position_avgs = [result['avg_pressure'] for result in analysis_results.values()]
            position_cv = np.std(position_avgs) / np.mean(position_avgs) if np.mean(position_avgs) > 0 else 0
            
            # 评估灵敏度等级
            if position_cv < 0.05:
                sensitivity_grade = "优秀"
            elif position_cv < 0.1:
                sensitivity_grade = "良好"
            elif position_cv < 0.2:
                sensitivity_grade = "一般"
            else:
                sensitivity_grade = "较差"
            
            # 保存分析结果
            self.sensitivity_analysis = {
                'results': analysis_results,
                'overall_stats': {
                    'avg_pressure': overall_avg,
                    'std_pressure': overall_std,
                    'cv_pressure': overall_cv,
                    'position_cv': position_cv,
                    'sensitivity_grade': sensitivity_grade
                },
                'test_info': {
                    'region_id': self.selected_region,
                    'weight_id': self.weight_id,
                    'positions_count': len(self.micro_positions),
                    'frames_per_position': self.frames_per_position,
                    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
                }
            }
            
            # 更新结果表格
            self.update_sensitivity_results_table(analysis_results)
            
            print(f"✅ 局部灵敏度分析完成")
            print(f"位置间变异系数: {position_cv:.3f} ({sensitivity_grade})")
            print(f"平均压力: {overall_avg:.2f} ± {overall_std:.2f}")
            
            QMessageBox.information(self, "分析完成", 
                                  f"局部灵敏度分析完成\n"
                                  f"位置间变异系数: {position_cv:.3f} ({sensitivity_grade})\n"
                                  f"平均压力: {overall_avg:.2f} ± {overall_std:.2f}")
        
        def update_sensitivity_results_table(self, results):
            """更新灵敏度结果表格"""
            self.sensitivity_results_table.setRowCount(len(results))
            
            for row, (position_id, data) in enumerate(results.items()):
                self.sensitivity_results_table.setItem(row, 0, QTableWidgetItem(position_id))
                self.sensitivity_results_table.setItem(row, 1, QTableWidgetItem(str(data['x'])))
                self.sensitivity_results_table.setItem(row, 2, QTableWidgetItem(str(data['y'])))
                self.sensitivity_results_table.setItem(row, 3, QTableWidgetItem(f"{data['avg_pressure']:.2f}"))
                self.sensitivity_results_table.setItem(row, 4, QTableWidgetItem(f"{data['std_pressure']:.2f}"))
                self.sensitivity_results_table.setItem(row, 5, QTableWidgetItem(f"{data['cv_pressure']:.3f}"))
        
        def save_sensitivity_results(self):
            """保存灵敏度结果"""
            if not hasattr(self, 'sensitivity_analysis'):
                QMessageBox.warning(self, "警告", "没有分析结果可保存")
                return
            
            # 选择保存目录
            output_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", "")
            if not output_dir:
                return
            
            try:
                # 生成时间戳
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # 保存JSON结果
                json_path = f"{output_dir}/local_sensitivity_analysis_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.sensitivity_analysis, f, indent=2, ensure_ascii=False)
                
                # 生成报告
                report_path = f"{output_dir}/local_sensitivity_report_{timestamp}.txt"
                self.generate_sensitivity_report(report_path)
                
                # 创建图表
                plot_path = f"{output_dir}/local_sensitivity_plots_{timestamp}.png"
                self.create_sensitivity_plots(plot_path)
                
                QMessageBox.information(self, "保存成功", 
                                      f"灵敏度结果已保存到:\n{output_dir}\n\n"
                                      f"文件包括:\n"
                                      f"• JSON结果: local_sensitivity_analysis_{timestamp}.json\n"
                                      f"• 分析报告: local_sensitivity_report_{timestamp}.txt\n"
                                      f"• 分析图表: local_sensitivity_plots_{timestamp}.png")
                
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存灵敏度结果时出错:\n{e}")
                print(f"❌ 保存灵敏度结果失败: {e}")
        
        def generate_sensitivity_report(self, output_path):
            """生成灵敏度分析报告"""
            print(f"\n📄 生成灵敏度分析报告...")
            
            report = []
            report.append("=" * 80)
            report.append("局部传感器灵敏度检验分析报告")
            report.append("=" * 80)
            report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"测试时间: {self.sensitivity_analysis['test_info']['timestamp']}")
            report.append("")
            
            # 测试信息
            test_info = self.sensitivity_analysis['test_info']
            report.append("📊 测试信息")
            report.append("-" * 60)
            report.append(f"测试区域: {test_info['region_id']}")
            report.append(f"砝码ID: {test_info['weight_id']}")
            report.append(f"位置数量: {test_info['positions_count']}")
            report.append(f"每位置帧数: {test_info['frames_per_position']}")
            report.append("")
            
            # 整体统计
            overall_stats = self.sensitivity_analysis['overall_stats']
            report.append("📊 整体统计")
            report.append("-" * 60)
            report.append(f"平均压力: {overall_stats['avg_pressure']:.2f}")
            report.append(f"标准差: {overall_stats['std_pressure']:.2f}")
            report.append(f"变异系数: {overall_stats['cv_pressure']:.3f}")
            report.append(f"位置间变异系数: {overall_stats['position_cv']:.3f}")
            report.append(f"灵敏度等级: {overall_stats['sensitivity_grade']}")
            report.append("")
            
            # 详细结果
            report.append("📊 详细结果")
            report.append("-" * 60)
            for position_id, result in self.sensitivity_analysis['results'].items():
                report.append(f"\n位置 {position_id}:")
                report.append(f"  坐标: ({result['x']}, {result['y']})")
                report.append(f"  偏移量: ({result['offset_x']:+d}, {result['offset_y']:+d})")
                report.append(f"  距离: {result['distance']:.2f}")
                report.append(f"  平均压力: {result['avg_pressure']:.2f}")
                report.append(f"  标准差: {result['std_pressure']:.2f}")
                report.append(f"  变异系数: {result['cv_pressure']:.3f}")
            
            # 总结和建议
            report.append("\n\n💡 总结和建议")
            report.append("-" * 60)
            
            position_cv = overall_stats['position_cv']
            if position_cv < 0.05:
                report.append("✅ 局部灵敏度优秀，传感器在微小位置变化时响应稳定")
            elif position_cv < 0.1:
                report.append("✅ 局部灵敏度良好，建议进一步优化")
            elif position_cv < 0.2:
                report.append("⚠️ 局部灵敏度一般，建议检查传感器校准")
            else:
                report.append("❌ 局部灵敏度较差，需要重新校准传感器")
            
            # 写入报告文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report))
            
            print(f"✅ 灵敏度分析报告已保存到: {output_path}")
            return report
        
        def create_sensitivity_plots(self, save_path=None):
            """创建灵敏度分析图表"""
            if not PYQTGRAPH_AVAILABLE:
                print("⚠️ PyQtGraph不可用，无法创建图表")
                return
            
            print("\n📊 创建灵敏度分析图表...")
            
            # 创建PyQtGraph窗口
            plot_window = pg.GraphicsLayoutWidget()
            plot_window.setWindowTitle('局部传感器灵敏度分析')
            plot_window.resize(1200, 800)
            
            # 保存窗口引用，防止被垃圾回收
            self.current_sensitivity_plot_window = plot_window
            
            # 创建2x2的子图布局
            # 压力分布图（左上）
            p1 = plot_window.addPlot(row=0, col=0)
            p1.setTitle('压力分布')
            p1.setLabel('left', '压力值')
            p1.setLabel('bottom', '位置ID')
            p1.showGrid(x=True, y=True, alpha=0.3)
            
            if hasattr(self, 'sensitivity_analysis'):
                results = self.sensitivity_analysis['results']
                position_ids = list(results.keys())
                avg_pressures = [results[pid]['avg_pressure'] for pid in position_ids]
                std_pressures = [results[pid]['std_pressure'] for pid in position_ids]
                
                # 创建误差棒图
                x_pos = np.arange(len(position_ids))
                error_bars = pg.ErrorBarItem(x=x_pos, y=avg_pressures, height=std_pressures)
                p1.addItem(error_bars)
                
                # 绘制散点图
                p1.plot(x_pos, avg_pressures, pen=None, symbol='o', symbolSize=8, 
                       symbolBrush=(0, 0, 255), symbolPen=(0, 0, 255))
                
                # 设置x轴标签
                ax = p1.getAxis('bottom')
                ax.setTicks([[(i, pid) for i, pid in enumerate(position_ids)]])
            
            # 变异系数图（右上）
            p2 = plot_window.addPlot(row=0, col=1)
            p2.setTitle('变异系数分布')
            p2.setLabel('left', '变异系数')
            p2.setLabel('bottom', '位置ID')
            p2.showGrid(x=True, y=True, alpha=0.3)
            
            if hasattr(self, 'sensitivity_analysis'):
                cv_pressures = [results[pid]['cv_pressure'] for pid in position_ids]
                
                # 绘制柱状图
                bars = pg.BarGraphItem(x=x_pos, height=cv_pressures, width=0.6, brush=(255, 0, 0))
                p2.addItem(bars)
                
                # 设置x轴标签
                ax = p2.getAxis('bottom')
                ax.setTicks([[(i, pid) for i, pid in enumerate(position_ids)]])
            
            # 位置分布图（左下）
            p3 = plot_window.addPlot(row=1, col=0)
            p3.setTitle('位置分布')
            p3.setLabel('left', 'Y坐标')
            p3.setLabel('bottom', 'X坐标')
            p3.showGrid(x=True, y=True, alpha=0.3)
            
            if hasattr(self, 'sensitivity_analysis'):
                x_coords = [results[pid]['x'] for pid in position_ids]
                y_coords = [results[pid]['y'] for pid in position_ids]
                
                # 绘制散点图，颜色表示压力大小
                scatter = pg.ScatterPlotItem(x=x_coords, y=y_coords, size=10, 
                                           brush=pg.mkBrush(0, 0, 255))
                p3.addItem(scatter)
                
                # 添加位置标签
                for i, pid in enumerate(position_ids):
                    text = pg.TextItem(text=pid, anchor=(0.5, 0))
                    text.setPos(x_coords[i], y_coords[i])
                    p3.addItem(text)
            
            # 距离-压力关系图（右下）
            p4 = plot_window.addPlot(row=1, col=1)
            p4.setTitle('距离-压力关系')
            p4.setLabel('left', '平均压力')
            p4.setLabel('bottom', '距离（像素）')
            p4.showGrid(x=True, y=True, alpha=0.3)
            
            if hasattr(self, 'sensitivity_analysis'):
                distances = [results[pid]['distance'] for pid in position_ids]
                
                # 绘制散点图
                p4.plot(distances, avg_pressures, pen=None, symbol='o', symbolSize=8, 
                       symbolBrush=(0, 255, 0), symbolPen=(0, 255, 0))
                
                # 添加趋势线
                if len(distances) > 1:
                    z = np.polyfit(distances, avg_pressures, 1)
                    p = np.poly1d(z)
                    p4.plot(distances, p(distances), pen=pg.mkPen((255, 0, 0), width=2))
            
            # 保存图表（如果需要）
            if save_path:
                try:
                    exporter = pg.exporters.ImageExporter(plot_window.scene())
                    exporter.export(save_path)
                    print(f"✅ 灵敏度分析图表已保存到: {save_path}")
                except Exception as e:
                    print(f"⚠️ 保存图表失败: {e}")
            
            # 显示图表窗口
            plot_window.show()
            
            # 添加保存按钮
            self.add_save_button_to_sensitivity_plot(plot_window)
            
            return plot_window
        
        def add_save_button_to_sensitivity_plot(self, plot_window):
            """在灵敏度图表窗口中添加保存按钮"""
            try:
                # 创建一个包含图表和按钮的主窗口
                main_window = QWidget()
                main_window.setWindowTitle("局部传感器灵敏度分析图表")
                main_window.resize(plot_window.width(), plot_window.height() + 60)
                
                # 保存主窗口引用，防止被垃圾回收
                self.current_sensitivity_main_window = main_window
                
                # 创建垂直布局
                layout = QVBoxLayout()
                
                # 添加图表窗口
                layout.addWidget(plot_window)
                
                # 创建保存按钮
                save_button = QPushButton("保存灵敏度图表")
                save_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 6px;
                        border: none;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #388e3c;
                    }
                """)
                
                # 连接按钮点击信号到保存函数
                save_button.clicked.connect(lambda: self.save_sensitivity_plot(plot_window))
                
                # 设置按钮大小
                save_button.setFixedHeight(40)
                
                # 添加按钮到布局
                layout.addWidget(save_button)
                
                # 设置主窗口布局
                main_window.setLayout(layout)
                
                # 显示主窗口
                main_window.show()
                
                print(f"✅ 保存按钮已添加到灵敏度图表窗口")
                
            except Exception as e:
                print(f"⚠️ 添加保存按钮失败: {e}")
                # 如果添加保存按钮失败，直接显示原始图表窗口
                plot_window.show()
        
        def save_sensitivity_plot(self, plot_window):
            """保存灵敏度图表"""
            try:
                filename, _ = QFileDialog.getSaveFileName(
                    self, "保存灵敏度图表", "", "PNG文件 (*.png);;JPEG文件 (*.jpg);;所有文件 (*)"
                )
                
                if filename:
                    # 使用PyQtGraph的保存功能
                    exporter = pg.exporters.ImageExporter(plot_window.scene())
                    exporter.export(filename)
                    QMessageBox.information(self, "成功", f"灵敏度图表已保存到:\n{filename}")
                    print(f"✅ 灵敏度图表已保存到: {filename}")
                else:
                    print(f"💡 用户取消了保存")
                    
            except Exception as e:
                print(f"⚠️ 保存灵敏度图表时出错: {e}")
                QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
        
        def plot_sensitivity_analysis(self):
            """绘制灵敏度分析图表"""
            if not hasattr(self, 'sensitivity_analysis'):
                QMessageBox.warning(self, "警告", "没有分析结果可绘制")
                return
            
            print("\n📊 绘制灵敏度分析图表...")
            try:
                plot_window = self.create_sensitivity_plots()
                if plot_window:
                    print("✅ 灵敏度分析图表已显示")
                    QMessageBox.information(self, "成功", "灵敏度分析图表已显示")
                else:
                    print("⚠️ 无法创建灵敏度分析图表")
                    QMessageBox.warning(self, "警告", "无法创建灵敏度分析图表")
            except Exception as e:
                print(f"❌ 绘制灵敏度分析图表时出错: {e}")
                QMessageBox.critical(self, "错误", f"绘制灵敏度分析图表时出错:\n{e}")
                import traceback
                traceback.print_exc()
        
        def create_guide_window(self):
            """创建引导窗口"""
            if not PYQTGRAPH_AVAILABLE:
                QMessageBox.warning(self, "警告", "PyQtGraph不可用，无法创建引导窗口")
                return None
            
            # 创建引导窗口
            self.guide_window = pg.GraphicsLayoutWidget()
            self.guide_window.setWindowTitle('局部灵敏度测试引导')
            self.guide_window.resize(800, 600)
            
            # 创建主图
            self.guide_plot = self.guide_window.addPlot()
            self.guide_plot.setTitle('按压位置引导')
            self.guide_plot.setLabel('left', 'Y坐标')
            self.guide_plot.setLabel('bottom', 'X坐标')
            self.guide_plot.showGrid(x=True, y=True, alpha=0.3)
            
            # 设置坐标轴范围
            self.guide_plot.setXRange(0, 63)
            self.guide_plot.setYRange(0, 63)
            
            # 设置Y轴向下 (0在顶部，63在底部)
            self.guide_plot.invertY(True)
            
            # 添加坐标轴刻度
            ax_x = self.guide_plot.getAxis('bottom')
            ax_y = self.guide_plot.getAxis('left')
            
            # 设置X轴刻度 (每8个传感器一个刻度)
            x_ticks = [(i, str(i)) for i in range(0, 64, 8)]
            ax_x.setTicks([x_ticks])
            
            # 设置Y轴刻度 (每8个传感器一个刻度)
            y_ticks = [(i, str(i)) for i in range(0, 64, 8)]
            ax_y.setTicks([y_ticks])
            
            # 创建传感器网格背景
            self.create_sensor_grid()
            
            return self.guide_window
        
        def create_sensor_grid(self):
            """创建传感器网格背景"""
            # 绘制64x64的传感器网格
            for i in range(64):
                # 垂直线
                line = pg.PlotDataItem(x=[i, i], y=[0, 63], pen=pg.mkPen((200, 200, 200), width=1))
                self.guide_plot.addItem(line)
                # 水平线
                line = pg.PlotDataItem(x=[0, 63], y=[i, i], pen=pg.mkPen((200, 200, 200), width=1))
                self.guide_plot.addItem(line)
        
        def show_guide_window(self):
            """显示引导窗口"""
            if not self.guide_window:
                self.create_guide_window()
            
            if self.guide_window:
                self.guide_window.show()
                self.update_guide_display()
                print("✅ 引导窗口已显示")
        
        def update_guide_display(self):
            """更新引导显示"""
            if not self.guide_window or not self.micro_positions:
                return
            
            # 清除之前的标记
            self.guide_plot.clear()
            self.create_sensor_grid()
            
            if self.current_position_index < len(self.micro_positions):
                current_pos = self.micro_positions[self.current_position_index]
                
                # 绘制所有位置（灰色小点）
                for i, pos in enumerate(self.micro_positions):
                    if i == self.current_position_index:
                        # 当前位置：红色大圆点
                        current_scatter = pg.ScatterPlotItem(
                            x=[pos['x']], y=[pos['y']], 
                            size=20, 
                            brush=pg.mkBrush(255, 0, 0),  # 红色
                            pen=pg.mkPen(255, 0, 0, width=2)
                        )
                        self.guide_plot.addItem(current_scatter)
                        
                        # 添加位置标签
                        text = pg.TextItem(
                            text=f"当前位置: {pos['id']}\n坐标: ({pos['x']}, {pos['y']})\n偏移: ({pos['offset_x']:+d}, {pos['offset_y']:+d})",
                            anchor=(0.5, 1),
                            color=(255, 0, 0)
                        )
                        text.setPos(pos['x'], pos['y'] - 5)
                        self.guide_plot.addItem(text)
                        
                        # 添加闪烁效果
                        if hasattr(self, 'blink_state'):
                            self.blink_state = not self.blink_state
                        else:
                            self.blink_state = True
                        
                        if self.blink_state:
                            # 添加闪烁圆圈
                            circle = pg.PlotDataItem(
                                x=[pos['x'] + 8*np.cos(np.linspace(0, 2*np.pi, 50))],
                                y=[pos['y'] + 8*np.sin(np.linspace(0, 2*np.pi, 50))],
                                pen=pg.mkPen(255, 255, 0, width=3)  # 黄色闪烁
                            )
                            self.guide_plot.addItem(circle)
                    else:
                        # 其他位置：灰色小点
                        other_scatter = pg.ScatterPlotItem(
                            x=[pos['x']], y=[pos['y']], 
                            size=8, 
                            brush=pg.mkBrush(150, 150, 150),  # 灰色
                            pen=pg.mkPen(150, 150, 150)
                        )
                        self.guide_plot.addItem(other_scatter)
                
                # 更新状态信息
                self.sensitivity_status_label.setText(
                    f"灵敏度测试状态: 请按压位置 {self.current_position_index + 1}/{len(self.micro_positions)} "
                    f"({current_pos['id']}) - 坐标({current_pos['x']}, {current_pos['y']})"
                )
                self.sensitivity_status_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                # 测试完成
                self.sensitivity_status_label.setText("灵敏度测试状态: 测试完成")
                self.sensitivity_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.guide_timer.stop()
        
        def start_guided_measurement(self):
            """开始引导式测量"""
            if not self.micro_positions:
                QMessageBox.warning(self, "警告", "请先生成微调位置")
                return
            
            weight_id = self.weight_id_input.text().strip()
            if not weight_id:
                QMessageBox.warning(self, "警告", "请输入砝码ID")
                return
            
            # 初始化测试数据
            self.sensitivity_data = {}
            self.current_position_index = 0
            self.current_frame = 0
            self.frames_per_position = self.frames_per_position_input.value()
            self.weight_id = weight_id
            
            # 更新UI状态
            self.sensitivity_measurement_active = True
            self.start_sensitivity_measurement_btn.setEnabled(False)
            self.start_guided_measurement_btn.setEnabled(False)
            self.stop_sensitivity_measurement_btn.setEnabled(True)
            self.generate_positions_btn.setEnabled(False)
            
            # 启用手动控制按钮
            self.next_position_btn.setEnabled(True)
            self.previous_position_btn.setEnabled(True)
            self.record_data_btn.setEnabled(True)
            
            # 显示进度条
            total_frames = len(self.micro_positions) * self.frames_per_position
            self.sensitivity_progress_bar.setMaximum(total_frames)
            self.sensitivity_progress_bar.setValue(0)
            self.sensitivity_progress_bar.setVisible(True)
            
            # 显示引导窗口
            self.show_guide_window()
            
            # 启动引导更新定时器
            self.guide_timer.start(500)  # 每500ms更新一次
            
            print(f"🚀 开始引导式局部灵敏度测试")
            print(f"测试区域: {self.selected_region}")
            print(f"砝码ID: {weight_id}")
            print(f"位置数量: {len(self.micro_positions)}")
            print(f"每位置帧数: {self.frames_per_position}")
            
            QMessageBox.information(self, "开始测试", 
                                  f"引导式测试已开始！\n\n"
                                  f"请按照引导窗口中的红色标记位置进行按压。\n"
                                  f"系统会自动检测按压并采集数据。\n\n"
                                  f"当前测试位置: {self.micro_positions[0]['id']}\n\n"
                                  f"操作说明：\n"
                                  f"• 按压指定位置后点击'记录数据'\n"
                                  f"• 或点击'下一个位置'自动记录并切换\n"
                                  f"• 可以点击'上一个位置'返回修改")
        
        def record_position_data(self):
            """记录当前位置的数据"""
            if not self.sensitivity_measurement_active or self.current_position_index >= len(self.micro_positions):
                return
            
            current_pos = self.micro_positions[self.current_position_index]
            position_id = current_pos['id']
            
            # 初始化位置数据
            if position_id not in self.sensitivity_data:
                self.sensitivity_data[position_id] = {
                    'x': current_pos['x'],
                    'y': current_pos['y'],
                    'offset_x': current_pos['offset_x'],
                    'offset_y': current_pos['offset_y'],
                    'distance': current_pos['distance'],
                    'pressure_sum': 0,
                    'frames': []
                }
            
            # 获取传感器数据（这里需要替换为实际的传感器数据获取）
            # 在实际应用中，这里应该调用传感器接口获取压力数据
            simulated_pressure = self.get_simulated_pressure_data(current_pos)
            
            # 记录数据
            self.sensitivity_data[position_id]['pressure_sum'] += simulated_pressure
            self.sensitivity_data[position_id]['frames'].append(simulated_pressure)
            
            self.current_frame += 1
            
            # 更新进度条
            self.sensitivity_progress_bar.setValue(self.current_frame)
            
            # 检查是否完成当前位置
            if self.current_frame % self.frames_per_position == 0:
                self.current_position_index += 1
                
                # 更新状态
                if self.current_position_index < len(self.micro_positions):
                    self.sensitivity_status_label.setText(
                        f"灵敏度测试状态: 正在测试位置 {self.current_position_index + 1}/{len(self.micro_positions)}"
                    )
                else:
                    self.sensitivity_status_label.setText("灵敏度测试状态: 测试完成")
                    self.sensitivity_status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.stop_sensitivity_measurement()
                    return
            
            # 继续下一帧
            QTimer.singleShot(100, self.start_data_collection)  # 100ms间隔
        
        def next_position(self):
            """手动切换到下一个位置"""
            if self.sensitivity_measurement_active and self.current_position_index < len(self.micro_positions):
                self.record_position_data()
        
        def previous_position(self):
            """手动切换到上一个位置"""
            if self.sensitivity_measurement_active and self.current_position_index > 0:
                self.current_position_index -= 1
                self.current_frame = max(0, self.current_frame - self.frames_per_position)
                self.sensitivity_progress_bar.setValue(self.current_frame)
                self.update_guide_display()

def save_pyqtgraph_plot_robust(plot_item, filename):
    """
    使用 pyqtgraph.exporters 来可靠地保存图表。
    这个函数确保在导出前所有内容都已渲染。

    参数:
        plot_item: 需要保存的图表对象 (例如 PlotWidget.getPlotItem())。
        filename (str): 保存的文件路径。
    """
    try:
        print(f"🚀 [Robust Save] 准备使用 ImageExporter 保存到: {filename}")
        
        # 1. 创建一个与图表项关联的导出器
        exporter = pg.exporters.ImageExporter(plot_item)

        # 2. (可选) 设置导出参数，例如宽度可以提高分辨率
        # exporter.parameters()['width'] = 1920
        
        # 3. 执行导出
        exporter.export(filename)
        
        print(f"✅ [Robust Save] 图表已成功保存。")
        return True
    except Exception as e:
        print(f"❌ [Robust Save] 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_pyqtgraph_plot(plot_widget, filename):
    """通用的PyQtGraph图表保存函数 - 改进版本"""
    try:
        print(f"🔍 开始保存图表到: {filename}")
        
        # 方法1: 尝试使用ImageExporter (最可靠的方法)
        try:
            if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                # 确定正确的plot_item
                if hasattr(plot_widget, 'scene'):
                    # 如果是GraphicsLayoutWidget，使用scene
                    exporter = pg.exporters.ImageExporter(plot_widget.scene())
                elif hasattr(plot_widget, 'plotItem'):
                    # 如果是PlotWidget，使用plotItem
                    exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
                elif hasattr(plot_widget, 'getPlotItem'):
                    # 如果是PlotWidget，使用getPlotItem()
                    exporter = pg.exporters.ImageExporter(plot_widget.getPlotItem())
                else:
                    # 直接使用plot_widget
                    exporter = pg.exporters.ImageExporter(plot_widget)
                
                # 强制更新场景
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                
                # 执行导出
                exporter.export(filename)
                print(f"✅ 使用ImageExporter保存图表成功: {filename}")
                return True
        except Exception as e:
            print(f"⚠️ ImageExporter保存失败: {e}")
        
        # 方法2: 尝试使用grab方法截图
        try:
            if hasattr(plot_widget, 'grab'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                pixmap = plot_widget.grab()
                if pixmap.save(filename):
                    print(f"✅ 使用grab方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ grab方法保存失败: {e}")
        
        # 方法3: 尝试使用QWidget的render方法
        try:
            if hasattr(plot_widget, 'render'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                pixmap = QPixmap(plot_widget.size())
                plot_widget.render(pixmap)
                if pixmap.save(filename):
                    print(f"✅ 使用render方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ render方法保存失败: {e}")
        
        # 方法4: 尝试使用QScreen截图
        try:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen and hasattr(plot_widget, 'winId'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                pixmap = screen.grabWindow(plot_widget.winId())
                if pixmap.save(filename):
                    print(f"✅ 使用屏幕截图方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ 屏幕截图方法保存失败: {e}")
        
        print(f"❌ 所有保存方法都失败了")
        return False
        
    except Exception as e:
        print(f"❌ 保存图表时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

class CalibrationDataLoader:
    """校准数据加载器"""
    
    def __init__(self):
        self.calibration_map = None
        self.reference_data = None
        self.loaded_file = None
        
    def load_calibration_data(self, filepath):
        """加载校准数据"""
        try:
            if filepath.endswith('.json'):
                return self.load_json_calibration(filepath)
            elif filepath.endswith('.npy'):
                return self.load_numpy_calibration(filepath)
            elif filepath.endswith('.csv'):
                return self.load_csv_calibration(filepath)
            else:
                raise ValueError("不支持的文件格式")
        except Exception as e:
            print(f"⚠️ 加载校准数据失败: {e}")
            return False
    
    def load_json_calibration(self, filepath):
        """加载JSON格式的校准数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'calibration_map' in data:
                # 新格式：包含校准映射
                self.calibration_map = np.array(data['calibration_map'])
                self.reference_data = np.array(data.get('reference_data', []))
            elif 'consistency_data' in data:
                # 一致性数据格式
                consistency_data = data['consistency_data']
                max_x = max(int(k.split(',')[0]) for k in consistency_data.keys())
                max_y = max(int(k.split(',')[1]) for k in consistency_data.keys())
                shape = (max_x + 1, max_y + 1)
                
                self.calibration_map = np.zeros(shape)
                for key, value in consistency_data.items():
                    x, y = map(int, key.split(','))
                    self.calibration_map[x, y] = value
            else:
                raise ValueError("无效的JSON校准数据格式")
            
            self.loaded_file = filepath
            print(f"✅ 成功加载JSON校准数据: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 加载JSON校准数据失败: {e}")
            return False
    
    def load_numpy_calibration(self, filepath):
        """加载NumPy格式的校准数据"""
        try:
            data = np.load(filepath, allow_pickle=True)
            
            if isinstance(data, np.ndarray):
                self.calibration_map = data
            elif isinstance(data, dict):
                self.calibration_map = data['calibration_map']
                self.reference_data = data.get('reference_data', None)
            else:
                raise ValueError("无效的NumPy校准数据格式")
            
            self.loaded_file = filepath
            print(f"✅ 成功加载NumPy校准数据: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 加载NumPy校准数据失败: {e}")
            return False
    
    def load_csv_calibration(self, filepath):
        """加载CSV格式的校准数据"""
        try:
            data = np.loadtxt(filepath, delimiter=',')
            self.calibration_map = data
            self.loaded_file = filepath
            print(f"✅ 成功加载CSV校准数据: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 加载CSV校准数据失败: {e}")
            return False
    
    def get_calibration_info(self):
        """获取校准数据信息"""
        if self.calibration_map is None:
            return None
        
        return {
            'shape': self.calibration_map.shape,
            'mean': np.mean(self.calibration_map),
            'std': np.std(self.calibration_map),
            'min': np.min(self.calibration_map),
            'max': np.max(self.calibration_map),
            'cv': np.std(self.calibration_map) / np.mean(self.calibration_map) if np.mean(self.calibration_map) > 0 else 0,
            'loaded_file': self.loaded_file
        }

class WeightCalibration:
    """砝码校准类"""
    
    def __init__(self):
        self.weights = {}  # 存储砝码信息 {weight_id: {mass, unit, force}}
        self.measurements = {}  # 存储测量数据 {weight_id: [measurements]}
        self.calibration_results = {}  # 存储校准结果
        self.baseline_data = []  # 存储基线数据（无负载时的噪声）
        self.baseline_corrected = False  # 是否已进行基线校正
        
    def add_weight(self, weight_id, mass, unit='g'):
        """添加砝码"""
        # 单位转换
        if unit.lower() == 'g':
            force = mass * 0.0098  # 转换为牛顿
        elif unit.lower() == 'kg':
            force = mass * 9.8
        elif unit.lower() == 'n':
            force = mass
        else:
            force = mass * 0.0098  # 默认按克处理
        
        self.weights[weight_id] = {
            'mass': mass,
            'unit': unit,
            'force': force
        }
        self.measurements[weight_id] = []
        print(f"✅ 添加砝码: {weight_id}, 质量: {mass}{unit}, 力: {force:.4f}N")
    
    def record_baseline(self, pressure_data):
        """记录基线数据"""
        total_pressure = np.sum(pressure_data)
        mean_pressure = np.mean(pressure_data)
        max_pressure = np.max(pressure_data)
        
        self.baseline_data.append({
            'timestamp': datetime.now(),
            'total_pressure': total_pressure,
            'mean_pressure': mean_pressure,
            'max_pressure': max_pressure,
            'raw_data': pressure_data.copy()
        })
        
        print(f"📊 记录基线数据: 总压力={total_pressure:.6f}, 平均压力={mean_pressure:.6f}")
    
    def get_baseline_stats(self):
        """获取基线统计信息"""
        if not self.baseline_data:
            return None
        
        total_pressures = [d['total_pressure'] for d in self.baseline_data]
        mean_pressures = [d['mean_pressure'] for d in self.baseline_data]
        max_pressures = [d['max_pressure'] for d in self.baseline_data]
        
        return {
            'count': len(self.baseline_data),
            'avg_total_pressure': np.mean(total_pressures),
            'std_total_pressure': np.std(total_pressures),
            'avg_mean_pressure': np.mean(mean_pressures),
            'std_mean_pressure': np.std(mean_pressures),
            'avg_max_pressure': np.mean(max_pressures),
            'std_max_pressure': np.std(max_pressures),
            'cv_total': np.std(total_pressures) / np.mean(total_pressures) if np.mean(total_pressures) > 0 else 0
        }
    
    def clear_baseline(self):
        """清空基线数据"""
        self.baseline_data.clear()
        self.baseline_corrected = False
        print("🗑️ 基线数据已清空")
    
    def record_measurement(self, weight_id, pressure_data):
        """记录测量数据（支持基线校正）"""
        if weight_id not in self.weights:
            print(f"❌ 砝码 {weight_id} 不存在")
            return
        
        total_pressure = np.sum(pressure_data)
        mean_pressure = np.mean(pressure_data)
        max_pressure = np.max(pressure_data)
        
        # 基线校正
        corrected_total = total_pressure
        corrected_mean = mean_pressure
        corrected_max = max_pressure
        
        if self.baseline_data:
            baseline_stats = self.get_baseline_stats()
            corrected_total = total_pressure - baseline_stats['avg_total_pressure']
            corrected_mean = mean_pressure - baseline_stats['avg_mean_pressure']
            corrected_max = max_pressure - baseline_stats['avg_max_pressure']
            self.baseline_corrected = True
            
            # 添加调试信息
            print(f"🔍 基线校正: 原始={total_pressure:.6f}, 基线={baseline_stats['avg_total_pressure']:.6f}, 校正后={corrected_total:.6f}")
        else:
            print(f"⚠️ 无基线数据，跳过校正")
        
        measurement = {
            'timestamp': datetime.now(),
            'total_pressure': total_pressure,
            'mean_pressure': mean_pressure,
            'max_pressure': max_pressure,
            'corrected_total_pressure': corrected_total,
            'corrected_mean_pressure': corrected_mean,
            'corrected_max_pressure': corrected_max,
            'raw_data': pressure_data.copy()
        }
        
        self.measurements[weight_id].append(measurement)
        
        print(f"📊 记录测量: 砝码={weight_id}, 原始总压力={total_pressure:.6f}, 校正后总压力={corrected_total:.6f}")
    
    def calculate_sensitivity(self):
        """计算敏感性（支持基线校正）"""
        if not self.measurements:
            print("❌ 没有测量数据")
            return {}
        
        results = {}
        
        for weight_id, measurements in self.measurements.items():
            if not measurements:
                continue
            
            weight_info = self.weights[weight_id]
            force = weight_info['force']
            
            # 使用校正后的数据计算敏感性
            if self.baseline_corrected:
                total_pressures = [m['corrected_total_pressure'] for m in measurements]
                mean_pressures = [m['corrected_mean_pressure'] for m in measurements]
                max_pressures = [m['corrected_max_pressure'] for m in measurements]
            else:
                total_pressures = [m['total_pressure'] for m in measurements]
                mean_pressures = [m['mean_pressure'] for m in measurements]
                max_pressures = [m['max_pressure'] for m in measurements]
            
            # 计算统计信息
            avg_total_pressure = np.mean(total_pressures)
            std_total_pressure = np.std(total_pressures)
            avg_mean_pressure = np.mean(mean_pressures)
            std_mean_pressure = np.std(mean_pressures)
            avg_max_pressure = np.mean(max_pressures)
            std_max_pressure = np.std(max_pressures)
            
            # 计算敏感性
            sensitivity_total = avg_total_pressure / force if force > 0 else 0
            sensitivity_mean = avg_mean_pressure / force if force > 0 else 0
            sensitivity_max = avg_max_pressure / force if force > 0 else 0
            
            # 计算变异系数
            cv = std_total_pressure / avg_total_pressure if avg_total_pressure > 0 else 0
            
            results[weight_id] = {
                'weight_info': weight_info,
                'measurement_count': len(measurements),
                'avg_total_pressure': avg_total_pressure,
                'std_total_pressure': std_total_pressure,
                'avg_mean_pressure': avg_mean_pressure,
                'std_mean_pressure': std_mean_pressure,
                'avg_max_pressure': avg_max_pressure,
                'std_max_pressure': std_max_pressure,
                'sensitivity_total': sensitivity_total,
                'sensitivity_mean': sensitivity_mean,
                'sensitivity_max': sensitivity_max,
                'cv': cv,
                'baseline_corrected': self.baseline_corrected
            }
        
        self.calibration_results = results
        return results
    
    def get_overall_sensitivity(self):
        """获取整体敏感性"""
        if not self.calibration_results:
            return None
        
        # 计算所有砝码的平均敏感性
        sensitivities_total = [r['sensitivity_total'] for r in self.calibration_results.values()]
        sensitivities_mean = [r['sensitivity_mean'] for r in self.calibration_results.values()]
        sensitivities_max = [r['sensitivity_max'] for r in self.calibration_results.values()]
        
        # 计算统计信息
        avg_sensitivity_total = np.mean(sensitivities_total)
        std_sensitivity_total = np.std(sensitivities_total)
        cv_sensitivity_total = std_sensitivity_total / avg_sensitivity_total if avg_sensitivity_total > 0 else 0
        
        # 计算测量点数量和总测量次数
        measurement_points = len(self.calibration_results)
        total_measurements = sum(r['measurement_count'] for r in self.calibration_results.values())
        
        return {
            'avg_sensitivity_total': avg_sensitivity_total,
            'avg_sensitivity_mean': np.mean(sensitivities_mean),
            'avg_sensitivity_max': np.mean(sensitivities_max),
            'std_sensitivity_total': std_sensitivity_total,
            'std_sensitivity_mean': np.std(sensitivities_mean),
            'std_sensitivity_max': np.std(sensitivities_max),
            'cv_sensitivity_total': cv_sensitivity_total,
            'measurement_points': measurement_points,
            'total_measurements': total_measurements
        }

class SensitivityCalibrationWidget(QWidget):
    """敏感性标定组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化校准数据加载器
        self.calibration_loader = CalibrationDataLoader()
        
        # 初始化砝码校准
        self.weight_calibration = WeightCalibration()
        
        # 测量相关属性
        self.position_measurement_active = False
        self.current_weight_id = None
        self.measurement_count = 0
        self.current_measurement = 0
        
        # 初始化UI
        self.init_ui()
        
        # 加载默认砝码
        self.load_default_weights()
        
        print("✅ 敏感性标定组件初始化完成")
    
    def load_default_weights(self):
        """加载默认砝码"""
        default_weights = [
            {"id": "1", "mass": 50.0, "unit": "g"},
            {"id": "2", "mass": 100.0, "unit": "g"},
            {"id": "3", "mass": 150.0, "unit": "g"},
            {"id": "4", "mass": 500.0, "unit": "g"},
            {"id": "5", "mass": 550.0, "unit": "g"},
            {"id": "6", "mass": 600.0, "unit": "g"},
            {"id": "7", "mass": 650.0, "unit": "g"}
        ]
        
        for weight in default_weights:
            self.weight_calibration.add_weight(
                weight["id"], 
                weight["mass"], 
                weight["unit"]
            )
        
        # 更新UI显示
        self.update_weight_table()
        self.update_weight_selection()
        
        print(f"✅ 已加载 {len(default_weights)} 个默认砝码")
        print("默认砝码: 50g, 100g, 150g, 500g, 550g, 600g, 650g")
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 校准数据加载组
        calibration_group = QGroupBox("校准数据加载")
        calibration_layout = QHBoxLayout()
        
        self.load_calibration_btn = QPushButton("加载校准数据")
        self.load_calibration_btn.clicked.connect(self.load_calibration_data)
        
        self.calibration_info_label = QLabel("校准数据: 未加载")
        self.calibration_info_label.setStyleSheet("color: red; font-weight: bold;")
        
        calibration_layout.addWidget(self.load_calibration_btn)
        calibration_layout.addWidget(self.calibration_info_label)
        calibration_layout.addStretch()
        
        calibration_group.setLayout(calibration_layout)
        
        # 砝码管理组
        weight_group = QGroupBox("砝码管理")
        weight_layout = QGridLayout()
        
        self.weight_id_input = QLineEdit()
        self.weight_id_input.setPlaceholderText("砝码ID (如: W1, W2)")
        
        self.weight_mass_input = QDoubleSpinBox()
        self.weight_mass_input.setRange(0.1, 10000)
        self.weight_mass_input.setValue(100.0)
        self.weight_mass_input.setSuffix(" g")
        
        self.weight_unit_combo = QComboBox()
        self.weight_unit_combo.addItems(["g", "kg", "N"])
        self.weight_unit_combo.setCurrentText("g")
        
        self.add_weight_btn = QPushButton("添加砝码")
        self.add_weight_btn.clicked.connect(self.add_weight)
        
        # 基线校正控制
        baseline_group = QGroupBox("基线校正")
        baseline_layout = QVBoxLayout()
        
        baseline_info_layout = QHBoxLayout()
        self.baseline_status_label = QLabel("基线状态: 未记录")
        self.baseline_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.baseline_count_label = QLabel("记录次数: 0")
        
        baseline_info_layout.addWidget(self.baseline_status_label)
        baseline_info_layout.addWidget(self.baseline_count_label)
        baseline_info_layout.addStretch()
        
        baseline_control_layout = QHBoxLayout()
        self.record_baseline_btn = QPushButton("记录基线")
        self.record_baseline_btn.clicked.connect(self.record_baseline)
        self.record_baseline_btn.setToolTip("记录无负载时的传感器噪声数据")
        
        self.clear_baseline_btn = QPushButton("清空基线")
        self.clear_baseline_btn.clicked.connect(self.clear_baseline)
        self.clear_baseline_btn.setToolTip("清空所有基线数据")
        
        self.show_baseline_btn = QPushButton("显示基线")
        self.show_baseline_btn.clicked.connect(self.show_baseline_info)
        self.show_baseline_btn.setToolTip("显示基线统计信息")
        
        baseline_control_layout.addWidget(self.record_baseline_btn)
        baseline_control_layout.addWidget(self.clear_baseline_btn)
        baseline_control_layout.addWidget(self.show_baseline_btn)
        baseline_control_layout.addStretch()
        
        baseline_layout.addLayout(baseline_info_layout)
        baseline_layout.addLayout(baseline_control_layout)
        baseline_group.setLayout(baseline_layout)
        
        # 砝码表格
        self.weight_table = QTableWidget()
        self.weight_table.setColumnCount(4)
        self.weight_table.setHorizontalHeaderLabels(["砝码ID", "质量", "单位", "力(N)"])
        self.weight_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.weight_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 砝码选择
        weight_selection_layout = QHBoxLayout()
        self.weight_selection_label = QLabel("选择砝码:")
        self.weight_combo = QComboBox()
        self.weight_combo.setMinimumWidth(150)
        
        weight_selection_layout.addWidget(self.weight_selection_label)
        weight_selection_layout.addWidget(self.weight_combo)
        weight_selection_layout.addStretch()
        
        # 测量控制
        measurement_group = QGroupBox("测量控制")
        measurement_layout = QGridLayout()
        
        self.measurement_count_input = QSpinBox()
        self.measurement_count_input.setRange(1, 1000)
        self.measurement_count_input.setValue(10)
        
        self.start_measurement_btn = QPushButton("开始测量")
        self.start_measurement_btn.clicked.connect(self.start_measurement)
        
        self.stop_measurement_btn = QPushButton("停止测量")
        self.stop_measurement_btn.clicked.connect(self.stop_measurement)
        self.stop_measurement_btn.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 测量状态显示
        self.measurement_status_label = QLabel("测量状态: 未开始")
        self.measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 组装砝码管理布局
        weight_layout.addWidget(QLabel("砝码ID:"), 0, 0)
        weight_layout.addWidget(self.weight_id_input, 0, 1)
        weight_layout.addWidget(QLabel("质量:"), 0, 2)
        weight_layout.addWidget(self.weight_mass_input, 0, 3)
        weight_layout.addWidget(self.weight_unit_combo, 0, 4)
        weight_layout.addWidget(self.add_weight_btn, 0, 5)
        
        # 重置和自定义默认砝码按钮
        self.reset_default_btn = QPushButton("重置默认砝码")
        self.reset_default_btn.clicked.connect(self.reset_default_weights)
        self.reset_default_btn.setToolTip("清空所有砝码并重新加载默认的7个砝码")
        
        self.custom_default_btn = QPushButton("自定义默认砝码")
        self.custom_default_btn.clicked.connect(self.customize_default_weights)
        self.custom_default_btn.setToolTip("自定义默认砝码列表")
        
        weight_layout.addWidget(self.reset_default_btn, 1, 0, 1, 3)
        weight_layout.addWidget(self.custom_default_btn, 1, 3, 1, 3)
        
        weight_group.setLayout(weight_layout)
        
        # 组装测量控制布局
        measurement_layout.addWidget(QLabel("测量次数:"), 0, 0)
        measurement_layout.addWidget(self.measurement_count_input, 0, 1)
        measurement_layout.addWidget(self.start_measurement_btn, 0, 2)
        measurement_layout.addWidget(self.stop_measurement_btn, 0, 3)
        measurement_layout.addWidget(self.progress_bar, 1, 0, 1, 4)
        measurement_layout.addWidget(self.measurement_status_label, 2, 0, 1, 4)
        
        measurement_group.setLayout(measurement_layout)
        
        # 结果显示组
        results_group = QGroupBox("标定结果")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "砝码ID", "质量(g)", "测量次数", "平均总压力", "标准差", 
            "敏感性(总)", "敏感性(平均)", "变异系数"
        ])
        
        self.calculate_sensitivity_btn = QPushButton("计算敏感性")
        self.calculate_sensitivity_btn.clicked.connect(self.calculate_sensitivity)
        
        self.save_results_btn = QPushButton("保存结果")
        self.save_results_btn.clicked.connect(self.save_results)
        
        results_layout.addWidget(self.results_table)
        
        results_buttons_layout = QHBoxLayout()
        results_buttons_layout.addWidget(self.calculate_sensitivity_btn)
        results_buttons_layout.addWidget(self.save_results_btn)
        results_buttons_layout.addStretch()
        
        results_layout.addLayout(results_buttons_layout)
        results_group.setLayout(results_layout)
        
        # 组装布局
        layout.addWidget(calibration_group)
        layout.addWidget(weight_group)
        layout.addWidget(baseline_group)  # 添加基线校正组
        layout.addWidget(self.weight_table)
        layout.addLayout(weight_selection_layout)
        layout.addWidget(measurement_group)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
        
        # 更新砝码选择下拉框
        self.update_weight_selection()
    
    def load_calibration_data(self):
        """加载校准数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择校准数据文件", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
            "所有支持格式 (*.json *.npy *.csv);;JSON文件 (*.json);;NumPy文件 (*.npy);;CSV文件 (*.csv)"
        )
        
        if filename:
            try:
                success = self.calibration_loader.load_calibration_data(filename)
                if success:
                    # 更新状态显示
                    info = self.calibration_loader.get_calibration_info()
                    self.calibration_info_label.setText(f"已加载: {info['loaded_file']} | 形状: {info['shape']} | 均值: {info['mean']:.4f}")
                    self.calibration_info_label.setStyleSheet("color: green; font-weight: bold;")
                    
                    # 通知主界面更新校准状态
                    parent = self.parent()
                    main_interface = None
                    
                    # 通过标签页控件找到主界面
                    if parent and hasattr(parent, 'parent'):
                        tab_widget = parent.parent()
                        if tab_widget and hasattr(tab_widget, 'parent'):
                            main_interface = tab_widget.parent()
                    
                    if main_interface and hasattr(main_interface, 'set_calibration_data'):
                        main_interface.set_calibration_data(self.calibration_loader.calibration_map)
                        print(f"✅ 已通知主界面更新校准状态")
                    else:
                        print(f"⚠️ 无法通知主界面更新校准状态")
                    
                    QMessageBox.information(self, "成功", f"校准数据加载成功\n文件: {info['loaded_file']}\n形状: {info['shape']}\n均值: {info['mean']:.4f}")
                else:
                    QMessageBox.critical(self, "错误", "校准数据加载失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载校准数据时出错: {e}")
                print(f"❌ 加载校准数据失败: {e}")
                import traceback
                traceback.print_exc()
    
    def add_weight(self):
        """添加砝码"""
        weight_id = self.weight_id_input.text().strip()
        mass = self.weight_mass_input.value()
        unit = self.weight_unit_combo.currentText()
        
        if not weight_id:
            QMessageBox.warning(self, "警告", "请输入砝码ID")
            return
        
        if mass <= 0:
            QMessageBox.warning(self, "警告", "质量必须大于0")
            return
        
        # 检查砝码ID是否已存在
        if weight_id in self.weight_calibration.weights:
            QMessageBox.warning(self, "警告", f"砝码ID '{weight_id}' 已存在")
            return
        
        # 添加砝码
        self.weight_calibration.add_weight(weight_id, mass, unit)
        
        # 清空输入框
        self.weight_id_input.clear()
        self.weight_mass_input.setValue(100)
        self.weight_unit_combo.setCurrentText("g")
        
        # 更新显示
        self.update_weight_table()
        self.update_weight_selection()
        
        print(f"✅ 添加砝码: {weight_id} - {mass}{unit}")
    
    def reset_default_weights(self):
        """重置为默认砝码"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置为默认砝码吗？\n这将清除所有当前砝码并加载默认的7个砝码。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空当前砝码
            self.weight_calibration.weights.clear()
            self.weight_calibration.measurements.clear()
            
            # 重新加载默认砝码
            self.load_default_weights()
            
            # 清空结果表格
            self.results_table.setRowCount(0)
            
            QMessageBox.information(self, "成功", "已重置为默认砝码")
            print("✅ 已重置为默认砝码")
    
    def customize_default_weights(self):
        """自定义默认砝码"""
        try:
            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("自定义默认砝码")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout()
            
            # 说明文本
            info_label = QLabel("请输入自定义的默认砝码列表，每行一个砝码，格式：ID,质量,单位")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # 当前默认砝码显示
            current_label = QLabel("当前默认砝码:")
            layout.addWidget(current_label)
            
            current_text = QTextEdit()
            current_text.setMaximumHeight(100)
            current_text.setPlainText("1,50.0,g\n2,100.0,g\n3,150.0,g\n4,500.0,g\n5,550.0,g\n6,600.0,g\n7,650.0,g")
            current_text.setReadOnly(True)
            layout.addWidget(current_text)
            
            # 自定义输入
            custom_label = QLabel("自定义砝码列表:")
            layout.addWidget(custom_label)
            
            custom_text = QTextEdit()
            custom_text.setMaximumHeight(150)
            custom_text.setPlaceholderText("请输入自定义砝码，格式：ID,质量,单位\n例如：\nW1,25.0,g\nW2,75.0,g\nW3,200.0,g")
            layout.addWidget(custom_text)
            
            # 按钮
            button_layout = QHBoxLayout()
            save_btn = QPushButton("保存")
            cancel_btn = QPushButton("取消")
            
            save_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                custom_text_content = custom_text.toPlainText().strip()
                if custom_text_content:
                    # 解析自定义砝码
                    custom_weights = []
                    lines = custom_text_content.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            parts = line.split(',')
                            if len(parts) >= 3:
                                weight_id = parts[0].strip()
                                try:
                                    mass = float(parts[1].strip())
                                    unit = parts[2].strip()
                                    custom_weights.append({
                                        "id": weight_id,
                                        "mass": mass,
                                        "unit": unit
                                    })
                                except ValueError:
                                    QMessageBox.warning(self, "错误", f"无效的质量值: {parts[1]}")
                                    return
                    
                    if custom_weights:
                        # 清空当前砝码
                        self.weight_calibration.weights.clear()
                        self.weight_calibration.measurements.clear()
                        
                        # 添加自定义砝码
                        for weight in custom_weights:
                            self.weight_calibration.add_weight(
                                weight["id"], 
                                weight["mass"], 
                                weight["unit"]
                            )
                        
                        # 更新显示
                        self.update_weight_table()
                        self.update_weight_selection()
                        
                        # 清空结果表格
                        self.results_table.setRowCount(0)
                        
                        QMessageBox.information(self, "成功", f"已设置 {len(custom_weights)} 个自定义默认砝码")
                        print(f"✅ 已设置 {len(custom_weights)} 个自定义默认砝码")
                    else:
                        QMessageBox.warning(self, "警告", "没有有效的砝码数据")
                else:
                    QMessageBox.warning(self, "警告", "请输入砝码数据")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"自定义默认砝码失败: {e}")
            print(f"❌ 自定义默认砝码失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_weight_table(self):
        """更新砝码表格"""
        self.weight_table.setRowCount(len(self.weight_calibration.weights))
        
        for row, (weight_id, weight_info) in enumerate(self.weight_calibration.weights.items()):
            self.weight_table.setItem(row, 0, QTableWidgetItem(weight_id))
            self.weight_table.setItem(row, 1, QTableWidgetItem(f"{weight_info['mass']:.1f}"))
            self.weight_table.setItem(row, 2, QTableWidgetItem(weight_info['unit']))
            self.weight_table.setItem(row, 3, QTableWidgetItem(f"{weight_info['force']:.4f}"))
    
    def update_weight_selection(self):
        """更新砝码选择下拉框"""
        self.weight_combo.clear()
        self.weight_combo.addItem("选择砝码")
        
        for weight_id in self.weight_calibration.weights.keys():
            self.weight_combo.addItem(weight_id)
        
        # 更新位置一致性分析组件的砝码选择
        parent = self.parent()
        if parent and hasattr(parent, 'position_consistency_widget'):
            self.parent().position_consistency_widget.update_weight_selection_for_consistency(self.weight_calibration.weights)
    
    def record_baseline(self):
        """记录基线数据"""
        if not hasattr(self, 'parent') or not self.parent():
            QMessageBox.warning(self, "警告", "无法获取传感器数据")
            return
        
        # 获取主界面 - 修复父窗口引用逻辑
        parent = self.parent()
        main_interface = None
        
        # 通过标签页控件找到主界面
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if not main_interface or not hasattr(main_interface, 'get_current_sensor_data'):
            QMessageBox.warning(self, "警告", "无法获取传感器数据")
            return
        
        # 检查传感器是否已连接
        if not hasattr(main_interface, 'is_running') or not main_interface.is_running:
            QMessageBox.warning(self, "警告", "传感器未连接，请先启动传感器")
            return
        
        # 获取当前传感器数据
        current_data = main_interface.get_current_sensor_data()
        if current_data is None:
            QMessageBox.warning(self, "警告", "无法获取传感器数据，请确保传感器已连接")
            return
        
        # 记录基线数据
        self.weight_calibration.record_baseline(current_data)
        
        # 更新UI显示
        self.update_baseline_display()
        
        print(f"✅ 基线数据记录成功，当前记录次数: {len(self.weight_calibration.baseline_data)}")
    
    def clear_baseline(self):
        """清空基线数据"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有基线数据吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.weight_calibration.clear_baseline()
            self.update_baseline_display()
            print("✅ 基线数据已清空")
    
    def show_baseline_info(self):
        """显示基线统计信息"""
        baseline_stats = self.weight_calibration.get_baseline_stats()
        
        if baseline_stats is None:
            QMessageBox.information(self, "基线信息", "没有基线数据")
            return
        
        info_text = f"""基线统计信息:

记录次数: {baseline_stats['count']}

总压力统计:
• 平均值: {baseline_stats['avg_total_pressure']:.6f}
• 标准差: {baseline_stats['std_total_pressure']:.6f}
• 变异系数: {baseline_stats['cv_total']*100:.2f}%

平均压力统计:
• 平均值: {baseline_stats['avg_mean_pressure']:.6f}
• 标准差: {baseline_stats['std_mean_pressure']:.6f}

最大压力统计:
• 平均值: {baseline_stats['avg_max_pressure']:.6f}
• 标准差: {baseline_stats['std_max_pressure']:.6f}

基线校正状态: {'已启用' if self.weight_calibration.baseline_corrected else '未启用'}"""
        
        QMessageBox.information(self, "基线统计信息", info_text)
    
    def update_baseline_display(self):
        """更新基线显示"""
        baseline_count = len(self.weight_calibration.baseline_data)
        
        if baseline_count > 0:
            self.baseline_status_label.setText("基线状态: 已记录")
            self.baseline_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.baseline_status_label.setText("基线状态: 未记录")
            self.baseline_status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.baseline_count_label.setText(f"记录次数: {baseline_count}")
    
    def start_measurement(self):
        """开始测量"""
        if self.weight_combo.currentText() == "选择砝码":
            QMessageBox.warning(self, "警告", "请选择砝码")
            return
        
        if self.calibration_loader.calibration_map is None:
            QMessageBox.warning(self, "警告", "请先加载校准数据")
            return
        
        # 检查父窗口的传感器连接状态 - 修复父窗口引用
        parent = self.parent()
        main_interface = None
        
        # 通过标签页控件找到主界面
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if main_interface and hasattr(main_interface, 'is_running'):
            if not main_interface.is_running:
                QMessageBox.warning(self, "警告", "请先启动传感器")
                return
        
        self.current_weight_id = self.weight_combo.currentText()
        self.measurement_count = self.measurement_count_input.value()
        self.position_measurement_active = True
        
        print(f"🚀 开始测量: 砝码={self.current_weight_id}, 次数={self.measurement_count}")
        print(f"✅ 测量状态: measurement_active={self.position_measurement_active}")
        
        self.start_measurement_btn.setEnabled(False)
        self.stop_measurement_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.measurement_count)
        self.progress_bar.setValue(0)
        
        # 通知主界面开始测量 - 修复父窗口引用
        if main_interface and hasattr(main_interface, 'start_sensitivity_measurement'):
            main_interface.start_sensitivity_measurement(self.current_weight_id, self.measurement_count)
            print(f"✅ 已通知主界面开始测量")
        else:
            print(f"⚠️ 主界面没有start_sensitivity_measurement方法")
            print(f"⚠️ 主界面类型: {type(main_interface) if main_interface else 'None'}")
            # 即使没有主界面方法，也要继续测量
            print(f"⚠️ 继续使用本地测量模式")
    
    def stop_measurement(self):
        """停止测量"""
        self.position_measurement_active = False
        self.start_measurement_btn.setEnabled(True)
        self.stop_measurement_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # 通知父窗口停止测量
        if hasattr(self.parent(), 'stop_sensitivity_measurement'):
            self.parent().stop_sensitivity_measurement()
    
    def record_measurement_data(self, pressure_data):
        """记录测量数据"""
        # 添加调试信息
        print(f"🔍 记录测量数据: measurement_active={self.position_measurement_active}, current_weight_id={self.current_weight_id}")
        
        if not self.position_measurement_active or self.current_weight_id is None:
            print(f"⚠️ 测量未激活或砝码ID为空")
            return
        
        try:
            # 记录测量数据
            self.weight_calibration.record_measurement(self.current_weight_id, pressure_data)
            
            # 获取当前测量次数
            current_count = len(self.weight_calibration.measurements[self.current_weight_id])
            print(f"✅ 记录成功，当前测量次数: {current_count}/{self.measurement_count}")
            self.progress_bar.setValue(current_count)
            
            # 更新测量状态标签
            self.measurement_status_label.setText(f"测量状态: 进行中 ({current_count}/{self.measurement_count})")
            
            # 强制更新UI
            QApplication.processEvents()
            
            if current_count >= self.measurement_count:
                print(f"✅ 测量完成，停止测量")
                self.stop_measurement()
                QMessageBox.information(self, "完成", f"砝码 {self.current_weight_id} 测量完成")
        except Exception as e:
            print(f"❌ 记录测量数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_sensitivity(self):
        """计算敏感性"""
        if not self.weight_calibration.weights:
            QMessageBox.warning(self, "警告", "请先添加砝码")
            return
        
        if not self.weight_calibration.measurements:
            QMessageBox.warning(self, "警告", "请先进行测量")
            return
        
        # 计算敏感性
        results = self.weight_calibration.calculate_sensitivity()
        if not results:
            QMessageBox.critical(self, "错误", "敏感性计算失败")
            return
        
        # 更新结果表格
        self.results_table.setRowCount(len(results))
        
        row = 0
        for weight_id, result in results.items():
            weight_info = result['weight_info']
            
            # 设置表格数据
            self.results_table.setItem(row, 0, QTableWidgetItem(str(weight_id)))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{weight_info['mass']:.1f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(result['measurement_count'])))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result['avg_total_pressure']:.6f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{result['std_total_pressure']:.6f}"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{result['sensitivity_total']:.6f}"))
            self.results_table.setItem(row, 6, QTableWidgetItem(f"{result['sensitivity_mean']:.6f}"))
            self.results_table.setItem(row, 7, QTableWidgetItem(f"{result['cv']:.3f}"))
            
            row += 1
        
        # 调整表格列宽
        self.results_table.resizeColumnsToContents()
        
        # 显示整体敏感性分析
        overall = self.weight_calibration.get_overall_sensitivity()
        if overall:
            analysis_text = f"""
整体敏感性分析:
- 平均敏感性(总): {overall['avg_sensitivity_total']:.6f}
- 敏感性标准差: {overall['std_sensitivity_total']:.6f}
- 敏感性变异系数: {overall['cv_sensitivity_total']:.3f}
- 测量点数量: {overall['measurement_points']}
- 总测量次数: {overall['total_measurements']}
"""
            QMessageBox.information(self, "敏感性分析完成", analysis_text)
        
        # 自动绘制质量-总压力关系图
        self.plot_mass_pressure_relationship(results)
        
        print("✅ 敏感性计算完成，图表已生成")
    
    def plot_mass_pressure_relationship(self, results):
        """绘制质量-总压力关系图 - 改进版本"""
        try:
            # 提取数据
            masses = []
            pressures = []
            sensitivities = []
            cvs = []
            
            for weight_id, result in results.items():
                mass = result['weight_info']['mass']
                pressure = result['avg_total_pressure']
                sensitivity = result['sensitivity_total']
                cv = result['cv']
                
                masses.append(mass)
                pressures.append(pressure)
                sensitivities.append(sensitivity)
                cvs.append(cv)
            
            # 创建PyQtGraph绘图窗口
            plot_window = pg.GraphicsLayoutWidget()
            plot_window.setWindowTitle('Sensitivity Calibration Results Analysis')
            plot_window.resize(1200, 800)
            
            # 创建2x2的子图布局
            # 1. 质量-总压力关系图
            p1 = plot_window.addPlot(row=0, col=0, title="Mass vs Total Pressure")
            p1.setLabel('left', 'Average Total Pressure')
            p1.setLabel('bottom', 'Mass (g)')
            p1.showGrid(x=True, y=True, alpha=0.3)
            
            # 绘制散点图和趋势线
            scatter1 = pg.ScatterPlotItem(x=masses, y=pressures, size=15, 
                                        pen=pg.mkPen('black', width=2), 
                                        brush=pg.mkBrush('blue'))
            p1.addItem(scatter1)
            
            # 添加趋势线
            if len(masses) > 1:
                z = np.polyfit(masses, pressures, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(min(masses), max(masses), 100)
                trend_y = p(trend_x)
                trend_line = pg.PlotDataItem(trend_x, trend_y, pen=pg.mkPen('red', width=3, style=pg.QtCore.Qt.DashLine))
                p1.addItem(trend_line)
                
                # 添加R²值
                r_squared = np.corrcoef(masses, pressures)[0, 1] ** 2
                r2_text = pg.TextItem(text=f'R² = {r_squared:.3f}', color='red', anchor=(0, 1))
                r2_text.setPos(min(masses), max(pressures))
                p1.addItem(r2_text)
            
            # 2. 质量-敏感性关系图
            p2 = plot_window.addPlot(row=0, col=1, title="Mass vs Sensitivity")
            p2.setLabel('left', 'Sensitivity (Total)')
            p2.setLabel('bottom', 'Mass (g)')
            p2.showGrid(x=True, y=True, alpha=0.3)
            
            scatter2 = pg.ScatterPlotItem(x=masses, y=sensitivities, size=15, 
                                        pen=pg.mkPen('black', width=2), 
                                        brush=pg.mkBrush('green'))
            p2.addItem(scatter2)
            
            # 添加趋势线
            if len(masses) > 1:
                z = np.polyfit(masses, sensitivities, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(min(masses), max(masses), 100)
                trend_y = p(trend_x)
                trend_line = pg.PlotDataItem(trend_x, trend_y, pen=pg.mkPen('red', width=3, style=pg.QtCore.Qt.DashLine))
                p2.addItem(trend_line)
                
                # 添加R²值
                r_squared = np.corrcoef(masses, sensitivities)[0, 1] ** 2
                r2_text = pg.TextItem(text=f'R² = {r_squared:.3f}', color='red', anchor=(0, 1))
                r2_text.setPos(min(masses), max(sensitivities))
                p2.addItem(r2_text)
            
            # 3. 压力-敏感性关系图
            p3 = plot_window.addPlot(row=1, col=0, title="Pressure vs Sensitivity")
            p3.setLabel('left', 'Sensitivity (Total)')
            p3.setLabel('bottom', 'Average Total Pressure')
            p3.showGrid(x=True, y=True, alpha=0.3)
            
            scatter3 = pg.ScatterPlotItem(x=pressures, y=sensitivities, size=15, 
                                        pen=pg.mkPen('black', width=2), 
                                        brush=pg.mkBrush('orange'))
            p3.addItem(scatter3)
            
            # 添加趋势线
            if len(pressures) > 1:
                z = np.polyfit(pressures, sensitivities, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(min(pressures), max(pressures), 100)
                trend_y = p(trend_x)
                trend_line = pg.PlotDataItem(trend_x, trend_y, pen=pg.mkPen('red', width=3, style=pg.QtCore.Qt.DashLine))
                p3.addItem(trend_line)
                
                # 添加R²值
                r_squared = np.corrcoef(pressures, sensitivities)[0, 1] ** 2
                r2_text = pg.TextItem(text=f'R² = {r_squared:.3f}', color='red', anchor=(0, 1))
                r2_text.setPos(min(pressures), max(sensitivities))
                p3.addItem(r2_text)
            
            # 4. 变异系数分析图
            p4 = plot_window.addPlot(row=1, col=1, title="Coefficient of Variation Analysis")
            p4.setLabel('left', 'Coefficient of Variation')
            p4.setLabel('bottom', 'Mass (g)')
            p4.showGrid(x=True, y=True, alpha=0.3)
            
            # 绘制变异系数柱状图
            x_pos = np.arange(len(masses))
            bars = pg.BarGraphItem(x=x_pos, height=cvs, width=0.6, 
                                 brush='lightcoral', pen='black')
            p4.addItem(bars)
            
            # 设置X轴标签
            ax4 = p4.getAxis('bottom')
            ax4.setTicks([[(i, f'{mass}g') for i, mass in enumerate(masses)]])
            
            # 添加数值标签
            for i, value in enumerate(cvs):
                if value > 0:
                    text = pg.TextItem(text=f'{value:.3f}', color='black')
                    text.setPos(i, value + max(cvs) * 0.02)
                    p4.addItem(text)
            
            # 添加统计信息
            if len(cvs) > 0:
                avg_cv = np.mean(cvs)
                std_cv = np.std(cvs)
                stats_text = f"Avg CV: {avg_cv:.3f}\nStd CV: {std_cv:.3f}"
                stats_item = pg.TextItem(text=stats_text, color='black', anchor=(0, 1))
                stats_item.setPos(0, max(cvs))
                p4.addItem(stats_item)
            
            # 强制更新和渲染
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 在图表窗口添加保存按钮
            self.add_save_button_to_plot(plot_window)
            
            print(f"✅ 质量-压力关系图绘制完成")
            print(f"💡 提示：图表窗口中有保存按钮")
            
        except Exception as e:
            print(f"⚠️ 绘制质量-压力关系图时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def save_plot_directly(self, plot_window, filename):
        """直接保存图表的方法"""
        try:
            # 方法1: 使用grab方法
            if hasattr(plot_window, 'grab'):
                pixmap = plot_window.grab()
                if pixmap.save(filename):
                    print(f"✅ 使用grab方法保存成功")
                    return True
            
            # 方法2: 使用render方法
            if hasattr(plot_window, 'render'):
                pixmap = QPixmap(plot_window.size())
                plot_window.render(pixmap)
                if pixmap.save(filename):
                    print(f"✅ 使用render方法保存成功")
                    return True
            
            # 方法3: 使用屏幕截图
            try:
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                if screen and hasattr(plot_window, 'winId'):
                    pixmap = screen.grabWindow(plot_window.winId())
                    if pixmap.save(filename):
                        print(f"✅ 使用屏幕截图方法保存成功")
                        return True
            except Exception as e:
                print(f"⚠️ 屏幕截图方法失败: {e}")
            
            return False
            
        except Exception as e:
            print(f"⚠️ 直接保存方法失败: {e}")
            return False
    
    def save_results(self):
        """保存结果"""
        if not self.weight_calibration.calibration_results:
            QMessageBox.warning(self, "警告", "没有结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存标定结果", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
            "JSON文件 (*.json);;CSV文件 (*.csv);;文本文件 (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_results_json(filename)
                elif filename.endswith('.csv'):
                    self.save_results_csv(filename)
                else:
                    self.save_results_txt(filename)
                
                QMessageBox.information(self, "成功", f"结果已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_results_json(self, filename):
        """保存为JSON格式"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'calibration_file': self.calibration_loader.loaded_file,
            'weights': self.weight_calibration.weights,
            'measurements': {},
            'results': self.weight_calibration.calibration_results,
            'overall_sensitivity': self.weight_calibration.get_overall_sensitivity()
        }
        
        # 转换测量数据为可序列化格式
        for weight_id, measurements in self.weight_calibration.measurements.items():
            data['measurements'][weight_id] = []
            for m in measurements:
                data['measurements'][weight_id].append({
                    'timestamp': m['timestamp'].isoformat(),
                    'total_pressure': m['total_pressure'],
                    'mean_pressure': m['mean_pressure'],
                    'max_pressure': m['max_pressure']
                })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_results_csv(self, filename):
        """保存为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['砝码ID', '质量(g)', '测量次数', '平均总压力', '标准差', 
                           '敏感性(总)', '敏感性(平均)', '变异系数'])
            
            for weight_id, result in self.weight_calibration.calibration_results.items():
                writer.writerow([
                    weight_id,
                    f"{result['weight_info']['mass']:.1f}",
                    result['measurement_count'],
                    f"{result['avg_total_pressure']:.6f}",
                    f"{result['std_total_pressure']:.6f}",
                    f"{result['sensitivity_total']:.6f}",
                    f"{result['sensitivity_mean']:.6f}",
                    f"{result['cv']:.3f}"
                ])
    
    def save_results_txt(self, filename):
        """保存为文本格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器敏感性标定结果\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"校准数据文件: {self.calibration_loader.loaded_file}\n\n")
            
            f.write("===== 砝码信息 =====\n")
            for weight_id, weight_info in self.weight_calibration.weights.items():
                f.write(f"{weight_id}: {weight_info['mass']}{weight_info['unit']} (力: {weight_info['force']:.4f}N)\n")
            
            f.write("\n===== 标定结果 =====\n")
            for weight_id, result in self.weight_calibration.calibration_results.items():
                f.write(f"\n砝码 {weight_id}:\n")
                f.write(f"  测量次数: {result['measurement_count']}\n")
                f.write(f"  平均总压力: {result['avg_total_pressure']:.6f}\n")
                f.write(f"  标准差: {result['std_total_pressure']:.6f}\n")
                f.write(f"  敏感性(总): {result['sensitivity_total']:.6f}\n")
                f.write(f"  敏感性(平均): {result['sensitivity_mean']:.6f}\n")
                f.write(f"  变异系数: {result['cv']:.3f}\n")
            
            overall = self.weight_calibration.get_overall_sensitivity()
            if overall:
                f.write(f"\n===== 整体敏感性 =====\n")
                f.write(f"平均敏感性(总压力): {overall['avg_sensitivity_total']:.6f} ± {overall['std_sensitivity_total']:.6f}\n")
                f.write(f"平均敏感性(平均压力): {overall['avg_sensitivity_mean']:.6f} ± {overall['std_sensitivity_mean']:.6f}\n")
                f.write(f"平均敏感性(最大压力): {overall['avg_sensitivity_max']:.6f} ± {overall['std_sensitivity_max']:.6f}\n")

    def add_save_button_to_plot(self, plot_window):
        """在图表窗口中添加一个保存按钮"""
        try:
            # 创建一个包含图表和按钮的主窗口
            main_window = QWidget()
            main_window.setWindowTitle("敏感性标定图表")
            main_window.resize(plot_window.width(), plot_window.height() + 60)  # 为按钮留出空间
            
            # 创建垂直布局
            layout = QVBoxLayout()
            
            # 添加图表窗口
            layout.addWidget(plot_window)
            
            # 创建保存按钮
            save_button = QPushButton("保存图表")
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50; /* 绿色背景 */
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: none;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049; /* 深绿色背景 */
                }
                QPushButton:pressed {
                    background-color: #388e3c; /* 更深的绿色背景 */
                }
            """)
            
            # 连接按钮点击信号到保存函数
            save_button.clicked.connect(lambda: self.save_plot_with_dialog(plot_window))
            
            # 设置按钮大小
            save_button.setFixedHeight(40)
            
            # 添加按钮到布局
            layout.addWidget(save_button)
            
            # 设置主窗口布局
            main_window.setLayout(layout)
            
            # 显示主窗口
            main_window.show()
            
            # 强制更新图表窗口
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 保存主窗口引用
            self.current_plot_window = main_window
            
            print(f"✅ 保存按钮已添加到图表窗口底部")
            
        except Exception as e:
            print(f"⚠️ 添加保存按钮失败: {e}")
            import traceback
            traceback.print_exc()
    
    def save_plot_with_dialog(self, plot_window):
        """通过对话框保存图表 - 改进版本"""
        try:
            # 弹出保存对话框
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存敏感性标定图表", 
                f"C:/Users/84672/Documents/Research/sensitivity_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
            )
            
            if filename:
                print(f"🔍 用户选择保存到: {filename}")
                
                # 保存前确保渲染 - 多次强制更新
                for i in range(3):
                    plot_window.scene().update()
                    QApplication.processEvents()
                    QTimer.singleShot(50, lambda: None)  # 短暂延迟
                
                # 方法1: 尝试使用可靠的保存函数
                if save_pyqtgraph_plot(plot_window, filename):
                    print(f"✅ 敏感性标定图表已保存到: {filename}")
                    QMessageBox.information(self, "成功", f"敏感性标定图表已保存到:\n{filename}")
                    return
                
                # 方法2: 如果通用保存函数失败，尝试使用robust保存函数
                print(f"⚠️ 通用保存函数失败，尝试使用robust保存函数...")
                if hasattr(plot_window, 'scene'):
                    if save_pyqtgraph_plot_robust(plot_window.scene(), filename):
                        print(f"✅ 使用robust保存函数成功: {filename}")
                        QMessageBox.information(self, "成功", f"敏感性标定图表已保存到:\n{filename}")
                        return
                
                # 方法3: 尝试直接保存
                print(f"⚠️ robust保存函数失败，尝试直接保存...")
                if self.save_plot_directly(plot_window, filename):
                    print(f"✅ 直接保存成功: {filename}")
                    QMessageBox.information(self, "成功", f"敏感性标定图表已保存到:\n{filename}")
                    return
                
                # 所有方法都失败
                QMessageBox.warning(self, "保存失败", "所有保存方法都失败了，请检查文件路径和权限")
            else:
                print(f"💡 用户取消了保存")
                
        except Exception as e:
            print(f"⚠️ 保存图表时出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
            import traceback
            traceback.print_exc()


class SensitivityCalibrationInterface(QWidget):
    """传感器敏感性标定界面"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.data_handler = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 校准数据
        self.calibration_map = None
        
        # 测量相关
        self.position_measurement_active = False
        self.current_weight_id = None
        self.measurement_count = 0
        self.current_measurement = 0
        
        # 局部灵敏度检验相关
        self.local_sensitivity_measurement_active = False
        self.current_local_sensitivity_position = None
        
        # 引导位置绘制标志
        self.guide_positions_drawn = False
        
        # 设置窗口属性
        self.setWindowTitle("传感器敏感性标定系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据处理器
        self.init_data_handler()
        
        # 延迟自动启动传感器（模拟模式）
        QTimer.singleShot(1000, self.auto_start_sensor)
        
        # 引导位置绘制标志
        self.guide_positions_drawn = False
    
    def auto_start_sensor(self):
        """自动启动传感器（模拟模式）"""
        try:
            if not self.is_running:
                print("🔄 自动启动传感器（模拟模式）...")
                self.start_sensor()
        except Exception as e:
            print(f"⚠️ 自动启动传感器时出错: {e}")
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧：传感器显示区域
        left_panel = QVBoxLayout()
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        
        # 传感器选择
        self.sensor_label = QLabel("传感器:")
        self.sensor_combo = QComboBox()
        self.sensor_combo.addItems(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        self.sensor_combo.setCurrentText("0")
        self.sensor_combo.currentTextChanged.connect(self.on_sensor_changed)
        
        # 模式选择
        self.mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["模拟模式", "真实传感器"])
        self.mode_combo.setCurrentText("模拟模式")
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        
        # 端口选择
        self.port_label = QLabel("端口:")
        self.port_input = QLineEdit()
        self.port_input.setText("0")
        self.port_input.setToolTip("输入端口号，例如：0, COM3, /dev/ttyUSB0")
        
        # 控制按钮
        self.start_button = QPushButton("开始")
        self.start_button.clicked.connect(self.start_sensor)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_sensor)
        self.stop_button.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 校准状态
        self.calibration_status_label = QLabel("校准: 未加载")
        self.calibration_status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 测量状态
        self.measurement_status_label = QLabel("测量: 未开始")
        self.measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 添加到控制布局
        control_layout.addWidget(self.sensor_label)
        control_layout.addWidget(self.sensor_combo)
        control_layout.addWidget(self.mode_label)
        control_layout.addWidget(self.mode_combo)
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.port_input)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.calibration_status_label)
        control_layout.addWidget(self.measurement_status_label)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        
        # PyQtGraph热力图显示区域
        self.heatmap_widget = pg.GraphicsLayoutWidget()
        self.heatmap_plot = self.heatmap_widget.addPlot()
        self.heatmap_item = pg.ImageItem()
        self.heatmap_plot.addItem(self.heatmap_item)
        
        # 添加颜色条
        self.colorbar = pg.ColorBarItem(values=(0, 0.01), colorMap='viridis')
        self.colorbar.setImageItem(self.heatmap_item)
        
        # 设置坐标轴
        self.heatmap_plot.setAspectLocked(False)
        # 设置Y轴向下 (0在顶部，63在底部)
        self.heatmap_plot.invertY(True)
        
        # 设置坐标轴标签
        self.heatmap_plot.setLabel('left', 'Y轴 (传感器行)')
        self.heatmap_plot.setLabel('bottom', 'X轴 (传感器列)')
        self.heatmap_plot.setTitle('传感器数据热力图')
        
        # 初始化热力图数据
        self.heatmap_data = np.zeros((64, 64))
        self.heatmap_item.setImage(self.heatmap_data)
        
        # 设置颜色映射和级别
        colormap = pg.colormap.get('viridis')
        self.heatmap_item.setColorMap(colormap)
        self.heatmap_item.setLevels([0, 0.01])
        
        # 添加坐标轴刻度
        ax_x = self.heatmap_plot.getAxis('bottom')
        ax_y = self.heatmap_plot.getAxis('left')
        
        # 设置X轴刻度 (每8个传感器一个刻度)
        x_ticks = [(i, str(i)) for i in range(0, 64, 8)]
        ax_x.setTicks([x_ticks])
        
        # 设置Y轴刻度 (每8个传感器一个刻度)
        y_ticks = [(i, str(i)) for i in range(0, 64, 8)]
        ax_y.setTicks([y_ticks])
        
        # 启用鼠标交互
        self.heatmap_plot.setMouseEnabled(x=True, y=True)
        self.heatmap_plot.setMenuEnabled(True)
        
        # 添加网格线
        self.heatmap_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # 组装左侧面板
        left_panel.addLayout(control_layout)
        left_panel.addWidget(self.heatmap_widget)
        
        # 右侧：功能面板（使用标签页）
        right_panel = QVBoxLayout()
        
        # 创建标签页控件
        self.function_tabs = QTabWidget()
        
        # 敏感性标定标签页
        self.sensitivity_widget = SensitivityCalibrationWidget(self)
        self.function_tabs.addTab(self.sensitivity_widget, "敏感性标定")
        
        # 敏感性分析标签页 - 新增
        self.sensitivity_analysis_widget = SensitivityAnalysisWidget(self)
        self.function_tabs.addTab(self.sensitivity_analysis_widget, "敏感性分析")

        # 位置一致性分析标签页 - 新增
        self.position_consistency_widget = PositionConsistencyWidget(self)
        self.function_tabs.addTab(self.position_consistency_widget, "位置一致性分析")

        # 局部灵敏度检验标签页 - 新增
        self.local_sensitivity_widget = LocalSensitivityWidget(self)
        self.function_tabs.addTab(self.local_sensitivity_widget, "局部灵敏度检验")

        
        right_panel.addWidget(self.function_tabs)
        
        # 组装主布局
        main_layout.addLayout(left_panel, 2)   # 左侧占2/3
        main_layout.addLayout(right_panel, 1)  # 右侧占1/3
        
        # 添加状态栏
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { border-top: 1px solid #ccc; }")
        
        # 状态栏信息标签
        self.status_bar_sensor = QLabel("传感器: --")
        self.status_bar_calibration = QLabel("校准: 未加载")
        self.status_bar_measurement = QLabel("测量: 未开始")
        self.status_bar_data = QLabel("数据: --")
        
        self.status_bar.addWidget(self.status_bar_sensor)
        self.status_bar.addWidget(self.status_bar_calibration)
        self.status_bar.addWidget(self.status_bar_measurement)
        self.status_bar.addWidget(self.status_bar_data)
        
        # 创建主窗口布局
        main_window_layout = QVBoxLayout()
        main_window_layout.addLayout(main_layout)
        main_window_layout.addWidget(self.status_bar)
        
        # 设置主布局
        self.setLayout(main_window_layout)
        
        # 延迟更新位置一致性分析的砝码选择
        QTimer.singleShot(100, self.update_position_consistency_weights)
    def start_position_consistency_measurement(self, position_id, weight_id, measurement_count):
        """开始位置一致性测量"""
        self.position_measurement_active = True
        self.current_weight_id = weight_id
        self.measurement_count = measurement_count
        self.current_measurement = 0
        
        self.measurement_status_label.setText(f"位置测量: {position_id} - {weight_id} ({measurement_count}次)")
        self.measurement_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.update_status_bar()
        
        print(f"🔍 开始位置一致性测量: 位置={position_id}, 砝码={weight_id}, 次数={measurement_count}")
    
    def stop_position_consistency_measurement(self):
        """停止位置一致性测量"""
        self.position_measurement_active = False
        self.current_weight_id = None
        self.measurement_count = 0
        self.current_measurement = 0
        
        self.measurement_status_label.setText("测量: 未开始")
        self.measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.update_status_bar()
        
        print("✅ 位置一致性测量已停止")
    def set_calibration_data(self, calibration_map):
        """设置校准数据"""
        self.calibration_map = calibration_map
        self.calibration_status_label.setText("校准: 已加载")
        self.calibration_status_label.setStyleSheet("color: green; font-weight: bold;")
        self.update_status_bar()
    
    def on_sensor_changed(self, sensor_id_text):
        """传感器选择变化时的处理函数"""
        if not self.is_running:
            try:
                sensor_id = int(sensor_id_text)
                print(f"🔄 传感器选择变化为: {sensor_id}")
                self.init_data_handler()
            except ValueError:
                print(f"⚠️ 无效的传感器ID: {sensor_id_text}")
    
    def on_mode_changed(self, mode_text):
        """模式选择变化时的处理函数"""
        if not self.is_running:
            print(f"🔄 模式选择变化为: {mode_text}")
            if mode_text == "真实传感器":
                if not DATA_HANDLER_AVAILABLE:
                    QMessageBox.warning(self, "警告", "真实传感器模式不可用，缺少必要的模块。\n请确保安装了data_processing和backends模块。")
                    self.mode_combo.setCurrentText("模拟模式")
                    return
            self.init_data_handler()
    
    def init_data_handler(self):
        """初始化数据处理器"""
        mode = self.mode_combo.currentText()
        
        if mode == "真实传感器" and DATA_HANDLER_AVAILABLE:
            try:
                sensor_id = int(self.sensor_combo.currentText())
                self.data_handler = DataHandler(LargeUsbSensorDriver, max_len=256)
                print(f"✅ 真实传感器数据处理器初始化成功，传感器ID: {sensor_id}")
            except Exception as e:
                print(f"⚠️ 真实传感器数据处理器初始化失败: {e}")
                self.data_handler = None
                QMessageBox.warning(self, "警告", f"真实传感器初始化失败: {e}\n将切换到模拟模式。")
                self.mode_combo.setCurrentText("模拟模式")
        else:
            print("⚠️ 使用模拟数据处理器")
            self.data_handler = None
    
    def generate_simulated_data(self):
        """生成模拟传感器数据"""
        # 创建一个64x64的模拟传感器数据
        data = np.random.rand(64, 64) * 0.001  # 基础噪声
        
        # 模拟传感器敏感度不均匀
        sensitivity_gradient = np.linspace(0.7, 1.3, 64)
        for i in range(64):
            data[i, :] *= sensitivity_gradient[i]
        
        # 模拟几个按压区域
        num_presses = np.random.randint(1, 3)
        for _ in range(num_presses):
            center_x = np.random.randint(8, 56)
            center_y = np.random.randint(8, 56)
            
            for i in range(64):
                for j in range(64):
                    distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if distance < 8:
                        press_strength = 0.001 + np.random.rand() * 0.002
                        data[i, j] += press_strength * np.exp(-distance / 4)
        
        # 确保数据在0-0.01范围内
        data = np.clip(data, 0.0, 0.01)
        
        return data
    
    def start_sensitivity_measurement(self, weight_id, measurement_count):
        """开始敏感性测量"""
        self.position_measurement_active = True
        self.current_weight_id = weight_id
        self.measurement_count = measurement_count
        self.current_measurement = 0
        
        self.measurement_status_label.setText(f"测量: {weight_id} ({measurement_count}次)")
        self.measurement_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.update_status_bar()
        
        # 同时设置敏感性标定组件的测量状态
        if hasattr(self, 'sensitivity_widget') and self.sensitivity_widget:
            self.sensitivity_widget.position_measurement_active = True
            self.sensitivity_widget.current_weight_id = weight_id
            self.sensitivity_widget.measurement_count = measurement_count
            self.sensitivity_widget.current_measurement = 0
            print(f"✅ 已设置敏感性标定组件测量状态")
        
        print(f"🔍 开始测量砝码 {weight_id}，共 {measurement_count} 次")
    
    def stop_sensitivity_measurement(self):
        """停止敏感性测量"""
        self.position_measurement_active = False
        self.current_weight_id = None
        self.measurement_count = 0
        self.current_measurement = 0
        
        self.measurement_status_label.setText("测量: 未开始")
        self.measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.update_status_bar()
        
        print("✅ 敏感性测量已停止")
    
    def get_current_sensor_data(self):
        """获取当前传感器数据 - 供基线校正使用"""
        if not self.is_running:
            return None
        
        try:
            if self.data_handler:
                # 使用真实传感器数据
                self.data_handler.trigger()
                with self.data_handler.lock:
                    if not self.data_handler.value:
                        return None
                    current_data = np.array(self.data_handler.value[-1])
            else:
                # 使用模拟数据
                current_data = self.generate_simulated_data()
            
            # 应用校准
            if self.calibration_map is not None:
                corrected_data = current_data * self.calibration_map
            else:
                corrected_data = current_data
            
            return corrected_data
            
        except Exception as e:
            print(f"⚠️ 获取传感器数据失败: {e}")
            return None
    
    def update_data(self):
        """更新数据显示"""
        try:
            if self.data_handler:
                # 使用真实传感器数据
                self.data_handler.trigger()
                with self.data_handler.lock:
                    if not self.data_handler.value:
                        return
                    current_data = np.array(self.data_handler.value[-1])
            else:
                # 使用模拟数据
                current_data = self.generate_simulated_data()
            
            # 应用校准
            if self.calibration_map is not None:
                corrected_data = current_data * self.calibration_map
            else:
                corrected_data = current_data
            
            # 更新热力图
            self.update_heatmap(corrected_data)
            
            # 更新数据信息
            self.update_data_info(corrected_data)
            
            # 处理测量数据
            if self.position_measurement_active:
                print(f"📊 测量中: {self.current_weight_id} ({self.current_measurement}/{self.measurement_count})")
                
                # 检查是否是位置一致性测量（通过检查是否有位置一致性组件在测量）
                is_position_measurement = False
                if hasattr(self, 'position_consistency_widget') and self.position_consistency_widget:
                    if hasattr(self.position_consistency_widget, 'position_measurement_active'):
                        is_position_measurement = self.position_consistency_widget.position_measurement_active
                
                # 只有在非位置一致性测量时才调用敏感性标定组件
                if not is_position_measurement:
                    # 处理敏感性标定测量
                    if hasattr(self, 'sensitivity_widget') and self.sensitivity_widget:
                        try:
                            self.sensitivity_widget.record_measurement_data(corrected_data)
                            print(f"✅ 数据已传递给敏感性标定组件")
                        except Exception as e:
                            print(f"❌ 调用record_measurement_data失败: {e}")
                            import traceback
                            traceback.print_exc()
                
                # 处理位置一致性测量
                if hasattr(self, 'position_consistency_widget') and self.position_consistency_widget:
                    try:
                        self.position_consistency_widget.record_position_measurement_data(corrected_data)
                        print(f"✅ 数据已传递给位置一致性分析组件")
                    except Exception as e:
                        print(f"❌ 调用record_position_measurement_data失败: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"⚠️ 位置一致性分析组件不存在")
                    print(f"⚠️ position_consistency_widget: {getattr(self, 'position_consistency_widget', 'Not found')}")
                
                self.current_measurement += 1
                
                # 更新测量进度
                if self.measurement_count > 0:
                    progress = (self.current_measurement / self.measurement_count) * 100
                else:
                    progress = 0
                self.measurement_status_label.setText(
                    f"测量: {self.current_weight_id} ({self.current_measurement}/{self.measurement_count}) [{progress:.1f}%]"
                )
                
                # 强制更新UI
                QApplication.processEvents()
                
                # 检查是否完成测量
                if self.current_measurement >= self.measurement_count:
                    print(f"✅ 测量完成，停止测量")
                    self.stop_position_consistency_measurement()
        except USBError:
            print("❌ USB连接错误，停止传感器")
            self.stop_sensor()
            QMessageBox.critical(self, "USB错误", "USB连接错误，传感器已停止")
        except Exception as e:
            print(f"⚠️ 更新数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_heatmap(self, data):
        """更新热力图"""
        try:
            if data is None or data.size == 0:
                return
                
            # 修复坐标映射问题：PyQtGraph ImageItem将第一维映射为Y轴，第二维映射为X轴
            # 传感器数据格式：data[row, col] -> 需要转置为 data[col, row] 以匹配PyQtGraph的 [y, x] 映射
            transposed_data = data.T  # 转置数据以匹配PyQtGraph的坐标映射
            
            # 使用PyQtGraph更新热力图
            self.heatmap_data = transposed_data
            self.heatmap_item.setImage(self.heatmap_data)
            
            # 动态调整颜色级别
            if data.max() > 0:
                # 使用数据的实际范围，但设置最小值为0
                max_val = data.max()
                min_val = data.min()
                
                # 如果最大值太小，使用固定范围
                if max_val < 0.001:
                    levels = [0, 0.01]
                else:
                    # 使用数据的实际范围，稍微扩展一点
                    range_val = max_val - min_val
                    levels = [min_val, max_val + range_val * 0.1]
                
                self.heatmap_item.setLevels(levels)
                
                # 更新颜色条范围
                self.colorbar.setLevels(levels)
                
                # 只在第一次绘制引导位置圆圈
                if not self.guide_positions_drawn:
                    self.draw_guide_positions()
            
        except Exception as e:
            print(f"⚠️ 更新热力图时出错: {e}")
    
    def update_data_info(self, data):
        """更新数据信息显示"""
        try:
            if data is not None and data.size > 0:
                # 计算总压力
                total_pressure = np.sum(data)
                
                # 更新状态栏数据信息
                self.status_bar_data.setText(f"压力: 最大={data.max():.4f}, 总压力={total_pressure:.6f}")
        except Exception as e:
            print(f"⚠️ 更新数据信息时出错: {e}")
    
    def start_sensor(self):
        """开始传感器连接"""
        if self.is_running:
            return
            
        sensor_id = int(self.sensor_combo.currentText())
        port = self.port_input.text()
        
        print(f"�� 尝试连接传感器 {sensor_id}，端口: {port}")
        
        if self.data_handler:
            try:
                if port.isdigit():
                    flag = self.data_handler.connect(port)
                else:
                    flag = self.data_handler.connect(port)
                    
                if flag:
                    self.is_running = True
                    self.timer.start(50)  # 20 FPS
                    self.update_ui_state()
                    self.status_label.setText(f"状态: 已连接 (传感器{sensor_id})")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.update_status_bar()
                    print(f"✅ 传感器 {sensor_id} 连接成功，端口: {port}")
                else:
                    self.status_label.setText("状态: 连接失败")
                    self.status_label.setStyleSheet("color: red; font-weight: bold;")
            except Exception as e:
                print(f"❌ 连接传感器时出错: {e}")
                self.status_label.setText("状态: 连接错误")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            # 模拟模式
            self.is_running = True
            self.timer.start(50)  # 20 FPS
            self.update_ui_state()
            self.status_label.setText(f"状态: 模拟模式 (传感器{sensor_id})")
            self.status_label.setStyleSheet("color: blue; font-weight: bold;")
            self.update_status_bar()
            print(f"✅ 模拟传感器 {sensor_id} 启动成功")
    
    def stop_sensor(self):
        """停止传感器连接"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.timer.stop()
        
        if self.data_handler:
            try:
                self.data_handler.disconnect()
                print("✅ 传感器已断开连接")
            except Exception as e:
                print(f"⚠️ 断开连接时出错: {e}")
        
        self.update_ui_state()
        self.status_label.setText("状态: 已断开")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.update_status_bar()
    
    def update_ui_state(self):
        """更新UI状态"""
        self.start_button.setEnabled(not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.sensor_combo.setEnabled(not self.is_running)
        self.mode_combo.setEnabled(not self.is_running)
        self.port_input.setEnabled(not self.is_running)
    
    def update_status_bar(self):
        """更新状态栏信息"""
        # 更新传感器信息
        if self.is_running:
            sensor_id = self.sensor_combo.currentText()
            if self.data_handler:
                self.status_bar_sensor.setText(f"传感器: {sensor_id} (已连接)")
            else:
                self.status_bar_sensor.setText(f"传感器: {sensor_id} (模拟)")
        else:
            self.status_bar_sensor.setText("传感器: 未连接")
        
        # 更新校准状态
        if self.calibration_map is not None:
            self.status_bar_calibration.setText("校准: 已加载")
        else:
            self.status_bar_calibration.setText("校准: 未加载")
        
        # 更新测量状态
        if self.position_measurement_active:
            self.status_bar_measurement.setText(f"测量: {self.current_weight_id}")
        else:
            self.status_bar_measurement.setText("测量: 未开始")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_sensor()
        event.accept()


    
    def draw_guide_positions(self):
        """绘制引导位置圆圈"""
        try:
            # 检查是否已经绘制过
            if self.guide_positions_drawn:
                print(f"✅ 引导位置已绘制，跳过重复绘制")
                return
                
            if hasattr(self, 'position_consistency_widget') and self.position_consistency_widget:
                guide_positions = self.position_consistency_widget.guide_positions
                
                for pos_id, position in guide_positions.items():
                    x, y = position['x'], position['y']
                    name = position['name']
                    color = position.get('color', 'red')
                    
                    # 绘制圆圈
                    circle = pg.CircleROI([x-2, y-2], [4, 4], pen=pg.mkPen(color, width=2))
                    self.heatmap_plot.addItem(circle)
                    
                    # 添加位置标签
                    text_item = pg.TextItem(text=name, color=color, anchor=(0, 0))
                    text_item.setPos(x + 3, y + 3)
                    self.heatmap_plot.addItem(text_item)
                    
                    # 添加位置ID标签
                    id_text = pg.TextItem(text=f"({pos_id})", color=color, anchor=(0, 1))
                    id_text.setPos(x + 3, y - 3)
                    self.heatmap_plot.addItem(id_text)
                
                # 标记为已绘制
                self.guide_positions_drawn = True
                print(f"✅ 已绘制 {len(guide_positions)} 个引导位置圆圈")
                
        except Exception as e:
            print(f"⚠️ 绘制引导位置圆圈时出错: {e}")
    

    def clear_guide_positions(self):
        """清除引导位置圆圈"""
        try:
            # 清除所有ROI和文本项
            # 使用ViewBox的childItems()方法获取子项
            for item in self.heatmap_plot.childItems():
                if isinstance(item, (pg.CircleROI, pg.TextItem)):
                    self.heatmap_plot.removeItem(item)
        except Exception as e:
            print(f"⚠️ 清除引导位置圆圈时出错: {e}")
            
    def update_guide_positions(self):
        """更新引导位置显示"""
        try:
            # 清除旧的引导位置
            self.clear_guide_positions()
            # 重新绘制引导位置
            self.draw_guide_positions()
        except Exception as e:
            print(f"⚠️ 更新引导位置显示时出错: {e}")
    
    
    def update_position_consistency_weights(self):
        """更新位置一致性分析的砝码选择"""
        if hasattr(self, 'sensitivity_widget') and hasattr(self.sensitivity_widget, 'weight_calibration') and hasattr(self.sensitivity_widget.weight_calibration, 'weights'):
            weights = self.sensitivity_widget.weight_calibration.weights
            if hasattr(self, 'position_consistency_widget'):
                self.position_consistency_widget.update_weight_selection_for_consistency(weights)
    
    def get_current_sensor_data_for_local_sensitivity(self):
        """获取当前传感器数据用于局部灵敏度检验"""
        """获取当前传感器数据"""
        if hasattr(self, 'data_handler') and self.data_handler is not None:
            try:
                # 获取传感器数据
                data = self.data_handler.get_data()
                if data is not None and len(data) > 0:
                    # 返回最新的数据
                    return data[-1]
                else:
                    print("⚠️ 传感器数据为空")
                    return None
            except Exception as e:
                print(f"❌ 获取传感器数据失败: {e}")
                return None
        else:
            print("⚠️ 数据处理器未初始化")
            return None
    
    def start_local_sensitivity_measurement(self, position_data):
        """开始局部灵敏度测量"""
        """开始局部灵敏度测量"""
        self.local_sensitivity_measurement_active = True
        self.current_local_sensitivity_position = position_data
        
        self.measurement_status_label.setText(f"局部灵敏度测量: {position_data['id']}")
        self.measurement_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.update_status_bar()
        
        print(f"🔍 开始局部灵敏度测量: 位置={position_data['id']}, 坐标=({position_data['x']}, {position_data['y']})")
    
    def stop_local_sensitivity_measurement(self):
        """停止局部灵敏度测量"""
        self.local_sensitivity_measurement_active = False
        self.current_local_sensitivity_position = None
        
        self.measurement_status_label.setText("测量: 未开始")
        self.measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.update_status_bar()
        
        print("✅ 局部灵敏度测量已停止")

# 使用示例和启动代码
def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = SensitivityCalibrationInterface()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()