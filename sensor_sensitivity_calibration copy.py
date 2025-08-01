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
                            QCheckBox, QGridLayout, QSplitter, QDialog, QMainWindow)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.colors as mcolors
from usb.core import USBError

# 设置matplotlib中文字体支持
def setup_chinese_font():
    """设置matplotlib中文字体支持"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, '测试中文', fontsize=12)
        plt.close(fig)
        print("✅ matplotlib中文字体设置成功")
        return True
    except Exception as e:
        print(f"⚠️ matplotlib中文字体设置失败: {e}")
        return False

# 初始化中文字体
CHINESE_FONT_AVAILABLE = setup_chinese_font()

# 导入数据处理器和USB驱动
try:
    from data_processing.data_handler import DataHandler
    from backends.usb_driver import LargeUsbSensorDriver
    DATA_HANDLER_AVAILABLE = True
    print("✅ 数据处理器模块导入成功")
except ImportError as e:
    print(f"⚠️ 数据处理器未找到: {e}")
    DATA_HANDLER_AVAILABLE = False

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
        self.reset_default_btn.setToolTip("清空所有砝码并重新加载默认砝码")
        
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
        """绘制质量-总压力关系图"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QMessageBox
            
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
            
            # 创建matplotlib图形
            fig = Figure(figsize=(14, 10), dpi=100)
            
            # 创建2x2的子图布局
            ax1 = fig.add_subplot(221)  # 质量-总压力关系
            ax2 = fig.add_subplot(222)  # 质量-敏感性关系
            ax3 = fig.add_subplot(223)  # 压力-敏感性关系
            ax4 = fig.add_subplot(224)  # 变异系数分析
            
            # 1. 质量-总压力关系图
            ax1.scatter(masses, pressures, s=120, alpha=0.8, c='blue', edgecolors='black', linewidth=1.5)
            ax1.plot(masses, pressures, 'r--', alpha=0.8, linewidth=2.5, label='趋势线')
            ax1.set_xlabel('质量 (g)', fontsize=12)
            ax1.set_ylabel('平均总压力', fontsize=12)
            ax1.set_title('质量-总压力关系', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=10)
            
            # 添加数据点标签
            for i, (mass, pressure) in enumerate(zip(masses, pressures)):
                ax1.annotate(f'{mass}g', (mass, pressure), 
                           xytext=(8, 8), textcoords='offset points', 
                           fontsize=10, alpha=0.9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            
            # 2. 质量-敏感性关系图
            ax2.scatter(masses, sensitivities, s=120, alpha=0.8, c='green', edgecolors='black', linewidth=1.5)
            ax2.plot(masses, sensitivities, 'r--', alpha=0.8, linewidth=2.5, label='趋势线')
            ax2.set_xlabel('质量 (g)', fontsize=12)
            ax2.set_ylabel('敏感性(总)', fontsize=12)
            ax2.set_title('质量-敏感性关系', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=10)
            
            # 添加数据点标签
            for i, (mass, sensitivity) in enumerate(zip(masses, sensitivities)):
                ax2.annotate(f'{mass}g', (mass, sensitivity), 
                           xytext=(8, 8), textcoords='offset points', 
                           fontsize=10, alpha=0.9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
            
            # 3. 压力-敏感性关系图
            ax3.scatter(pressures, sensitivities, s=120, alpha=0.8, c='orange', edgecolors='black', linewidth=1.5)
            ax3.set_xlabel('平均总压力', fontsize=12)
            ax3.set_ylabel('敏感性(总)', fontsize=12)
            ax3.set_title('压力-敏感性关系', fontsize=14, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # 添加数据点标签
            for i, (pressure, sensitivity) in enumerate(zip(pressures, sensitivities)):
                ax3.annotate(f'{masses[i]}g', (pressure, sensitivity), 
                           xytext=(8, 8), textcoords='offset points', 
                           fontsize=10, alpha=0.9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
            
            # 4. 变异系数分析图
            colors = ['green' if cv < 0.01 else 'orange' if cv < 0.05 else 'red' for cv in cvs]
            bars = ax4.bar(range(len(masses)), cvs, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
            ax4.set_xlabel('砝码质量', fontsize=12)
            ax4.set_ylabel('变异系数', fontsize=12)
            ax4.set_title('测量稳定性分析', fontsize=14, fontweight='bold')
            ax4.set_xticks(range(len(masses)))
            ax4.set_xticklabels([f'{mass}g' for mass in masses], fontsize=10)
            ax4.grid(True, alpha=0.3)
            
            # 添加阈值线
            ax4.axhline(y=0.01, color='green', linestyle='--', alpha=0.8, linewidth=2, label='优秀 (<1%)')
            ax4.axhline(y=0.05, color='orange', linestyle='--', alpha=0.8, linewidth=2, label='良好 (<5%)')
            ax4.legend(fontsize=10)
            
            # 添加数值标签
            for i, (bar, cv) in enumerate(zip(bars, cvs)):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                        f'{cv:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
            
            # 调整子图间距
            fig.tight_layout(pad=2.0)
            
            # 显示分析结果信息
            info_text = f"""敏感性分析图表已生成！

分析结果:
• 砝码数量: {len(masses)}个
• 总测量次数: {sum(r['measurement_count'] for r in results.values())}
• 质量范围: {min(masses)}g - {max(masses)}g
• 压力范围: {min(pressures):.6f} - {max(pressures):.6f}
• 敏感性范围: {min(sensitivities):.6f} - {max(sensitivities):.6f}

图表包含4个子图:
1. 质量-总压力关系
2. 质量-敏感性关系  
3. 压力-敏感性关系
4. 测量稳定性分析

是否保存图表？"""
            
            # 询问是否保存图表
            msg = QMessageBox(self)
            msg.setWindowTitle("敏感性分析完成")
            msg.setText(info_text)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.button(QMessageBox.Yes).setText("保存图表")
            msg.button(QMessageBox.No).setText("不保存")
            
            if msg.exec_() == QMessageBox.Yes:
                self.save_plot(fig)
            
            print("✅ 质量-压力关系图已生成")
            
        except Exception as e:
            print(f"❌ 绘制图表失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "警告", f"绘制图表失败: {e}")
    
    def save_plot(self, fig):
        """保存图表"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存图表", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
                "PNG图片 (*.png);;JPG图片 (*.jpg);;PDF文件 (*.pdf);;SVG文件 (*.svg)"
            )
            
            if filename:
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图表已保存到: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存图表失败: {e}")
    
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
        
        # 设置窗口属性
        self.setWindowTitle("传感器敏感性标定系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据处理器
        self.init_data_handler()
        
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
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.port_input)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.calibration_status_label)
        control_layout.addWidget(self.measurement_status_label)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        
        # 热力图显示区域
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 初始化热力图和颜色条
        self.heatmap = None
        self.colorbar = None
        
        # 添加matplotlib工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 数据信息显示
        info_layout = QHBoxLayout()
        self.max_value_label = QLabel("最大值: --")
        self.min_value_label = QLabel("最小值: --")
        self.mean_value_label = QLabel("平均值: --")
        self.total_pressure_label = QLabel("总压力: --")
        self.sensor_info_label = QLabel("传感器: --")
        
        info_layout.addWidget(self.sensor_info_label)
        info_layout.addWidget(self.max_value_label)
        info_layout.addWidget(self.min_value_label)
        info_layout.addWidget(self.mean_value_label)
        info_layout.addWidget(self.total_pressure_label)
        info_layout.addStretch()
        
        # 组装左侧面板
        left_panel.addLayout(control_layout)
        left_panel.addWidget(self.toolbar)
        left_panel.addWidget(self.canvas)
        left_panel.addLayout(info_layout)
        
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

        
        right_panel.addWidget(self.function_tabs)
        
        # 组装主布局
        main_layout.addLayout(left_panel, 2)   # 左侧占2/3
        main_layout.addLayout(right_panel, 1)  # 右侧占1/3
        
        self.setLayout(main_layout)
        
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
    
    def init_data_handler(self):
        """初始化数据处理器"""
        if DATA_HANDLER_AVAILABLE:
            try:
                sensor_id = int(self.sensor_combo.currentText())
                self.data_handler = DataHandler(LargeUsbSensorDriver, max_len=256)
                print(f"✅ 数据处理器初始化成功，传感器ID: {sensor_id}")
            except Exception as e:
                print(f"⚠️ 数据处理器初始化失败: {e}")
                self.data_handler = None
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
                    f"测量: {self.current_weight_id} ({self.current_measurement}/{self.measurement_count})"
                )
                
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
                
            # 固定数值范围为0-0.01
            min_val = 0.0
            max_val = 0.01
            
            # 如果热力图已存在，直接更新数据
            if self.heatmap is not None:
                self.heatmap.set_array(data)
                self.heatmap.set_clim(min_val, max_val)
            else:
                # 第一次创建热力图
                self.heatmap = self.ax.imshow(data, cmap='viridis', aspect='auto', 
                                            vmin=min_val, vmax=max_val, origin='lower')
                
                # 添加颜色条
                self.colorbar = self.figure.colorbar(self.heatmap, ax=self.ax, 
                                                   orientation='vertical', 
                                                   shrink=0.8, aspect=20)
                
                # 设置颜色条标签
                self.colorbar.set_label('压力值 (0-0.01)', fontsize=10)
                
                # 设置坐标轴
                self.ax.set_xlabel('X轴')
                self.ax.set_ylabel('Y轴')
                self.ax.set_title('传感器数据热力图')
                
                # 添加网格
                self.ax.grid(True, alpha=0.3)
            
            # 更新画布
            
            # 清除之前的引导位置圆圈
            for artist in self.ax.get_children():
                if hasattr(artist, 'get_label') and artist.get_label() == 'guide_position':
                    artist.remove()
            
            # 添加引导位置圆圈
            self.draw_guide_positions()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 更新热力图时出错: {e}")
    
    def update_data_info(self, data):
        """更新数据信息显示"""
        try:
            if data is not None and data.size > 0:
                self.max_value_label.setText(f"最大值: {data.max():.4f}")
                self.min_value_label.setText(f"最小值: {data.min():.4f}")
                self.mean_value_label.setText(f"平均值: {data.mean():.4f}")
                
                # 计算总压力
                total_pressure = np.sum(data)
                self.total_pressure_label.setText(f"总压力: {total_pressure:.6f}")
                
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
        
        print(f"🔍 尝试连接传感器 {sensor_id}，端口: {port}")
        
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
                    self.sensor_info_label.setText(f"传感器: {sensor_id}")
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
            self.sensor_info_label.setText(f"传感器: {sensor_id} (模拟)")
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
        self.sensor_info_label.setText("传感器: --")
        self.update_status_bar()
    
    def update_ui_state(self):
        """更新UI状态"""
        self.start_button.setEnabled(not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.sensor_combo.setEnabled(not self.is_running)
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
        """在热力图上绘制引导位置圆圈"""
        try:
            # 获取位置一致性分析组件的引导位置
            if hasattr(self, 'position_consistency_widget') and self.position_consistency_widget:
                guide_positions = self.position_consistency_widget.guide_positions
                
                # 定义颜色和样式
                colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan']
                color_index = 0
                
                for pos_id, pos_info in guide_positions.items():
                    x, y = pos_info['x'], pos_info['y']
                    name = pos_info['name']
                    
                    # 选择颜色
                    color = colors[color_index % len(colors)]
                    color_index += 1
                    
                    # 绘制圆圈
                    circle = plt.Circle((x, y), radius=2, color=color, fill=False, 
                                      linewidth=2, label='guide_position')
                    self.ax.add_patch(circle)
                    
                    # 添加位置标签
                    self.ax.text(x + 3, y + 3, name, fontsize=8, color=color, 
                               weight='bold', ha='left', va='bottom',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
                    
                    # 添加位置ID标签
                    self.ax.text(x + 3, y - 3, f"({pos_id})", fontsize=7, color=color,
                               ha='left', va='top')
                
                print(f"✅ 已绘制 {len(guide_positions)} 个引导位置圆圈")
                
        except Exception as e:
            print(f"⚠️ 绘制引导位置圆圈时出错: {e}")
    
    def update_guide_positions(self):
        """更新引导位置显示"""
        try:
            # 重新绘制引导位置
            self.draw_guide_positions()
            # 更新画布
            self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 更新引导位置显示时出错: {e}")
    
    
    def update_position_consistency_weights(self):
        """更新位置一致性分析的砝码选择"""
        try:
            if hasattr(self, 'sensitivity_widget') and self.sensitivity_widget:
                if hasattr(self, 'position_consistency_widget') and self.position_consistency_widget:
                    self.position_consistency_widget.update_weight_selection_for_consistency(
                        self.sensitivity_widget.weight_calibration.weights
                    )
                    print("✅ 位置一致性分析砝码选择已更新")
        except Exception as e:
            print(f"⚠️ 更新位置一致性分析砝码选择时出错: {e}")
    
class SensitivityAnalysisWidget(QWidget):
    """敏感性分析组件 - 新增"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 分析控制组
        control_group = QGroupBox("敏感性分析")
        control_layout = QHBoxLayout()
        
        self.load_analysis_data_btn = QPushButton("加载分析数据")
        self.load_analysis_data_btn.clicked.connect(self.load_analysis_data)
        
        self.generate_report_btn = QPushButton("生成分析报告")
        self.generate_report_btn.clicked.connect(self.generate_analysis_report)
        self.generate_report_btn.setEnabled(False)
        
        self.plot_sensitivity_btn = QPushButton("绘制敏感性曲线")
        self.plot_sensitivity_btn.clicked.connect(self.plot_sensitivity_curves)
        self.plot_sensitivity_btn.setEnabled(False)
        
        control_layout.addWidget(self.load_analysis_data_btn)
        control_layout.addWidget(self.generate_report_btn)
        control_layout.addWidget(self.plot_sensitivity_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        
        # 分析结果显示
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        
        results_layout.addWidget(self.analysis_text)
        results_group.setLayout(results_layout)
        
        # 组装布局
        layout.addWidget(control_group)
        layout.addWidget(results_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def load_analysis_data(self):
        """加载分析数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择分析数据文件", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.analysis_data = json.load(f)
                
                self.generate_report_btn.setEnabled(True)
                self.plot_sensitivity_btn.setEnabled(True)
                
                # 显示基本信息
                self.display_basic_info()
                
                QMessageBox.information(self, "成功", "分析数据加载成功")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载分析数据失败: {e}")
    
    def display_basic_info(self):
        """显示基本信息"""
        if not self.analysis_data:
            return
        
        info_text = f"""
敏感性标定数据分析
生成时间: {self.analysis_data.get('timestamp', '未知')}
校准文件: {self.analysis_data.get('calibration_file', '未知')}

砝码数量: {len(self.analysis_data.get('weights', {}))}
测量数据: {len(self.analysis_data.get('measurements', {}))}
标定结果: {len(self.analysis_data.get('results', {}))}

===== 砝码信息 =====
"""
        
        for weight_id, weight_info in self.analysis_data.get('weights', {}).items():
            info_text += f"{weight_id}: {weight_info['mass']}{weight_info['unit']} (力: {weight_info['force']:.4f}N)\n"
        
        self.analysis_text.setText(info_text)
    
    def generate_analysis_report(self):
        """生成分析报告"""
        if not self.analysis_data:
            QMessageBox.warning(self, "警告", "请先加载分析数据")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存分析报告", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", "文本文件 (*.txt);;HTML文件 (*.html)"
        )
        
        if filename:
            try:
                if filename.endswith('.html'):
                    self.generate_html_report(filename)
                else:
                    self.generate_text_report(filename)
                
                QMessageBox.information(self, "成功", f"分析报告已保存到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成报告失败: {e}")
    
    def generate_text_report(self, filename):
        """生成文本报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器敏感性标定分析报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始数据文件: {self.analysis_data.get('calibration_file', '未知')}\n")
            f.write(f"数据生成时间: {self.analysis_data.get('timestamp', '未知')}\n\n")
            
            # 整体敏感性分析
            overall = self.analysis_data.get('overall_sensitivity', {})
            if overall:
                f.write("===== 整体敏感性分析 =====\n")
                f.write(f"平均敏感性(总压力): {overall.get('avg_sensitivity_total', 0):.6f} ± {overall.get('std_sensitivity_total', 0):.6f}\n")
                f.write(f"平均敏感性(平均压力): {overall.get('avg_sensitivity_mean', 0):.6f} ± {overall.get('std_sensitivity_mean', 0):.6f}\n")
                f.write(f"平均敏感性(最大压力): {overall.get('avg_sensitivity_max', 0):.6f} ± {overall.get('std_sensitivity_max', 0):.6f}\n\n")
            
            # 详细结果分析
            f.write("===== 详细标定结果 =====\n")
            for weight_id, result in self.analysis_data.get('results', {}).items():
                f.write(f"\n砝码 {weight_id}:\n")
                f.write(f"  质量: {result['weight_info']['mass']}{result['weight_info']['unit']}\n")
                f.write(f"  测量次数: {result['measurement_count']}\n")
                f.write(f"  平均总压力: {result['avg_total_pressure']:.6f}\n")
                f.write(f"  标准差: {result['std_total_pressure']:.6f}\n")
                f.write(f"  敏感性(总): {result['sensitivity_total']:.6f}\n")
                f.write(f"  敏感性(平均): {result['sensitivity_mean']:.6f}\n")
                f.write(f"  变异系数: {result['cv']:.3f}\n")
            
            # 质量评估
            f.write("\n===== 质量评估 =====\n")
            if overall:
                cv_values = [r['cv'] for r in self.analysis_data.get('results', {}).values()]
                avg_cv = np.mean(cv_values)
                f.write(f"平均变异系数: {avg_cv:.3f}\n")
                
                if avg_cv < 0.1:
                    f.write("评估结果: 优秀 - 传感器一致性很好\n")
                elif avg_cv < 0.2:
                    f.write("评估结果: 良好 - 传感器一致性较好\n")
                elif avg_cv < 0.3:
                    f.write("评估结果: 一般 - 传感器一致性中等\n")
                else:
                    f.write("评估结果: 较差 - 传感器一致性需要改进\n")
    
    def generate_html_report(self, filename):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>传感器敏感性标定分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .poor {{ color: red; }}
    </style>
</head>
<body>
    <h1>传感器敏感性标定分析报告</h1>
    <p><strong>报告生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>原始数据文件:</strong> {self.analysis_data.get('calibration_file', '未知')}</p>
    <p><strong>数据生成时间:</strong> {self.analysis_data.get('timestamp', '未知')}</p>
    
    <h2>整体敏感性分析</h2>
"""
        
        overall = self.analysis_data.get('overall_sensitivity', {})
        if overall:
            html_content += f"""
    <table>
        <tr><th>指标</th><th>数值</th></tr>
        <tr><td>平均敏感性(总压力)</td><td>{overall.get('avg_sensitivity_total', 0):.6f} ± {overall.get('std_sensitivity_total', 0):.6f}</td></tr>
        <tr><td>平均敏感性(平均压力)</td><td>{overall.get('avg_sensitivity_mean', 0):.6f} ± {overall.get('std_sensitivity_mean', 0):.6f}</td></tr>
        <tr><td>平均敏感性(最大压力)</td><td>{overall.get('avg_sensitivity_max', 0):.6f} ± {overall.get('std_sensitivity_max', 0):.6f}</td></tr>
    </table>
"""
        
        html_content += """
    <h2>详细标定结果</h2>
    <table>
        <tr>
            <th>砝码ID</th>
            <th>质量</th>
            <th>测量次数</th>
            <th>平均总压力</th>
            <th>标准差</th>
            <th>敏感性(总)</th>
            <th>变异系数</th>
        </tr>
"""
        
        for weight_id, result in self.analysis_data.get('results', {}).items():
            cv_class = "good" if result['cv'] < 0.1 else "warning" if result['cv'] < 0.2 else "poor"
            html_content += f"""
        <tr>
            <td>{weight_id}</td>
            <td>{result['weight_info']['mass']}{result['weight_info']['unit']}</td>
            <td>{result['measurement_count']}</td>
            <td>{result['avg_total_pressure']:.6f}</td>
            <td>{result['std_total_pressure']:.6f}</td>
            <td>{result['sensitivity_total']:.6f}</td>
            <td class="{cv_class}">{result['cv']:.3f}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def plot_sensitivity_curves(self):
        """绘制敏感性曲线"""
        if not self.analysis_data:
            QMessageBox.warning(self, "警告", "请先加载分析数据")
            return
        
        try:
            # 创建图形
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            results = self.analysis_data.get('results', {})
            if not results:
                QMessageBox.warning(self, "警告", "没有标定结果数据")
                return
            
            # 准备数据
            weights = []
            masses = []
            sensitivities_total = []
            sensitivities_mean = []
            cvs = []
            
            for weight_id, result in results.items():
                weights.append(weight_id)
                masses.append(result['weight_info']['mass'])
                sensitivities_total.append(result['sensitivity_total'])
                sensitivities_mean.append(result['sensitivity_mean'])
                cvs.append(result['cv'])
            
            # 1. 敏感性 vs 质量
            ax1.plot(masses, sensitivities_total, 'bo-', label='总压力敏感性')
            ax1.plot(masses, sensitivities_mean, 'ro-', label='平均压力敏感性')
            ax1.set_xlabel('质量 (g)')
            ax1.set_ylabel('敏感性')
            ax1.set_title('敏感性 vs 质量')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 变异系数 vs 质量
            ax2.plot(masses, cvs, 'go-')
            ax2.set_xlabel('质量 (g)')
            ax2.set_ylabel('变异系数')
            ax2.set_title('变异系数 vs 质量')
            ax2.grid(True, alpha=0.3)
            
            # 3. 压力 vs 质量
            pressures = [result['avg_total_pressure'] for result in results.values()]
            ax3.plot(masses, pressures, 'mo-')
            ax3.set_xlabel('质量 (g)')
            ax3.set_ylabel('平均总压力')
            ax3.set_title('压力 vs 质量')
            ax3.grid(True, alpha=0.3)
            
            # 4. 敏感性分布直方图
            ax4.hist(sensitivities_total, bins=len(sensitivities_total), alpha=0.7, color='skyblue', edgecolor='black')
            ax4.set_xlabel('敏感性')
            ax4.set_ylabel('频次')
            ax4.set_title('敏感性分布')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图片
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存敏感性曲线图", "", "PNG图片 (*.png);;JPG图片 (*.jpg);;PDF文件 (*.pdf)"
            )
            
            if filename:
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"敏感性曲线图已保存到: {filename}")
            
            plt.show()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制敏感性曲线失败: {e}")
class PositionConsistencyWidget(QWidget):
    """位置一致性分析组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 位置一致性分析相关属性
        self.guide_positions = {}  # 存储引导位置 {position_id: {x, y, name, description}}
        self.position_measurements = {}  # 存储位置测量数据 {position_id: {weight_id: [measurements]}}
        # 位置数据存储
        self.position_data = {}  # 存储每个位置的数据
        self.current_weight_id = None
        self.measurement_count = 0
        self.consistency_results = {}  # 存储一致性分析结果
        self.current_position_id = None
        self.position_measurement_active = False
        
        # 初始化UI
        self.init_ui()
        
        # 加载默认引导位置
        self.load_default_positions()
        
        print("✅ 位置一致性分析组件初始化完成")
    
    def load_default_positions(self):
        """加载默认引导位置"""
        default_positions = [
            {"id": "center", "name": "中心位置", "x": 32, "y": 32, "description": "传感器中心位置"},
            {"id": "top_left", "name": "左上角", "x": 16, "y": 16, "description": "左上角位置"},
            {"id": "top_right", "name": "右上角", "x": 48, "y": 16, "description": "右上角位置"},
            {"id": "bottom_left", "name": "左下角", "x": 16, "y": 48, "description": "左下角位置"},
            {"id": "bottom_right", "name": "右下角", "x": 48, "y": 48, "description": "右下角位置"},
            {"id": "top_center", "name": "上中位置", "x": 32, "y": 16, "description": "上中位置"},
            {"id": "bottom_center", "name": "下中位置", "x": 32, "y": 48, "description": "下中位置"},
            {"id": "left_center", "name": "左中位置", "x": 16, "y": 32, "description": "左中位置"},
            {"id": "right_center", "name": "右中位置", "x": 48, "y": 32, "description": "右中位置"}
        ]
        
        for pos in default_positions:
            self.guide_positions[pos["id"]] = {
                "name": pos["name"],
                "x": pos["x"],
                "y": pos["y"],
                "description": pos["description"]
            }
            self.position_measurements[pos["id"]] = {}
        
        # 更新UI显示
        self.update_position_table()
        self.update_position_selection()
        
        print(f"✅ 已加载 {len(default_positions)} 个默认引导位置")
        
        # 通知主界面更新引导位置显示
        if hasattr(self.parent(), 'update_guide_positions'):
            self.parent().update_guide_positions()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 引导位置管理组
        position_group = QGroupBox("引导位置管理")
        position_layout = QGridLayout()
        
        self.position_id_input = QLineEdit()
        self.position_id_input.setPlaceholderText("位置ID (如: pos1, center)")
        
        self.position_name_input = QLineEdit()
        self.position_name_input.setPlaceholderText("位置名称 (如: 中心位置)")
        
        self.position_x_input = QSpinBox()
        self.position_x_input.setRange(0, 63)
        self.position_x_input.setValue(32)
        self.position_x_input.setSuffix(" X")
        
        self.position_y_input = QSpinBox()
        self.position_y_input.setRange(0, 63)
        self.position_y_input.setValue(32)
        self.position_y_input.setSuffix(" Y")
        
        self.position_desc_input = QLineEdit()
        self.position_desc_input.setPlaceholderText("位置描述")
        
        self.add_position_btn = QPushButton("添加位置")
        self.add_position_btn.clicked.connect(self.add_guide_position)
        
        # 组装位置管理布局
        position_layout.addWidget(QLabel("位置ID:"), 0, 0)
        position_layout.addWidget(self.position_id_input, 0, 1)
        position_layout.addWidget(QLabel("位置名称:"), 0, 2)
        position_layout.addWidget(self.position_name_input, 0, 3)
        position_layout.addWidget(QLabel("X坐标:"), 1, 0)
        position_layout.addWidget(self.position_x_input, 1, 1)
        position_layout.addWidget(QLabel("Y坐标:"), 1, 2)
        position_layout.addWidget(self.position_y_input, 1, 3)
        position_layout.addWidget(QLabel("描述:"), 2, 0)
        position_layout.addWidget(self.position_desc_input, 2, 1, 1, 3)
        position_layout.addWidget(self.add_position_btn, 3, 0, 1, 4)
        
        # 重置和自定义默认位置按钮
        self.reset_positions_btn = QPushButton("重置默认位置")
        self.reset_positions_btn.clicked.connect(self.reset_default_positions)
        self.reset_positions_btn.setToolTip("清空所有位置并重新加载默认位置")
        
        self.custom_positions_btn = QPushButton("自定义位置")
        self.custom_positions_btn.clicked.connect(self.customize_positions)
        self.custom_positions_btn.setToolTip("自定义引导位置列表")
        
        position_layout.addWidget(self.reset_positions_btn, 4, 0, 1, 2)
        position_layout.addWidget(self.custom_positions_btn, 4, 2, 1, 2)
        
        position_group.setLayout(position_layout)
        
        # 位置表格
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels(["位置ID", "名称", "X坐标", "Y坐标", "描述"])
        self.position_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.position_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 位置一致性测试组
        consistency_group = QGroupBox("位置一致性测试")
        consistency_layout = QVBoxLayout()
        
        # 位置选择
        position_selection_layout = QHBoxLayout()
        self.position_selection_label = QLabel("选择测试位置:")
        self.position_combo = QComboBox()
        self.position_combo.setMinimumWidth(150)
        
        position_selection_layout.addWidget(self.position_selection_label)
        position_selection_layout.addWidget(self.position_combo)
        position_selection_layout.addStretch()
        
        # 砝码选择
        weight_selection_layout = QHBoxLayout()
        self.consistency_weight_label = QLabel("选择测试砝码:")
        self.consistency_weight_combo = QComboBox()
        self.consistency_weight_combo.setMinimumWidth(150)
        
        weight_selection_layout.addWidget(self.consistency_weight_label)
        weight_selection_layout.addWidget(self.consistency_weight_combo)
        weight_selection_layout.addStretch()
        
        # 测量控制
        measurement_control_layout = QGridLayout()
        
        self.position_measurement_count_input = QSpinBox()
        self.position_measurement_count_input.setRange(1, 1000)
        self.position_measurement_count_input.setValue(10)
        
        self.start_position_measurement_btn = QPushButton("开始位置测试")
        self.start_position_measurement_btn.clicked.connect(self.start_position_measurement)
        
        self.stop_position_measurement_btn = QPushButton("停止位置测试")
        self.stop_position_measurement_btn.clicked.connect(self.stop_position_measurement)
        self.stop_position_measurement_btn.setEnabled(False)
        
        self.position_progress_bar = QProgressBar()
        self.position_progress_bar.setVisible(False)
        
        # 位置测量状态显示
        self.position_measurement_status_label = QLabel("位置测试状态: 未开始")
        self.position_measurement_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 组装测量控制布局
        measurement_control_layout.addWidget(QLabel("测量次数:"), 0, 0)
        measurement_control_layout.addWidget(self.position_measurement_count_input, 0, 1)
        measurement_control_layout.addWidget(self.start_position_measurement_btn, 0, 2)
        measurement_control_layout.addWidget(self.stop_position_measurement_btn, 0, 3)
        measurement_control_layout.addWidget(self.position_progress_bar, 1, 0, 1, 4)
        measurement_control_layout.addWidget(self.position_measurement_status_label, 2, 0, 1, 4)
        
        # 组装一致性测试布局
        consistency_layout.addLayout(position_selection_layout)
        consistency_layout.addLayout(weight_selection_layout)
        consistency_layout.addLayout(measurement_control_layout)
        
        consistency_group.setLayout(consistency_layout)
        
        # 位置一致性结果显示组
        consistency_results_group = QGroupBox("位置一致性结果")
        consistency_results_layout = QVBoxLayout()
        
        self.consistency_results_table = QTableWidget()
        self.consistency_results_table.setColumnCount(7)
        self.consistency_results_table.setHorizontalHeaderLabels([
            "位置ID", "位置名称", "砝码ID", "测量次数", "平均总压力", "标准差", "变异系数"
        ])
        
        self.calculate_consistency_btn = QPushButton("计算位置一致性")
        self.calculate_consistency_btn.clicked.connect(self.calculate_position_consistency)
        
        self.save_consistency_results_btn = QPushButton("保存一致性结果")
        self.save_consistency_results_btn.clicked.connect(self.save_consistency_results)
        
        self.plot_consistency_btn = QPushButton("绘制一致性图表")
        self.plot_consistency_btn.clicked.connect(self.plot_consistency_analysis)
        
        consistency_results_layout.addWidget(self.consistency_results_table)
        
        results_buttons_layout = QHBoxLayout()
        results_buttons_layout.addWidget(self.calculate_consistency_btn)
        results_buttons_layout.addWidget(self.save_consistency_results_btn)
        results_buttons_layout.addWidget(self.plot_consistency_btn)
        results_buttons_layout.addStretch()
        
        consistency_results_layout.addLayout(results_buttons_layout)
        consistency_results_group.setLayout(consistency_results_layout)
        
        # 组装主布局
        layout.addWidget(position_group)
        layout.addWidget(self.position_table)
        layout.addWidget(consistency_group)
        layout.addWidget(consistency_results_group)
        
        self.setLayout(layout)
        
        # 更新位置选择下拉框
        self.update_position_selection()
    
    def add_guide_position(self):
        """添加引导位置"""
        position_id = self.position_id_input.text().strip()
        position_name = self.position_name_input.text().strip()
        x = self.position_x_input.value()
        y = self.position_y_input.value()
        description = self.position_desc_input.text().strip()
        
        if not position_id:
            QMessageBox.warning(self, "警告", "请输入位置ID")
            return
        
        if not position_name:
            QMessageBox.warning(self, "警告", "请输入位置名称")
            return
        
        # 检查位置ID是否已存在
        if position_id in self.guide_positions:
            QMessageBox.warning(self, "警告", f"位置ID '{position_id}' 已存在")
            return
        
        # 检查坐标是否在有效范围内
        if x < 0 or x > 63 or y < 0 or y > 63:
            QMessageBox.warning(self, "警告", "坐标必须在0-63范围内")
            return
        
        # 添加引导位置
        self.guide_positions[position_id] = {
            "name": position_name,
            "x": x,
            "y": y,
            "description": description
        }
        self.position_measurements[position_id] = {}
        
        # 清空输入框
        self.position_id_input.clear()
        self.position_name_input.clear()
        self.position_x_input.setValue(32)
        self.position_y_input.setValue(32)
        self.position_desc_input.clear()
        
        # 更新显示
        self.update_position_table()
        self.update_position_selection()
        
        print(f"✅ 添加引导位置: {position_id} - {position_name} ({x}, {y})")
    
    def reset_default_positions(self):
        """重置为默认位置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置为默认引导位置吗？\n这将清除所有当前位置并加载默认的9个位置。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空当前位置
            self.guide_positions.clear()
            self.position_measurements.clear()
            
            # 重新加载默认位置
            self.load_default_positions()
            
            # 清空结果表格
            self.consistency_results_table.setRowCount(0)
            
            QMessageBox.information(self, "成功", "已重置为默认引导位置")
            print("✅ 已重置为默认引导位置")
        
        # 通知主界面更新引导位置显示
        if hasattr(self.parent(), 'update_guide_positions'):
            self.parent().update_guide_positions()
    
    def customize_positions(self):
        """自定义引导位置"""
        try:
            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("自定义引导位置")
            dialog.setModal(True)
            dialog.resize(600, 500)
            
            layout = QVBoxLayout()
            
            # 说明文本
            info_label = QLabel("请输入自定义的引导位置列表，每行一个位置，格式：ID,名称,X坐标,Y坐标,描述")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # 当前默认位置显示
            current_label = QLabel("当前默认位置:")
            layout.addWidget(current_label)
            
            current_text = QTextEdit()
            current_text.setMaximumHeight(150)
            current_text.setPlainText("center,中心位置,32,32,传感器中心位置\ntop_left,左上角,16,16,左上角位置\ntop_right,右上角,48,16,右上角位置\nbottom_left,左下角,16,48,左下角位置\nbottom_right,右下角,48,48,右下角位置\ntop_center,上中位置,32,16,上中位置\nbottom_center,下中位置,32,48,下中位置\nleft_center,左中位置,16,32,左中位置\nright_center,右中位置,48,32,右中位置")
            current_text.setReadOnly(True)
            layout.addWidget(current_text)
            
            # 自定义输入
            custom_label = QLabel("自定义位置列表:")
            layout.addWidget(custom_label)
            
            custom_text = QTextEdit()
            custom_text.setMaximumHeight(200)
            custom_text.setPlaceholderText("请输入自定义位置，格式：ID,名称,X坐标,Y坐标,描述\n例如：\npos1,测试位置1,20,20,第一个测试位置\npos2,测试位置2,40,40,第二个测试位置")
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
                    # 解析自定义位置
                    custom_positions = []
                    lines = custom_text_content.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            parts = line.split(',')
                            if len(parts) >= 5:
                                position_id = parts[0].strip()
                                position_name = parts[1].strip()
                                try:
                                    x = int(parts[2].strip())
                                    y = int(parts[3].strip())
                                    description = parts[4].strip()
                                    
                                    if x < 0 or x > 63 or y < 0 or y > 63:
                                        QMessageBox.warning(self, "错误", f"无效的坐标值: ({x}, {y})")
                                        return
                                    
                                    custom_positions.append({
                                        "id": position_id,
                                        "name": position_name,
                                        "x": x,
                                        "y": y,
                                        "description": description
                                    })
                                except ValueError:
                                    QMessageBox.warning(self, "错误", f"无效的坐标值: {parts[2]}, {parts[3]}")
                                    return
                    
                    if custom_positions:
                        # 清空当前位置
                        self.guide_positions.clear()
                        self.position_measurements.clear()
                        
                        # 添加自定义位置
                        for pos in custom_positions:
                            self.guide_positions[pos["id"]] = {
                                "name": pos["name"],
                                "x": pos["x"],
                                "y": pos["y"],
                                "description": pos["description"]
                            }
                            self.position_measurements[pos["id"]] = {}
                        
                        # 更新显示
                        self.update_position_table()
                        self.update_position_selection()
                        
                        # 清空结果表格
                        self.consistency_results_table.setRowCount(0)
                        
                        QMessageBox.information(self, "成功", f"已设置 {len(custom_positions)} 个自定义引导位置")
                        print(f"✅ 已设置 {len(custom_positions)} 个自定义引导位置")
                    else:
                        QMessageBox.warning(self, "警告", "没有有效的位置数据")
                else:
                    QMessageBox.warning(self, "警告", "请输入位置数据")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"自定义引导位置失败: {e}")
            print(f"❌ 自定义引导位置失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_position_table(self):
        """更新位置表格"""
        self.position_table.setRowCount(len(self.guide_positions))
        
        for row, (position_id, position_info) in enumerate(self.guide_positions.items()):
            self.position_table.setItem(row, 0, QTableWidgetItem(position_id))
            self.position_table.setItem(row, 1, QTableWidgetItem(position_info['name']))
            self.position_table.setItem(row, 2, QTableWidgetItem(str(position_info['x'])))
            self.position_table.setItem(row, 3, QTableWidgetItem(str(position_info['y'])))
            self.position_table.setItem(row, 4, QTableWidgetItem(position_info['description']))
    
    def update_position_selection(self):
        """更新位置选择下拉框"""
        self.position_combo.clear()
        self.position_combo.addItem("选择位置")
        
        for position_id in self.guide_positions.keys():
            self.position_combo.addItem(position_id)
    
    def update_weight_selection_for_consistency(self, weights):
        """更新一致性测试的砝码选择下拉框"""
        self.consistency_weight_combo.clear()
        self.consistency_weight_combo.addItem("选择砝码")
        
        for weight_id in weights.keys():
            self.consistency_weight_combo.addItem(weight_id)
    
    def start_position_measurement(self):
        """开始位置测量"""
        if self.position_combo.currentText() == "选择位置":
            QMessageBox.warning(self, "警告", "请选择测试位置")
            return
        
        if self.consistency_weight_combo.currentText() == "选择砝码":
            QMessageBox.warning(self, "警告", "请选择测试砝码")
            return
        
        # 检查校准数据
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if main_interface and hasattr(main_interface, 'calibration_map'):
            if main_interface.calibration_map is None:
                QMessageBox.warning(self, "警告", "请先加载校准数据")
                return
        
        # 检查传感器连接状态
        if main_interface and hasattr(main_interface, 'is_running'):
            if not main_interface.is_running:
                QMessageBox.warning(self, "警告", "请先启动传感器")
                return
        
        self.current_position_id = self.position_combo.currentText()
        self.current_weight_id = self.consistency_weight_combo.currentText()
        self.measurement_count = self.position_measurement_count_input.value()
        self.position_measurement_active = True
        
        print(f"🚀 开始位置测量: 位置={self.current_position_id}, 砝码={self.current_weight_id}, 次数={self.measurement_count}")
        
        self.start_position_measurement_btn.setEnabled(False)
        self.stop_position_measurement_btn.setEnabled(True)
        self.position_progress_bar.setVisible(True)
        self.position_progress_bar.setMaximum(self.measurement_count)
        self.position_progress_bar.setValue(0)
        
        # 通知主界面开始位置测量
        if main_interface and hasattr(main_interface, 'start_position_consistency_measurement'):
            main_interface.start_position_consistency_measurement(
                self.current_position_id, 
                self.current_weight_id, 
                self.measurement_count
            )
            print(f"✅ 已通知主界面开始位置测量")
    
    def stop_position_measurement(self):
        """停止位置测量"""
        self.position_measurement_active = False
        self.start_position_measurement_btn.setEnabled(True)
        self.stop_position_measurement_btn.setEnabled(False)
        self.position_progress_bar.setVisible(False)
        
        # 通知主界面停止位置测量
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if main_interface and hasattr(main_interface, 'stop_position_consistency_measurement'):
            main_interface.stop_position_consistency_measurement()
    
    def record_position_measurement_data(self, pressure_data):
        """记录位置测量数据（支持位置区分）"""
        if not self.position_measurement_active or self.current_position_id is None or self.current_weight_id is None:
            return
        
        try:
            # 计算压力数据
            total_pressure = np.sum(pressure_data)
            mean_pressure = np.mean(pressure_data)
            max_pressure = np.max(pressure_data)
            
            # 基线校正（从主界面获取基线数据）
            corrected_total = total_pressure
            corrected_mean = mean_pressure
            corrected_max = max_pressure
            
            parent = self.parent()
            main_interface = None
            
            if parent and hasattr(parent, 'parent'):
                tab_widget = parent.parent()
                if tab_widget and hasattr(tab_widget, 'parent'):
                    main_interface = tab_widget.parent()
            
            if main_interface and hasattr(main_interface, 'sensitivity_widget'):
                weight_calibration = main_interface.sensitivity_widget.weight_calibration
                
                if weight_calibration.baseline_data:
                    baseline_stats = weight_calibration.get_baseline_stats()
                    corrected_total = total_pressure - baseline_stats['avg_total_pressure']
                    corrected_mean = mean_pressure - baseline_stats['avg_mean_pressure']
                    corrected_max = max_pressure - baseline_stats['avg_max_pressure']
            
            # 创建测量记录
            measurement = {
                'timestamp': datetime.now(),
                'position_id': self.current_position_id,
                'weight_id': self.current_weight_id,
                'total_pressure': total_pressure,
                'mean_pressure': mean_pressure,
                'max_pressure': max_pressure,
                'corrected_total_pressure': corrected_total,
                'corrected_mean_pressure': corrected_mean,
                'corrected_max_pressure': corrected_max,
                'raw_data': pressure_data.copy()
            }
            
            # 初始化位置数据存储
            if self.current_position_id not in self.position_data:
                self.position_data[self.current_position_id] = {}
            
            if self.current_weight_id not in self.position_data[self.current_position_id]:
                self.position_data[self.current_position_id][self.current_weight_id] = []
            
            # 存储测量数据
            self.position_data[self.current_position_id][self.current_weight_id].append(measurement)
            
            # 获取当前测量次数
            current_count = len(self.position_data[self.current_position_id][self.current_weight_id])
            print(f"✅ 位置测量记录成功: 位置={self.current_position_id}, 砝码={self.current_weight_id}, 次数={current_count}/{self.measurement_count}")
            self.position_progress_bar.setValue(current_count)
            
            if current_count >= self.measurement_count:
                print(f"✅ 位置测量完成，停止测量")
                self.stop_position_measurement()
                QMessageBox.information(self, "完成", f"位置 {self.current_position_id} 砝码 {self.current_weight_id} 测量完成")
                
        except Exception as e:
            print(f"❌ 记录位置测量数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_position_consistency(self):
        """计算位置一致性（使用位置专用数据）"""
        if not self.position_data:
            QMessageBox.warning(self, "警告", "请先进行位置测量")
            return
        
        # 获取砝码信息
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if not main_interface or not hasattr(main_interface, 'sensitivity_widget'):
            QMessageBox.warning(self, "警告", "无法获取砝码信息")
            return
        
        weight_calibration = main_interface.sensitivity_widget.weight_calibration
        
        # 计算每个位置的一致性
        results = {}
        
        for position_id, position_weights in self.position_data.items():
            position_results = {}
            
            for weight_id, measurements in position_weights.items():
                if not measurements:
                    continue
                
                weight_info = weight_calibration.weights[weight_id]
                force = weight_info['force']
                
                # 使用校正后的数据计算一致性
                total_pressures = [m['corrected_total_pressure'] for m in measurements]
                mean_pressures = [m['corrected_mean_pressure'] for m in measurements]
                max_pressures = [m['corrected_max_pressure'] for m in measurements]
                
                # 计算统计信息
                avg_total_pressure = np.mean(total_pressures)
                std_total_pressure = np.std(total_pressures)
                avg_mean_pressure = np.mean(mean_pressures)
                std_mean_pressure = np.std(mean_pressures)
                avg_max_pressure = np.mean(max_pressures)
                std_max_pressure = np.std(max_pressures)
                
                # 计算变异系数
                cv_total = std_total_pressure / avg_total_pressure if avg_total_pressure > 0 else 0
                cv_mean = std_mean_pressure / avg_mean_pressure if avg_mean_pressure > 0 else 0
                cv_max = std_max_pressure / avg_max_pressure if avg_max_pressure > 0 else 0
                
                position_results[weight_id] = {
                    'weight_info': weight_info,
                    'measurement_count': len(measurements),
                    'avg_total_pressure': avg_total_pressure,
                    'std_total_pressure': std_total_pressure,
                    'avg_mean_pressure': avg_mean_pressure,
                    'std_mean_pressure': std_mean_pressure,
                    'avg_max_pressure': avg_max_pressure,
                    'std_max_pressure': std_max_pressure,
                    'cv': cv_total,  # 使用总压力的变异系数作为主要CV
                    'cv_total': cv_total,
                    'cv_mean': cv_mean,
                    'cv_max': cv_max,
                    'sensitivity_total': avg_total_pressure / force if force > 0 else 0
                }
            
            results[position_id] = position_results
        
        # 更新结果显示
        self.update_consistency_results_table(results)
        
        # 显示分析结果
        self.show_consistency_analysis(results)
        
        print(f"✅ 位置一致性分析完成，共分析 {len(results)} 个位置")
    
    def update_consistency_results_table(self, results):
        """更新一致性结果表格"""
        # 计算总行数
        total_rows = 0
        for position_results in results.values():
            total_rows += len(position_results)
        
        self.consistency_results_table.setRowCount(total_rows)
        
        row = 0
        for position_id, position_results in results.items():
            position_name = self.guide_positions[position_id]['name']
            
            for weight_id, result in position_results.items():
                # 设置表格数据
                self.consistency_results_table.setItem(row, 0, QTableWidgetItem(str(position_id)))
                self.consistency_results_table.setItem(row, 1, QTableWidgetItem(position_name))
                self.consistency_results_table.setItem(row, 2, QTableWidgetItem(str(weight_id)))
                self.consistency_results_table.setItem(row, 3, QTableWidgetItem(str(result['measurement_count'])))
                self.consistency_results_table.setItem(row, 4, QTableWidgetItem(f"{result['avg_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 5, QTableWidgetItem(f"{result['std_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 6, QTableWidgetItem(f"{result['cv']:.3f}"))
                
                row += 1
        
        # 调整表格列宽
        self.consistency_results_table.resizeColumnsToContents()
    
    def show_consistency_analysis(self, results):
        """显示一致性分析结果"""
        if not results:
            return
        
        # 计算整体一致性指标
        all_cvs = []
        all_sensitivities = []
        
        for position_results in results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        analysis_text = f"""位置一致性分析结果:

整体统计:
• 平均变异系数: {avg_cv:.3f} ± {std_cv:.3f}
• 平均敏感性: {avg_sensitivity:.6f} ± {std_sensitivity:.6f}
• 位置间一致性CV: {position_consistency_cv:.3f}

位置数量: {len(results)}
总测量点: {sum(len(pos_results) for pos_results in results.values())}

一致性评估:
"""
        
        if position_consistency_cv < 0.05:
            analysis_text += "• 位置一致性: 优秀 (<5%)\n"
        elif position_consistency_cv < 0.1:
            analysis_text += "• 位置一致性: 良好 (5-10%)\n"
        elif position_consistency_cv < 0.2:
            analysis_text += "• 位置一致性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 位置一致性: 较差 (>20%)\n"
        
        if avg_cv < 0.05:
            analysis_text += "• 测量稳定性: 优秀 (<5%)\n"
        elif avg_cv < 0.1:
            analysis_text += "• 测量稳定性: 良好 (5-10%)\n"
        elif avg_cv < 0.2:
            analysis_text += "• 测量稳定性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 测量稳定性: 较差 (>20%)\n"
        
        QMessageBox.information(self, "位置一致性分析完成", analysis_text)
    
    def save_consistency_results(self):
        """保存一致性结果"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存位置一致性结果", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
            "JSON文件 (*.json);;CSV文件 (*.csv);;文本文件 (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_consistency_results_json(filename)
                elif filename.endswith('.csv'):
                    self.save_consistency_results_csv(filename)
                else:
                    self.save_consistency_results_txt(filename)
                
                QMessageBox.information(self, "成功", f"结果已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_consistency_results_json(self, filename):
        """保存为JSON格式"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'guide_positions': self.guide_positions,
            'consistency_results': self.consistency_results,
            'analysis_summary': self.get_consistency_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_consistency_results_csv(self, filename):
        """保存为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['位置ID', '位置名称', '砝码ID', '测量次数', '平均总压力', '标准差', '变异系数'])
            
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                for weight_id, result in position_results.items():
                    writer.writerow([
                        position_id,
                        position_name,
                        weight_id,
                        result['measurement_count'],
                        f"{result['avg_total_pressure']:.6f}",
                        f"{result['std_total_pressure']:.6f}",
                        f"{result['cv']:.3f}"
                    ])
    
    def save_consistency_results_txt(self, filename):
        """保存为文本格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器位置一致性分析结果\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("===== 引导位置信息 =====\n")
            for position_id, position_info in self.guide_positions.items():
                f.write(f"{position_id}: {position_info['name']} ({position_info['x']}, {position_info['y']}) - {position_info['description']}\n")
            
            f.write("\n===== 一致性分析结果 =====\n")
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                f.write(f"\n位置 {position_id} ({position_name}):\n")
                
                for weight_id, result in position_results.items():
                    f.write(f"  砝码 {weight_id}:\n")
                    f.write(f"    测量次数: {result['measurement_count']}\n")
                    f.write(f"    平均总压力: {result['avg_total_pressure']:.6f}\n")
                    f.write(f"    标准差: {result['std_total_pressure']:.6f}\n")
                    f.write(f"    敏感性(总): {result['sensitivity_total']:.6f}\n")
                    f.write(f"    变异系数: {result['cv']:.3f}\n")
            
            # 添加分析摘要
            summary = self.get_consistency_summary()
            f.write(f"\n===== 分析摘要 =====\n")
            f.write(f"平均变异系数: {summary['avg_cv']:.3f} ± {summary['std_cv']:.3f}\n")
            f.write(f"平均敏感性: {summary['avg_sensitivity']:.6f} ± {summary['std_sensitivity']:.6f}\n")
            f.write(f"位置间一致性CV: {summary['position_consistency_cv']:.3f}\n")
    
    def get_consistency_summary(self):
        """获取一致性分析摘要"""
        if not self.consistency_results:
            return {}
        
        all_cvs = []
        all_sensitivities = []
        
        for position_results in self.consistency_results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in self.consistency_results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        return {
            'avg_cv': avg_cv,
            'std_cv': std_cv,
            'avg_sensitivity': avg_sensitivity,
            'std_sensitivity': std_sensitivity,
            'position_consistency_cv': position_consistency_cv
        }
    
    def plot_consistency_analysis(self):
        """绘制一致性分析图表"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有一致性结果数据")
            return
        
        try:
            # 创建图形
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            # 准备数据
            positions = []
            position_names = []
            avg_sensitivities = []
            avg_cvs = []
            all_sensitivities = []
            
            for position_id, position_results in self.consistency_results.items():
                positions.append(position_id)
                position_names.append(self.guide_positions[position_id]['name'])
                
                position_sensitivities = [result['sensitivity_total'] for result in position_results.values()]
                position_cvs = [result['cv'] for result in position_results.values()]
                
                avg_sensitivities.append(np.mean(position_sensitivities))
                avg_cvs.append(np.mean(position_cvs))
                all_sensitivities.extend(position_sensitivities)
            
            # 1. 位置敏感性对比
            bars1 = ax1.bar(range(len(positions)), avg_sensitivities, alpha=0.8, color='skyblue', edgecolor='black')
            ax1.set_xlabel('位置')
            ax1.set_ylabel('平均敏感性')
            ax1.set_title('各位置平均敏感性对比')
            ax1.set_xticks(range(len(positions)))
            ax1.set_xticklabels(position_names, rotation=45, ha='right')
            ax1.grid(True, alpha=0.3)
            
            # 添加数值标签
            for i, (bar, value) in enumerate(zip(bars1, avg_sensitivities)):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.0001,
                        f'{value:.4f}', ha='center', va='bottom', fontsize=9)
            
            # 2. 位置变异系数对比
            bars2 = ax2.bar(range(len(positions)), avg_cvs, alpha=0.8, color='lightcoral', edgecolor='black')
            ax2.set_xlabel('位置')
            ax2.set_ylabel('平均变异系数')
            ax2.set_title('各位置平均变异系数对比')
            ax2.set_xticks(range(len(positions)))
            ax2.set_xticklabels(position_names, rotation=45, ha='right')
            ax2.grid(True, alpha=0.3)
            
            # 添加数值标签
            for i, (bar, value) in enumerate(zip(bars2, avg_cvs)):
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.001,
                        f'{value:.3f}', ha='center', va='bottom', fontsize=9)
            
            # 3. 敏感性分布直方图
            ax3.hist(all_sensitivities, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            ax3.set_xlabel('敏感性')
            ax3.set_ylabel('频次')
            ax3.set_title('所有位置敏感性分布')
            ax3.grid(True, alpha=0.3)
            
            # 4. 位置一致性热力图
            # 创建位置-砝码矩阵
            position_ids = list(self.consistency_results.keys())
            weight_ids = set()
            for position_results in self.consistency_results.values():
                weight_ids.update(position_results.keys())
            weight_ids = sorted(list(weight_ids))
            
            consistency_matrix = np.zeros((len(position_ids), len(weight_ids)))
            for i, position_id in enumerate(position_ids):
                for j, weight_id in enumerate(weight_ids):
                    if weight_id in self.consistency_results[position_id]:
                        consistency_matrix[i, j] = self.consistency_results[position_id][weight_id]['sensitivity_total']
            
            im = ax4.imshow(consistency_matrix, cmap='viridis', aspect='auto')
            ax4.set_xlabel('砝码')
            ax4.set_ylabel('位置')
            ax4.set_title('位置-砝码敏感性热力图')
            ax4.set_xticks(range(len(weight_ids)))
            ax4.set_xticklabels(weight_ids, rotation=45)
            ax4.set_yticks(range(len(position_ids)))
            ax4.set_yticklabels([self.guide_positions[pid]['name'] for pid in position_ids])
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax4)
            cbar.set_label('敏感性')
            
            # 添加数值标签
            for i in range(len(position_ids)):
                for j in range(len(weight_ids)):
                    if consistency_matrix[i, j] > 0:
                        ax4.text(j, i, f'{consistency_matrix[i, j]:.4f}', 
                               ha='center', va='center', fontsize=8, color='white')
            
            plt.tight_layout()
            
            # 保存图片
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存一致性分析图", "", "PNG图片 (*.png);;JPG图片 (*.jpg);;PDF文件 (*.pdf)"
            )
            
            if filename:
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"一致性分析图已保存到: {filename}")
            
            plt.show()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制一致性分析图失败: {e}")
            print(f"❌ 绘制一致性分析图失败: {e}")
            import traceback
            traceback.print_exc()


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