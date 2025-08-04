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
from PyQt5.QtCore import QTimer, pyqtSignal, QSize
import pyqtgraph as pg
from usb.core import USBError
import json
from datetime import datetime
import threading
import time
import csv

# 导入位置校准管理器
try:
    from position_calibration_manager import PositionCalibrationManager
    POSITION_CALIBRATION_AVAILABLE = True
    print("✅ 位置校准管理器模块导入成功")
except ImportError as e:
    print(f"⚠️ 位置校准管理器未找到: {e}")
    print("⚠️ 将使用传统校准方式")
    POSITION_CALIBRATION_AVAILABLE = False

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

class CalibrationAnalysisDialog(QtWidgets.QDialog):
    """校正数据分析弹窗"""
    
    def __init__(self, raw_data, calibrated_data, calibration_loader, parent=None):
        super().__init__(parent)
        self.raw_data = raw_data
        self.calibrated_data = calibrated_data
        self.calibration_loader = calibration_loader
        self.parent = parent  # 保存父窗口引用
        
        self.setWindowTitle("校正数据分析 (实时)")
        self.setGeometry(200, 200, 1000, 700)
        self.setModal(False)  # 改为非模态，允许实时更新
        
        # 创建定时器用于实时更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_analysis_data)
        self.update_timer.start(500)  # 每500ms更新一次
        
        self.init_ui()
        self.analyze_data()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题和状态
        title_layout = QHBoxLayout()
        
        title_label = QLabel("校正数据分析 (实时)")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # 实时状态指示器
        self.realtime_indicator = QLabel("● 实时更新中")
        self.realtime_indicator.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold; margin: 10px;")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.realtime_indicator)
        
        layout.addLayout(title_layout)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 统计信息选项卡
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "统计信息")
        
        # 热力图对比选项卡
        heatmap_tab = self.create_heatmap_tab()
        tab_widget.addTab(heatmap_tab, "热力图对比")
        
        # 差异分析选项卡
        diff_tab = self.create_diff_tab()
        tab_widget.addTab(diff_tab, "差异分析")
        
        # 校正映射信息选项卡
        cal_info_tab = self.create_cal_info_tab()
        tab_widget.addTab(cal_info_tab, "校正映射信息")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        # 实时更新控制
        self.pause_btn = QPushButton("暂停更新")
        self.pause_btn.clicked.connect(self.toggle_update)
        self.pause_btn.setStyleSheet("background-color: #ffc107; color: white; font-weight: bold; padding: 6px;")
        
        self.update_interval_label = QLabel("更新间隔: 500ms")
        self.update_interval_label.setStyleSheet("font-size: 11px; color: #666; margin: 5px;")
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 8px;")
        
        export_btn = QPushButton("导出分析报告")
        export_btn.clicked.connect(self.export_report)
        export_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.update_interval_label)
        button_layout.addStretch()
        button_layout.addWidget(export_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def toggle_update(self):
        """切换更新状态"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.pause_btn.setText("继续更新")
            self.pause_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
            self.realtime_indicator.setText("○ 已暂停")
            self.realtime_indicator.setStyleSheet("font-size: 12px; color: #6c757d; font-weight: bold; margin: 10px;")
        else:
            self.update_timer.start(500)
            self.pause_btn.setText("暂停更新")
            self.pause_btn.setStyleSheet("background-color: #ffc107; color: white; font-weight: bold; padding: 6px;")
            self.realtime_indicator.setText("● 实时更新中")
            self.realtime_indicator.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold; margin: 10px;")
    
    def update_analysis_data(self):
        """实时更新分析数据"""
        try:
            # 检查数据是否有效
            if self.raw_data is None or self.calibrated_data is None:
                return
            
            # 确保数据是numpy数组
            if not isinstance(self.raw_data, np.ndarray):
                self.raw_data = np.array(self.raw_data)
            if not isinstance(self.calibrated_data, np.ndarray):
                self.calibrated_data = np.array(self.calibrated_data)
            
            # 检查数据形状是否正确
            if self.raw_data.shape != (64, 64) or self.calibrated_data.shape != (64, 64):
                print(f"⚠️ 数据形状不正确: raw={self.raw_data.shape}, cal={self.calibrated_data.shape}")
                return
            
            # 更新各个选项卡的数据
            self.update_stats_tab()
            self.update_heatmap_tab()
            self.update_diff_tab()
            
            # 更新分析结果
            self.analyze_data()
            
        except Exception as e:
            print(f"⚠️ 实时更新分析数据失败: {e}")
    
    def update_stats_tab(self):
        """更新统计信息选项卡"""
        try:
            if not hasattr(self, 'raw_stats_labels') or not hasattr(self, 'cal_stats_labels'):
                return
            
            # 重新计算统计信息
            raw_stats = self.calculate_stats(self.raw_data)
            cal_stats = self.calculate_stats(self.calibrated_data)
            
            # 更新原始数据统计标签
            if len(self.raw_stats_labels) >= 6:
                self.raw_stats_labels[0].setText(f"总压力: {raw_stats['total']:.4f} N")
                self.raw_stats_labels[1].setText(f"平均压力: {raw_stats['mean']:.6f} N")
                self.raw_stats_labels[2].setText(f"标准差: {raw_stats['std']:.6f} N")
                self.raw_stats_labels[3].setText(f"最大值: {raw_stats['max']:.6f} N")
                self.raw_stats_labels[4].setText(f"最小值: {raw_stats['min']:.6f} N")
                self.raw_stats_labels[5].setText(f"变异系数: {raw_stats['cv']:.4f}")
            
            # 更新校正后数据统计标签
            if len(self.cal_stats_labels) >= 6:
                self.cal_stats_labels[0].setText(f"总压力: {cal_stats['total']:.4f} N")
                self.cal_stats_labels[1].setText(f"平均压力: {cal_stats['mean']:.6f} N")
                self.cal_stats_labels[2].setText(f"标准差: {cal_stats['std']:.6f} N")
                self.cal_stats_labels[3].setText(f"最大值: {cal_stats['max']:.6f} N")
                self.cal_stats_labels[4].setText(f"最小值: {cal_stats['min']:.6f} N")
                self.cal_stats_labels[5].setText(f"变异系数: {cal_stats['cv']:.4f}")
            
            # 更新校正效果
            if hasattr(self, 'effect_label'):
                try:
                    total_diff = cal_stats['total'] - raw_stats['total']
                    mean_diff = cal_stats['mean'] - raw_stats['mean']
                    std_diff = cal_stats['std'] - raw_stats['std']
                    cv_diff = cal_stats['cv'] - raw_stats['cv']
                    
                    effect_text = f"总压力变化: {total_diff:+.4f} N ({total_diff/raw_stats['total']*100:+.2f}%)\n"
                    effect_text += f"平均压力变化: {mean_diff:+.6f} N ({mean_diff/raw_stats['mean']*100:+.2f}%)\n"
                    effect_text += f"标准差变化: {std_diff:+.6f} N ({std_diff/raw_stats['std']*100:+.2f}%)\n"
                    effect_text += f"变异系数变化: {cv_diff:+.4f} ({cv_diff/raw_stats['cv']*100:+.2f}%)"
                    
                    self.effect_label.setText(effect_text)
                except ZeroDivisionError:
                    self.effect_label.setText("校正效果: 数据异常")
                    
        except Exception as e:
            print(f"⚠️ 更新统计信息失败: {e}")
    
    def update_heatmap_tab(self):
        """更新热力图选项卡"""
        try:
            # 更新原始数据热力图
            if hasattr(self, 'raw_image') and self.raw_image is not None:
                self.raw_image.setImage(self.raw_data.T)
                
                # 更新颜色条范围
                raw_min, raw_max = np.min(self.raw_data), np.max(self.raw_data)
                if hasattr(self, 'raw_colorbar') and self.raw_colorbar is not None:
                    self.raw_colorbar.setLevels((raw_min, raw_max))
            
            # 更新校正后数据热力图
            if hasattr(self, 'cal_image') and self.cal_image is not None:
                self.cal_image.setImage(self.calibrated_data.T)
                
                # 更新颜色条范围
                cal_min, cal_max = np.min(self.calibrated_data), np.max(self.calibrated_data)
                if hasattr(self, 'cal_colorbar') and self.cal_colorbar is not None:
                    self.cal_colorbar.setLevels((cal_min, cal_max))
                    
        except Exception as e:
            print(f"⚠️ 更新热力图失败: {e}")
    
    def update_diff_tab(self):
        """更新差异分析选项卡"""
        try:
            # 计算新的差异
            diff_data = self.calibrated_data - self.raw_data
            
            # 更新差异热力图
            if hasattr(self, 'diff_image') and self.diff_image is not None:
                self.diff_image.setImage(diff_data.T)
                
                # 更新颜色条范围
                diff_min, diff_max = np.min(diff_data), np.max(diff_data)
                if hasattr(self, 'diff_colorbar') and self.diff_colorbar is not None:
                    self.diff_colorbar.setLevels((diff_min, diff_max))
            
            # 更新差异统计
            if hasattr(self, 'diff_stats_labels') and len(self.diff_stats_labels) >= 6:
                diff_stats = self.calculate_stats(diff_data)
                self.diff_stats_labels[0].setText(f"总差异: {diff_stats['total']:.4f} N")
                self.diff_stats_labels[1].setText(f"平均差异: {diff_stats['mean']:.6f} N")
                self.diff_stats_labels[2].setText(f"标准差: {diff_stats['std']:.6f} N")
                self.diff_stats_labels[3].setText(f"最大差异: {diff_stats['max']:.6f} N")
                self.diff_stats_labels[4].setText(f"最小差异: {diff_stats['min']:.6f} N")
                self.diff_stats_labels[5].setText(f"差异范围: {diff_stats['max'] - diff_stats['min']:.6f} N")
                    
        except Exception as e:
            print(f"⚠️ 更新差异分析失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 停止定时器
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
                print("✅ 校正数据分析定时器已停止")
            
            # 清理资源
            if hasattr(self, 'raw_image'):
                self.raw_image = None
            if hasattr(self, 'cal_image'):
                self.cal_image = None
            if hasattr(self, 'diff_image'):
                self.diff_image = None
            if hasattr(self, 'raw_colorbar'):
                self.raw_colorbar = None
            if hasattr(self, 'cal_colorbar'):
                self.cal_colorbar = None
            if hasattr(self, 'diff_colorbar'):
                self.diff_colorbar = None
            
            print("✅ 校正数据分析窗口已关闭")
            event.accept()
            
        except Exception as e:
            print(f"⚠️ 关闭校正数据分析窗口时出错: {e}")
            event.accept()
    
    def create_stats_tab(self):
        """创建统计信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 基本统计信息
        stats_group = QGroupBox("基本统计信息")
        stats_layout = QGridLayout()
        
        # 原始数据统计
        raw_stats = self.calculate_stats(self.raw_data)
        stats_layout.addWidget(QLabel("原始数据:"), 0, 0)
        
        # 保存原始数据统计标签为实例变量
        self.raw_stats_labels = []
        self.raw_stats_labels.append(QLabel(f"总压力: {raw_stats['total']:.4f} N"))
        self.raw_stats_labels.append(QLabel(f"平均压力: {raw_stats['mean']:.6f} N"))
        self.raw_stats_labels.append(QLabel(f"标准差: {raw_stats['std']:.6f} N"))
        self.raw_stats_labels.append(QLabel(f"最大值: {raw_stats['max']:.6f} N"))
        self.raw_stats_labels.append(QLabel(f"最小值: {raw_stats['min']:.6f} N"))
        self.raw_stats_labels.append(QLabel(f"变异系数: {raw_stats['cv']:.4f}"))
        
        stats_layout.addWidget(self.raw_stats_labels[0], 0, 1)
        stats_layout.addWidget(self.raw_stats_labels[1], 0, 2)
        stats_layout.addWidget(self.raw_stats_labels[2], 0, 3)
        stats_layout.addWidget(self.raw_stats_labels[3], 1, 1)
        stats_layout.addWidget(self.raw_stats_labels[4], 1, 2)
        stats_layout.addWidget(self.raw_stats_labels[5], 1, 3)
        
        # 校正后数据统计
        cal_stats = self.calculate_stats(self.calibrated_data)
        stats_layout.addWidget(QLabel("校正后数据:"), 2, 0)
        
        # 保存校正后数据统计标签为实例变量
        self.cal_stats_labels = []
        self.cal_stats_labels.append(QLabel(f"总压力: {cal_stats['total']:.4f} N"))
        self.cal_stats_labels.append(QLabel(f"平均压力: {cal_stats['mean']:.6f} N"))
        self.cal_stats_labels.append(QLabel(f"标准差: {cal_stats['std']:.6f} N"))
        self.cal_stats_labels.append(QLabel(f"最大值: {cal_stats['max']:.6f} N"))
        self.cal_stats_labels.append(QLabel(f"最小值: {cal_stats['min']:.6f} N"))
        self.cal_stats_labels.append(QLabel(f"变异系数: {cal_stats['cv']:.4f}"))
        
        stats_layout.addWidget(self.cal_stats_labels[0], 2, 1)
        stats_layout.addWidget(self.cal_stats_labels[1], 2, 2)
        stats_layout.addWidget(self.cal_stats_labels[2], 2, 3)
        stats_layout.addWidget(self.cal_stats_labels[3], 3, 1)
        stats_layout.addWidget(self.cal_stats_labels[4], 3, 2)
        stats_layout.addWidget(self.cal_stats_labels[5], 3, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 校正效果分析
        effect_group = QGroupBox("校正效果分析")
        effect_layout = QVBoxLayout()
        
        # 计算校正效果
        total_diff = cal_stats['total'] - raw_stats['total']
        mean_diff = cal_stats['mean'] - raw_stats['mean']
        std_diff = cal_stats['std'] - raw_stats['std']
        cv_diff = cal_stats['cv'] - raw_stats['cv']
        
        effect_text = f"总压力变化: {total_diff:+.4f} N ({total_diff/raw_stats['total']*100:+.2f}%)\n"
        effect_text += f"平均压力变化: {mean_diff:+.6f} N ({mean_diff/raw_stats['mean']*100:+.2f}%)\n"
        effect_text += f"标准差变化: {std_diff:+.6f} N ({std_diff/raw_stats['std']*100:+.2f}%)\n"
        effect_text += f"变异系数变化: {cv_diff:+.4f} ({cv_diff/raw_stats['cv']*100:+.2f}%)"
        
        # 保存校正效果标签为实例变量
        self.effect_label = QLabel(effect_text)
        self.effect_label.setStyleSheet("font-family: monospace; font-size: 12px; background-color: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px;")
        effect_layout.addWidget(self.effect_label)
        
        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_heatmap_tab(self):
        """创建热力图对比选项卡"""
        widget = QWidget()
        layout = QHBoxLayout()
        
        # 原始数据热力图
        raw_group = QGroupBox("原始数据热力图")
        raw_layout = QVBoxLayout()
        
        raw_plot = pg.GraphicsLayoutWidget()
        raw_plot_widget = raw_plot.addPlot()
        raw_plot_widget.setLabel('left', 'Y轴')
        raw_plot_widget.setLabel('bottom', 'X轴')
        raw_plot_widget.setTitle('原始数据')
        raw_plot_widget.invertY(True)
        
        # 保存原始数据图像项为实例变量
        self.raw_image = pg.ImageItem()
        raw_plot_widget.addItem(self.raw_image)
        self.raw_image.setImage(self.raw_data.T)
        
        # 保存原始数据颜色条为实例变量
        self.raw_colorbar = pg.ColorBarItem(
            values=(np.min(self.raw_data), np.max(self.raw_data)),
            colorMap='viridis',
            label='压力强度'
        )
        self.raw_colorbar.setImageItem(self.raw_image)
        
        raw_layout.addWidget(raw_plot)
        raw_group.setLayout(raw_layout)
        
        # 校正后数据热力图
        cal_group = QGroupBox("校正后数据热力图")
        cal_layout = QVBoxLayout()
        
        cal_plot = pg.GraphicsLayoutWidget()
        cal_plot_widget = cal_plot.addPlot()
        cal_plot_widget.setLabel('left', 'Y轴')
        cal_plot_widget.setLabel('bottom', 'X轴')
        cal_plot_widget.setTitle('校正后数据')
        cal_plot_widget.invertY(True)
        
        # 保存校正后数据图像项为实例变量
        self.cal_image = pg.ImageItem()
        cal_plot_widget.addItem(self.cal_image)
        self.cal_image.setImage(self.calibrated_data.T)
        
        # 保存校正后数据颜色条为实例变量
        self.cal_colorbar = pg.ColorBarItem(
            values=(np.min(self.calibrated_data), np.max(self.calibrated_data)),
            colorMap='viridis',
            label='压力强度'
        )
        self.cal_colorbar.setImageItem(self.cal_image)
        
        cal_layout.addWidget(cal_plot)
        cal_group.setLayout(cal_layout)
        
        layout.addWidget(raw_group)
        layout.addWidget(cal_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_diff_tab(self):
        """创建差异分析选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 计算差异
        diff_data = self.calibrated_data - self.raw_data
        diff_stats = self.calculate_stats(diff_data)
        
        # 差异统计
        diff_group = QGroupBox("差异统计")
        diff_layout = QGridLayout()
        
        diff_layout.addWidget(QLabel("差异数据:"), 0, 0)
        
        # 保存差异统计标签为实例变量
        self.diff_stats_labels = []
        self.diff_stats_labels.append(QLabel(f"总差异: {diff_stats['total']:.4f} N"))
        self.diff_stats_labels.append(QLabel(f"平均差异: {diff_stats['mean']:.6f} N"))
        self.diff_stats_labels.append(QLabel(f"标准差: {diff_stats['std']:.6f} N"))
        self.diff_stats_labels.append(QLabel(f"最大差异: {diff_stats['max']:.6f} N"))
        self.diff_stats_labels.append(QLabel(f"最小差异: {diff_stats['min']:.6f} N"))
        self.diff_stats_labels.append(QLabel(f"差异范围: {diff_stats['max'] - diff_stats['min']:.6f} N"))
        
        diff_layout.addWidget(self.diff_stats_labels[0], 0, 1)
        diff_layout.addWidget(self.diff_stats_labels[1], 0, 2)
        diff_layout.addWidget(self.diff_stats_labels[2], 0, 3)
        diff_layout.addWidget(self.diff_stats_labels[3], 1, 1)
        diff_layout.addWidget(self.diff_stats_labels[4], 1, 2)
        diff_layout.addWidget(self.diff_stats_labels[5], 1, 3)
        
        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)
        
        # 差异热力图
        diff_heatmap_group = QGroupBox("差异热力图")
        diff_heatmap_layout = QVBoxLayout()
        
        diff_plot = pg.GraphicsLayoutWidget()
        diff_plot_widget = diff_plot.addPlot()
        diff_plot_widget.setLabel('left', 'Y轴')
        diff_plot_widget.setLabel('bottom', 'X轴')
        diff_plot_widget.setTitle('校正差异 (校正后 - 原始)')
        diff_plot_widget.invertY(True)
        
        # 保存差异图像项为实例变量
        self.diff_image = pg.ImageItem()
        diff_plot_widget.addItem(self.diff_image)
        self.diff_image.setImage(diff_data.T)
        
        # 保存差异颜色条为实例变量
        self.diff_colorbar = pg.ColorBarItem(
            values=(np.min(diff_data), np.max(diff_data)),
            colorMap='CET-CBC1',  # 使用pyqtgraph支持的双极颜色映射
            label='差异值'
        )
        self.diff_colorbar.setImageItem(self.diff_image)
        
        diff_heatmap_layout.addWidget(diff_plot)
        diff_heatmap_group.setLayout(diff_heatmap_layout)
        layout.addWidget(diff_heatmap_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_cal_info_tab(self):
        """创建校正映射信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 校正映射信息
        if self.calibration_loader and self.calibration_loader.calibration_data:
            cal_data = self.calibration_loader.calibration_data
            
            # 基本信息
            info_group = QGroupBox("校正映射基本信息")
            info_layout = QVBoxLayout()
            
            info_text = f"校正文件: {os.path.basename(self.calibration_loader.loaded_file) if self.calibration_loader.loaded_file else '未知'}\n"
            info_text += f"校正类型: {cal_data.get('description', '未知')}\n"
            info_text += f"时间戳: {cal_data.get('timestamp', '未知')}\n"
            
            if 'calibration_map' in cal_data and cal_data['calibration_map'] is not None:
                cal_map = cal_data['calibration_map']
                map_info = self.calibration_loader.get_calibration_map_info()
                if map_info:
                    info_text += f"\n校正映射统计:\n"
                    info_text += f"形状: {map_info['shape']}\n"
                    info_text += f"平均值: {map_info['mean']:.6f}\n"
                    info_text += f"标准差: {map_info['std']:.6f}\n"
                    info_text += f"最小值: {map_info['min']:.6f}\n"
                    info_text += f"最大值: {map_info['max']:.6f}\n"
                    info_text += f"中位数: {map_info['median']:.6f}\n"
                    info_text += f"变异系数: {map_info['cv']:.6f}"
            
            info_label = QLabel(info_text)
            info_label.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px;")
            info_layout.addWidget(info_label)
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
            
            # 校正映射热力图
            if 'calibration_map' in cal_data and cal_data['calibration_map'] is not None:
                cal_map_group = QGroupBox("校正映射热力图")
                cal_map_layout = QVBoxLayout()
                
                cal_map_plot = pg.GraphicsLayoutWidget()
                cal_map_plot_widget = cal_map_plot.addPlot()
                cal_map_plot_widget.setLabel('left', 'Y轴')
                cal_map_plot_widget.setLabel('bottom', 'X轴')
                cal_map_plot_widget.setTitle('校正映射系数')
                cal_map_plot_widget.invertY(True)
                
                cal_map_image = pg.ImageItem()
                cal_map_plot_widget.addItem(cal_map_image)
                cal_map_image.setImage(cal_data['calibration_map'].T)
                
                cal_map_colorbar = pg.ColorBarItem(
                    values=(np.min(cal_data['calibration_map']), np.max(cal_data['calibration_map'])),
                    colorMap='viridis',
                    label='校正系数'
                )
                cal_map_colorbar.setImageItem(cal_map_image)
                
                cal_map_layout.addWidget(cal_map_plot)
                cal_map_group.setLayout(cal_map_layout)
                layout.addWidget(cal_map_group)
        else:
            no_cal_label = QLabel("未加载校正映射数据")
            no_cal_label.setStyleSheet("font-size: 14px; color: #6c757d; text-align: center; margin: 20px;")
            layout.addWidget(no_cal_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def calculate_stats(self, data):
        """计算数据统计信息"""
        return {
            'total': np.sum(data),
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'cv': np.std(data) / np.mean(data) if np.mean(data) > 0 else 0
        }
    
    def analyze_data(self):
        """分析数据"""
        # 检查校正是否生效
        raw_total = np.sum(self.raw_data)
        cal_total = np.sum(self.calibrated_data)
        
        if abs(cal_total - raw_total) < 1e-10:
            print("⚠️ 校正可能未生效：原始数据和校正后数据完全相同")
        else:
            print(f"✅ 校正已生效：总压力从 {raw_total:.4f}N 变为 {cal_total:.4f}N")
    
    def export_report(self):
        """导出分析报告"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存分析报告", 
                f"校正分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("校正数据分析报告\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # 基本统计信息
                    raw_stats = self.calculate_stats(self.raw_data)
                    cal_stats = self.calculate_stats(self.calibrated_data)
                    
                    f.write("原始数据统计:\n")
                    f.write(f"  总压力: {raw_stats['total']:.4f} N\n")
                    f.write(f"  平均压力: {raw_stats['mean']:.6f} N\n")
                    f.write(f"  标准差: {raw_stats['std']:.6f} N\n")
                    f.write(f"  最大值: {raw_stats['max']:.6f} N\n")
                    f.write(f"  最小值: {raw_stats['min']:.6f} N\n")
                    f.write(f"  变异系数: {raw_stats['cv']:.4f}\n\n")
                    
                    f.write("校正后数据统计:\n")
                    f.write(f"  总压力: {cal_stats['total']:.4f} N\n")
                    f.write(f"  平均压力: {cal_stats['mean']:.6f} N\n")
                    f.write(f"  标准差: {cal_stats['std']:.6f} N\n")
                    f.write(f"  最大值: {cal_stats['max']:.6f} N\n")
                    f.write(f"  最小值: {cal_stats['min']:.6f} N\n")
                    f.write(f"  变异系数: {cal_stats['cv']:.4f}\n\n")
                    
                    # 校正效果
                    total_diff = cal_stats['total'] - raw_stats['total']
                    f.write("校正效果:\n")
                    f.write(f"  总压力变化: {total_diff:+.4f} N ({total_diff/raw_stats['total']*100:+.2f}%)\n")
                    
                    # 校正映射信息
                    if self.calibration_loader and self.calibration_loader.calibration_data:
                        f.write(f"\n校正映射信息:\n")
                        f.write(f"  文件: {self.calibration_loader.loaded_file}\n")
                        f.write(f"  描述: {self.calibration_loader.calibration_data.get('description', '未知')}\n")
                
                QMessageBox.information(self, "成功", f"分析报告已保存到: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")

class CalibrationDataLoader:
    """校准数据加载器 - 参考sensor_sensitivity_calibration.py"""
    
    def __init__(self):
        self.calibration_data = None
        self.loaded_file = None
        
    def load_calibration_data(self, filepath):
        """加载校准数据"""
        try:
            # 保存现有的校准数据
            existing_data = self.calibration_data.copy() if self.calibration_data else {}
            
            if filepath.endswith('.json'):
                success = self.load_json_calibration(filepath)
            elif filepath.endswith('.npy'):
                success = self.load_numpy_calibration(filepath)
            elif filepath.endswith('.csv'):
                success = self.load_csv_calibration(filepath)
            else:
                raise ValueError("不支持的文件格式")
            
            if success and existing_data:
                # 合并校准数据，而不是覆盖
                self.merge_calibration_data(existing_data)
            
            return success
            
        except Exception as e:
            print(f"⚠️ 加载校准数据失败: {e}")
            return False
    
    def merge_calibration_data(self, existing_data):
        """合并校准数据"""
        try:
            if not self.calibration_data:
                return
            
            # 合并数据，保留所有有用的信息
            merged_data = existing_data.copy()
            
            # 合并传感器校准映射（.npy文件）
            if 'calibration_map' in self.calibration_data and self.calibration_data['calibration_map'] is not None:
                merged_data['calibration_map'] = self.calibration_data['calibration_map']
                merged_data['sensor_calibration_loaded'] = True
                merged_data['sensor_calibration_file'] = self.loaded_file
                print(f"✅ 已合并传感器校准映射")
            
            # 合并压力-质量转换参数（JSON文件）
            if 'coefficient' in self.calibration_data:
                merged_data['coefficient'] = self.calibration_data['coefficient']
                merged_data['bias'] = self.calibration_data['bias']
                merged_data['zero_pressure'] = self.calibration_data.get('zero_pressure', 0.0)
                merged_data['is_zeroed'] = self.calibration_data.get('is_zeroed', False)
                merged_data['pressure_calibration_loaded'] = True
                merged_data['pressure_calibration_file'] = self.loaded_file
                print(f"✅ 已合并压力-质量转换参数")
            
            # 合并其他信息
            if 'timestamp' in self.calibration_data:
                merged_data['timestamp'] = self.calibration_data['timestamp']
            if 'description' in self.calibration_data:
                merged_data['description'] = self.calibration_data['description']
            
            # 更新校准数据
            self.calibration_data = merged_data
            
            print(f"✅ 校准数据合并完成")
            print(f"   传感器校准: {'已加载' if merged_data.get('sensor_calibration_loaded') else '未加载'}")
            print(f"   压力-质量转换: {'已加载' if merged_data.get('pressure_calibration_loaded') else '未加载'}")
            
        except Exception as e:
            print(f"⚠️ 合并校准数据失败: {e}")
    
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
            elif 'positions' in data and 'metadata' in data:
                # 位置校准数据格式
                positions = data.get('positions', {})
                if positions:
                    # 使用中心位置作为默认校准参数
                    center_pos = positions.get('center', {})
                    if center_pos and 'calibration' in center_pos:
                        cal = center_pos['calibration']
                        self.calibration_data = {
                            'coefficient': cal.get('slope', 1730.6905),
                            'bias': cal.get('intercept', 126.1741),
                            'zero_pressure': 0.0,
                            'is_zeroed': False,
                            'timestamp': cal.get('last_updated', ''),
                            'description': f"位置校准数据 - {center_pos.get('name', '中心位置')}",
                            'is_position_calibration': True,
                            'total_positions': len(positions)
                        }
                        print(f"✅ 检测到位置校准数据，包含 {len(positions)} 个位置")
                        print(f"   使用中心位置校准参数: 斜率={cal.get('slope', 1730.6905):.4f}, R²={cal.get('r_squared', 0.0):.4f}")
                    else:
                        # 如果没有中心位置，使用默认参数
                        self.calibration_data = {
                            'coefficient': 1730.6905,
                            'bias': 126.1741,
                            'zero_pressure': 0.0,
                            'is_zeroed': False,
                            'timestamp': data.get('metadata', {}).get('created_date', ''),
                            'description': f"位置校准数据 - 默认参数",
                            'is_position_calibration': True,
                            'total_positions': len(positions)
                        }
                        print(f"✅ 检测到位置校准数据，包含 {len(positions)} 个位置")
                        print(f"   使用默认校准参数: 系数=1730.6905, 偏置=126.1741")
                else:
                    raise ValueError("位置校准数据中没有找到有效的位置信息")
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
        
        # 添加位置校准管理器
        if POSITION_CALIBRATION_AVAILABLE:
            self.position_calibration_manager = PositionCalibrationManager(r'C:\Users\84672\Documents\Research\balance-sensor\position_calibration_data.json')
            self.use_position_calibration = True
            print("✅ 启用位置校准功能")
        else:
            self.position_calibration_manager = None
            self.use_position_calibration = False
            print("⚠️ 使用传统校准方式")
        
        # 当前使用的校准位置信息
        self.current_calibration_position = None
        self.current_calibration_distance = None
        
        # 尝试自动加载校准数据
        self.auto_load_calibration()
        
        self.init_ui()
        
    def init_ui(self):
        """初始化称重UI"""
        layout = QVBoxLayout()
        
        # 校准参数组
        calibration_group = QGroupBox("校准参数")
        calibration_layout = QGridLayout()
        
        if self.use_position_calibration:
            # 位置校准模式 - 显示位置信息而不是具体系数
            self.calibration_mode_label = QLabel("校准模式: 位置智能校准")
            self.calibration_mode_label.setStyleSheet("font-weight: bold; color: #28a745;")
            
            self.current_position_label = QLabel("当前位置: 未检测")
            self.current_position_label.setStyleSheet("font-weight: bold; color: #007bff;")
            
            self.position_distance_label = QLabel("距离: --")
            self.position_distance_label.setStyleSheet("font-size: 11px; color: #666;")
            
            self.calibration_quality_label = QLabel("校准质量: --")
            self.calibration_quality_label.setStyleSheet("font-size: 11px; color: #666;")
            
            # 公式显示（动态更新）
            self.formula_label = QLabel("公式: 质量 = k × 压力 + b (基于位置自动选择)")
            self.formula_label.setStyleSheet("font-weight: bold; color: #0066cc;")
            
            # 位置校准信息显示
            self.position_info_label = QLabel("位置校准信息: 等待数据...")
            self.position_info_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
            self.position_info_label.setWordWrap(True)
            self.position_info_label.setMinimumHeight(60)
            
            calibration_layout.addWidget(self.calibration_mode_label, 0, 0, 1, 2)
            calibration_layout.addWidget(self.current_position_label, 1, 0, 1, 2)
            calibration_layout.addWidget(self.position_distance_label, 2, 0)
            calibration_layout.addWidget(self.calibration_quality_label, 2, 1)
            calibration_layout.addWidget(self.formula_label, 3, 0, 1, 2)
            calibration_layout.addWidget(self.position_info_label, 4, 0, 1, 2)
            
        else:
            # 传统校准模式 - 显示系数和偏置输入框
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
        if self.use_position_calibration:
            # 位置校准模式 - 更新位置校准摘要
            self.update_position_calibration_summary()
        else:
            # 传统校准模式 - 更新公式和参数显示
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
            formula_text = f"公式: 质量 = {self.calibration_coefficient:.4f} × (当前压力 - {self.zero_pressure:.4f})"
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
    
    def calculate_weight(self, pressure_data):
        """计算重量"""
        if not self.is_zeroed:
            return 0.0
        
        if self.use_position_calibration and self.position_calibration_manager:
            # 使用位置校准管理器
            try:
                # 注意：位置校准管理器需要原始数据来计算压力重心
                # 但最终重量计算应该使用校准后的数据
                
                # 步骤1: 使用原始数据计算位置和校准参数
                result = self.position_calibration_manager.calculate_weight(pressure_data, self.zero_pressure)
                
                # 步骤2: 使用校准参数计算最终重量（基于校准后的数据）
                cal_params = result['calibration_params']
                slope = cal_params['slope']
                intercept = cal_params['intercept']
                
                # 使用校准后的压力数据计算重量
                calibrated_pressure_sum = np.sum(pressure_data)  # 这里已经是校准后的数据
                net_pressure = calibrated_pressure_sum - self.zero_pressure
                
                if self.is_zeroed:
                    weight = slope * net_pressure
                else:
                    weight = slope * net_pressure + intercept
                
                # 更新当前校准位置信息
                self.current_calibration_position = cal_params['position_name']
                self.current_calibration_distance = cal_params['distance']
                
                # 更新UI显示
                self.update_position_calibration_display(cal_params)
                
                return max(0.0, weight)
                
            except Exception as e:
                print(f"⚠️ 位置校准计算失败: {e}")
                # 回退到传统方法
                return self._calculate_weight_traditional(pressure_data)
        else:
            # 使用传统校准方法
            return self._calculate_weight_traditional(pressure_data)
    
    def _calculate_weight_traditional(self, pressure_data):
        """传统校准方法计算重量"""
        # 计算总压力
        pressure_sum = np.sum(pressure_data)
        
        # 计算净压力（减去归零压力）
        net_pressure = pressure_sum - self.zero_pressure
        
        # 计算重量 - 归零后只使用斜率，不使用偏置
        if self.is_zeroed:
            # 已归零：重量 = 斜率 × 净压力
            weight = self.calibration_coefficient * net_pressure
        else:
            # 未归零：重量 = 斜率 × 净压力 + 偏置
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
    
    def process_pressure_data(self, pressure_data):
        """处理压力数据"""
        if not self.measurement_active:
            return
        
        # 计算总压力
        pressure_sum = np.sum(pressure_data)
        
        # 更新压力显示
        self.pressure_label.setText(f"当前压力: {pressure_sum:.4f} N")
        
        # 计算净压力
        net_pressure = pressure_sum - self.zero_pressure
        self.net_pressure_label.setText(f"净压力: {net_pressure:.4f} N")
        
        # 计算重量 - 传递完整的压力数据
        weight = self.calculate_weight(pressure_data)
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
                    
                    # 更新UI - 只在传统校准模式下更新输入框
                    if not self.use_position_calibration:
                        if hasattr(self, 'coefficient_input'):
                            self.coefficient_input.setText(str(self.calibration_coefficient))
                        if hasattr(self, 'bias_input'):
                            self.bias_input.setText(str(self.calibration_bias))
                    
                    # 更新归零状态显示
                    if self.is_zeroed:
                        self.zero_status_label.setText("状态: 已归零")
                        self.zero_status_label.setStyleSheet("color: green; font-weight: bold;")
                        self.zero_pressure_label.setText(f"归零压力: {self.zero_pressure:.4f} N")
                    else:
                        self.zero_status_label.setText("状态: 未归零")
                        self.zero_status_label.setStyleSheet("color: red; font-weight: bold;")
                        self.zero_pressure_label.setText("归零压力: -- N")
                    
                    # 更新公式和参数显示 - 根据模式选择
                    if self.use_position_calibration:
                        # 位置校准模式 - 更新位置校准摘要
                        self.update_position_calibration_summary()
                    else:
                        # 传统校准模式 - 更新公式和参数显示
                        if hasattr(self, 'update_formula_display'):
                            self.update_formula_display()
                        if hasattr(self, 'update_params_display'):
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
    
    def update_position_calibration_display(self, cal_params):
        """更新位置校准信息显示"""
        if not self.use_position_calibration:
            return
        
        try:
            # 更新位置标签
            position_name = cal_params.get('position_name', '未知位置')
            self.current_position_label.setText(f"当前位置: {position_name}")
            
            # 更新距离标签
            distance = cal_params.get('distance', float('inf'))
            if distance == float('inf'):
                distance_text = "使用备用"
                distance_color = "#dc3545"
            else:
                distance_text = f"{distance:.2f}"
                if distance < 5:
                    distance_color = "#28a745"  # 绿色
                elif distance < 15:
                    distance_color = "#ffc107"  # 黄色
                else:
                    distance_color = "#dc3545"  # 红色
            
            self.position_distance_label.setText(f"距离: {distance_text}")
            self.position_distance_label.setStyleSheet(f"font-size: 11px; color: {distance_color};")
            
            # 更新校准质量标签
            r_squared = cal_params.get('r_squared', 0.0)
            if r_squared >= 0.99:
                quality_text = "优秀"
                quality_color = "#28a745"
            elif r_squared >= 0.95:
                quality_text = "良好"
                quality_color = "#ffc107"
            else:
                quality_text = "一般"
                quality_color = "#dc3545"
            
            self.calibration_quality_label.setText(f"校准质量: {quality_text} (R²={r_squared:.3f})")
            self.calibration_quality_label.setStyleSheet(f"font-size: 11px; color: {quality_color};")
            
            # 更新公式显示
            slope = cal_params.get('slope', 0.0)
            intercept = cal_params.get('intercept', 0.0)
            if self.is_zeroed:
                formula_text = f"公式: 质量 = {slope:.2f} × (当前压力 - {self.zero_pressure:.2f})"
            else:
                formula_text = f"公式: 质量 = {slope:.2f} × 压力 + {intercept:.2f}"
            self.formula_label.setText(formula_text)
            
            # 更新详细信息
            pressure_center = cal_params.get('pressure_center')
            if pressure_center:
                center_text = f"压力重心: ({pressure_center[0]:.1f}, {pressure_center[1]:.1f})"
            else:
                center_text = "压力重心: 无法计算"
            
            info_text = f"位置: {position_name}\n"
            info_text += f"斜率: {slope:.2f}\n"
            if not self.is_zeroed:
                info_text += f"截距: {intercept:.2f}\n"
            info_text += f"距离: {distance_text}\n"
            info_text += f"R²: {r_squared:.4f}\n"
            info_text += f"{center_text}"
            
            if cal_params.get('is_fallback', False):
                info_text += "\n⚠️ 使用备用校准"
                self.position_info_label.setStyleSheet("font-size: 11px; color: #dc3545; font-family: monospace; background-color: #f8d7da; padding: 8px; border: 1px solid #f5c6cb; border-radius: 4px;")
            else:
                self.position_info_label.setStyleSheet("font-size: 11px; color: #155724; font-family: monospace; background-color: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px;")
            
            self.position_info_label.setText(info_text)
            
        except Exception as e:
            print(f"⚠️ 更新位置校准显示失败: {e}")
            self.position_info_label.setText("位置校准信息: 显示错误")
            self.position_info_label.setStyleSheet("font-size: 11px; color: #721c24; font-family: monospace; background-color: #f8d7da; padding: 8px; border: 1px solid #f5c6cb; border-radius: 4px;")

    def save_position_calibration(self):
        """保存位置校准数据"""
        if not self.use_position_calibration or not self.position_calibration_manager:
            QMessageBox.warning(self, "警告", "位置校准功能未启用")
            return
        
        # 设置默认路径
        default_path = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test"
        
        # 确保目录存在
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存位置校准数据", 
            os.path.join(default_path, "position_calibration_data.json"),
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if self.position_calibration_manager.save_calibration_data(filename):
                    QMessageBox.information(self, "成功", f"位置校准数据已保存到: {filename}")
                else:
                    QMessageBox.critical(self, "错误", "保存位置校准数据失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_position_calibration(self):
        """加载位置校准数据"""
        if not self.use_position_calibration:
            QMessageBox.warning(self, "警告", "位置校准功能未启用")
            return
        
        # 设置默认路径
        default_path = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test"
        
        # 确保目录存在
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载位置校准数据", default_path, 
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if self.position_calibration_manager.load_calibration_data(filename):
                    QMessageBox.information(self, "成功", f"位置校准数据已加载: {filename}")
                    # 更新显示
                    self.update_position_calibration_summary()
                else:
                    QMessageBox.critical(self, "错误", "加载位置校准数据失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def show_position_calibration_info(self):
        """显示位置校准信息"""
        if not self.use_position_calibration or not self.position_calibration_manager:
            QMessageBox.warning(self, "警告", "位置校准功能未启用")
            return
        
        try:
            summary = self.position_calibration_manager.get_calibration_summary()
            
            info_text = f"位置校准数据摘要:\n"
            info_text += f"总位置数: {summary['total_positions']}\n\n"
            
            for position_id, info in summary['positions'].items():
                info_text += f"📍 {info['name']} ({position_id}):\n"
                info_text += f"   坐标: {info['coordinates']}\n"
                info_text += f"   斜率: {info['slope']:.2f}\n"
                info_text += f"   截距: {info['intercept']:.2f}\n"
                info_text += f"   R²: {info['r_squared']:.4f}\n"
                info_text += f"   测量次数: {info['measurement_count']}\n"
                if info['last_updated']:
                    info_text += f"   更新时间: {info['last_updated']}\n"
                info_text += "\n"
            
            QMessageBox.information(self, "位置校准信息", info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取位置校准信息失败: {e}")
    
    def update_position_calibration_summary(self):
        """更新位置校准摘要显示"""
        if not self.use_position_calibration or not self.position_calibration_manager:
            return
        
        try:
            summary = self.position_calibration_manager.get_calibration_summary()
            
            # 更新位置信息标签
            if hasattr(self, 'position_info_label'):
                summary_text = f"已加载 {summary['total_positions']} 个校准位置\n"
                
                # 显示前几个位置的信息
                count = 0
                for position_id, info in summary['positions'].items():
                    if count < 3:  # 只显示前3个
                        summary_text += f"{info['name']}: R²={info['r_squared']:.3f}\n"
                        count += 1
                    else:
                        summary_text += f"... 还有 {summary['total_positions'] - 3} 个位置\n"
                        break
                
                self.position_info_label.setText(summary_text)
                self.position_info_label.setStyleSheet("font-size: 11px; color: #155724; font-family: monospace; background-color: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px;")
                
        except Exception as e:
            print(f"⚠️ 更新位置校准摘要失败: {e}")
    
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
    
    def update_heatmap(self, pressure_data):
        """更新热力图显示"""
        try:
            if pressure_data is None or pressure_data.size == 0:
                return
            
            # 确保数据是64x64
            if pressure_data.shape != (64, 64):
                print(f"⚠️ 压力数据形状不正确: {pressure_data.shape}, 期望 (64, 64)")
                return
            
            # 转置数据以正确显示坐标
            # 原始数据: pressure_data[i, j] 对应传感器位置 (i, j)
            # 转置后: transposed_data[i, j] 对应显示位置 (j, i)
            transposed_data = pressure_data.T
            
            # 更新热力图图像
            self.heatmap_image.setImage(transposed_data)
            
            # 更新颜色条范围
            data_min = np.min(pressure_data)
            data_max = np.max(pressure_data)
            self.heatmap_colorbar.setLevels((data_min, data_max))
            
            # 更新信息标签
            total_pressure = np.sum(pressure_data)
            mean_pressure = np.mean(pressure_data)
            max_pressure = np.max(pressure_data)
            
            info_text = f"总压力: {total_pressure:.2f}N\n"
            info_text += f"平均压力: {mean_pressure:.3f}N\n"
            info_text += f"最大压力: {max_pressure:.3f}N\n"
            info_text += f"数据范围: [{data_min:.3f}, {data_max:.3f}]"
            
            self.heatmap_info_label.setText(info_text)
            
        except Exception as e:
            print(f"⚠️ 更新热力图失败: {e}")
            self.heatmap_info_label.setText("热力图更新失败")
    
    def auto_scale_heatmap(self):
        """自动缩放热力图"""
        try:
            if hasattr(self, 'heatmap_plot_widget'):
                self.heatmap_plot_widget.autoRange()
                print("✅ 热力图已自动缩放")
        except Exception as e:
            print(f"⚠️ 自动缩放失败: {e}")
    
    def reset_heatmap_scale(self):
        """重置热力图缩放"""
        try:
            if hasattr(self, 'heatmap_plot_widget'):
                # 重置到默认视图
                self.heatmap_plot_widget.setXRange(0, 64)
                self.heatmap_plot_widget.setYRange(0, 64)
                print("✅ 热力图缩放已重置")
        except Exception as e:
            print(f"⚠️ 重置缩放失败: {e}")
    
    def show_calibration_analysis(self):
        """显示校正数据分析弹窗"""
        try:
            # 检查是否有当前数据
            if not hasattr(self, 'current_raw_data') or self.current_raw_data is None:
                QMessageBox.warning(self, "警告", "没有可用的传感器数据，请先连接传感器")
                return
            
            # 获取校准加载器
            calibration_loader = None
            if hasattr(self.weight_widget, 'calibration_loader'):
                calibration_loader = self.weight_widget.calibration_loader
            
            # 创建分析弹窗（非模态）
            if not hasattr(self, 'analysis_dialog') or self.analysis_dialog is None:
                self.analysis_dialog = CalibrationAnalysisDialog(
                    self.current_raw_data, 
                    self.current_calibrated_data,
                    calibration_loader,
                    self
                )
                # 连接关闭信号
                self.analysis_dialog.finished.connect(self.on_analysis_dialog_closed)
            
            # 显示窗口
            self.analysis_dialog.show()
            self.analysis_dialog.raise_()
            self.analysis_dialog.activateWindow()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建分析弹窗失败: {e}")
    
    def on_analysis_dialog_closed(self, result):
        """分析弹窗关闭时的回调"""
        self.analysis_dialog = None
    
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
            
            # 保存原始数据
            self.current_raw_data = current_data.copy()
            
            # 应用校准映射（使用 weight_widget 的校准加载器）
            calibrated_data = current_data.copy()
            if hasattr(self.weight_widget, 'calibration_loader') and self.weight_widget.calibration_loader:
                try:
                    calibrated_data = self.weight_widget.calibration_loader.apply_calibration_map(current_data)
                    if calibrated_data is not current_data:
                        print(f"✅ 已应用校准映射")
                        current_data = calibrated_data
                except Exception as e:
                    print(f"⚠️ 应用校准映射失败: {e}")
            
            # 保存校正后数据
            self.current_calibrated_data = current_data.copy()
            
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
            
            # 传递给称重组件处理 - 传递完整的压力数据
            self.weight_widget.process_pressure_data(current_data)
            
            # 更新热力图显示
            self.update_heatmap(current_data)
            
            # 如果分析弹窗存在，更新其数据
            if hasattr(self, 'analysis_dialog') and self.analysis_dialog is not None:
                try:
                    self.analysis_dialog.raw_data = self.current_raw_data.copy()
                    self.analysis_dialog.calibrated_data = self.current_calibrated_data.copy()
                except Exception as e:
                    print(f"⚠️ 更新分析弹窗数据失败: {e}")
            
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
        try:
            # 停止传感器
            self.stop_sensor()
            
            # 关闭分析弹窗
            if hasattr(self, 'analysis_dialog') and self.analysis_dialog is not None:
                self.analysis_dialog.close()
                self.analysis_dialog = None
                print("✅ 分析弹窗已关闭")
            
            event.accept()
        except Exception as e:
            print(f"⚠️ 关闭窗口时出错: {e}")
            event.accept()

    def auto_load_calibration(self):
        """自动加载校准数据"""
        try:
            # 首先尝试加载传感器校准映射（.npy文件）
            sensor_calibration_file = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\校正数据-200帧.npy"
            
            if os.path.exists(sensor_calibration_file):
                print(f"🔍 尝试加载传感器校准映射: {sensor_calibration_file}")
                if self.calibration_loader.load_calibration_data(sensor_calibration_file):
                    print(f"✅ 成功加载传感器校准映射: {sensor_calibration_file}")
                    
                    # 显示传感器校准映射信息
                    cal_data = self.calibration_loader.calibration_data
                    if 'calibration_map' in cal_data:
                        cal_map = cal_data['calibration_map']
                        print(f"   传感器校准映射形状: {cal_map.shape}")
                        print(f"   传感器校准映射统计: 均值={np.mean(cal_map):.6f}, 标准差={np.std(cal_map):.6f}")
                        print(f"   传感器校准映射范围: [{np.min(cal_map):.6f}, {np.max(cal_map):.6f}]")
                else:
                    print(f"❌ 加载传感器校准映射失败: {sensor_calibration_file}")
            
            # 然后尝试加载压力-质量转换参数（JSON文件）
            pressure_calibration_files = [
                r"C:\Users\84672\Documents\Research\balance-sensor\position_calibration_data.json",
                "config/calibration_config.json",
                "../config/calibration_config.json"
            ]
            
            pressure_loaded = False
            for file_path in pressure_calibration_files:
                if os.path.exists(file_path):
                    print(f"🔍 尝试加载压力-质量转换参数: {file_path}")
                    if self.calibration_loader.load_calibration_data(file_path):
                        pressure_loaded = True
                        print(f"✅ 成功加载压力-质量转换参数: {file_path}")
                        
                        # 显示压力-质量转换参数信息
                        cal_data = self.calibration_loader.calibration_data
                        print(f"   压力-质量转换系数: {cal_data.get('coefficient', 'N/A')}")
                        print(f"   压力-质量转换偏置: {cal_data.get('bias', 'N/A')}")
                        print(f"   归零压力: {cal_data.get('zero_pressure', 'N/A')}")
                        print(f"   已归零: {cal_data.get('is_zeroed', 'N/A')}")
                        break
            
            if not pressure_loaded:
                print("⚠️ 未找到压力-质量转换参数文件，使用默认参数")
                # 如果没有找到压力-质量转换参数，创建默认参数
                self.create_default_pressure_calibration()
                
        except Exception as e:
            print(f"⚠️ 自动加载校准数据失败: {e}")
            self.create_default_calibration()
    
    def create_default_pressure_calibration(self):
        """创建默认压力-质量转换参数"""
        try:
            # 如果已经有传感器校准映射，只更新压力-质量转换参数
            if hasattr(self.calibration_loader, 'calibration_data') and self.calibration_loader.calibration_data:
                existing_data = self.calibration_loader.calibration_data
                
                # 更新压力-质量转换参数，保留传感器校准映射
                existing_data.update({
                    'coefficient': self.calibration_coefficient,
                    'bias': self.calibration_bias,
                    'zero_pressure': 0.0,
                    'is_zeroed': False,
                    'pressure_calibration_timestamp': '2024-01-01 00:00:00',
                    'pressure_calibration_description': '默认压力-质量转换参数'
                })
                
                print(f"✅ 已添加默认压力-质量转换参数: 系数={self.calibration_coefficient}, 偏置={self.calibration_bias}")
            else:
                # 如果没有任何校准数据，创建完整的默认校准
                self.create_default_calibration()
                
        except Exception as e:
            print(f"⚠️ 创建默认压力-质量转换参数失败: {e}")
    
    def create_default_calibration(self):
        """创建默认校准数据"""
        try:
            # 创建默认校准数据
            default_calibration = {
                'coefficient': self.calibration_coefficient,
                'bias': self.calibration_bias,
                'zero_pressure': 0.0,
                'is_zeroed': False,
                'timestamp': '2024-01-01 00:00:00',
                'description': '默认校准参数',
                'is_default': True
            }
            
            # 设置到校准加载器
            self.calibration_loader.calibration_data = default_calibration
            self.calibration_loader.loaded_file = "默认参数"
            
            print(f"✅ 已创建默认校准数据: 系数={self.calibration_coefficient}, 偏置={self.calibration_bias}")
            
        except Exception as e:
            print(f"⚠️ 创建默认校准数据失败: {e}")


class WeightMeasurementInterface(QWidget):
    """称重测量主界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化简化模式状态
        self.simple_mode = False
        
        # 应用状态
        self.is_running = False
        self.data_handler = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        # 数据存储
        self.current_raw_data = None
        self.current_calibrated_data = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据处理器
        self.init_data_handler()
        
        # 初始化位置校准摘要显示
        if hasattr(self.weight_widget, 'update_position_calibration_summary'):
            self.weight_widget.update_position_calibration_summary()
    
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
        self.sensor_combo.addItems(["模拟传感器", "真实传感器"])
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
        
        # 创建水平布局来放置传感器组和压力组
        top_layout = QHBoxLayout()
        top_layout.addWidget(sensor_group)
        top_layout.addWidget(pressure_group)
        
        left_panel.addLayout(top_layout)
        
        # 称重组件
        self.weight_widget = WeightMeasurementWidget(self)
        left_panel.addWidget(self.weight_widget)
        
        # 热力图显示组（简化模式下隐藏）
        self.heatmap_group = QGroupBox("压力分布热力图")
        heatmap_layout = QVBoxLayout()
        
        # 热力图控制按钮
        heatmap_control_layout = QHBoxLayout()
        
        self.auto_scale_btn = QPushButton("自动缩放")
        self.auto_scale_btn.clicked.connect(self.auto_scale_heatmap)
        self.auto_scale_btn.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold; padding: 6px;")
        
        self.reset_scale_btn = QPushButton("重置缩放")
        self.reset_scale_btn.clicked.connect(self.reset_heatmap_scale)
        self.reset_scale_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 6px;")
        
        self.analysis_btn = QPushButton("校正数据分析")
        self.analysis_btn.clicked.connect(self.show_calibration_analysis)
        self.analysis_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
        
        heatmap_control_layout.addWidget(self.auto_scale_btn)
        heatmap_control_layout.addWidget(self.reset_scale_btn)
        heatmap_control_layout.addWidget(self.analysis_btn)
        heatmap_control_layout.addStretch()
        
        heatmap_layout.addLayout(heatmap_control_layout)
        
        # 热力图显示区域
        self.heatmap_plot_widget = pg.GraphicsLayoutWidget()
        self.heatmap_plot = self.heatmap_plot_widget.addPlot()
        self.heatmap_plot.setLabel('left', 'Y轴')
        self.heatmap_plot.setLabel('bottom', 'X轴')
        self.heatmap_plot.setTitle('压力分布热力图')
        self.heatmap_plot.invertY(True)
        
        self.heatmap_image = pg.ImageItem()
        self.heatmap_plot.addItem(self.heatmap_image)
        
        self.heatmap_colorbar = pg.ColorBarItem(
            values=(0, 1),
            colorMap='viridis',
            label='压力强度'
        )
        self.heatmap_colorbar.setImageItem(self.heatmap_image)
        
        heatmap_layout.addWidget(self.heatmap_plot_widget)
        
        # 热力图信息标签
        self.heatmap_info_label = QLabel("热力图信息: 等待数据...")
        self.heatmap_info_label.setStyleSheet("font-size: 11px; color: #666; font-style: italic;")
        heatmap_layout.addWidget(self.heatmap_info_label)
        
        self.heatmap_group.setLayout(heatmap_layout)
        
        # 校准信息组（简化模式下隐藏）
        self.calibration_group = QGroupBox("校准信息")
        calibration_layout = QVBoxLayout()
        
        # 校准信息显示
        self.calibration_info_label = QLabel("未加载校准文件")
        self.calibration_info_label.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        # 校准控制按钮
        calibration_control_layout = QHBoxLayout()
        
        self.load_cal_btn = QPushButton("加载校准")
        self.load_cal_btn.clicked.connect(self.weight_widget.load_calibration)
        self.load_cal_btn.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold; padding: 6px;")
        
        self.save_cal_btn = QPushButton("保存校准")
        self.save_cal_btn.clicked.connect(self.weight_widget.save_calibration)
        self.save_cal_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
        
        self.cal_info_btn = QPushButton("校准信息")
        self.cal_info_btn.clicked.connect(self.show_calibration_info)
        self.cal_info_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 6px;")
        
        calibration_control_layout.addWidget(self.load_cal_btn)
        calibration_control_layout.addWidget(self.save_cal_btn)
        calibration_control_layout.addWidget(self.cal_info_btn)
        calibration_control_layout.addStretch()
        
        calibration_layout.addWidget(self.calibration_info_label)
        calibration_layout.addLayout(calibration_control_layout)
        
        self.calibration_group.setLayout(calibration_layout)
        
        # 添加热力图和校准组到左侧面板
        left_panel.addWidget(self.heatmap_group)
        left_panel.addWidget(self.calibration_group)
        
        # 组装主布局
        main_layout.addLayout(left_panel, 1)   # 左侧占1/3
        
        self.setLayout(main_layout)
        
        # 初始化数据处理器
        self.init_data_handler()
        
        # 初始化校准加载器
        self.calibration_loader = CalibrationDataLoader()
        
        # 应用简化模式
        self.apply_simple_mode()
    
    def init_data_handler(self):
        """初始化数据处理器"""
        if DATA_HANDLER_AVAILABLE:
            try:
                sensor_text = self.sensor_combo.currentText()
                
                # 确定传感器ID
                if sensor_text == "模拟传感器":
                    sensor_id = 0
                    print("✅ 使用模拟传感器模式")
                    self.data_handler = None
                elif sensor_text == "真实传感器":
                    sensor_id = 1
                    self.data_handler = DataHandler(LargeUsbSensorDriver, max_len=256)
                    print(f"✅ 数据处理器初始化成功，传感器ID: {sensor_id}")
                else:
                    # 尝试解析为数字
                    try:
                        sensor_id = int(sensor_text)
                        self.data_handler = DataHandler(LargeUsbSensorDriver, max_len=256)
                        print(f"✅ 数据处理器初始化成功，传感器ID: {sensor_id}")
                    except ValueError:
                        print(f"⚠️ 无效的传感器ID: {sensor_text}")
                        self.data_handler = None
                        
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
                if sensor_id_text == "模拟传感器":
                    sensor_id = 0
                elif sensor_id_text == "真实传感器":
                    sensor_id = 1
                else:
                    # 尝试解析为数字
                    sensor_id = int(sensor_id_text)
                
                print(f"🔄 传感器选择变化为: {sensor_id_text} (ID: {sensor_id})")
                self.init_data_handler()
            except ValueError:
                print(f"⚠️ 无效的传感器选择: {sensor_id_text}")
    
    def start_sensor(self):
        """开始传感器连接"""
        if self.is_running:
            return
            
        sensor_text = self.sensor_combo.currentText()
        port = self.port_input.text()
        
        # 确定传感器ID
        if sensor_text == "模拟传感器":
            sensor_id = 0
        elif sensor_text == "真实传感器":
            sensor_id = 1
        else:
            try:
                sensor_id = int(sensor_text)
            except ValueError:
                sensor_id = 0
        
        print(f"🔍 尝试连接传感器 {sensor_id} ({sensor_text})，端口: {port}")
        
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
    
    def update_heatmap(self, pressure_data):
        """更新热力图显示"""
        try:
            if pressure_data is None or pressure_data.size == 0:
                return
            
            # 确保数据是64x64
            if pressure_data.shape != (64, 64):
                print(f"⚠️ 压力数据形状不正确: {pressure_data.shape}, 期望 (64, 64)")
                return
            
            # 转置数据以正确显示坐标
            # 原始数据: pressure_data[i, j] 对应传感器位置 (i, j)
            # 转置后: transposed_data[i, j] 对应显示位置 (j, i)
            transposed_data = pressure_data.T
            
            # 更新热力图图像
            self.heatmap_image.setImage(transposed_data)
            
            # 更新颜色条范围
            data_min = np.min(pressure_data)
            data_max = np.max(pressure_data)
            self.heatmap_colorbar.setLevels((data_min, data_max))
            
            # 更新信息标签
            total_pressure = np.sum(pressure_data)
            mean_pressure = np.mean(pressure_data)
            max_pressure = np.max(pressure_data)
            
            info_text = f"总压力: {total_pressure:.2f}N\n"
            info_text += f"平均压力: {mean_pressure:.3f}N\n"
            info_text += f"最大压力: {max_pressure:.3f}N\n"
            info_text += f"数据范围: [{data_min:.3f}, {data_max:.3f}]"
            
            self.heatmap_info_label.setText(info_text)
            
        except Exception as e:
            print(f"⚠️ 更新热力图失败: {e}")
            self.heatmap_info_label.setText("热力图更新失败")
    
    def auto_scale_heatmap(self):
        """自动缩放热力图"""
        try:
            if hasattr(self, 'heatmap_plot_widget'):
                self.heatmap_plot_widget.autoRange()
                print("✅ 热力图已自动缩放")
        except Exception as e:
            print(f"⚠️ 自动缩放失败: {e}")
    
    def reset_heatmap_scale(self):
        """重置热力图缩放"""
        try:
            if hasattr(self, 'heatmap_plot_widget'):
                # 重置到默认视图
                self.heatmap_plot_widget.setXRange(0, 64)
                self.heatmap_plot_widget.setYRange(0, 64)
                print("✅ 热力图缩放已重置")
        except Exception as e:
            print(f"⚠️ 重置缩放失败: {e}")
    
    def show_calibration_analysis(self):
        """显示校正数据分析弹窗"""
        try:
            # 检查是否有当前数据
            if not hasattr(self, 'current_raw_data') or self.current_raw_data is None:
                QMessageBox.warning(self, "警告", "没有可用的传感器数据，请先连接传感器")
                return
            
            # 获取校准加载器
            calibration_loader = None
            if hasattr(self.weight_widget, 'calibration_loader'):
                calibration_loader = self.weight_widget.calibration_loader
            
            # 创建分析弹窗（非模态）
            if not hasattr(self, 'analysis_dialog') or self.analysis_dialog is None:
                self.analysis_dialog = CalibrationAnalysisDialog(
                    self.current_raw_data, 
                    self.current_calibrated_data,
                    calibration_loader,
                    self
                )
                # 连接关闭信号
                self.analysis_dialog.finished.connect(self.on_analysis_dialog_closed)
            
            # 显示窗口
            self.analysis_dialog.show()
            self.analysis_dialog.raise_()
            self.analysis_dialog.activateWindow()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建分析弹窗失败: {e}")
    
    def on_analysis_dialog_closed(self, result):
        """分析弹窗关闭时的回调"""
        self.analysis_dialog = None
    
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
            
            # 保存原始数据
            self.current_raw_data = current_data.copy()
            
            # 应用校准映射（使用 weight_widget 的校准加载器）
            calibrated_data = current_data.copy()
            if hasattr(self.weight_widget, 'calibration_loader') and self.weight_widget.calibration_loader:
                try:
                    calibrated_data = self.weight_widget.calibration_loader.apply_calibration_map(current_data)
                    if calibrated_data is not current_data:
                        print(f"✅ 已应用校准映射")
                        current_data = calibrated_data
                except Exception as e:
                    print(f"⚠️ 应用校准映射失败: {e}")
            
            # 保存校正后数据
            self.current_calibrated_data = current_data.copy()
            
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
            
            # 传递给称重组件处理 - 传递完整的压力数据
            self.weight_widget.process_pressure_data(current_data)
            
            # 更新热力图显示
            self.update_heatmap(current_data)
            
            # 如果分析弹窗存在，更新其数据
            if hasattr(self, 'analysis_dialog') and self.analysis_dialog is not None:
                try:
                    self.analysis_dialog.raw_data = self.current_raw_data.copy()
                    self.analysis_dialog.calibrated_data = self.current_calibrated_data.copy()
                except Exception as e:
                    print(f"⚠️ 更新分析弹窗数据失败: {e}")
            
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
        try:
            # 停止传感器
            self.stop_sensor()
            
            # 关闭分析弹窗
            if hasattr(self, 'analysis_dialog') and self.analysis_dialog is not None:
                self.analysis_dialog.close()
                self.analysis_dialog = None
                print("✅ 分析弹窗已关闭")
            
            event.accept()
        except Exception as e:
            print(f"⚠️ 关闭窗口时出错: {e}")
            event.accept()

    def toggle_simple_mode(self):
        """切换简化模式"""
        self.simple_mode = not self.simple_mode
        self.apply_simple_mode()
        
        if self.simple_mode:
            self.simple_mode_btn.setText("完整模式")
            self.simple_mode_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px 12px; font-size: 10px;")
            print("✅ 已切换到简化模式")
        else:
            self.simple_mode_btn.setText("简化模式")
            self.simple_mode_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 6px 12px; font-size: 10px;")
            print("✅ 已切换到完整模式")
    
    def apply_simple_mode(self):
        """应用简化模式设置"""
        if self.simple_mode:
            # 隐藏调试信息
            self.heatmap_group.hide()
            self.calibration_group.hide()
            
            # 调整窗口大小
            self.setFixedSize(600, 400)
            
            # 更新窗口标题
            self.setWindowTitle("称重测量应用 - 简化模式")
        else:
            # 显示调试信息
            self.heatmap_group.show()
            self.calibration_group.show()
            
            # 恢复窗口大小
            self.setFixedSize(QSize())
            
            # 更新窗口标题
            self.setWindowTitle("称重测量系统 - 调试模式")


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