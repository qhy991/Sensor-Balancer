#!/usr/bin/env python3
"""
局部传感器灵敏度检验界面
用于测试传感器在局部区域的灵敏度一致性
"""

import json
import csv
import numpy as np
from datetime import datetime
import random
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, 
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, 
    QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog, QDialog, 
    QApplication, QSizePolicy
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import pyqtgraph as pg
from PyQt5.QtGui import QPixmap

# 检查PyQtGraph可用性
try:
    import pyqtgraph as pg
    import pyqtgraph.exporters
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("⚠️ PyQtGraph不可用，图表功能将被禁用")

# 导入保存图表的通用函数
try:
    from sensor_sensitivity_calibration import save_pyqtgraph_plot, save_pyqtgraph_plot_robust
except ImportError:
    def save_pyqtgraph_plot_robust(plot_item, filename):
        """使用 pyqtgraph.exporters 来可靠地保存图表"""
        try:
            if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                exporter = pg.exporters.ImageExporter(plot_item)
                exporter.export(filename)
                print(f"✅ [Robust Save] 图表已成功保存到: {filename}")
                return True
            else:
                print("⚠️ pyqtgraph.exporters.ImageExporter不可用")
                return False
        except Exception as e:
            print(f"❌ [Robust Save] 保存失败: {e}")
            return False
    
    def save_pyqtgraph_plot(plot_window, filename):
        """保存PyQtGraph图表的通用函数"""
        try:
            print(f"🔍 开始保存图表到: {filename}")
            
            # 方法1: 尝试使用ImageExporter
            try:
                if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                    exporter = pg.exporters.ImageExporter(plot_window.scene())
                    exporter.export(filename)
                    print(f"✅ 使用ImageExporter保存图表成功: {filename}")
                    return True
            except Exception as e:
                print(f"⚠️ ImageExporter保存失败: {e}")
            
            # 方法2: 尝试使用grab方法截图
            try:
                if hasattr(plot_window, 'grab'):
                    pixmap = plot_window.grab()
                    if pixmap.save(filename):
                        print(f"✅ 使用grab方法保存图表成功: {filename}")
                        return True
            except Exception as e:
                print(f"⚠️ grab方法保存失败: {e}")
            
            print(f"❌ 所有保存方法都失败了")
            return False
            
        except Exception as e:
            print(f"❌ 保存图表时出错: {e}")
            return False


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
        
        # 停止引导定时器
        if hasattr(self, 'guide_timer') and self.guide_timer.isActive():
            self.guide_timer.stop()
            print("🛑 引导定时器已停止")
        
        # 关闭引导窗口
        if hasattr(self, 'guide_window') and self.guide_window:
            try:
                self.guide_window.close()
                self.guide_window = None
                print("🛑 引导窗口已关闭")
            except Exception as e:
                print(f"⚠️ 关闭引导窗口时出错: {e}")
        
        # 重置UI状态
        self.start_sensitivity_measurement_btn.setEnabled(True)
        self.start_guided_measurement_btn.setEnabled(True)
        self.stop_sensitivity_measurement_btn.setEnabled(False)
        self.generate_positions_btn.setEnabled(True)
        self.sensitivity_progress_bar.setVisible(False)
        
        # 禁用手动控制按钮
        self.next_position_btn.setEnabled(False)
        self.previous_position_btn.setEnabled(False)
        self.record_data_btn.setEnabled(False)
        
        # 更新状态标签
        if hasattr(self, 'sensitivity_data') and self.sensitivity_data:
            self.sensitivity_status_label.setText(f"灵敏度测试状态: 已停止 (采集数据位置: {len(self.sensitivity_data)} 个)")
            self.sensitivity_status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.sensitivity_status_label.setText("灵敏度测试状态: 已停止")
            self.sensitivity_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 启用分析按钮（如果有数据）
        if hasattr(self, 'sensitivity_data') and self.sensitivity_data:
            self.analyze_sensitivity_btn.setEnabled(True)
            self.save_sensitivity_results_btn.setEnabled(True)
            self.plot_sensitivity_btn.setEnabled(True)
        
        print(f"✅ 局部灵敏度测试已停止")
        if hasattr(self, 'sensitivity_data'):
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
        
        # 添加窗口关闭事件处理
        self.guide_window.closeEvent = self.on_guide_window_closed
        
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
            line = pg.PlotDataItem(x=np.array([i, i]), y=np.array([0, 63]), pen=pg.mkPen((200, 200, 200), width=1))
            self.guide_plot.addItem(line)
            # 水平线
            line = pg.PlotDataItem(x=np.array([0, 63]), y=np.array([i, i]), pen=pg.mkPen((200, 200, 200), width=1))
            self.guide_plot.addItem(line)
    
    def show_guide_window(self):
        """显示引导窗口"""
        if not self.guide_window:
            self.create_guide_window()
        
        if self.guide_window:
            self.guide_window.show()
            self.update_guide_display()
            print("✅ 引导窗口已显示")
    
    def on_guide_window_closed(self, event):
        """引导窗口关闭事件处理"""
        print("🛑 引导窗口已关闭，停止灵敏度测试")
        
        # 如果测试正在进行中，询问用户是否确认停止
        if self.sensitivity_measurement_active:
            reply = QMessageBox.question(
                self, "确认停止测试", 
                "引导窗口已关闭，是否停止当前的灵敏度测试？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.stop_sensitivity_measurement()
            else:
                # 用户选择不停止，重新显示引导窗口
                self.show_guide_window()
                event.ignore()  # 阻止窗口关闭
                return
        
        # 清理引导窗口引用
        self.guide_window = None
        event.accept()
    
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
                        angles = np.linspace(0, 2*np.pi, 50)
                        circle_x = pos['x'] + 8*np.cos(angles)
                        circle_y = pos['y'] + 8*np.sin(angles)
                        circle = pg.PlotDataItem(
                            x=circle_x, y=circle_y,
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
            
            # 检查是否完成所有位置
            if self.current_position_index >= len(self.micro_positions):
                # 停止引导定时器
                if hasattr(self, 'guide_timer') and self.guide_timer.isActive():
                    self.guide_timer.stop()
                    print("🛑 引导定时器已停止（测试完成）")
                
                # 更新状态
                self.sensitivity_status_label.setText("灵敏度测试状态: 测试完成")
                self.sensitivity_status_label.setStyleSheet("color: green; font-weight: bold;")
                
                # 禁用手动控制按钮
                self.next_position_btn.setEnabled(False)
                self.previous_position_btn.setEnabled(False)
                self.record_data_btn.setEnabled(False)
                
                # 停止测试
                self.stop_sensitivity_measurement()
                
                # 显示完成消息
                QMessageBox.information(self, "测试完成", 
                                      f"🎉 所有位置的测试已完成！\n\n"
                                      f"采集数据位置: {len(self.sensitivity_data)} 个\n"
                                      f"总帧数: {self.current_frame}\n\n"
                                      f"现在可以：\n"
                                      f"• 点击'分析局部灵敏度'查看结果\n"
                                      f"• 点击'保存灵敏度结果'保存数据\n"
                                      f"• 点击'绘制灵敏度图表'查看图表")
                return
            else:
                # 提示下一个位置
                next_pos = self.micro_positions[self.current_position_index]
                QMessageBox.information(self, "位置完成", 
                                      f"✅ 位置 {position_id} 测试完成！\n\n"
                                      f"请移动到下一个位置: {next_pos['id']}\n"
                                      f"坐标: ({next_pos['x']}, {next_pos['y']})\n"
                                      f"偏移量: ({next_pos['offset_x']:+d}, {next_pos['offset_y']:+d})")
    
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


if __name__ == "__main__":
    # 测试代码
    import sys
    app = QApplication(sys.argv)
    widget = LocalSensitivityWidget()
    widget.show()
    sys.exit(app.exec_())