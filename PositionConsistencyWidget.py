import json
import csv
import numpy as np
from datetime import datetime
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

# 添加matplotlib支持，确保中文显示
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from matplotlib import rcParams
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 尝试设置中文字体
    chinese_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
    for font in chinese_fonts:
        try:
            fm.findfont(font)
            plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
            break
        except:
            continue
    
    MATPLOTLIB_AVAILABLE = True
    print("✅ Matplotlib已加载，支持中文显示")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib不可用，图表功能将被禁用")

# 添加scipy支持
try:
    from scipy import stats
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
    print("✅ SciPy已加载")
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ SciPy不可用，统计分析功能将被禁用")

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
        """保存PyQtGraph图表的通用函数 - 改进版本"""
        try:
            print(f"🔍 开始保存图表到: {filename}")
            
            # 方法1: 尝试使用ImageExporter (最可靠的方法)
            try:
                if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                    # 确定正确的plot_item
                    if hasattr(plot_window, 'scene'):
                        # 如果是GraphicsLayoutWidget，使用scene
                        exporter = pg.exporters.ImageExporter(plot_window.scene())
                    elif hasattr(plot_window, 'plotItem'):
                        # 如果是PlotWidget，使用plotItem
                        exporter = pg.exporters.ImageExporter(plot_window.plotItem)
                    elif hasattr(plot_window, 'getPlotItem'):
                        # 如果是PlotWidget，使用getPlotItem()
                        exporter = pg.exporters.ImageExporter(plot_window.getPlotItem())
                    else:
                        # 直接使用plot_window
                        exporter = pg.exporters.ImageExporter(plot_window)
                    
                    # 强制更新场景
                    if hasattr(plot_window, 'scene'):
                        plot_window.scene().update()
                    
                    # 执行导出
                    exporter.export(filename)
                    print(f"✅ 使用ImageExporter保存图表成功: {filename}")
                    return True
            except Exception as e:
                print(f"⚠️ ImageExporter保存失败: {e}")
            
            # 方法2: 尝试使用grab方法截图
            try:
                if hasattr(plot_window, 'grab'):
                    # 强制更新
                    if hasattr(plot_window, 'scene'):
                        plot_window.scene().update()
                    QApplication.processEvents()
                    
                    pixmap = plot_window.grab()
                    if pixmap.save(filename):
                        print(f"✅ 使用grab方法保存图表成功: {filename}")
                        return True
            except Exception as e:
                print(f"⚠️ grab方法保存失败: {e}")
            
            # 方法3: 尝试使用QWidget的render方法
            try:
                if hasattr(plot_window, 'render'):
                    # 强制更新
                    if hasattr(plot_window, 'scene'):
                        plot_window.scene().update()
                    QApplication.processEvents()
                    
                    pixmap = QPixmap(plot_window.size())
                    plot_window.render(pixmap)
                    if pixmap.save(filename):
                        print(f"✅ 使用render方法保存图表成功: {filename}")
                        return True
            except Exception as e:
                print(f"⚠️ render方法保存失败: {e}")
            
            print(f"❌ 所有保存方法都失败了")
            return False
            
        except Exception as e:
            print(f"❌ 保存图表时出错: {e}")
            return False

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
        
        # 位置一致性和线性度分析相关属性
        self.position_analysis = {}  # 存储位置一致性分析结果
        self.linearity_analysis = {}  # 存储线性度分析结果
        self.analysis_results = {}  # 存储完整分析结果
        
        # 初始化UI
        self.init_ui()
        
        # 加载默认引导位置
        self.load_default_positions()
        
        print("✅ 位置一致性分析组件初始化完成")
    
    def load_default_positions(self):
        """加载默认引导位置"""
        # 坐标映射分析：
        # 1. 原始传感器数据：data[row, col]
        # 2. 转置后数据：data[col, row] = data[x, y]
        # 3. PyQtGraph ImageItem：第一维为Y轴，第二维为X轴
        # 4. invertY(True)：Y轴反转，Y坐标需要从63-y转换
        # 
        # 转换公式：
        # 原始坐标(row, col) -> 转置后(col, row) -> 反转Y轴(col, 63-row)
        # 但是根据实际显示，Y轴反转的计算应该是：Y坐标 = row
        default_positions = [
            {"id": "center", "name": "中心位置", "x": 32, "y": 32, "description": "传感器中心位置"},  # (32,32) -> (32,32)
            {"id": "top_left", "name": "左上角", "x": 16, "y": 16, "description": "左上角位置"},  # (16,16) -> (16,16)
            {"id": "top_right", "name": "右上角", "x": 48, "y": 16, "description": "右上角位置"},  # (48,16) -> (48,16)
            {"id": "bottom_left", "name": "左下角", "x": 16, "y": 48, "description": "左下角位置"},  # (16,48) -> (16,48)
            {"id": "bottom_right", "name": "右下角", "x": 48, "y": 48, "description": "右下角位置"},  # (48,48) -> (48,48)
            {"id": "top_center", "name": "上中位置", "x": 32, "y": 16, "description": "上中位置"},  # (32,16) -> (32,16)
            {"id": "bottom_center", "name": "下中位置", "x": 32, "y": 48, "description": "下中位置"},  # (32,48) -> (32,48)
            {"id": "left_center", "name": "左中位置", "x": 16, "y": 32, "description": "左中位置"},  # (16,32) -> (16,32)
            {"id": "right_center", "name": "右中位置", "x": 48, "y": 32, "description": "右中位置"}  # (48,32) -> (48,32)
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
        
        self.save_consistency_plot_btn = QPushButton("保存一致性图表")
        self.save_consistency_plot_btn.clicked.connect(self.save_current_consistency_plot)
        self.save_consistency_plot_btn.setEnabled(False)  # 初始状态禁用
        
        consistency_results_layout.addWidget(self.consistency_results_table)
        
        results_buttons_layout = QHBoxLayout()
        results_buttons_layout.addWidget(self.calculate_consistency_btn)
        results_buttons_layout.addWidget(self.save_consistency_results_btn)
        results_buttons_layout.addWidget(self.plot_consistency_btn)
        results_buttons_layout.addWidget(self.save_consistency_plot_btn)
        results_buttons_layout.addStretch()
        
        consistency_results_layout.addLayout(results_buttons_layout)
        consistency_results_group.setLayout(consistency_results_layout)
        
        # 位置一致性和线性度分析组
        analysis_group = QGroupBox("位置一致性和线性度分析")
        analysis_layout = QVBoxLayout()
        
        # 分析控制按钮
        analysis_buttons_layout = QHBoxLayout()
        
        self.analyze_position_consistency_btn = QPushButton("分析位置一致性")
        self.analyze_position_consistency_btn.clicked.connect(self.analyze_position_consistency)
        self.analyze_position_consistency_btn.setToolTip("分析同一砝码在不同位置的压力一致性")
        
        self.analyze_linearity_btn = QPushButton("分析线性度")
        self.analyze_linearity_btn.clicked.connect(self.analyze_linearity)
        self.analyze_linearity_btn.setToolTip("分析不同砝码在同一位置的压力线性关系")
        
        self.run_full_analysis_btn = QPushButton("运行完整分析")
        self.run_full_analysis_btn.clicked.connect(self.run_full_analysis)
        self.run_full_analysis_btn.setToolTip("运行位置一致性和线性度完整分析")
        
        self.save_analysis_results_btn = QPushButton("保存分析结果")
        self.save_analysis_results_btn.clicked.connect(self.save_analysis_results)
        self.save_analysis_results_btn.setEnabled(False)
        
        analysis_buttons_layout.addWidget(self.analyze_position_consistency_btn)
        analysis_buttons_layout.addWidget(self.analyze_linearity_btn)
        analysis_buttons_layout.addWidget(self.run_full_analysis_btn)
        analysis_buttons_layout.addWidget(self.save_analysis_results_btn)
        analysis_buttons_layout.addStretch()
        
        # 分析结果显示
        self.analysis_results_text = QTextEdit()
        self.analysis_results_text.setMaximumHeight(200)
        self.analysis_results_text.setPlaceholderText("分析结果将在这里显示...")
        
        analysis_layout.addLayout(analysis_buttons_layout)
        analysis_layout.addWidget(self.analysis_results_text)
        
        analysis_group.setLayout(analysis_layout)
        
        # 组装主布局
        layout.addWidget(position_group)
        layout.addWidget(self.position_table)
        layout.addWidget(consistency_group)
        layout.addWidget(consistency_results_group)
        layout.addWidget(analysis_group)
        
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
            current_text.setPlainText("center,中心位置,32,32,传感器中心位置\ntop_left,左上角,47,16,左上角位置\ntop_right,右上角,47,48,右上角位置\nbottom_left,左下角,16,16,左下角位置\nbottom_right,右下角,16,48,右下角位置\ntop_center,上中位置,47,32,上中位置\nbottom_center,下中位置,16,32,下中位置\nleft_center,左中位置,32,16,左中位置\nright_center,右中位置,32,48,右中位置")
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
    def plot_consistency_analysis(self):
        """绘制一致性分析图表 - 改进版本"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有一致性结果数据")
            return
        
        try:
            # 验证数据完整性
            if not PYQTGRAPH_AVAILABLE:
                QMessageBox.critical(self, "错误", "PyQtGraph模块不可用，无法绘制图表")
                return
            
            # 检查数据是否为空
            if len(self.consistency_results) == 0:
                QMessageBox.warning(self, "警告", "一致性结果数据为空")
                return
            
            print(f"🔍 开始绘制一致性分析图表，数据包含 {len(self.consistency_results)} 个位置")
            
            # 创建PyQtGraph绘图窗口
            plot_window = pg.GraphicsLayoutWidget()
            plot_window.setWindowTitle('Position Consistency Analysis')
            plot_window.resize(1400, 1000)
            
            # 准备数据 - 改进版本
            positions = []
            position_names = []
            avg_sensitivities = []
            avg_cvs = []
            all_sensitivities = []
            
            for position_id, position_results in self.consistency_results.items():
                if not position_results:  # 跳过空的位置结果
                    continue
                    
                positions.append(position_id)
                position_name = self.guide_positions.get(position_id, {}).get('name', position_id)
                position_names.append(position_name)
                
                # 收集该位置的所有敏感性数据 - 改进：包含负值
                position_sensitivities = []
                position_cvs = []
                
                for result in position_results.values():
                    if 'sensitivity_total' in result:
                        # 包含所有数值，包括负值
                        sensitivity = result['sensitivity_total']
                        if abs(sensitivity) > 1e-8:  # 过滤掉极小值
                            position_sensitivities.append(sensitivity)
                    
                    if 'cv' in result and result['cv'] >= 0:
                        position_cvs.append(result['cv'])
                
                # 计算平均值
                if position_sensitivities:
                    avg_sensitivity = np.mean(position_sensitivities)
                    avg_sensitivities.append(avg_sensitivity)
                    all_sensitivities.extend(position_sensitivities)
                else:
                    avg_sensitivities.append(0)
                
                if position_cvs:
                    avg_cv = np.mean(position_cvs)
                    avg_cvs.append(avg_cv)
                else:
                    avg_cvs.append(0)
            
            # 检查是否有有效数据
            if not positions or len(avg_sensitivities) == 0:
                QMessageBox.warning(self, "警告", "没有有效的图表数据")
                return
            
            print(f"📊 准备绘制 {len(positions)} 个位置的数据")
            
            # 创建2x2子图布局
            # 1. 位置敏感性对比 (左上)
            p1 = plot_window.addPlot(row=0, col=0, title="Average Sensitivity by Position")
            p1.setLabel('left', 'Average Sensitivity')
            p1.setLabel('bottom', 'Position')
            p1.showGrid(x=True, y=True, alpha=0.3)
            
            # 创建柱状图 - 改进：支持负值
            x_pos = np.arange(len(positions))
            
            # 分别绘制正值和负值
            positive_heights = [h if h > 0 else 0 for h in avg_sensitivities]
            negative_heights = [abs(h) if h < 0 else 0 for h in avg_sensitivities]
            
            # 正值柱状图
            if any(positive_heights):
                bars1_pos = pg.BarGraphItem(x=x_pos, height=positive_heights, width=0.6, 
                                          brush='skyblue', pen='black')
                p1.addItem(bars1_pos)
            
            # 负值柱状图
            if any(negative_heights):
                bars1_neg = pg.BarGraphItem(x=x_pos, height=negative_heights, width=0.6, 
                                          brush='lightcoral', pen='black')
                p1.addItem(bars1_neg)
            
            # 设置X轴标签
            ax1 = p1.getAxis('bottom')
            ax1.setTicks([[(i, name) for i, name in enumerate(position_names)]])
            
            # 添加数值标签 - 改进：显示所有值
            for i, value in enumerate(avg_sensitivities):
                if abs(value) > 1e-6:  # 显示非零值
                    text = pg.TextItem(text=f'{value:.4f}', color='black')
                    if value > 0:
                        text.setPos(i, value + max(avg_sensitivities) * 0.02)
                    else:
                        text.setPos(i, value - max([abs(v) for v in avg_sensitivities]) * 0.02)
                    p1.addItem(text)
            
            # 2. 位置变异系数对比 (右上)
            p2 = plot_window.addPlot(row=0, col=1, title="Average Coefficient of Variation by Position")
            p2.setLabel('left', 'Average CV')
            p2.setLabel('bottom', 'Position')
            p2.showGrid(x=True, y=True, alpha=0.3)
            
            bars2 = pg.BarGraphItem(x=x_pos, height=avg_cvs, width=0.6, 
                                  brush='lightcoral', pen='black')
            p2.addItem(bars2)
            
            # 设置X轴标签
            ax2 = p2.getAxis('bottom')
            ax2.setTicks([[(i, name) for i, name in enumerate(position_names)]])
            
            # 添加数值标签
            for i, value in enumerate(avg_cvs):
                if value > 0:  # 只显示非零值
                    text = pg.TextItem(text=f'{value:.3f}', color='black')
                    text.setPos(i, value + max(avg_cvs) * 0.02)
                    p2.addItem(text)
            
            # 3. 敏感性分布直方图 (左下)
            p3 = plot_window.addPlot(row=1, col=0, title="Sensitivity Distribution (All Positions)")
            p3.setLabel('left', 'Frequency')
            p3.setLabel('bottom', 'Sensitivity')
            p3.showGrid(x=True, y=True, alpha=0.3)
            
            # 计算直方图 - 改进：包含负值
            if all_sensitivities:
                # 使用更合适的bins数量
                bins_count = min(20, max(5, len(all_sensitivities) // 3))
                hist, bins = np.histogram(all_sensitivities, bins=bins_count)
                x_hist = (bins[:-1] + bins[1:]) / 2
                bars3 = pg.BarGraphItem(x=x_hist, height=hist, width=(bins[1]-bins[0])*0.8,
                                      brush='lightgreen', pen='black')
                p3.addItem(bars3)
                
                # 添加统计信息
                mean_sens = np.mean(all_sensitivities)
                std_sens = np.std(all_sensitivities)
                stats_text = f"Mean: {mean_sens:.4f}\nStd: {std_sens:.4f}"
                stats_item = pg.TextItem(text=stats_text, color='black', anchor=(0, 1))
                stats_item.setPos(bins[0], max(hist))
                p3.addItem(stats_item)
            
            # 4. 位置一致性热力图 (右下) - 改进版本
            p4 = plot_window.addPlot(row=1, col=1, title="Position-Weight Sensitivity Heatmap")
            p4.setLabel('left', 'Position')
            p4.setLabel('bottom', 'Weight ID')
            
            # 创建位置-砝码矩阵 - 修复版本：添加转置
            position_ids = list(self.consistency_results.keys())
            weight_ids = set()
            for position_results in self.consistency_results.values():
                weight_ids.update(position_results.keys())
            weight_ids = sorted(list(weight_ids))
            
            if position_ids and weight_ids:
                consistency_matrix = np.zeros((len(position_ids), len(weight_ids)))
                valid_data_count = 0
                total_data_count = 0
                
                for i, position_id in enumerate(position_ids):
                    for j, weight_id in enumerate(weight_ids):
                        total_data_count += 1
                        if (position_id in self.consistency_results and 
                            weight_id in self.consistency_results[position_id] and
                            'sensitivity_total' in self.consistency_results[position_id][weight_id]):
                            
                            sensitivity_value = self.consistency_results[position_id][weight_id]['sensitivity_total']
                            consistency_matrix[i, j] = sensitivity_value
                            
                            # 检查是否为有效数据（非零且合理范围）
                            if abs(sensitivity_value) > 1e-6:  # 包含负值
                                valid_data_count += 1
                                print(f"✅ 有效数据: 位置={position_id}, 砝码={weight_id}, 敏感性={sensitivity_value:.6f}")
                            else:
                                print(f"⚠️ 小数值: 位置={position_id}, 砝码={weight_id}, 敏感性={sensitivity_value:.6f}")
                        else:
                            print(f"❌ 缺失数据: 位置={position_id}, 砝码={weight_id}")
                
                print(f"📊 数据统计: 有效数据={valid_data_count}/{total_data_count} ({valid_data_count/total_data_count*100:.1f}%)")
                
                # 检查数据范围 - 改进：包含负值
                non_zero_data = consistency_matrix[abs(consistency_matrix) > 1e-6]
                if len(non_zero_data) > 0:
                    data_min = non_zero_data.min()
                    data_max = non_zero_data.max()
                    data_mean = non_zero_data.mean()
                    print(f"📈 数据范围: 最小值={data_min:.6f}, 最大值={data_max:.6f}, 平均值={data_mean:.6f}")
                    
                    # 改进的颜色映射范围
                    if data_max > data_min:
                        # 使用对称的颜色映射范围
                        abs_max = max(abs(data_min), abs(data_max))
                        levels = [-abs_max, abs_max]
                        print(f"🔍 使用对称颜色映射: {levels}")
                    else:
                        levels = [-0.001, 0.001]  # 默认范围
                        print(f"🔍 使用默认颜色映射: {levels}")
                else:
                    print(f"⚠️ 没有有效数据")
                    levels = [-0.001, 0.001]  # 默认范围
                
                # 转置矩阵：让砝码ID在Y轴，位置在X轴
                consistency_matrix = consistency_matrix.T
                print(f"🔄 矩阵已转置: 从 ({len(position_ids)}, {len(weight_ids)}) 变为 ({len(weight_ids)}, {len(position_ids)})")
                
                # 创建热力图
                img_item = pg.ImageItem(consistency_matrix)
                p4.addItem(img_item)
                
                # 设置颜色映射 - 修复版本
                try:
                    # 强制使用彩色映射，避免灰度图
                    print(f"🔍 设置颜色映射...")
                    
                    # 方法1: 尝试使用RdBu映射（红蓝映射，适合正负值）
                    try:
                        colormap = pg.colormap.get('RdBu')
                        if colormap is not None:
                            print(f"✅ 使用RdBu颜色映射")
                            img_item.setColorMap(colormap)
                        else:
                            raise Exception("RdBu颜色映射不可用")
                    except Exception as e1:
                        print(f"⚠️ RdBu映射失败: {e1}")
                        
                        # 方法2: 尝试使用plasma映射
                        try:
                            colormap = pg.colormap.get('plasma')
                            if colormap is not None:
                                print(f"✅ 使用plasma颜色映射")
                                img_item.setColorMap(colormap)
                            else:
                                raise Exception("plasma颜色映射不可用")
                        except Exception as e2:
                            print(f"⚠️ plasma映射失败: {e2}")
                            
                            # 方法3: 尝试使用viridis映射
                            try:
                                colormap = pg.colormap.get('viridis')
                                if colormap is not None:
                                    print(f"✅ 使用viridis颜色映射")
                                    img_item.setColorMap(colormap)
                                else:
                                    raise Exception("viridis颜色映射不可用")
                            except Exception as e3:
                                print(f"⚠️ viridis映射失败: {e3}")
                                
                                # 方法4: 创建自定义颜色映射
                                try:
                                    print(f"🔧 创建自定义颜色映射...")
                                    # 创建从蓝色到红色的渐变
                                    colors = [
                                        (0, 0, 255),    # 蓝色
                                        (0, 255, 255),  # 青色
                                        (0, 255, 0),    # 绿色
                                        (255, 255, 0),  # 黄色
                                        (255, 0, 0)     # 红色
                                    ]
                                    positions = np.linspace(0, 1, len(colors))
                                    colormap = pg.ColorMap(positions, colors)
                                    img_item.setColorMap(colormap)
                                    print(f"✅ 使用自定义颜色映射")
                                except Exception as e4:
                                    print(f"❌ 自定义颜色映射失败: {e4}")
                                    # 最后尝试：直接设置RGB值
                                    try:
                                        print(f"🔧 尝试直接设置RGB值...")
                                        # 强制设置彩色显示
                                        img_item.setLevels(levels)
                                        print(f"✅ 直接设置levels完成")
                                    except Exception as e5:
                                        print(f"❌ 直接设置RGB值失败: {e5}")
                    
                    # 设置颜色级别
                    img_item.setLevels(levels)
                    print(f"✅ 颜色级别设置完成: {levels}")
                    
                except Exception as e:
                    print(f"❌ 颜色映射设置完全失败: {e}")
                    # 最后的备用方案：强制刷新
                    try:
                        img_item.setLevels(levels)
                        print(f"✅ 使用备用方案设置levels")
                    except Exception as e_final:
                        print(f"❌ 备用方案也失败: {e_final}")
                
                # 强制更新图像显示
                try:
                    img_item.updateImage()
                    print(f"✅ 强制更新图像显示")
                except Exception as e:
                    print(f"⚠️ 强制更新图像显示失败: {e}")
                
                # 设置坐标轴 - 修复版本：保持原始坐标轴标签，只转置数据
                p4.setAspectLocked(False)
                # 移除 p4.invertY(True) 来修复Y轴颠倒问题
                print(f"🔧 设置坐标轴：移除Y轴反转，保持正常方向")
                
                # 设置X轴标签 - 保持为砝码ID
                ax4_x = p4.getAxis('bottom')
                ax4_x.setTicks([[(i, str(wid)) for i, wid in enumerate(weight_ids)]])
                
                # 设置Y轴标签 - 保持为位置，但按物理坐标排序
                ax4_y = p4.getAxis('left')
                # 根据物理坐标Y值排序位置（Y值越小越在上方）
                position_order = []
                for pid in position_ids:
                    pos_info = self.guide_positions.get(pid, {})
                    pos_name = pos_info.get('name', pid)
                    y_coord = pos_info.get('y', 32)  # 默认中心位置
                    position_order.append((pid, pos_name, y_coord))
                
                # 按Y坐标排序：Y值小的在上方
                position_order.sort(key=lambda x: x[2])
                print(f"🔍 按Y坐标排序的位置: {[(pid, name, y) for pid, name, y in position_order]}")
                
                # 提取排序后的位置ID和名称
                sorted_position_ids = [pid for pid, name, y in position_order]
                y_labels = [name for pid, name, y in position_order]
                ax4_y.setTicks([[(i, label) for i, label in enumerate(y_labels)]])
                
                print(f"🔍 X轴砝码顺序: {list(weight_ids)}")
                print(f"🔍 Y轴位置顺序: {y_labels}")
                
                # 重新排列数据矩阵以匹配新的Y轴顺序（位置顺序）
                # 注意：转置后的矩阵维度是 (weight_ids, position_ids)
                reordered_matrix = np.zeros_like(consistency_matrix)
                for new_i, (pid, name, y) in enumerate(position_order):
                    old_i = position_ids.index(pid)
                    reordered_matrix[:, new_i] = consistency_matrix[:, old_i]  # 转置后是列操作
                    print(f"  位置 {name} (Y={y}): 从列 {old_i} 移动到列 {new_i}")
                
                # 更新图像数据
                img_item.setImage(reordered_matrix)
                print(f"✅ 数据矩阵已重新排序以匹配物理布局")
                
                # 添加数值标签 - 使用重新排序后的矩阵
                for i in range(len(weight_ids)):  # Y轴：砝码ID
                    for j in range(len(position_ids)):  # X轴：位置
                        value = reordered_matrix[i, j]
                        if abs(value) > 1e-6:  # 显示有效数据
                            # 根据背景颜色选择文字颜色
                            if abs(value) < abs_max * 0.5:
                                text_color = 'black'  # 浅色背景用黑字
                            else:
                                text_color = 'white'  # 深色背景用白字
                            
                            text = pg.TextItem(text=f'{value:.3f}', 
                                             color=text_color, anchor=(0.5, 0.5))
                            text.setPos(j, i)
                            p4.addItem(text)
                        else:
                            # 对于无效数据，显示"<0.001"
                            text = pg.TextItem(text='<0.001', 
                                             color='gray', anchor=(0.5, 0.5))
                            text.setPos(j, i)
                            p4.addItem(text)
                
                # 添加颜色条 - 修复版本
                try:
                    print(f"🔍 创建颜色条...")
                    
                    # 获取当前使用的颜色映射
                    current_colormap = None
                    
                    # 尝试获取当前图像项的颜色映射
                    try:
                        if hasattr(img_item, 'colorMap'):
                            current_colormap = img_item.colorMap()
                            print(f"✅ 获取到当前颜色映射")
                    except Exception as e:
                        print(f"⚠️ 获取当前颜色映射失败: {e}")
                    
                    # 如果获取失败，使用默认的plasma映射
                    if current_colormap is None:
                        try:
                            current_colormap = pg.colormap.get('plasma')
                            print(f"✅ 使用默认plasma颜色映射")
                        except Exception as e:
                            print(f"⚠️ 默认颜色映射失败: {e}")
                            # 创建简单的颜色映射
                            colors = [(0, 0, 255), (255, 0, 0)]  # 蓝到红
                            positions = [0, 1]
                            current_colormap = pg.ColorMap(positions, colors)
                            print(f"✅ 创建简单颜色映射")
                    
                    # 创建颜色条
                    colorbar = pg.ColorBarItem(values=levels, 
                                             colorMap=current_colormap, 
                                             label='Sensitivity')
                    colorbar.setImageItem(img_item)
                    print(f"✅ 颜色条创建成功")
                    
                except Exception as e:
                    print(f"❌ 颜色条创建失败: {e}")
                    # 尝试简单的颜色条
                    try:
                        colorbar = pg.ColorBarItem(values=levels, label='Sensitivity')
                        colorbar.setImageItem(img_item)
                        print(f"✅ 简单颜色条创建成功")
                    except Exception as e2:
                        print(f"❌ 简单颜色条也失败: {e2}")
                        pass
                
                # 添加数据统计信息
                info_text = f"Valid: {valid_data_count}/{total_data_count} ({valid_data_count/total_data_count*100:.1f}%)"
                if len(non_zero_data) > 0:
                    info_text += f"\nRange: {data_min:.4f} to {data_max:.4f}"
                
                # 在图表上添加统计信息
                info_item = pg.TextItem(text=info_text, color='black', anchor=(0, 0))
                info_item.setPos(0, len(position_ids) + 0.5)
                p4.addItem(info_item)
                
            else:
                print(f"⚠️ 没有位置或砝码数据")
                # 显示空数据提示
                empty_text = pg.TextItem(text="No Data", color='red', anchor=(0.5, 0.5))
                empty_text.setPos(0, 0)
                p4.addItem(empty_text)
            
            # 强制更新和渲染
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 在图表窗口添加保存按钮
            self.add_save_button_to_plot(plot_window)
            
            print(f"✅ 一致性分析图表绘制完成")
            print(f"💡 提示：图表窗口中有保存按钮")
            
            # 启用保存图表按钮
            self.save_consistency_plot_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制一致性分析图失败: {e}")
            print(f"❌ 绘制一致性分析图失败: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            # 更新进度条并添加调试信息
            self.position_progress_bar.setValue(current_count)
            print(f"🔍 进度条已更新: 当前值={self.position_progress_bar.value()}, 最大值={self.position_progress_bar.maximum()}, 可见性={self.position_progress_bar.isVisible()}")
            
            # 更新主界面状态栏
            if main_interface and hasattr(main_interface, 'measurement_status_label'):
                progress = (current_count / self.measurement_count) * 100
                main_interface.measurement_status_label.setText(
                    f"位置测量: {self.current_position_id}-{self.current_weight_id} ({current_count}/{self.measurement_count}) [{progress:.1f}%]"
                )
            
            # 强制更新UI
            QApplication.processEvents()
            
            if current_count >= self.measurement_count:
                print(f"✅ 位置测量完成，停止测量")
                self.stop_position_measurement()
                QMessageBox.information(self, "完成", f"位置 {self.current_position_id} 砝码 {self.current_weight_id} 测量完成")
                
        except Exception as e:
            print(f"❌ 记录位置测量数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_position_consistency(self):
        """计算位置一致性（使用位置专用数据） - 修复版本"""
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
        
        print(f"🔍 开始计算位置一致性，数据概览:")
        print(f"  位置数量: {len(self.position_data)}")
        for position_id, position_weights in self.position_data.items():
            print(f"  位置 {position_id}: {len(position_weights)} 个砝码")
            for weight_id, measurements in position_weights.items():
                print(f"    砝码 {weight_id}: {len(measurements)} 次测量")
        
        # 计算每个位置的一致性
        results = {}
        
        for position_id, position_weights in self.position_data.items():
            position_results = {}
            
            for weight_id, measurements in position_weights.items():
                if not measurements:
                    print(f"⚠️ 位置 {position_id} 砝码 {weight_id} 没有测量数据")
                    continue
                
                # 检查砝码是否存在
                if weight_id not in weight_calibration.weights:
                    print(f"⚠️ 砝码 {weight_id} 不存在于校准数据中")
                    continue
                
                weight_info = weight_calibration.weights[weight_id]
                force = weight_info['force']
                
                print(f"🔧 计算位置 {position_id} 砝码 {weight_id}:")
                print(f"  砝码信息: 质量={weight_info['mass']}{weight_info['unit']}, 力={force:.3f}N")
                print(f"  测量次数: {len(measurements)}")
                
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
                
                # 计算敏感性
                sensitivity_total = avg_total_pressure / force if force > 0 else 0
                
                print(f"  平均总压力: {avg_total_pressure:.6f}")
                print(f"  标准差: {std_total_pressure:.6f}")
                print(f"  敏感性: {sensitivity_total:.6f}")
                print(f"  变异系数: {cv_total:.3f}")
                
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
                    'sensitivity_total': sensitivity_total
                }
            
            if position_results:
                results[position_id] = position_results
                print(f"✅ 位置 {position_id} 计算完成，包含 {len(position_results)} 个砝码数据")
            else:
                print(f"⚠️ 位置 {position_id} 没有有效数据")
        
        if not results:
            QMessageBox.warning(self, "警告", "没有有效的位置一致性数据")
            return
        
        # 验证数据正确性
        print(f"\n🔍 数据验证:")
        for position_id, position_results in results.items():
            print(f"  位置 {position_id}:")
            for weight_id, result in position_results.items():
                sensitivity = result['sensitivity_total']
                print(f"    砝码 {weight_id}: 敏感性 = {sensitivity:.6f}")
        
        # 检查是否有重复的敏感性值
        all_sensitivities = []
        for position_id, position_results in results.items():
            for weight_id, result in position_results.items():
                all_sensitivities.append((position_id, weight_id, result['sensitivity_total']))
        
        # 按敏感性值分组
        sensitivity_groups = {}
        for pos_id, weight_id, sensitivity in all_sensitivities:
            if sensitivity not in sensitivity_groups:
                sensitivity_groups[sensitivity] = []
            sensitivity_groups[sensitivity].append((pos_id, weight_id))
        
        duplicate_found = False
        for sensitivity, positions in sensitivity_groups.items():
            if len(positions) > 1:
                print(f"  ⚠️ 发现重复敏感性值 {sensitivity:.6f} 在以下位置:")
                for pos_id, weight_id in positions:
                    print(f"    - 位置 {pos_id}, 砝码 {weight_id}")
                duplicate_found = True
        
        if duplicate_found:
            print(f"  ⚠️ 警告：发现重复的敏感性值，可能存在数据处理问题")
        
        # 更新结果显示
        self.update_consistency_results_table(results)
        
        # 存储结果到组件属性中
        self.consistency_results = results
        
        # 显示分析结果
        self.show_consistency_analysis(results)
        
        print(f"✅ 位置一致性分析完成，共分析 {len(results)} 个位置")
        print(f"📊 结果已存储到 consistency_results 中")
        
        # 显示数据摘要
        total_measurements = sum(len(pos_results) for pos_results in results.values())
        QMessageBox.information(self, "分析完成", 
                              f"位置一致性分析完成\n"
                              f"位置数量: {len(results)}\n"
                              f"总测量点: {total_measurements}\n"
                              f"{'⚠️ 发现重复数据，请检查测量过程' if duplicate_found else '✅ 数据正常'}")
    
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
    
    
    
    def save_consistency_plot(self, plot_window):
        """保存一致性分析图 - 改进版本"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存一致性分析图", 
                f"consistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
            )
            
            if filename:
                print(f"🔍 尝试保存图表到: {filename}")
                
                # 保存前确保渲染 - 多次强制更新
                for i in range(3):
                    if hasattr(plot_window, 'scene'):
                        plot_window.scene().update()
                    QApplication.processEvents()
                    QTimer.singleShot(50, lambda: None)  # 短暂延迟
                
                # 方法1: 尝试使用改进的保存函数
                if save_pyqtgraph_plot(plot_window, filename):
                    print(f"✅ 一致性分析图已保存到: {filename}")
                    QMessageBox.information(self, "成功", f"一致性分析图已保存到:\n{filename}")
                    return
                
                # 方法2: 如果失败，尝试使用robust保存函数
                print(f"⚠️ 改进的保存函数失败，尝试使用robust保存函数...")
                if hasattr(plot_window, 'scene'):
                    if save_pyqtgraph_plot_robust(plot_window.scene(), filename):
                        print(f"✅ 使用robust保存函数成功: {filename}")
                        QMessageBox.information(self, "成功", f"一致性分析图已保存到:\n{filename}")
                        return
                
                # 方法3: 尝试直接保存
                print(f"⚠️ robust保存函数失败，尝试直接保存...")
                if self.save_plot_directly(plot_window, filename):
                    print(f"✅ 直接保存成功: {filename}")
                    QMessageBox.information(self, "成功", f"一致性分析图已保存到:\n{filename}")
                    return
                
                # 所有方法都失败
                QMessageBox.warning(self, "保存失败", "所有保存方法都失败了，请检查文件路径和权限")
                
        except Exception as e:
            print(f"⚠️ 保存一致性分析图时出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
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
    
    def save_current_consistency_plot(self):
        """保存当前的一致性分析图表 - 改进版本"""
        if not hasattr(self, 'current_plot_window') or self.current_plot_window is None:
            QMessageBox.warning(self, "警告", "没有可保存的图表，请先绘制一致性分析图表")
            return
        
        try:
            # 检查主窗口是否仍然有效
            if not hasattr(self.current_plot_window, 'layout'):
                QMessageBox.warning(self, "警告", "图表窗口无效，请重新绘制图表")
                return
            
            # 获取图表窗口
            layout = self.current_plot_window.layout()
            if layout and layout.count() > 0:
                plot_window = layout.itemAt(0).widget()
                if hasattr(plot_window, 'scene'):
                    # 弹出保存对话框
                    filename, _ = QFileDialog.getSaveFileName(
                        self, "保存一致性分析图表", 
                        f"consistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
                    )
                    
                    if filename:
                        print(f"🔍 用户选择保存到: {filename}")
                        
                        # 保存前确保渲染 - 多次强制更新
                        for i in range(3):
                            plot_window.scene().update()
                            QApplication.processEvents()
                            QTimer.singleShot(50, lambda: None)  # 短暂延迟
                        
                        # 方法1: 尝试使用改进的保存函数
                        if save_pyqtgraph_plot(plot_window, filename):
                            print(f"✅ 一致性分析图表已保存到: {filename}")
                            QMessageBox.information(self, "成功", f"一致性分析图表已保存到:\n{filename}")
                            return
                        
                        # 方法2: 如果失败，尝试使用robust保存函数
                        print(f"⚠️ 改进的保存函数失败，尝试使用robust保存函数...")
                        if save_pyqtgraph_plot_robust(plot_window.scene(), filename):
                            print(f"✅ 使用robust保存函数成功: {filename}")
                            QMessageBox.information(self, "成功", f"一致性分析图表已保存到:\n{filename}")
                            return
                        
                        # 方法3: 尝试直接保存
                        print(f"⚠️ robust保存函数失败，尝试直接保存...")
                        if self.save_plot_directly(plot_window, filename):
                            print(f"✅ 直接保存成功: {filename}")
                            QMessageBox.information(self, "成功", f"一致性分析图表已保存到:\n{filename}")
                            return
                        
                        # 所有方法都失败
                        QMessageBox.warning(self, "保存失败", "所有保存方法都失败了，请检查文件路径和权限")
                    else:
                        print(f"💡 用户取消了保存")
                else:
                    QMessageBox.warning(self, "警告", "无法找到有效的图表窗口")
            else:
                QMessageBox.warning(self, "警告", "无法找到图表窗口")
            
        except Exception as e:
            print(f"⚠️ 保存一致性分析图时出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
            import traceback
            traceback.print_exc()
    
    def add_save_button_to_plot(self, plot_window):
        """在图表窗口中添加一个保存按钮"""
        try:
            # 创建一个包含图表和按钮的主窗口
            main_window = QWidget()
            main_window.setWindowTitle("一致性分析图表")
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
            save_button.clicked.connect(lambda: self.save_consistency_plot(plot_window))
            
            # 设置按钮大小
            save_button.setFixedHeight(40)
            
            # 添加按钮到布局
            layout.addWidget(save_button)
            
            # 设置主窗口布局
            main_window.setLayout(layout)
            
            # 保存主窗口引用（在显示前保存）
            self.current_plot_window = main_window
            
            # 强制更新图表窗口
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 显示主窗口
            main_window.show()
            
            # 再次强制更新确保显示正确
            main_window.update()
            QApplication.processEvents()
            
            print(f"✅ 保存按钮已添加到图表窗口底部")
            
        except Exception as e:
            print(f"⚠️ 添加保存按钮失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 如果添加保存按钮失败，直接显示原始图表窗口
            try:
                plot_window.show()
                print(f"✅ 显示原始图表窗口")
            except Exception as e2:
                print(f"❌ 显示原始图表窗口也失败: {e2}")
                QMessageBox.critical(self, "错误", f"无法显示图表窗口: {e2}")
    
    
    