"""
传感器敏感性标定程�?
使用不同质量的砝码对传感器进行敏感性标�?
载入现有校准数据，计算压力总和，评估传感器敏感�?
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
    from pyqtgraph import ImageView, ColorMap, ColorBarItem
    PYQTGRAPH_AVAILABLE = True
    
    # 配置PyQtGraph
    pg.setConfigOption('background', 'w')  # 白色背景
    pg.setConfigOption('foreground', 'k')  # 黑色前景
    pg.setConfigOption('antialias', True)  # 抗锯�?
    pg.setConfigOption('useOpenGL', True)  # 使用OpenGL加�?
    pg.setConfigOption('leftButtonPan', True)  # 左键平移
    
    print("�?PyQtGraph模块导入成功")
except ImportError as e:
    print(f"⚠️ PyQtGraph未找�? {e}")
    PYQTGRAPH_AVAILABLE = False

# 导入数据处理器和USB驱动
try:
    from data_processing.data_handler import DataHandler
    from backends.usb_driver import LargeUsbSensorDriver
    DATA_HANDLER_AVAILABLE = True
    print("�?数据处理器模块导入成�?)
except ImportError as e:
    print(f"⚠️ 数据处理器未找到: {e}")
    DATA_HANDLER_AVAILABLE = False

# 导入分离出的组件�?
try:
    from SensitivityAnalysisWidget import SensitivityAnalysisWidget
    print("�?SensitivityAnalysisWidget模块导入成功")
except ImportError as e:
    print(f"⚠️ SensitivityAnalysisWidget未找�? {e}")
    # 如果导入失败，定义一个空的占位类
    class SensitivityAnalysisWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setLayout(QVBoxLayout())
            label = QLabel("SensitivityAnalysisWidget模块未找�?)
            self.layout().addWidget(label)

try:
    from PositionConsistencyWidget import PositionConsistencyWidget
    print("�?PositionConsistencyWidget模块导入成功")
except ImportError as e:
    print(f"⚠️ PositionConsistencyWidget未找�? {e}")
    # 如果导入失败，定义一个空的占位类
    class PositionConsistencyWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setLayout(QVBoxLayout())
            label = QLabel("PositionConsistencyWidget模块未找�?)
            self.layout().addWidget(label)

# 导入Exporter
try:
    import pyqtgraph.exporters
    PYQTGRAPH_EXPORTER_AVAILABLE = True
except ImportError:
    PYQTGRAPH_EXPORTER_AVAILABLE = False
    print("⚠️ pyqtgraph.exporters 不可用，请更�?pyqtgraph 版本�?)

def save_pyqtgraph_plot(plot_widget, filename):
    """使用 pyqtgraph.exporters 来可靠地保存图表"""
    if not PYQTGRAPH_EXPORTER_AVAILABLE:
        print("�?保存失败：pyqtgraph.exporters 模块缺失�?)
        return False
        
    try:
        print(f"🚀 使用 pyqtgraph.exporters 开始保存图表到 {filename}...")
        
        # 确定要导出的对象
        if hasattr(plot_widget, 'plotItem'):
            # 如果�?PlotWidget，导出其 plotItem
            plot_item = plot_widget.plotItem
        elif hasattr(plot_widget, 'scene'):
            # 如果�?GraphicsLayoutWidget，导出整个场�?
            plot_item = plot_widget.scene()
        else:
            # 默认尝试导出整个 widget
            plot_item = plot_widget
        
        exporter = pyqtgraph.exporters.ImageExporter(plot_item)
        
        # 可选：设置导出参数，例如分辨率
        # exporter.parameters()['width'] = 1200  # 设置导出图片的宽�?
        
        exporter.export(filename)
        print(f"�?图表成功保存�? {filename}")
        return True
    except Exception as e:
        print(f"�?使用 pyqtgraph.exporters 保存失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 如果 exporters 失败，尝试备用方�?
        print(f"⚠️ 尝试备用保存方法...")
        return save_pyqtgraph_plot_fallback(plot_widget, filename)

def save_pyqtgraph_plot_fallback(plot_widget, filename):
    """备用保存方法"""
    # 方法1: 尝试使用grab方法截图
    try:
        if hasattr(plot_widget, 'grab'):
            pixmap = plot_widget.grab()
            if pixmap.save(filename):
                print(f"�?使用grab方法保存图表成功: {filename}")
                return True
    except Exception as e:
        print(f"⚠️ grab方法保存失败: {e}")
    
    # 方法2: 尝试使用QWidget的render方法
    try:
        if hasattr(plot_widget, 'render'):
            pixmap = QPixmap(plot_widget.size())
            plot_widget.render(pixmap)
            if pixmap.save(filename):
                print(f"�?使用render方法保存图表成功: {filename}")
                return True
    except Exception as e:
        print(f"⚠️ render方法保存失败: {e}")
    
    # 方法3: 尝试使用QScreen截图
    try:
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(plot_widget.winId())
            if pixmap.save(filename):
                print(f"�?使用屏幕截图方法保存图表成功: {filename}")
                return True
    except Exception as e:
        print(f"⚠️ 屏幕截图方法保存失败: {e}")
    
    print(f"❌ 所有保存方法都失败了")
    return False

class CalibrationDataLoader:
        
