"""
简单的传感器连接和热力图显示界面
基于原始代码简化，专注于传感器连接和原始数据显示
新增：传感器一致性评估功能
"""

import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QMessageBox, QVBoxLayout,
                            QGroupBox, QTextEdit, QFileDialog, QProgressBar,QTabWidget)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from usb.core import USBError
import json
from datetime import datetime

# 添加box-demo copy目录到Python路径
# current_dir = os.path.dirname(os.path.abspath(__file__))
# box_demo_path = os.path.join(current_dir, "box-demo copy")
# if os.path.exists(box_demo_path):
#     sys.path.insert(0, box_demo_path)
#     print(f"✅ 已添加路径: {box_demo_path}")
# else:
#     print(f"⚠️ 路径不存在: {box_demo_path}")

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
    """一致性热力图显示窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("传感器一致性热力图")
        self.setGeometry(200, 200, 1000, 800)  # 增大窗口尺寸
        self.setWindowFlags(QtCore.Qt.Window)  # 设置为独立窗口
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("传感器一致性热力图")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 热力图显示区域 - 完全重写
        heatmap_layout = QHBoxLayout()
        
        # 左侧：热力图
        self.heatmap_widget = pg.GraphicsLayoutWidget()
        self.heatmap_plot = self.heatmap_widget.addPlot() 
        self.heatmap_plot.setAspectLocked(False)
        
        # 创建图像项
        self.heatmap_image = pg.ImageItem()
        self.heatmap_plot.addItem(self.heatmap_image)
        
        # 设置坐标轴
        self.heatmap_plot.setLabel('left', 'Y轴')
        self.heatmap_plot.setLabel('bottom', 'X轴')
        self.heatmap_plot.setTitle('传感器数据热力图')
        
        # 右侧：增强的颜色条
        colorbar_layout = QVBoxLayout()
        
        # 颜色条标题
        colorbar_title = QLabel("数值范围")
        colorbar_title.setAlignment(QtCore.Qt.AlignCenter)
        colorbar_title.setStyleSheet("font-weight: bold; font-size: 12px; margin: 5px; color: #333;")
        colorbar_layout.addWidget(colorbar_title)
        
        # 创建增强的颜色条容器
        colorbar_container = QWidget()
        colorbar_container.setFixedWidth(120)  # 增加宽度
        colorbar_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        colorbar_container_layout = QVBoxLayout(colorbar_container)
        colorbar_container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 创建颜色条
        self.colorbar_widget = pg.GraphicsLayoutWidget()
        self.colorbar_widget.setFixedHeight(300)  # 增加高度
        self.colorbar_plot = self.colorbar_widget.addPlot()
        self.colorbar_plot.setAspectLocked(False)
        
        # 创建颜色条图像
        self.colorbar_image = pg.ImageItem()
        self.colorbar_plot.addItem(self.colorbar_image)
        
        # 设置颜色条坐标轴样式
        self.colorbar_plot.setLabel('left', '数值', color='#333', size='10pt')
        self.colorbar_plot.hideAxis('bottom')
        self.colorbar_plot.hideAxis('top')
        self.colorbar_plot.hideAxis('right')
        
        # 设置坐标轴样式
        self.colorbar_plot.getAxis('left').setPen(pg.mkPen(color='#333', width=1))
        self.colorbar_plot.getAxis('left').setTextPen(pg.mkPen(color='#333'))
        
        # 添加颜色条到容器
        colorbar_container_layout.addWidget(self.colorbar_widget)
        
        # 添加数值标签
        self.min_value_colorbar_label = QLabel("最小值: --")
        self.min_value_colorbar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        self.max_value_colorbar_label = QLabel("最大值: --")
        self.max_value_colorbar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        colorbar_container_layout.addWidget(self.max_value_colorbar_label)
        colorbar_container_layout.addStretch()
        colorbar_container_layout.addWidget(self.min_value_colorbar_label)
        
        colorbar_layout.addWidget(colorbar_container)
        colorbar_layout.addStretch()
        
        # 组装热力图布局
        heatmap_layout.addWidget(self.heatmap_widget, 4)  # 热力图占4/5
        heatmap_layout.addLayout(colorbar_layout, 1)      # 颜色条占1/5
        
        layout.addLayout(heatmap_layout)
        
        # 统计信息
        stats_group = QGroupBox("一致性统计信息")
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("统计信息: --")
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        # 添加详细统计信息
        self.detail_stats_label = QLabel("")
        self.detail_stats_label.setStyleSheet("font-size: 11px;")
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(self.detail_stats_label)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.save_heatmap_btn = QPushButton("保存热力图")
        self.save_heatmap_btn.clicked.connect(self.save_heatmap)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_heatmap_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def update_data(self, consistency_data):
        """更新一致性数据 - 增强版"""
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
            # 计算有效数据范围（排除最小的10%数据）
            sorted_values = np.sort(values)
            cutoff_index = max(1, int(len(sorted_values) * 0.1))  # 至少保留1个点
            min_meaningful = sorted_values[cutoff_index]
            
            # 创建显示矩阵，小于阈值的设为0
            display_matrix = matrix.copy()
            display_matrix[display_matrix < min_meaningful] = 0
            
            # 更新热力图
            self.heatmap_image.setImage(display_matrix.T)  # 转置以匹配显示方向
            
            # 设置颜色范围（从有意义的最小值到最大值）
            if display_matrix.max() > 0:
                min_val, max_val = min_meaningful, display_matrix.max()
                self.heatmap_image.setLevels((min_val, max_val))
                
                # 使用与主界面一致的颜色映射逻辑
                data_range = max_val - min_val
                if data_range < 0.1:
                    colormap = pg.colormap.get('plasma')
                elif data_range < 0.5:
                    colormap = pg.colormap.get('viridis')
                else:
                    colormap = pg.colormap.get('turbo')
                
                self.heatmap_image.setColorMap(colormap)
                
                # 更新颜色条
                self.update_colorbar(min_val, max_val)
            
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
        
    def update_colorbar(self, min_val, max_val):
        """更新颜色条 - 增强版"""
        try:
            # 创建颜色条数据 - 修复：确保数据从最小值到最大值渐变，垂直方向
            # 注意：pyqtgraph中Y轴向下为正，所以需要反转数据顺序
            colorbar_data = np.linspace(max_val, min_val, 100).reshape(100, 1)
            self.colorbar_image.setImage(colorbar_data)
            
            # 重要：设置颜色条的数据范围，确保与热力图一致
            self.colorbar_image.setLevels((min_val, max_val))
            
            # 使用与主界面一致的颜色映射逻辑
            data_range = max_val - min_val
            if data_range < 0.1:
                colormap = pg.colormap.get('plasma')
            elif data_range < 0.5:
                colormap = pg.colormap.get('viridis')
            else:
                colormap = pg.colormap.get('turbo')
            
            self.colorbar_image.setColorMap(colormap)
            
            # 设置颜色条标签 - 设置正确的Y轴范围
            self.colorbar_plot.setYRange(min_val, max_val)
            self.colorbar_plot.setXRange(0, 1)  # 固定X轴范围
            
            # 更新数值标签
            self.min_value_colorbar_label.setText(f"最小值: {min_val:.4f}")
            self.max_value_colorbar_label.setText(f"最大值: {max_val:.4f}")
            
            # 动态调整标签颜色
            if max_val > min_val * 2:  # 如果最大值是最最小值的2倍以上
                self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #d63384; font-weight: bold; margin: 2px;")
                self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #0d6efd; font-weight: bold; margin: 2px;")
            else:
                self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
                self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
                
        except Exception as e:
            print(f"⚠️ 更新颜色条时出错: {e}")
        
    def save_heatmap(self):
        """保存热力图"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存热力图", "", "PNG图片 (*.png);;JPG图片 (*.jpg)"
        )
        
        if filename:
            try:
                # 截取热力图区域并保存
                self.heatmap_widget.grab().save(filename)
                QMessageBox.information(self, "成功", f"热力图已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

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
        self.show_consistency_btn.setEnabled(True)  # 启用显示一致性图按钮
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

class SimpleSensorInterface(QWidget):
    """简单的传感器连接和热力图显示界面 - 增强版"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.data_handler = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 校正相关属性
        self.correction_enabled = False
        self.calibration_map = None
        
        # 一致性评估组件
        self.consistency_widget = ConsistencyAssessmentWidget()
        
        # 校正组件 - 新增
        self.calibration_widget = CalibrationWidget(self)  # 传递self作为parent
        
        # 简化校正组件 - 新增
        self.uniform_calibration_widget = UniformObjectCalibration(self) if UNIFORM_CALIBRATION_AVAILABLE else None
        
        # 设置窗口属性
        self.setWindowTitle("传感器界面 - 一致性分析与校正系统")
        self.setGeometry(100, 100, 1400, 900)  # 增大窗口以容纳新功能
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据处理器
        self.init_data_handler()
        
    def init_ui(self):
        """初始化用户界面 - 修改版"""
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
        
        # 颜色映射选择器 - 新增
        self.colormap_label = QLabel("颜色方案:")
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["自动", "viridis", "plasma", "turbo", "inferno", "magma", "cividis"])
        self.colormap_combo.setCurrentText("自动")
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        self.colormap_combo.setToolTip("选择热力图颜色方案")
        
        # 校正状态指示 - 新增
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
        control_layout.addWidget(self.colormap_label)  # 新增
        control_layout.addWidget(self.colormap_combo)   # 新增
        control_layout.addWidget(self.correction_status_label)  # 新增
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        
        # 热力图显示区域 - 完全重写
        heatmap_layout = QHBoxLayout()
        
        # 左侧：热力图
        self.heatmap_widget = pg.GraphicsLayoutWidget()
        self.heatmap_plot = self.heatmap_widget.addPlot() 
        self.heatmap_plot.setAspectLocked(False)
        
        # 创建图像项
        self.heatmap_image = pg.ImageItem()
        self.heatmap_plot.addItem(self.heatmap_image)
        
        # 设置坐标轴
        self.heatmap_plot.setLabel('left', 'Y轴')
        self.heatmap_plot.setLabel('bottom', 'X轴')
        self.heatmap_plot.setTitle('传感器数据热力图')
        
        # 右侧：增强的颜色条
        colorbar_layout = QVBoxLayout()
        
        # 颜色条标题
        colorbar_title = QLabel("数值范围")
        colorbar_title.setAlignment(QtCore.Qt.AlignCenter)
        colorbar_title.setStyleSheet("font-weight: bold; font-size: 12px; margin: 5px; color: #333;")
        colorbar_layout.addWidget(colorbar_title)
        
        # 创建增强的颜色条容器
        colorbar_container = QWidget()
        colorbar_container.setFixedWidth(120)  # 增加宽度
        colorbar_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        colorbar_container_layout = QVBoxLayout(colorbar_container)
        colorbar_container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 创建颜色条
        self.colorbar_widget = pg.GraphicsLayoutWidget()
        self.colorbar_widget.setFixedHeight(300)  # 增加高度
        self.colorbar_plot = self.colorbar_widget.addPlot()
        self.colorbar_plot.setAspectLocked(False)
        
        # 创建颜色条图像
        self.colorbar_image = pg.ImageItem()
        self.colorbar_plot.addItem(self.colorbar_image)
        
        # 设置颜色条坐标轴样式
        self.colorbar_plot.setLabel('left', '数值', color='#333', size='10pt')
        self.colorbar_plot.hideAxis('bottom')
        self.colorbar_plot.hideAxis('top')
        self.colorbar_plot.hideAxis('right')
        
        # 设置坐标轴样式
        self.colorbar_plot.getAxis('left').setPen(pg.mkPen(color='#333', width=1))
        self.colorbar_plot.getAxis('left').setTextPen(pg.mkPen(color='#333'))
        
        # 添加颜色条到容器
        colorbar_container_layout.addWidget(self.colorbar_widget)
        
        # 添加数值标签
        self.min_value_colorbar_label = QLabel("最小值: --")
        self.min_value_colorbar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        self.max_value_colorbar_label = QLabel("最大值: --")
        self.max_value_colorbar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        colorbar_container_layout.addWidget(self.max_value_colorbar_label)
        colorbar_container_layout.addStretch()
        colorbar_container_layout.addWidget(self.min_value_colorbar_label)
        
        colorbar_layout.addWidget(colorbar_container)
        colorbar_layout.addStretch()
        
        # 组装热力图布局
        heatmap_layout.addWidget(self.heatmap_widget, 4)  # 热力图占4/5
        heatmap_layout.addLayout(colorbar_layout, 1)      # 颜色条占1/5
        
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
        left_panel.addLayout(heatmap_layout)  # 添加热力图布局
        left_panel.addLayout(info_layout)
        
        # 右侧：功能面板（使用标签页）
        right_panel = QVBoxLayout()
        
        # 创建标签页控件
        self.function_tabs = QTabWidget()
        
        # 一致性评估标签页
        self.function_tabs.addTab(self.consistency_widget, "一致性评估")
        
        # 校正系统标签页 - 新增
        self.function_tabs.addTab(self.calibration_widget, "校正系统")
        
        # 简化校正标签页 - 新增
        if self.uniform_calibration_widget:
            self.function_tabs.addTab(self.uniform_calibration_widget, "简化校正")
        
        right_panel.addWidget(self.function_tabs)
        
        # 组装主布局
        main_layout.addLayout(left_panel, 2)   # 左侧占2/3
        main_layout.addLayout(right_panel, 1)  # 右侧占1/3
        
        self.setLayout(main_layout)
        
    def set_correction_enabled(self, enabled, calibration_map=None):
        """设置校正功能状态 - 新增方法"""
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
    
    def update_data(self):
        """更新数据显示 - 修改版，添加校正功能"""
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
            
            # 应用校正 - 新增功能
            if self.correction_enabled and self.calibration_map is not None:
                try:
                    # 优先使用简化校正系统
                    if self.uniform_calibration_widget and self.uniform_calibration_widget.enable_correction_check.isChecked():
                        corrected_data = self.uniform_calibration_widget.apply_correction(current_data)
                        if corrected_data is not None:
                            current_data = corrected_data
                    # 否则使用传统校正系统
                    elif hasattr(self.calibration_widget, 'apply_correction'):
                        corrected_data = self.calibration_widget.apply_correction(current_data)
                        if corrected_data is not None:
                            current_data = corrected_data
                except Exception as e:
                    print(f"⚠️ 校正应用失败: {e}")
                    # 校正失败时继续使用原始数据
                
            # 更新热力图
            self.update_heatmap(current_data)
            
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
    
    def get_data_handler_status(self):
        """获取数据处理器状态信息 - 新增调试方法"""
        status = {
            'has_data_handler': self.data_handler is not None,
            'is_running': self.is_running,
            'data_handler_type': type(self.data_handler).__name__ if self.data_handler else 'None'
        }
        
        if self.data_handler:
            try:
                with self.data_handler.lock:
                    status['has_value'] = self.data_handler.value is not None
                    status['value_length'] = len(self.data_handler.value) if self.data_handler.value else 0
            except Exception as e:
                status['lock_error'] = str(e)
        
        return status
    
    def generate_simulated_data(self):
        """生成模拟传感器数据 - 增强版，模拟不一致性"""
        # 创建一个64x64的模拟传感器数据，包含已知的不一致性
        data = np.random.rand(64, 64) * 0.01
        
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
                        press_strength = 0.3 + np.random.rand() * 0.4
                        data[i, j] += press_strength * np.exp(-distance / 5)
                        
        return data
    
    def save_current_data(self):
        """保存当前传感器数据 - 新增方法"""
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
        """导出一致性分析报告 - 新增方法"""
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
    
    def create_advanced_menu(self):
        """创建高级功能菜单 - 新增方法"""
        menubar = self.menuBar() if hasattr(self, 'menuBar') else None
        
        if menubar:
            # 数据菜单
            data_menu = menubar.addMenu('数据')
            
            save_action = data_menu.addAction('保存当前数据')
            save_action.triggered.connect(self.save_current_data)
            
            export_action = data_menu.addAction('导出一致性报告')
            export_action.triggered.connect(self.export_consistency_report)
            
            # 校正菜单
            calibration_menu = menubar.addMenu('校正')
            
            quick_calibration_action = calibration_menu.addAction('快速校正')
            quick_calibration_action.triggered.connect(self.quick_calibration)
            
            reset_calibration_action = calibration_menu.addAction('重置校正')
            reset_calibration_action.triggered.connect(self.reset_calibration)
    
    def quick_calibration(self):
        """快速校正功能 - 新增方法"""
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
        elif result == QMessageBox.No:
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
        """重置校正功能 - 新增方法"""
        self.set_correction_enabled(False)
        self.calibration_map = None
        
        # 重置校正组件状态
        if hasattr(self.calibration_widget, 'enable_correction_check'):
            self.calibration_widget.enable_correction_check.setChecked(False)
        
        # 重置简化校正组件状态
        if self.uniform_calibration_widget:
            self.uniform_calibration_widget.enable_correction_check.setChecked(False)
            self.uniform_calibration_widget.calibration_map = None
            self.uniform_calibration_widget.reference_data = None
        
        QMessageBox.information(self, "重置完成", "校正功能已重置")
    
    # 保持原有的其他方法不变...
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
            
            # 手动选择颜色映射
            colormap = pg.colormap.get(colormap_name)
            if colormap:
                self.heatmap_image.setColorMap(colormap)
                # 同时更新颜色条
                if hasattr(self, 'colorbar_image'):
                    self.colorbar_image.setColorMap(colormap)
                print(f"✅ 颜色映射已更新为: {colormap_name}")
            else:
                print(f"⚠️ 未找到颜色映射: {colormap_name}")
                
        except Exception as e:
            print(f"⚠️ 更新颜色映射时出错: {e}")
    
    def get_colormap(self, data_range):
        """获取颜色映射 - 根据用户选择或自动选择"""
        colormap_name = self.colormap_combo.currentText()
        
        if colormap_name == "自动":
            # 自动模式，根据数据范围选择
            if data_range < 0.1:
                return pg.colormap.get('plasma')
            elif data_range < 0.5:
                return pg.colormap.get('viridis')
            else:
                return pg.colormap.get('turbo')
        else:
            # 手动选择
            return pg.colormap.get(colormap_name)
    
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
                    self.update_ui_state()
                    self.status_label.setText(f"状态: 已连接 (传感器{sensor_id})")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.sensor_info_label.setText(f"传感器: {sensor_id}")
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
            self.timer.start(100)
            self.update_ui_state()
            self.status_label.setText(f"状态: 模拟模式 (传感器{sensor_id})")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.sensor_info_label.setText(f"传感器: {sensor_id} (模拟)")
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
        self.sensor_info_label.setText("传感器: --")
        
        self.clear_heatmap()
    
    def update_ui_state(self):
        """更新UI状态"""
        self.start_button.setEnabled(not self.is_running)
        self.stop_button.setEnabled(self.is_running)
        self.port_input.setEnabled(not self.is_running)
        self.sensor_combo.setEnabled(not self.is_running)
    
    def update_consistency_stats(self):
        """更新一致性统计信息"""
        stats = self.consistency_widget.get_statistics()
        if stats:
            cv_percent = stats['cv'] * 100
            stats_text = f"一致性: 均值={stats['mean']:.4f}, 标准差={stats['std']:.4f}, CV={cv_percent:.1f}%"
            self.consistency_stats_label.setText(stats_text)
        else:
            self.consistency_stats_label.setText("一致性统计: --")
    
    def update_heatmap(self, data):
        """更新热力图显示 - 增强版"""
        try:
            if data is None or data.size == 0:
                return
                
            display_data = apply_swap(data.T) if 'apply_swap' in globals() else data.T
            self.heatmap_image.setImage(display_data)
            
            if data.max() > data.min():
                sorted_data = np.sort(data.flatten())
                cutoff_index = max(1, int(len(sorted_data) * 0.05))
                min_meaningful = sorted_data[cutoff_index]
                max_val = data.max()
                
                if max_val - min_meaningful < 0.001:
                    # 如果数据范围很小，使用完整范围
                    min_val, max_val = data.min(), data.max()
                    self.heatmap_image.setLevels((min_val, max_val))
                    # 更新颜色条
                    self.update_colorbar(min_val, max_val)
                else:
                    # 使用有意义的数据范围
                    self.heatmap_image.setLevels((min_meaningful, max_val))
                    # 更新颜色条
                    self.update_colorbar(min_meaningful, max_val)
                
                # 使用新的颜色映射选择逻辑
                data_range = max_val - min_meaningful
                colormap = self.get_colormap(data_range)
                if colormap:
                    self.heatmap_image.setColorMap(colormap)
                
        except Exception as e:
            print(f"⚠️ 更新热力图时出错: {e}")
    
    def update_colorbar(self, min_val, max_val):
        """更新颜色条 - 增强版"""
        try:
            # 创建颜色条数据 - 修复：确保数据从最小值到最大值渐变，垂直方向
            # 注意：pyqtgraph中Y轴向下为正，所以需要反转数据顺序
            colorbar_data = np.linspace(max_val, min_val, 100).reshape(100, 1)
            self.colorbar_image.setImage(colorbar_data)
            
            # 重要：设置颜色条的数据范围，确保与热力图一致
            self.colorbar_image.setLevels((min_val, max_val))
            
            # 使用与主界面一致的颜色映射逻辑
            data_range = max_val - min_val
            if data_range < 0.1:
                colormap = pg.colormap.get('plasma')
            elif data_range < 0.5:
                colormap = pg.colormap.get('viridis')
            else:
                colormap = pg.colormap.get('turbo')
            
            self.colorbar_image.setColorMap(colormap)
            
            # 设置颜色条标签 - 设置正确的Y轴范围
            self.colorbar_plot.setYRange(min_val, max_val)
            self.colorbar_plot.setXRange(0, 1)  # 固定X轴范围
            
            # 更新数值标签
            self.min_value_colorbar_label.setText(f"最小值: {min_val:.4f}")
            self.max_value_colorbar_label.setText(f"最大值: {max_val:.4f}")
            
            # 动态调整标签颜色
            if max_val > min_val * 2:  # 如果最大值是最最小值的2倍以上
                self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #d63384; font-weight: bold; margin: 2px;")
                self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #0d6efd; font-weight: bold; margin: 2px;")
            else:
                self.max_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
                self.min_value_colorbar_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
                
        except Exception as e:
            print(f"⚠️ 更新颜色条时出错: {e}")
    
    def update_data_info(self, data):
        """更新数据信息显示"""
        try:
            if data is not None and data.size > 0:
                self.max_value_label.setText(f"最大值: {data.max():.4f}")
                self.min_value_label.setText(f"最小值: {data.min():.4f}")
                self.mean_value_label.setText(f"平均值: {data.mean():.4f}")
        except Exception as e:
            print(f"⚠️ 更新数据信息时出错: {e}")
    
    def clear_heatmap(self):
        """清空热力图"""
        try:
            if self.data_handler and hasattr(self.data_handler.driver, 'SENSOR_SHAPE'):
                shape = self.data_handler.driver.SENSOR_SHAPE
            else:
                shape = (64, 64)
                
            empty_data = np.zeros(shape)
            self.heatmap_image.setImage(empty_data)
            
            # 设置空数据的颜色条范围
            self.heatmap_image.setLevels((0, 1))
            self.update_colorbar(0, 1)
            
            self.max_value_label.setText("最大值: --")
            self.min_value_label.setText("最小值: --")
            self.mean_value_label.setText("平均值: --")
            self.consistency_stats_label.setText("一致性统计: --")
        except Exception as e:
            print(f"⚠️ 清空热力图时出错: {e}")
    
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
    window = SimpleSensorInterface()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()