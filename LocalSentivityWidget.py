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
        control_layout.addWidget(self.stop_sensitivity_measurement_btn)
        control_layout.addWidget(self.sensitivity_progress_bar)
        control_layout.addWidget(self.sensitivity_status_label)
        control_layout.addStretch()
        
        # 组装灵敏度测试布局
        sensitivity_layout.addLayout(region_selection_layout)
        sensitivity_layout.addLayout(params_layout)
        sensitivity_layout.addLayout(control_layout)
        
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
        
        print(f"✅ 已生成 {len(self.micro_positions)} 个微调位置")
        QMessageBox.information(self, "成功", f"已生成 {len(self.micro_positions)} 个微调位置")
    
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
        self.stop_sensitivity_measurement_btn.setEnabled(False)
        self.generate_positions_btn.setEnabled(True)
        self.sensitivity_progress_bar.setVisible(False)
        
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
                json.dum