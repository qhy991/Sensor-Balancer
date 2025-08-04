"""
传感器称重工具
基于传感器压力总和与质量的一次函数关系进行称重
支持归零功能和实时质量显示
"""

import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QMessageBox, QVBoxLayout,
                            QGroupBox, QTextEdit, QFileDialog, QProgressBar, QTabWidget,
                            QGridLayout, QFrame, QLCDNumber, QSlider, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import QTimer, pyqtSignal
import pyqtgraph as pg
from usb.core import USBError
import json
from datetime import datetime
import threading
import time
import csv

# 导入数据处理器和USB驱动
try:
    from data_processing.data_handler import DataHandler
    from backends.usb_driver import LargeUsbSensorDriver
    from interfaces.public.utils import apply_swap
    DATA_HANDLER_AVAILABLE = True
    print("✅ 数据处理器模块导入成功")
except ImportError as e:
    print(f"⚠️ 数据处理器未找到: {e}")
    print("⚠️ 将使用模拟数据模式")
    DATA_HANDLER_AVAILABLE = False

class CalibrationDataLoader:
    """校准数据加载器 - 参考sensor_sensitivity_calibration.py"""
    
    def __init__(self):
        self.calibration_data = None
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
            
            # 支持多种JSON格式
            if 'coefficient' in data and 'bias' in data:
                # 简单格式：系数和偏置
                self.calibration_data = {
                    'coefficient': data['coefficient'],
                    'bias': data['bias'],
                    'zero_pressure': data.get('zero_pressure', 0.0),
                    'is_zeroed': data.get('is_zeroed', False),
                    'timestamp': data.get('timestamp', ''),
                    'description': data.get('description', '')
                }
            elif 'calibration_map' in data:
                # 复杂格式：包含校准映射
                self.calibration_data = {
                    'calibration_map': np.array(data['calibration_map']),
                    'reference_data': np.array(data.get('reference_data', [])),
                    'coefficient': data.get('coefficient', 1.0),
                    'bias': data.get('bias', 0.0),
                    'zero_pressure': data.get('zero_pressure', 0.0),
                    'is_zeroed': data.get('is_zeroed', False),
                    'timestamp': data.get('timestamp', ''),
                    'description': data.get('description', '')
                }
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
            
            # 如果数据是包含字典的numpy数组，提取字典
            if isinstance(data, np.ndarray) and data.dtype == object:
                if len(data) == 1 and isinstance(data[0], dict):
                    data = data[0]
                elif len(data) == 0:
                    raise ValueError("空的NumPy数组")
            
            if isinstance(data, np.ndarray) and data.dtype != object:
                # 纯数值数组，检查是否为校准映射
                filename = os.path.basename(filepath)
                coefficient = 1730.6905  # 默认值
                bias = 126.1741  # 默认值
                
                if data.shape == (64, 64):
                    # 这是64x64的校准映射矩阵，用于传感器一致性校正
                    description = f"传感器校准映射 (从{filename}加载)"
                    print(f"✅ 检测到64x64校准映射矩阵，用于传感器一致性校正")
                    print(f"  映射统计: 均值={np.mean(data):.6f}, 标准差={np.std(data):.6f}")
                    print(f"  映射范围: [{np.min(data):.6f}, {np.max(data):.6f}]")
                else:
                    # 其他形状的数组
                    description = f"校准映射数据 (从{filename}加载)"
                    print(f"⚠️ 检测到形状为{data.shape}的校准映射数据")
                
                self.calibration_data = {
                    'calibration_map': data,
                    'coefficient': coefficient,
                    'bias': bias,
                    'zero_pressure': 0.0,
                    'is_zeroed': False,
                    'timestamp': datetime.now().isoformat(),
                    'description': description,
                    'is_calibration_map_only': True,  # 标记这是纯校准映射
                    'map_shape': data.shape,
                    'map_mean': float(np.mean(data)),
                    'map_std': float(np.std(data)),
                    'map_min': float(np.min(data)),
                    'map_max': float(np.max(data))
                }
                
                print(f"⚠️ 使用默认参数: 系数={coefficient}, 偏置={bias}")
                print(f"⚠️ 如需调整参数，请在界面上手动修改")
            
            elif isinstance(data, dict):
                # 字典格式
                self.calibration_data = {
                    'calibration_map': data.get('calibration_map'),
                    'reference_data': data.get('reference_data'),
                    'coefficient': data.get('coefficient', 1730.6905),
                    'bias': data.get('bias', 126.1741),
                    'zero_pressure': data.get('zero_pressure', 0.0),
                    'is_zeroed': data.get('is_zeroed', False),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'description': data.get('description', 'NumPy校准数据'),
                    'is_calibration_map_only': False
                }
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
            # 尝试读取为简单的系数和偏置
            with open(filepath, 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig处理BOM
                reader = csv.reader(f)
                rows = list(reader)
                
            if len(rows) >= 2 and len(rows[0]) >= 2:
                # 假设第一行是标题，第二行是数据
                try:
                    coefficient = float(rows[1][0])
                    bias = float(rows[1][1])
                    zero_pressure = float(rows[1][2]) if len(rows[1]) > 2 else 0.0
                    is_zeroed = bool(int(rows[1][3])) if len(rows[1]) > 3 else False
                    
                    self.calibration_data = {
                        'coefficient': coefficient,
                        'bias': bias,
                        'zero_pressure': zero_pressure,
                        'is_zeroed': is_zeroed,
                        'timestamp': datetime.now().isoformat(),
                        'description': 'CSV校准数据'
                    }
                except (ValueError, IndexError):
                    # 如果不是简单格式，尝试作为校准映射读取
                    data = np.loadtxt(filepath, delimiter=',')
                    self.calibration_data = {
                        'calibration_map': data,
                        'coefficient': 1.0,
                        'bias': 0.0,
                        'zero_pressure': 0.0,
                        'is_zeroed': False,
                        'timestamp': datetime.now().isoformat(),
                        'description': 'CSV校准映射数据'
                    }
            else:
                raise ValueError("CSV文件格式不正确")
            
            self.loaded_file = filepath
            print(f"✅ 成功加载CSV校准数据: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 加载CSV校准数据失败: {e}")
            return False
    
    def get_calibration_info(self):
        """获取校准数据信息"""
        if self.calibration_data is None:
            return None
        
        info = {
            'loaded_file': self.loaded_file,
            'coefficient': self.calibration_data.get('coefficient', 0.0),
            'bias': self.calibration_data.get('bias', 0.0),
            'zero_pressure': self.calibration_data.get('zero_pressure', 0.0),
            'is_zeroed': self.calibration_data.get('is_zeroed', False),
            'timestamp': self.calibration_data.get('timestamp', ''),
            'description': self.calibration_data.get('description', '')
        }
        
        if 'calibration_map' in self.calibration_data and self.calibration_data['calibration_map'] is not None:
            cal_map = self.calibration_data['calibration_map']
            # 检查是否为numpy数组
            if isinstance(cal_map, np.ndarray):
                info.update({
                    'calibration_map_shape': cal_map.shape,
                    'calibration_map_mean': float(np.mean(cal_map)),
                    'calibration_map_std': float(np.std(cal_map)),
                    'calibration_map_min': float(np.min(cal_map)),
                    'calibration_map_max': float(np.max(cal_map))
                })
        
        return info
    
    def apply_calibration_map(self, raw_data):
        """应用校准映射到原始传感器数据"""
        if self.calibration_data is None or 'calibration_map' not in self.calibration_data:
            return raw_data
        
        calibration_map = self.calibration_data['calibration_map']
        if calibration_map is None:
            return raw_data
        
        # 确保数据形状匹配
        if raw_data.shape != calibration_map.shape:
            print(f"⚠️ 数据形状不匹配: 原始数据{raw_data.shape} vs 校准映射{calibration_map.shape}")
            return raw_data
        
        # 应用校准映射：原始数据 * 校准映射
        calibrated_data = raw_data * calibration_map
        
        return calibrated_data
    
    def get_calibration_map_info(self):
        """获取校准映射的详细信息"""
        if self.calibration_data is None or 'calibration_map' not in self.calibration_data:
            return None
        
        calibration_map = self.calibration_data['calibration_map']
        if calibration_map is None:
            return None
        
        return {
            'shape': calibration_map.shape,
            'mean': float(np.mean(calibration_map)),
            'std': float(np.std(calibration_map)),
            'min': float(np.min(calibration_map)),
            'max': float(np.max(calibration_map)),
            'median': float(np.median(calibration_map)),
            'cv': float(np.std(calibration_map) / np.mean(calibration_map)) if np.mean(calibration_map) > 0 else 0
        }

class WeightMeasurementWidget(QWidget):
    """称重测量组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zero_pressure = 0.0  # 归零时的压力总和
        self.is_zeroed = False    # 是否已归零
        self.measurement_active = False  # 测量是否激活
        self.calibration_coefficient = 1730.6905  # 一次函数系数 - 使用用户提供的新参数
        self.calibration_bias = 126.1741  # 一次函数偏置 - 使用用户提供的新参数
        self.current_weight = 0.0  # 当前重量
        self.weight_history = []  # 重量历史记录
        self.max_history_length = 100  # 最大历史记录长度
        
        # 添加校准数据加载器
        self.calibration_loader = CalibrationDataLoader()
        
        self.init_ui()
        
    def init_ui(self):
        """初始化称重UI"""
        layout = QVBoxLayout()
        
        # 校准参数组
        calibration_group = QGroupBox("校准参数")
        calibration_layout = QGridLayout()
        
        # 系数输入 - 使用QLineEdit替代QDoubleSpinBox
        self.coefficient_label = QLabel("系数 (k):")
        self.coefficient_input = QLineEdit()
        self.coefficient_input.setText("1730.6905")
        self.coefficient_input.setPlaceholderText("输入系数，如: 1730.6905")
        self.coefficient_input.setToolTip("输入系数值，支持科学计数法如: 1.7306905e+03")
        self.coefficient_input.textChanged.connect(self.on_coefficient_changed)
        
        # 偏置输入 - 使用QLineEdit替代QDoubleSpinBox
        self.bias_label = QLabel("偏置 (b):")
        self.bias_input = QLineEdit()
        self.bias_input.setText("126.1741")
        self.bias_input.setPlaceholderText("输入偏置，如: 126.1741")
        self.bias_input.setToolTip("输入偏置值，支持科学计数法如: 1.261741e+02")
        self.bias_input.textChanged.connect(self.on_bias_changed)
        
        # 公式显示
        self.formula_label = QLabel("公式: 质量 = k × 压力 + b")
        self.formula_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        
        # 当前参数值显示（科学计数法）
        self.current_params_label = QLabel("当前参数: k=1.73e+03 (1730.6905), b=1.26e+02 (126.1741)")
        self.current_params_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace;")
        self.current_params_label.setWordWrap(True)  # 允许换行
        
        calibration_layout.addWidget(self.coefficient_label, 0, 0)
        calibration_layout.addWidget(self.coefficient_input, 0, 1)
        calibration_layout.addWidget(self.bias_label, 1, 0)
        calibration_layout.addWidget(self.bias_input, 1, 1)
        calibration_layout.addWidget(self.formula_label, 2, 0, 1, 2)
        calibration_layout.addWidget(self.current_params_label, 3, 0, 1, 2)
        
        calibration_group.setLayout(calibration_layout)
        
        # 归零控制组
        zero_group = QGroupBox("归零控制")
        zero_layout = QHBoxLayout()
        
        self.zero_btn = QPushButton("归零")
        self.zero_btn.clicked.connect(self.perform_zero)
        self.zero_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        
        self.zero_status_label = QLabel("状态: 未归零")
        self.zero_status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.zero_pressure_label = QLabel("归零压力: -- N")
        
        zero_layout.addWidget(self.zero_btn)
        zero_layout.addWidget(self.zero_status_label)
        zero_layout.addWidget(self.zero_pressure_label)
        zero_layout.addStretch()
        
        zero_group.setLayout(zero_layout)
        
        # 重量显示组
        weight_group = QGroupBox("重量显示")
        weight_layout = QVBoxLayout()
        
        # 大数字显示
        self.weight_display = QLCDNumber()
        self.weight_display.setDigitCount(8)
        self.weight_display.setSegmentStyle(QLCDNumber.Flat)
        self.weight_display.setStyleSheet("background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px;")
        self.weight_display.display("0.000")
        
        # 单位标签
        self.weight_unit_label = QLabel("克 (g)")
        self.weight_unit_label.setAlignment(QtCore.Qt.AlignCenter)
        self.weight_unit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        
        weight_layout.addWidget(self.weight_display)
        weight_layout.addWidget(self.weight_unit_label)
        
        weight_group.setLayout(weight_layout)
        
        # 测量控制组
        measurement_group = QGroupBox("测量控制")
        measurement_layout = QHBoxLayout()
        
        self.start_measurement_btn = QPushButton("开始测量")
        self.start_measurement_btn.clicked.connect(self.start_measurement)
        self.start_measurement_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 8px;")
        
        self.stop_measurement_btn = QPushButton("停止测量")
        self.stop_measurement_btn.clicked.connect(self.stop_measurement)
        self.stop_measurement_btn.setEnabled(False)
        self.stop_measurement_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 8px;")
        
        self.hold_btn = QPushButton("保持读数")
        self.hold_btn.clicked.connect(self.hold_reading)
        self.hold_btn.setEnabled(False)
        
        self.clear_history_btn = QPushButton("清空历史")
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        measurement_layout.addWidget(self.start_measurement_btn)
        measurement_layout.addWidget(self.stop_measurement_btn)
        measurement_layout.addWidget(self.hold_btn)
        measurement_layout.addWidget(self.clear_history_btn)
        measurement_layout.addStretch()
        
        measurement_group.setLayout(measurement_layout)
        
        # 实时信息组
        info_group = QGroupBox("实时信息")
        info_layout = QGridLayout()
        
        self.pressure_label = QLabel("当前压力: -- N")
        self.pressure_label.setStyleSheet("font-weight: bold;")
        
        self.net_pressure_label = QLabel("净压力: -- N")
        self.net_pressure_label.setStyleSheet("font-weight: bold;")
        
        self.stability_label = QLabel("稳定性: --")
        self.stability_label.setStyleSheet("font-weight: bold;")
        
        self.measurement_status_label = QLabel("测量状态: 停止")
        self.measurement_status_label.setStyleSheet("color: red; font-weight: bold;")
        
        info_layout.addWidget(self.pressure_label, 0, 0)
        info_layout.addWidget(self.net_pressure_label, 0, 1)
        info_layout.addWidget(self.stability_label, 1, 0)
        info_layout.addWidget(self.measurement_status_label, 1, 1)
        
        info_group.setLayout(info_layout)
        
        # 重量历史图表
        history_group = QGroupBox("重量历史")
        history_layout = QVBoxLayout()
        
        self.history_plot = pg.GraphicsLayoutWidget()
        self.history_plot.setFixedHeight(200)
        self.history_plot_widget = self.history_plot.addPlot()
        self.history_plot_widget.setLabel('left', '重量 (g)')
        self.history_plot_widget.setLabel('bottom', '时间')
        self.history_plot_widget.setTitle('重量变化曲线')
        
        # 创建曲线
        self.history_curve = self.history_plot_widget.plot(pen=pg.mkPen(color='blue', width=2))
        
        history_layout.addWidget(self.history_plot)
        history_group.setLayout(history_layout)
        
        # 组装布局
        layout.addWidget(calibration_group)
        layout.addWidget(zero_group)
        layout.addWidget(weight_group)
        layout.addWidget(measurement_group)
        layout.addWidget(info_group)
        layout.addWidget(history_group)
        
        self.setLayout(layout)
        
        # 初始化显示
        self.update_formula_display()
        self.update_params_display()
    
    def on_coefficient_changed(self, text):
        """系数输入框变化时的处理"""
        try:
            self.calibration_coefficient = float(text)
            self.update_formula_display()
            self.update_params_display()
            if self.measurement_active:
                self.calculate_weight()
        except ValueError:
            self.current_params_label.setText("当前参数: 无效输入")
    
    def on_bias_changed(self, text):
        """偏置输入框变化时的处理"""
        try:
            self.calibration_bias = float(text)
            self.update_formula_display()
            self.update_params_display()
            if self.measurement_active:
                self.calculate_weight()
        except ValueError:
            self.current_params_label.setText("当前参数: 无效输入")
    
    def update_formula_display(self):
        """更新公式显示"""
        if self.is_zeroed:
            formula_text = f"公式: 质量 = {self.calibration_coefficient:.4f} × (当前压力 - {self.zero_pressure:.4f}) + {self.calibration_bias:.4f}"
        else:
            formula_text = f"公式: 质量 = {self.calibration_coefficient:.4f} × 压力 + {self.calibration_bias:.4f}"
        self.formula_label.setText(formula_text)
    
    def update_params_display(self):
        """更新参数显示"""
        self.current_params_label.setText(f"当前参数: k={self.calibration_coefficient:.2e} ({self.calibration_coefficient:.6f}), b={self.calibration_bias:.2e} ({self.calibration_bias:.6f})")
    
    def perform_zero(self):
        """执行归零操作"""
        if not hasattr(self.parent(), 'data_handler') or not self.parent().data_handler:
            QMessageBox.warning(self, "警告", "请先连接传感器")
            return
        
        try:
            # 获取当前压力总和
            self.parent().data_handler.trigger()
            with self.parent().data_handler.lock:
                if self.parent().data_handler.value:
                    current_data = np.array(self.parent().data_handler.value[-1])
                    current_pressure = np.sum(current_data)
                else:
                    QMessageBox.warning(self, "警告", "无法获取传感器数据")
                    return
            
            # 设置归零压力
            self.zero_pressure = current_pressure
            self.is_zeroed = True
            
            # 更新UI
            self.zero_status_label.setText("状态: 已归零")
            self.zero_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.zero_pressure_label.setText(f"归零压力: {self.zero_pressure:.4f} N")
            
            # 更新公式显示
            self.update_formula_display()
            
            # 清空重量历史
            self.clear_history()
            
            QMessageBox.information(self, "归零成功", f"归零完成，基准压力: {self.zero_pressure:.4f} N")
            
        except Exception as e:
            QMessageBox.critical(self, "归零失败", f"归零操作失败: {e}")
    
    def start_measurement(self):
        """开始测量"""
        if not self.is_zeroed:
            QMessageBox.warning(self, "警告", "请先进行归零操作")
            return
        
        self.measurement_active = True
        self.start_measurement_btn.setEnabled(False)
        self.stop_measurement_btn.setEnabled(True)
        self.hold_btn.setEnabled(True)
        self.measurement_status_label.setText("测量状态: 进行中")
        self.measurement_status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def stop_measurement(self):
        """停止测量"""
        self.measurement_active = False
        self.start_measurement_btn.setEnabled(True)
        self.stop_measurement_btn.setEnabled(False)
        self.hold_btn.setEnabled(False)
        self.measurement_status_label.setText("测量状态: 停止")
        self.measurement_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def hold_reading(self):
        """保持当前读数"""
        if self.measurement_active:
            # 暂停测量但保持当前显示
            self.measurement_status_label.setText("测量状态: 保持")
            self.measurement_status_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def clear_history(self):
        """清空重量历史"""
        self.weight_history.clear()
        self.history_curve.setData([], [])
    
    def calculate_weight(self, pressure_sum):
        """计算重量"""
        if not self.is_zeroed:
            return 0.0
        
        # 计算净压力（减去归零压力）
        net_pressure = pressure_sum - self.zero_pressure
        
        # 使用用户要求的公式：(当前压力 - 归零压力) × 系数 + 偏置
        weight = self.calibration_coefficient * net_pressure + self.calibration_bias
        
        return max(0.0, weight)  # 确保重量不为负
    
    def update_weight_display(self, weight):
        """更新重量显示"""
        self.current_weight = weight
        self.weight_display.display(f"{weight:.3f}")
        
        # 添加到历史记录
        timestamp = time.time()
        self.weight_history.append((timestamp, weight))
        
        # 限制历史记录长度
        if len(self.weight_history) > self.max_history_length:
            self.weight_history.pop(0)
        
        # 更新历史图表
        if len(self.weight_history) > 1:
            times = [t - self.weight_history[0][0] for t, _ in self.weight_history]
            weights = [w for _, w in self.weight_history]
            self.history_curve.setData(times, weights)
    
    def process_pressure_data(self, pressure_sum):
        """处理压力数据"""
        if not self.measurement_active:
            return
        
        # 更新压力显示
        self.pressure_label.setText(f"当前压力: {pressure_sum:.4f} N")
        
        # 计算净压力
        net_pressure = pressure_sum - self.zero_pressure
        self.net_pressure_label.setText(f"净压力: {net_pressure:.4f} N")
        
        # 计算重量
        weight = self.calculate_weight(pressure_sum)
        self.update_weight_display(weight)
        
        # 计算稳定性（基于最近几次读数的标准差）
        if len(self.weight_history) >= 5:
            recent_weights = [w for _, w in self.weight_history[-5:]]
            stability = np.std(recent_weights)
            if stability < 0.01:
                stability_text = "稳定"
                stability_color = "green"
            elif stability < 0.05:
                stability_text = "较稳定"
                stability_color = "orange"
            else:
                stability_text = "不稳定"
                stability_color = "red"
            
            self.stability_label.setText(f"稳定性: {stability_text}")
            self.stability_label.setStyleSheet(f"font-weight: bold; color: {stability_color};")
    
    def save_calibration(self):
        """保存校准参数 - 支持多种格式"""
        # 设置默认路径
        default_path = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test"
        
        # 确保目录存在
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
        
        filename, file_filter = QFileDialog.getSaveFileName(
            self, "保存校准参数", default_path, 
            "JSON文件 (*.json);;CSV文件 (*.csv);;NumPy文件 (*.npy)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_calibration_json(filename)
                elif filename.endswith('.csv'):
                    self.save_calibration_csv(filename)
                elif filename.endswith('.npy'):
                    self.save_calibration_numpy(filename)
                else:
                    # 根据文件过滤器添加扩展名
                    if 'JSON' in file_filter:
                        filename += '.json'
                        self.save_calibration_json(filename)
                    elif 'CSV' in file_filter:
                        filename += '.csv'
                        self.save_calibration_csv(filename)
                    elif 'NumPy' in file_filter:
                        filename += '.npy'
                        self.save_calibration_numpy(filename)
                
                QMessageBox.information(self, "成功", f"校准参数已保存到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_calibration_json(self, filename):
        """保存为JSON格式"""
        calibration_data = {
            'timestamp': datetime.now().isoformat(),
            'coefficient': self.calibration_coefficient,
            'bias': self.calibration_bias,
            'zero_pressure': self.zero_pressure,
            'is_zeroed': self.is_zeroed,
            'description': '传感器称重校准参数',
            'formula': f'质量 = {self.calibration_coefficient:.6f} × (当前压力 - {self.zero_pressure:.6f}) + {self.calibration_bias:.6f}' if self.is_zeroed else f'质量 = {self.calibration_coefficient:.6f} × 压力 + {self.calibration_bias:.6f}'
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(calibration_data, f, indent=2, ensure_ascii=False)
    
    def save_calibration_csv(self, filename):
        """保存为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['参数', '数值', '单位', '说明'])
            writer.writerow(['coefficient', f'{self.calibration_coefficient:.6f}', '', '校准系数'])
            writer.writerow(['bias', f'{self.calibration_bias:.6f}', 'g', '校准偏置'])
            writer.writerow(['zero_pressure', f'{self.zero_pressure:.6f}', 'N', '归零压力'])
            writer.writerow(['is_zeroed', '1' if self.is_zeroed else '0', '', '是否已归零'])
            writer.writerow(['timestamp', datetime.now().isoformat(), '', '保存时间'])
    
    def save_calibration_numpy(self, filename):
        """保存为NumPy格式"""
        calibration_data = {
            'coefficient': self.calibration_coefficient,
            'bias': self.calibration_bias,
            'zero_pressure': self.zero_pressure,
            'is_zeroed': self.is_zeroed,
            'timestamp': datetime.now().isoformat(),
            'description': '传感器称重校准参数'
        }
        
        np.save(filename, calibration_data)
    
    def load_calibration(self):
        """加载校准参数 - 支持多种格式"""
        # 设置默认路径
        default_path = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test"
        
        # 确保目录存在
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载校准参数", default_path, 
            "所有支持的文件 (*.json *.csv *.npy);;JSON文件 (*.json);;CSV文件 (*.csv);;NumPy文件 (*.npy)"
        )
        
        if filename:
            try:
                # 使用校准数据加载器
                if self.calibration_loader.load_calibration_data(filename):
                    calibration_data = self.calibration_loader.calibration_data
                    
                    # 更新参数
                    self.calibration_coefficient = calibration_data.get('coefficient', self.calibration_coefficient)
                    self.calibration_bias = calibration_data.get('bias', self.calibration_bias)
                    self.zero_pressure = calibration_data.get('zero_pressure', 0.0)
                    self.is_zeroed = calibration_data.get('is_zeroed', False)
                    
                    # 更新UI
                    self.coefficient_input.setText(str(self.calibration_coefficient))
                    self.bias_input.setText(str(self.calibration_bias))
                    
                    if self.is_zeroed:
                        self.zero_status_label.setText("状态: 已归零")
                        self.zero_status_label.setStyleSheet("color: green; font-weight: bold;")
                        self.zero_pressure_label.setText(f"归零压力: {self.zero_pressure:.4f} N")
                    else:
                        self.zero_status_label.setText("状态: 未归零")
                        self.zero_status_label.setStyleSheet("color: red; font-weight: bold;")
                        self.zero_pressure_label.setText("归零压力: -- N")
                    
                    # 更新公式和参数显示
                    self.update_formula_display()
                    self.update_params_display()
                    
                    # 同步主界面的校准数据加载器
                    if hasattr(self.parent(), 'calibration_loader'):
                        self.parent().calibration_loader = self.calibration_loader
                        # 更新主界面的校准信息显示
                        if hasattr(self.parent(), 'update_calibration_info_display'):
                            self.parent().update_calibration_info_display()
                    
                    # 显示校准信息
                    info = self.calibration_loader.get_calibration_info()
                    if info:
                        info_text = f"文件: {os.path.basename(filename)}\n"
                        info_text += f"系数: {info['coefficient']:.6f}\n"
                        info_text += f"偏置: {info['bias']:.6f} g\n"
                        info_text += f"归零压力: {info['zero_pressure']:.6f} N\n"
                        info_text += f"已归零: {'是' if info['is_zeroed'] else '否'}\n"
                        if info.get('timestamp'):
                            info_text += f"时间: {info['timestamp']}\n"
                        if info.get('description'):
                            info_text += f"描述: {info['description']}"
                        
                        # 如果是纯校准映射数据，添加特殊提示
                        if self.calibration_loader.calibration_data.get('is_calibration_map_only', False):
                            info_text += f"\n\n⚠️ 注意: 这是纯校准映射数据，使用了默认的系数和偏置值。"
                            info_text += f"\n如需调整参数，请在界面上手动修改。"
                        
                        QMessageBox.information(self, "校准参数已加载", info_text)
                    else:
                        QMessageBox.information(self, "成功", f"校准参数已加载: {filename}")
                else:
                    QMessageBox.critical(self, "错误", "加载校准数据失败")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")

class WeightMeasurementInterface(QWidget):
    """称重测量主界面"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.data_handler = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 添加校准数据加载器
        self.calibration_loader = CalibrationDataLoader()
        
        # 称重组件
        self.weight_widget = WeightMeasurementWidget(self)
        
        # 设置窗口属性
        self.setWindowTitle("传感器称重工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据处理器
        self.init_data_handler()
        
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧：传感器控制区域
        left_panel = QVBoxLayout()
        
        # 传感器控制组
        sensor_group = QGroupBox("传感器控制")
        sensor_layout = QGridLayout()
        
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
        self.start_button = QPushButton("连接传感器")
        self.start_button.clicked.connect(self.start_sensor)
        self.start_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        
        self.stop_button = QPushButton("断开传感器")
        self.stop_button.clicked.connect(self.stop_sensor)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 8px;")
        
        # 状态标签
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        sensor_layout.addWidget(self.sensor_label, 0, 0)
        sensor_layout.addWidget(self.sensor_combo, 0, 1)
        sensor_layout.addWidget(self.port_label, 1, 0)
        sensor_layout.addWidget(self.port_input, 1, 1)
        sensor_layout.addWidget(self.start_button, 2, 0)
        sensor_layout.addWidget(self.stop_button, 2, 1)
        sensor_layout.addWidget(self.status_label, 3, 0, 1, 2)
        
        sensor_group.setLayout(sensor_layout)
        
        # 压力显示组
        pressure_group = QGroupBox("压力信息")
        pressure_layout = QVBoxLayout()
        
        self.total_pressure_label = QLabel("总压力: -- N")
        self.total_pressure_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        
        self.max_pressure_label = QLabel("最大压力: -- N")
        self.max_pressure_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        
        self.min_pressure_label = QLabel("最小压力: -- N")
        self.min_pressure_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        
        pressure_layout.addWidget(self.total_pressure_label)
        pressure_layout.addWidget(self.max_pressure_label)
        pressure_layout.addWidget(self.min_pressure_label)
        
        pressure_group.setLayout(pressure_layout)
        
        # 校准文件操作组
        file_group = QGroupBox("校准文件")
        file_layout = QVBoxLayout()
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        self.save_calibration_btn = QPushButton("保存校准")
        self.save_calibration_btn.clicked.connect(self.weight_widget.save_calibration)
        self.save_calibration_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
        
        self.load_calibration_btn = QPushButton("加载校准")
        self.load_calibration_btn.clicked.connect(self.weight_widget.load_calibration)
        self.load_calibration_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 6px;")
        
        self.show_calibration_info_btn = QPushButton("校准信息")
        self.show_calibration_info_btn.clicked.connect(self.show_calibration_info)
        self.show_calibration_info_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 6px;")
        
        button_layout.addWidget(self.save_calibration_btn)
        button_layout.addWidget(self.load_calibration_btn)
        button_layout.addWidget(self.show_calibration_info_btn)
        
        # 校准信息显示
        self.calibration_info_label = QLabel("未加载校准文件")
        self.calibration_info_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.calibration_info_label.setWordWrap(True)
        self.calibration_info_label.setMinimumHeight(60)
        
        file_layout.addLayout(button_layout)
        file_layout.addWidget(self.calibration_info_label)
        
        file_group.setLayout(file_layout)
        
        # 组装左侧面板
        left_panel.addWidget(sensor_group)
        left_panel.addWidget(pressure_group)
        left_panel.addWidget(file_group)
        left_panel.addStretch()
        
        # 右侧：称重显示区域
        right_panel = QVBoxLayout()
        right_panel.addWidget(self.weight_widget)
        
        # 组装主布局
        main_layout.addLayout(left_panel, 1)   # 左侧占1/3
        main_layout.addLayout(right_panel, 2)  # 右侧占2/3
        
        self.setLayout(main_layout)
        
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
    
    def on_sensor_changed(self, sensor_id_text):
        """传感器选择变化时的处理函数"""
        if not self.is_running:
            try:
                sensor_id = int(sensor_id_text)
                print(f"🔄 传感器选择变化为: {sensor_id}")
                self.init_data_handler()
            except ValueError:
                print(f"⚠️ 无效的传感器ID: {sensor_id_text}")
    
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
                    self.timer.start(100)  # 100ms更新频率
                    self.update_ui_state()
                    self.status_label.setText(f"状态: 已连接 (传感器{sensor_id})")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    print(f"✅ 传感器 {sensor_id} 连接成功，端口: {port}")
                else:
                    self.status_label.setText("状态: 连接失败")
                    self.status_label.setStyleSheet("color: red; font-weight: bold;")
                    print(f"❌ 传感器 {sensor_id} 连接失败，端口: {port}")
                    QMessageBox.warning(self, "连接失败", f"传感器 {sensor_id} 连接失败，端口: {port}")
            except Exception as e:
                self.status_label.setText("状态: 连接错误")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                print(f"❌ 传感器 {sensor_id} 连接错误: {e}")
                QMessageBox.critical(self, "连接错误", f"传感器 {sensor_id} 连接错误: {e}")
        else:
            # 使用模拟数据
            self.is_running = True
            self.timer.start(200)  # 200ms更新频率
            self.update_ui_state()
            self.status_label.setText(f"状态: 模拟模式 (传感器{sensor_id})")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            print(f"✅ 模拟模式启动，传感器 {sensor_id}")
    
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
    
    def update_ui_state(self):
        """更新UI状态"""
        self.start_button.setEnabled(not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.port_input.setEnabled(not self.is_running)
        self.sensor_combo.setEnabled(not self.is_running)
    
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
            
            # 应用校准映射（如果有的话）
            if hasattr(self, 'calibration_loader') and self.calibration_loader:
                calibrated_data = self.calibration_loader.apply_calibration_map(current_data)
                if calibrated_data is not current_data:
                    print(f"✅ 已应用校准映射")
                    current_data = calibrated_data
            
            # 计算压力总和
            pressure_sum = np.sum(current_data)
            
            # 更新压力显示
            self.total_pressure_label.setText(f"总压力: {pressure_sum:.4f} N")
            
            # 更新最大最小压力（基于历史数据）
            if not hasattr(self, 'pressure_history'):
                self.pressure_history = []
            
            self.pressure_history.append(pressure_sum)
            if len(self.pressure_history) > 100:
                self.pressure_history.pop(0)
            
            if len(self.pressure_history) > 1:
                max_pressure = max(self.pressure_history)
                min_pressure = min(self.pressure_history)
                self.max_pressure_label.setText(f"最大压力: {max_pressure:.4f} N")
                self.min_pressure_label.setText(f"最小压力: {min_pressure:.4f} N")
            
            # 传递给称重组件处理
            self.weight_widget.process_pressure_data(pressure_sum)
            
        except USBError:
            print("❌ USB连接错误，停止传感器")
            self.stop_sensor()
            QMessageBox.critical(self, "USB错误", "USB连接错误，传感器已停止")
        except Exception as e:
            print(f"⚠️ 更新数据时出错: {e}")
    
    def generate_simulated_data(self):
        """生成模拟传感器数据"""
        # 创建一个64x64的模拟传感器数据
        data = np.random.rand(64, 64) * 0.01
        
        # 模拟一个中心压力点（模拟物体重量）
        center_x, center_y = 32, 32
        for i in range(64):
            for j in range(64):
                distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                if distance < 15:
                    # 模拟物体重量（1-5N的随机重量）
                    weight = 2.0 + np.random.rand() * 3.0
                    data[i, j] += weight * np.exp(-distance / 8)
        
        return data
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_sensor()
        event.accept()
    
    def show_calibration_info(self):
        """显示校准信息"""
        info = self.calibration_loader.get_calibration_info()
        if info:
            info_text = f"校准文件信息:\n"
            info_text += f"文件: {os.path.basename(info['loaded_file'])}\n"
            info_text += f"系数: {info['coefficient']:.6f}\n"
            info_text += f"偏置: {info['bias']:.6f} g\n"
            info_text += f"归零压力: {info['zero_pressure']:.6f} N\n"
            info_text += f"已归零: {'是' if info['is_zeroed'] else '否'}\n"
            if info.get('timestamp'):
                info_text += f"时间: {info['timestamp']}\n"
            if info.get('description'):
                info_text += f"描述: {info['description']}\n"
            
            # 如果有校准映射信息
            map_info = self.calibration_loader.get_calibration_map_info()
            if map_info:
                info_text += f"\n校准映射信息:\n"
                info_text += f"形状: {map_info['shape']}\n"
                info_text += f"平均值: {map_info['mean']:.6f}\n"
                info_text += f"标准差: {map_info['std']:.6f}\n"
                info_text += f"最小值: {map_info['min']:.6f}\n"
                info_text += f"最大值: {map_info['max']:.6f}\n"
                info_text += f"中位数: {map_info['median']:.6f}\n"
                info_text += f"变异系数: {map_info['cv']:.6f}\n"
                
                # 如果是64x64的校准映射，添加特殊说明
                if map_info['shape'] == (64, 64):
                    info_text += f"\n说明: 这是64x64传感器校准映射，用于校正传感器不一致性。\n"
                    info_text += f"每个元素对应一个传感器位置，用于对原始数据进行放缩校正。"
            
            QMessageBox.information(self, "校准信息", info_text)
        else:
            QMessageBox.information(self, "校准信息", "未加载校准文件")
    
    def update_calibration_info_display(self):
        """更新校准信息显示"""
        info = self.calibration_loader.get_calibration_info()
        if info:
            display_text = f"文件: {os.path.basename(info['loaded_file'])}\n"
            display_text += f"系数: {info['coefficient']:.4f}\n"
            display_text += f"偏置: {info['bias']:.4f} g\n"
            display_text += f"归零: {'是' if info['is_zeroed'] else '否'}"
            
            if 'calibration_map_shape' in info:
                display_text += f"\n映射: {info['calibration_map_shape']}"
            
            self.calibration_info_label.setText(display_text)
            self.calibration_info_label.setStyleSheet("font-size: 11px; color: #28a745; font-family: monospace; background-color: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px;")
        else:
            self.calibration_info_label.setText("未加载校准文件")
            self.calibration_info_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")


# 使用示例和启动代码
def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = WeightMeasurementInterface()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 