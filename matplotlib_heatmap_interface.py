"""
使用matplotlib的传感器连接和热力图显示界面
基于matplotlib实现，提供更稳定的热力图和颜色条显示
新增：传感器一致性评估功能、校正系统、高级功能
"""

import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QMessageBox, QVBoxLayout,
                            QGroupBox, QTextEdit, QFileDialog, QProgressBar, QTabWidget)
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.colors as mcolors
from usb.core import USBError
import json
from datetime import datetime

# 设置matplotlib中文字体支持
def setup_chinese_font():
    """设置matplotlib中文字体支持"""
    try:
        # 尝试设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 测试中文字体是否可用
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, '测试中文', fontsize=12)
        plt.close(fig)
        print("✅ matplotlib中文字体设置成功")
        return True
    except Exception as e:
        print(f"⚠️ matplotlib中文字体设置失败: {e}")
        print("⚠️ 将使用默认字体")
        return False

# 初始化中文字体
CHINESE_FONT_AVAILABLE = setup_chinese_font()

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

# 导入校正组件
try:
    from calibration_system import CalibrationWidget
    CALIBRATION_AVAILABLE = True
    print("✅ 校正组件导入成功")
except ImportError as e:
    print(f"⚠️ 校正组件未找到: {e}")
    CALIBRATION_AVAILABLE = False

# 导入简化校正系统
try:
    from uniform_calibration import UniformObjectCalibration
    UNIFORM_CALIBRATION_AVAILABLE = True
    print("✅ 简化校正系统导入成功")
except ImportError as e:
    print(f"⚠️ 简化校正系统未找到: {e}")
    UNIFORM_CALIBRATION_AVAILABLE = False

class ConsistencyHeatmapWindow(QWidget):
    """一致性热力图显示窗口 - matplotlib版本"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("传感器一致性热力图")
        self.setGeometry(200, 200, 1000, 800)
        self.setWindowFlags(QtCore.Qt.Window)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("传感器一致性热力图")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 热力图显示区域
        heatmap_layout = QHBoxLayout()
        
        # 左侧：热力图
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 初始化热力图和颜色条
        self.heatmap = None
        self.colorbar = None
        
        # 添加matplotlib工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 右侧：统计信息
        stats_layout = QVBoxLayout()
        
        # 统计信息组
        stats_group = QGroupBox("一致性统计信息")
        stats_inner_layout = QVBoxLayout()
        
        self.stats_label = QLabel("统计信息: --")
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.detail_stats_label = QLabel("")
        self.detail_stats_label.setStyleSheet("font-size: 11px;")
        
        stats_inner_layout.addWidget(self.stats_label)
        stats_inner_layout.addWidget(self.detail_stats_label)
        stats_group.setLayout(stats_inner_layout)
        stats_layout.addWidget(stats_group)
        
        # 控制按钮
        button_layout = QVBoxLayout()
        
        self.save_heatmap_btn = QPushButton("保存热力图")
        self.save_heatmap_btn.clicked.connect(self.save_heatmap)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_heatmap_btn)
        button_layout.addWidget(self.close_btn)
        button_layout.addStretch()
        
        stats_layout.addLayout(button_layout)
        
        # 组装热力图布局
        heatmap_layout.addWidget(self.toolbar)
        heatmap_layout.addWidget(self.canvas, 4)
        heatmap_layout.addLayout(stats_layout, 1)
        
        layout.addLayout(heatmap_layout)
        
        self.setLayout(layout)
        
    def update_data(self, consistency_data):
        """更新一致性数据"""
        if not consistency_data:
            return
            
        # 确定数据形状
        max_x = max(pos[0] for pos in consistency_data.keys()) + 1
        max_y = max(pos[1] for pos in consistency_data.keys()) + 1
        shape = (max_x, max_y)
        
        # 创建一致性矩阵
        matrix = np.zeros(shape)
        for (x, y), value in consistency_data.items():
            matrix[x, y] = value
            
        # 过滤掉很小的值，只显示有意义的范围
        values = list(consistency_data.values())
        if values:
            # 固定数值范围为0-0.01
            min_meaningful = 0.0
            max_val = 0.01
            
            # 创建显示矩阵，限制在固定范围内
            display_matrix = np.clip(matrix, min_meaningful, max_val)
            
            # 更新热力图
            if self.heatmap is not None:
                self.heatmap.set_array(display_matrix.T)
                self.heatmap.set_clim(min_meaningful, max_val)
            else:
                # 第一次创建热力图
                self.heatmap = self.ax.imshow(display_matrix.T, cmap='viridis', 
                                            aspect='auto', origin='lower',
                                            vmin=min_meaningful, vmax=max_val)
                
                # 添加颜色条
                self.colorbar = self.figure.colorbar(self.heatmap, ax=self.ax)
                self.colorbar.set_label('压力值 (0-0.01)', fontsize=10)
                
                # 设置坐标轴
                self.ax.set_xlabel('X轴')
                self.ax.set_ylabel('Y轴')
                self.ax.set_title('传感器一致性热力图')
                
                # 添加网格
                self.ax.grid(True, alpha=0.3)
            
            # 更新画布
            self.canvas.draw()
            
        # 更新统计信息
        values = list(consistency_data.values())
        mean_val = np.mean(values)
        std_val = np.std(values)
        cv_percent = (std_val / mean_val * 100) if mean_val > 0 else 0
        min_val = np.min(values)
        max_val = np.max(values)
        
        stats_text = f"数据点: {len(values)}, 均值: {mean_val:.4f}, 标准差: {std_val:.4f}, 变异系数: {cv_percent:.1f}%"
        self.stats_label.setText(stats_text)
        
        detail_text = f"最小值: {min_val:.4f}, 最大值: {max_val:.4f}, 范围: {max_val-min_val:.4f}"
        self.detail_stats_label.setText(detail_text)
        
    def save_heatmap(self):
        """保存热力图"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存热力图", "", "PNG图片 (*.png);;JPG图片 (*.jpg);;PDF文件 (*.pdf)"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"热力图已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

class MatplotlibHeatmapWidget(QWidget):
    """基于matplotlib的热力图显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        
        # 初始化热力图和颜色条
        self.heatmap = None
        self.colorbar = None
        
        # 添加matplotlib工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 组装布局
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
    def update_heatmap(self, data, colormap='viridis'):
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
                self.heatmap.set_cmap(colormap)
            else:
                # 第一次创建热力图
                self.heatmap = self.ax.imshow(data, cmap=colormap, aspect='auto', 
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
            self.canvas.draw()
            
        except Exception as e:
            print(f"⚠️ 更新热力图时出错: {e}")
    
    def clear_heatmap(self):
        """清空热力图"""
        try:
            # 清除图形
            self.ax.clear()
            
            # 重置热力图和颜色条
            self.heatmap = None
            self.colorbar = None
            
            # 设置标签
            self.ax.set_xlabel('X轴')
            self.ax.set_ylabel('Y轴')
            self.ax.set_title('传感器数据热力图')
            self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 清空热力图时出错: {e}")

class ConsistencyAssessmentWidget(QWidget):
    """传感器一致性评估组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.consistency_data = {}  # 存储一致性数据 {(x, y): max_value}
        self.assessment_active = False
        self.recorded_frames = 0
        self.init_ui()
        
    def init_ui(self):
        """初始化一致性评估UI"""
        layout = QVBoxLayout()
        
        # 控制组
        control_group = QGroupBox("一致性评估控制")
        control_layout = QHBoxLayout()
        
        self.start_assessment_btn = QPushButton("开始评估")
        self.start_assessment_btn.clicked.connect(self.start_assessment)
        self.stop_assessment_btn = QPushButton("停止评估")
        self.stop_assessment_btn.clicked.connect(self.stop_assessment)
        self.stop_assessment_btn.setEnabled(False)
        
        self.clear_data_btn = QPushButton("清空数据")
        self.clear_data_btn.clicked.connect(self.clear_data)
        
        self.save_data_btn = QPushButton("保存数据")
        self.save_data_btn.clicked.connect(self.save_data)
        self.save_data_btn.setEnabled(False)
        
        self.show_consistency_btn = QPushButton("显示一致性图")
        self.show_consistency_btn.clicked.connect(self.show_consistency_heatmap)
        self.show_consistency_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_assessment_btn)
        control_layout.addWidget(self.stop_assessment_btn)
        control_layout.addWidget(self.clear_data_btn)
        control_layout.addWidget(self.save_data_btn)
        control_layout.addWidget(self.show_consistency_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        
        # 信息显示组
        info_group = QGroupBox("评估信息")
        info_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 未开始")
        self.frames_label = QLabel("记录帧数: 0")
        self.points_label = QLabel("有效数据点: 0")
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.frames_label)
        info_layout.addWidget(self.points_label)
        
        info_group.setLayout(info_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 日志显示
        log_group = QGroupBox("评估日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 组装布局
        layout.addWidget(control_group)
        layout.addWidget(info_group)
        layout.addWidget(self.progress_bar)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
        # 一致性热力图窗口
        self.consistency_window = None
        
    def show_consistency_heatmap(self):
        """显示一致性热力图"""
        if not self.consistency_data:
            QMessageBox.warning(self, "警告", "没有一致性数据可显示")
            return
            
        # 创建一致性热力图窗口
        if self.consistency_window is None:
            self.consistency_window = ConsistencyHeatmapWindow(self)
            
        # 更新数据并显示
        self.consistency_window.update_data(self.consistency_data)
        self.consistency_window.show()
        self.consistency_window.raise_()
        
    def start_assessment(self):
        """开始一致性评估"""
        self.assessment_active = True
        self.start_assessment_btn.setEnabled(False)
        self.stop_assessment_btn.setEnabled(True)
        self.save_data_btn.setEnabled(False)
        self.status_label.setText("状态: 评估中...")
        self.log_message("开始一致性评估")
        
    def stop_assessment(self):
        """停止一致性评估"""
        self.assessment_active = False
        self.start_assessment_btn.setEnabled(True)
        self.stop_assessment_btn.setEnabled(False)
        self.save_data_btn.setEnabled(True)
        self.show_consistency_btn.setEnabled(True)
        self.status_label.setText("状态: 评估完成")
        self.log_message("一致性评估完成")
        
    def clear_data(self):
        """清空一致性数据"""
        self.consistency_data.clear()
        self.recorded_frames = 0
        self.frames_label.setText("记录帧数: 0")
        self.points_label.setText("有效数据点: 0")
        self.log_message("数据已清空")
        
    def save_data(self):
        """保存一致性数据"""
        if not self.consistency_data:
            QMessageBox.warning(self, "警告", "没有数据可保存")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存一致性数据", "", "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_as_json(filename)
                elif filename.endswith('.csv'):
                    self.save_as_csv(filename)
                else:
                    filename += '.json'
                    self.save_as_json(filename)
                    
                self.log_message(f"数据已保存到: {filename}")
                QMessageBox.information(self, "成功", f"数据已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
                
    def save_as_json(self, filename):
        """保存为JSON格式"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'recorded_frames': self.recorded_frames,
            'data_points': len(self.consistency_data),
            'consistency_data': {f"{x},{y}": value for (x, y), value in self.consistency_data.items()}
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def save_as_csv(self, filename):
        """保存为CSV格式"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['X', 'Y', 'Max_Value'])
            for (x, y), value in self.consistency_data.items():
                writer.writerow([x, y, value])
                
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def process_frame(self, data):
        """处理一帧数据，更新一致性数据"""
        if not self.assessment_active or data is None:
            return
            
        self.recorded_frames += 1
        self.frames_label.setText(f"记录帧数: {self.recorded_frames}")
        
        # 调试信息
        data_max = np.max(data)
        data_mean = np.mean(data)
        
        # 记录所有数据点，只保留最大值
        new_points = 0
        updated_points = 0
        
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                value = data[i, j]
                pos = (i, j)
                
                if pos in self.consistency_data:
                    if value > self.consistency_data[pos]:
                        self.consistency_data[pos] = value
                        updated_points += 1
                else:
                    self.consistency_data[pos] = value
                    new_points += 1
        
        # 更新统计信息
        if new_points > 0 or updated_points > 0:
            self.log_message(f"新增{new_points}个数据点，更新{updated_points}个数据点")
            
        self.points_label.setText(f"有效数据点: {len(self.consistency_data)}")
        
        # 每100帧记录一次调试信息
        if self.recorded_frames % 100 == 0:
            self.log_message(f"当前数据范围: 最小值={data.min():.4f}, 最大值={data_max:.4f}, 平均值={data_mean:.4f}")
        
    def get_consistency_matrix(self, shape):
        """获取一致性矩阵"""
        matrix = np.zeros(shape)
        for (x, y), value in self.consistency_data.items():
            if 0 <= x < shape[0] and 0 <= y < shape[1]:
                matrix[x, y] = value
        return matrix
        
    def get_statistics(self):
        """获取一致性统计信息"""
        if not self.consistency_data:
            return None
            
        values = list(self.consistency_data.values())
        return {
            'count': len(values),
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'cv': np.std(values) / np.mean(values) if np.mean(values) > 0 else 0  # 变异系数
        }

class MatplotlibSensorInterface(QWidget):
    """基于matplotlib的传感器连接和热力图显示界面 - 增强版"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.data_handler = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 校正相关属性
        self.correction_enabled = False
        self.calibration_map = None
        
        # FPS计数器
        self.fps_counter = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.frame_count = 0
        self.last_fps_update = datetime.now()
        
        # 一致性评估组件
        self.consistency_widget = ConsistencyAssessmentWidget()
        
        # 校正组件
        self.calibration_widget = CalibrationWidget(self) if CALIBRATION_AVAILABLE else None
        
        # 简化校正组件
        self.uniform_calibration_widget = UniformObjectCalibration(self) if UNIFORM_CALIBRATION_AVAILABLE else None
        
        # 设置窗口属性
        self.setWindowTitle("传感器界面 - matplotlib版本 (支持中文与校正系统)")
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
        
        # 颜色映射选择器
        self.colormap_label = QLabel("颜色方案:")
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["自动", "viridis", "plasma", "inferno", "magma", "cividis", "turbo", "coolwarm", "RdYlBu"])
        self.colormap_combo.setCurrentText("自动")
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        self.colormap_combo.setToolTip("选择热力图颜色方案")
        
        # 校正状态指示
        self.correction_status_label = QLabel("校正: 关闭")
        self.correction_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 状态标签
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 添加到控制布局
        control_layout.addWidget(self.sensor_label)
        control_layout.addWidget(self.sensor_combo)
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.port_input)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.colormap_label)
        control_layout.addWidget(self.colormap_combo)
        control_layout.addWidget(self.correction_status_label)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        
        # 添加工具栏
        toolbar_layout = QHBoxLayout()
        
        # 快速功能按钮
        self.quick_calibration_btn = QPushButton("快速校正")
        self.quick_calibration_btn.clicked.connect(self.quick_calibration)
        self.quick_calibration_btn.setToolTip("快速校正传感器")
        
        self.save_data_btn = QPushButton("保存数据")
        self.save_data_btn.clicked.connect(self.save_current_data)
        self.save_data_btn.setToolTip("保存当前传感器数据")
        
        self.export_report_btn = QPushButton("导出报告")
        self.export_report_btn.clicked.connect(self.export_consistency_report)
        self.export_report_btn.setToolTip("导出一致性分析报告")
        
        self.reset_calibration_btn = QPushButton("重置校正")
        self.reset_calibration_btn.clicked.connect(self.reset_calibration)
        self.reset_calibration_btn.setToolTip("重置校正设置")
        
        toolbar_layout.addWidget(self.quick_calibration_btn)
        toolbar_layout.addWidget(self.save_data_btn)
        toolbar_layout.addWidget(self.export_report_btn)
        toolbar_layout.addWidget(self.reset_calibration_btn)
        toolbar_layout.addStretch()
        
        # 热力图显示区域
        self.heatmap_widget = MatplotlibHeatmapWidget()
        
        # 数据信息显示
        info_layout = QHBoxLayout()
        self.max_value_label = QLabel("最大值: --")
        self.min_value_label = QLabel("最小值: --")
        self.mean_value_label = QLabel("平均值: --")
        self.sensor_info_label = QLabel("传感器: --")
        
        info_layout.addWidget(self.sensor_info_label)
        info_layout.addWidget(self.max_value_label)
        info_layout.addWidget(self.min_value_label)
        info_layout.addWidget(self.mean_value_label)
        info_layout.addStretch()
        
        # 一致性统计信息
        self.consistency_stats_label = QLabel("一致性统计: --")
        info_layout.addWidget(self.consistency_stats_label)
        
        # 组装左侧面板
        left_panel.addLayout(control_layout)
        left_panel.addLayout(toolbar_layout) # 添加工具栏布局
        left_panel.addWidget(self.heatmap_widget)
        left_panel.addLayout(info_layout)
        
        # 右侧：功能面板（使用标签页）
        right_panel = QVBoxLayout()
        
        # 创建标签页控件
        self.function_tabs = QTabWidget()
        
        # 一致性评估标签页
        self.function_tabs.addTab(self.consistency_widget, "一致性评估")
        
        # 校正系统标签页
        if self.calibration_widget:
            self.function_tabs.addTab(self.calibration_widget, "校正系统")
        
        # 简化校正标签页
        if self.uniform_calibration_widget:
            self.function_tabs.addTab(self.uniform_calibration_widget, "简化校正")
        
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
        self.status_bar_correction = QLabel("校正: 关闭")
        self.status_bar_data = QLabel("数据: --")
        self.status_bar_fps = QLabel("FPS: --")
        
        self.status_bar.addWidget(self.status_bar_sensor)
        self.status_bar.addWidget(self.status_bar_correction)
        self.status_bar.addWidget(self.status_bar_data)
        self.status_bar.addPermanentWidget(self.status_bar_fps)
        
        # 创建主窗口布局
        main_window_layout = QVBoxLayout()
        main_window_layout.addLayout(main_layout)
        main_window_layout.addWidget(self.status_bar)
        
        # 创建主容器
        main_container = QWidget()
        main_container.setLayout(main_window_layout)
        
        # 设置主布局
        self.setLayout(main_window_layout)
        
        # 设置右键菜单
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 为热力图组件也设置右键菜单
        self.heatmap_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.heatmap_widget.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        menu = self.create_advanced_menu()
        menu.exec_(self.mapToGlobal(position))
    
    def set_correction_enabled(self, enabled, calibration_map=None):
        """设置校正功能状态"""
        self.correction_enabled = enabled
        if calibration_map is not None:
            self.calibration_map = calibration_map
            
        # 更新状态显示
        if enabled:
            self.correction_status_label.setText("校正: 开启")
            self.correction_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.correction_status_label.setText("校正: 关闭")
            self.correction_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        # 同步简化校正系统的状态
        if self.uniform_calibration_widget:
            self.uniform_calibration_widget.enable_correction_check.setChecked(enabled)
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
    
    def on_colormap_changed(self, colormap_name):
        """颜色映射选择变化时的处理函数"""
        print(f"🔄 颜色映射选择变化为: {colormap_name}")
        # 如果传感器正在运行，立即更新显示
        if self.is_running:
            self.update_colormap()
    
    def update_colormap(self):
        """更新颜色映射"""
        try:
            colormap_name = self.colormap_combo.currentText()
            
            if colormap_name == "自动":
                # 自动模式，根据数据范围选择
                return  # 在update_heatmap中处理
            
            print(f"✅ 颜色映射已更新为: {colormap_name}")
        except Exception as e:
            print(f"⚠️ 更新颜色映射时出错: {e}")
    
    def get_colormap(self, data_range):
        """获取颜色映射 - 根据用户选择"""
        colormap_name = self.colormap_combo.currentText()
        
        if colormap_name == "自动":
            # 自动模式，对于固定范围0-0.01，使用viridis
            return 'viridis'
        else:
            # 手动选择
            return colormap_name
    
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
        """生成模拟传感器数据 - 增强版，模拟不一致性，固定范围0-0.01"""
        # 创建一个64x64的模拟传感器数据，包含已知的不一致性
        data = np.random.rand(64, 64) * 0.001  # 基础噪声，范围0-0.001
        
        # 模拟传感器敏感度不均匀（左侧敏感度较低，右侧较高）
        sensitivity_gradient = np.linspace(0.7, 1.3, 64)
        for i in range(64):
            data[i, :] *= sensitivity_gradient[i]
        
        # 模拟几个死区
        dead_zones = [(10, 15, 5), (40, 50, 3), (55, 20, 4)]  # (x, y, radius)
        for x, y, r in dead_zones:
            for i in range(max(0, x-r), min(64, x+r)):
                for j in range(max(0, y-r), min(64, y+r)):
                    if (i-x)**2 + (j-y)**2 <= r**2:
                        data[i, j] *= 0.1  # 降低响应
        
        # 随机生成按压区域
        num_presses = np.random.randint(2, 5)
        for _ in range(num_presses):
            center_x = np.random.randint(8, 56)
            center_y = np.random.randint(8, 56)
            
            for i in range(64):
                for j in range(64):
                    distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if distance < 10:
                        press_strength = 0.001 + np.random.rand() * 0.003  # 按压强度0.001-0.004
                        data[i, j] += press_strength * np.exp(-distance / 5)
        
        # 确保数据在0-0.01范围内
        data = np.clip(data, 0.0, 0.01)
        
        return data
    
    def save_current_data(self):
        """保存当前传感器数据"""
        if not self.is_running:
            QMessageBox.warning(self, "警告", "传感器未运行")
            return
        
        try:
            if self.data_handler:
                self.data_handler.trigger()
                with self.data_handler.lock:
                    if self.data_handler.value:
                        current_data = np.array(self.data_handler.value[-1])
                    else:
                        return
            else:
                current_data = self.generate_simulated_data()
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存当前数据", "", "Numpy文件 (*.npy);;CSV文件 (*.csv)"
            )
            
            if filename:
                if filename.endswith('.npy'):
                    np.save(filename, current_data)
                else:
                    np.savetxt(filename, current_data, delimiter=',')
                
                QMessageBox.information(self, "成功", f"数据已保存到: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def export_consistency_report(self):
        """导出一致性分析报告"""
        if not self.consistency_widget.consistency_data:
            QMessageBox.warning(self, "警告", "没有一致性数据")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出一致性报告", "", "文本文件 (*.txt);;HTML文件 (*.html)"
        )
        
        if filename:
            try:
                stats = self.consistency_widget.get_statistics()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 准备统计数据的格式化字符串
                mean_str = f"{stats['mean']:.4f}" if stats else 'N/A'
                std_str = f"{stats['std']:.4f}" if stats else 'N/A'
                cv_str = f"{stats['cv']*100:.1f}" if stats else 'N/A'
                min_str = f"{stats['min']:.4f}" if stats else 'N/A'
                max_str = f"{stats['max']:.4f}" if stats else 'N/A'
                
                report_content = f"""
传感器一致性分析报告
生成时间: {timestamp}
传感器: {self.sensor_combo.currentText()}

===== 基础统计 =====
数据点数量: {stats['count'] if stats else 0}
平均响应: {mean_str}
标准差: {std_str}
变异系数: {cv_str}%
最小值: {min_str}
最大值: {max_str}

===== 一致性评估 =====
记录帧数: {self.consistency_widget.recorded_frames}
评估状态: {'进行中' if self.consistency_widget.assessment_active else '已完成'}

===== 建议 =====
"""
                
                # 根据变异系数给出建议
                if stats and stats['cv'] > 0.3:
                    report_content += "- 传感器一致性较差，建议进行校正\n"
                elif stats and stats['cv'] > 0.15:
                    report_content += "- 传感器一致性中等，可考虑校正以提高精度\n"
                else:
                    report_content += "- 传感器一致性良好\n"
                
                # 保存报告
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                QMessageBox.information(self, "成功", f"报告已导出到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def quick_calibration(self):
        """快速校正功能"""
        if not self.is_running:
            QMessageBox.warning(self, "警告", "请先启动传感器")
            return
        
        # 询问用户选择校正方式
        msg = QMessageBox(self)
        msg.setWindowTitle("选择校正方式")
        msg.setText("请选择校正方式：\n\n1. 简化校正：使用均匀物体（如书本、平板）\n2. 传统校正：使用标准压力测试")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText("简化校正")
        msg.button(QMessageBox.No).setText("传统校正")
        
        result = msg.exec_()
        
        if result == QMessageBox.Yes and self.uniform_calibration_widget:
            # 切换到简化校正标签页
            self.function_tabs.setCurrentIndex(2)  # 简化校正标签页
            # 自动开始收集
            self.uniform_calibration_widget.start_reference_collection()
        elif result == QMessageBox.No and self.calibration_widget:
            # 切换到传统校正标签页
            self.function_tabs.setCurrentIndex(1)
            
            # 显示快速校正对话框
            msg = QMessageBox(self)
            msg.setWindowTitle("快速校正")
            msg.setText("快速校正将自动收集数据并生成校正映射。\n请确保传感器上有均匀的测试负载。")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            
            if msg.exec_() == QMessageBox.Ok:
                # 自动设置收集参数并开始
                self.calibration_widget.start_pressure_spin.setValue(1.0)
                self.calibration_widget.pressure_increment_spin.setValue(0.5)
                self.calibration_widget.steps_spin.setValue(3)
                self.calibration_widget.frames_per_step_spin.setValue(30)
                
                # 开始收集
                self.calibration_widget.start_calibration_collection()
    
    def reset_calibration(self):
        """重置校正功能"""
        self.set_correction_enabled(False)
        self.calibration_map = None
        
        # 重置校正组件状态
        if self.calibration_widget and hasattr(self.calibration_widget, 'enable_correction_check'):
            self.calibration_widget.enable_correction_check.setChecked(False)
        
        # 重置简化校正组件状态
        if self.uniform_calibration_widget:
            self.uniform_calibration_widget.enable_correction_check.setChecked(False)
            self.uniform_calibration_widget.calibration_map = None
            self.uniform_calibration_widget.reference_data = None
        
        QMessageBox.information(self, "重置完成", "校正功能已重置")
    
    def update_fps(self):
        """更新FPS计数"""
        now = datetime.now()
        time_diff = (now - self.last_fps_update).total_seconds()
        if time_diff > 0:
            self.fps_counter = self.frame_count / time_diff
            self.frame_count = 0
            self.last_fps_update = now
            self.update_status_bar()
    
    def update_data(self):
        """更新数据显示 - 修改版，添加校正功能"""
        try:
            # 增加帧计数
            self.frame_count += 1
            
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
            
            # 应用校正
            if self.correction_enabled and self.calibration_map is not None:
                try:
                    # 优先使用简化校正系统
                    if self.uniform_calibration_widget and self.uniform_calibration_widget.enable_correction_check.isChecked():
                        corrected_data = self.uniform_calibration_widget.apply_correction(current_data)
                        if corrected_data is not None:
                            current_data = corrected_data
                    # 否则使用传统校正系统
                    elif self.calibration_widget and hasattr(self.calibration_widget, 'apply_correction'):
                        corrected_data = self.calibration_widget.apply_correction(current_data)
                        if corrected_data is not None:
                            current_data = corrected_data
                except Exception as e:
                    print(f"⚠️ 校正应用失败: {e}")
                    # 校正失败时继续使用原始数据
                
            # 更新热力图
            colormap_name = self.get_colormap(current_data.max() - current_data.min())
            self.heatmap_widget.update_heatmap(current_data, colormap_name)
            
            # 更新数据信息
            self.update_data_info(current_data)
            
            # 处理一致性评估数据
            self.consistency_widget.process_frame(current_data)
            
            # 更新一致性统计信息
            self.update_consistency_stats()
            
        except USBError:
            print("❌ USB连接错误，停止传感器")
            self.stop_sensor()
            QMessageBox.critical(self, "USB错误", "USB连接错误，传感器已停止")
        except Exception as e:
            print(f"⚠️ 更新数据时出错: {e}")
    
    def update_data_info(self, data):
        """更新数据信息显示"""
        try:
            if data is not None and data.size > 0:
                self.max_value_label.setText(f"最大值: {data.max():.4f}")
                self.min_value_label.setText(f"最小值: {data.min():.4f}")
                self.mean_value_label.setText(f"平均值: {data.mean():.4f}")
                
                # 更新状态栏数据信息，显示固定范围
                self.status_bar_data.setText(f"压力: 最大={data.max():.4f}, 平均={data.mean():.4f} (范围: 0-0.01)")
        except Exception as e:
            print(f"⚠️ 更新数据信息时出错: {e}")
    
    def update_consistency_stats(self):
        """更新一致性统计信息"""
        stats = self.consistency_widget.get_statistics()
        if stats:
            cv_percent = stats['cv'] * 100
            stats_text = f"一致性: 均值={stats['mean']:.4f}, 标准差={stats['std']:.4f}, CV={cv_percent:.1f}%"
            self.consistency_stats_label.setText(stats_text)
        else:
            self.consistency_stats_label.setText("一致性统计: --")
    
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
                    self.timer.start(50)
                    self.fps_timer.start(1000)  # 每秒更新一次FPS
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
            self.timer.start(50)
            self.fps_timer.start(1000)  # 每秒更新一次FPS
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
        self.fps_timer.stop() # 停止FPS计时器
        
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
    
    def get_data_handler_status(self):
        """获取数据处理器状态"""
        if self.data_handler:
            return {
                'connected': self.is_running,
                'sensor_id': self.sensor_combo.currentText(),
                'port': self.port_input.text(),
                'data_available': self.data_handler.value is not None and len(self.data_handler.value) > 0
            }
        else:
            return {
                'connected': self.is_running,
                'sensor_id': self.sensor_combo.currentText(),
                'port': self.port_input.text(),
                'data_available': False,
                'mode': 'simulation'
            }
    
    def create_advanced_menu(self):
        """创建高级功能菜单"""
        menu = QtWidgets.QMenu(self)
        
        # 数据保存功能
        save_data_action = menu.addAction("保存当前数据")
        save_data_action.triggered.connect(self.save_current_data)
        
        # 一致性报告导出
        export_report_action = menu.addAction("导出一致性报告")
        export_report_action.triggered.connect(self.export_consistency_report)
        
        menu.addSeparator()
        
        # 快速校正功能
        quick_calibration_action = menu.addAction("快速校正")
        quick_calibration_action.triggered.connect(self.quick_calibration)
        
        # 重置校正
        reset_calibration_action = menu.addAction("重置校正")
        reset_calibration_action.triggered.connect(self.reset_calibration)
        
        menu.addSeparator()
        
        # 数据处理器状态
        status_action = menu.addAction("数据处理器状态")
        status_action.triggered.connect(self.show_data_handler_status)
        
        menu.addSeparator()
        
        # 帮助功能
        help_action = menu.addAction("使用帮助")
        help_action.triggered.connect(self.show_help)
        
        about_action = menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
        
        return menu
    
    def show_data_handler_status(self):
        """显示数据处理器状态"""
        status = self.get_data_handler_status()
        
        status_text = f"""
数据处理器状态:
连接状态: {'已连接' if status['connected'] else '未连接'}
传感器ID: {status['sensor_id']}
端口: {status['port']}
数据可用: {'是' if status['data_available'] else '否'}
"""
        
        if 'mode' in status:
            status_text += f"模式: {status['mode']}"
        
        QMessageBox.information(self, "数据处理器状态", status_text)
    
    def show_help(self):
        """显示使用帮助"""
        help_text = """
传感器界面使用帮助

===== 基本操作 =====
1. 选择传感器ID和端口
2. 点击"开始"按钮连接传感器
3. 观察热力图显示实时数据
4. 点击"停止"按钮断开连接

===== 数据显示 =====
• 压力数值范围固定为: 0-0.01
• 热力图颜色映射固定在此范围内
• 超出范围的值会被限制在边界内

===== 一致性评估 =====
1. 切换到"一致性评估"标签页
2. 点击"开始评估"开始收集数据
3. 在传感器上进行各种操作
4. 点击"停止评估"结束收集
5. 点击"显示一致性图"查看结果

===== 校正功能 =====
1. 快速校正：点击"快速校正"按钮
2. 传统校正：使用"校正系统"标签页
3. 简化校正：使用"简化校正"标签页
4. 重置校正：点击"重置校正"按钮

===== 数据保存 =====
1. 右键菜单 -> "保存当前数据"
2. 右键菜单 -> "导出一致性报告"
3. 工具栏按钮快速访问

===== 快捷键 =====
右键点击：打开高级功能菜单
"""
        QMessageBox.information(self, "使用帮助", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
传感器界面 - matplotlib版本

版本: 2.0
基于matplotlib实现，提供稳定的热力图显示

功能特性:
✓ 实时传感器数据显示
✓ 一致性评估分析
✓ 校正系统支持
✓ 数据保存和导出
✓ 中文界面支持
✓ 模拟数据模式

技术支持: 传感器研究团队
"""
        QMessageBox.about(self, "关于", about_text)
    
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
        
        # 更新校正状态
        if self.correction_enabled:
            self.status_bar_correction.setText("校正: 开启")
        else:
            self.status_bar_correction.setText("校正: 关闭")
        
        # 更新FPS
        if hasattr(self, 'fps_counter'):
            self.status_bar_fps.setText(f"FPS: {self.fps_counter:.1f}")
        else:
            self.status_bar_fps.setText("FPS: --")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_sensor()
        
        # 停止校正数据收集线程
        if hasattr(self.calibration_widget, 'collection_thread') and self.calibration_widget.collection_thread:
            self.calibration_widget.collection_thread.stop()
            self.calibration_widget.collection_thread.wait()
        
        # 停止简化校正系统的定时器
        if self.uniform_calibration_widget:
            self.uniform_calibration_widget.collection_timer.stop()
        
        event.accept()


# 使用示例和启动代码
def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MatplotlibSensorInterface()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
                 