"""
校正系统集成模块
为现有的传感器界面添加校正功能
"""

from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QSpinBox, QDoubleSpinBox, 
                            QCheckBox, QProgressDialog, QMessageBox, QFileDialog,
                            QTableWidget, QTableWidgetItem, QTabWidget, QWidget)
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import json
import pickle
from datetime import datetime

class CalibrationDataCollector(QThread):
    """校正数据收集线程"""
    progress_updated = pyqtSignal(int)
    data_collected = pyqtSignal(dict)
    message_updated = pyqtSignal(str)
    
    def __init__(self, data_handler, collection_settings):
        super().__init__()
        self.data_handler = data_handler
        self.settings = collection_settings
        self.is_running = False
        
    def run(self):
        """收集校正数据"""
        self.is_running = True
        collected_data = {}
        
        total_steps = self.settings['steps']
        frames_per_step = self.settings['frames_per_step']
        
        self.message_updated.emit("开始收集校正数据...")
        
        for step in range(total_steps):
            if not self.is_running:
                break
                
            step_pressure = self.settings['start_pressure'] + step * self.settings['pressure_increment']
            
            self.message_updated.emit(f"步骤 {step+1}/{total_steps}: 施加压力 {step_pressure:.2f}")
            
            # 收集当前压力下的数据
            step_data = []
            for frame in range(frames_per_step):
                if not self.is_running:
                    break
                    
                # 从传感器获取数据
                if self.data_handler:
                    try:
                        self.data_handler.trigger()
                        with self.data_handler.lock:
                            if self.data_handler.value and len(self.data_handler.value) > 0:
                                current_data = np.array(self.data_handler.value[-1])
                                step_data.append(current_data)
                            else:
                                print(f"⚠️ 步骤 {step+1}, 帧 {frame+1}: 无有效数据")
                    except Exception as e:
                        print(f"⚠️ 步骤 {step+1}, 帧 {frame+1}: 数据获取失败 - {e}")
                else:
                    print("⚠️ data_handler不可用")
                    break
                
                # 更新进度
                progress = int(((step * frames_per_step + frame + 1) / (total_steps * frames_per_step)) * 100)
                self.progress_updated.emit(progress)
                
                self.msleep(50)  # 50ms间隔
            
            if step_data:
                # 计算该压力下的平均响应
                avg_response = np.mean(step_data, axis=0)
                collected_data[step_pressure] = {
                    'average_response': avg_response,
                    'std_response': np.std(step_data, axis=0),
                    'frame_count': len(step_data)
                }
        
        self.data_collected.emit(collected_data)
        self.message_updated.emit("数据收集完成")
    
    def stop(self):
        """停止收集"""
        self.is_running = False

class CalibrationWidget(QWidget):
    """校正功能组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calibration_data = {}  # 存储校正数据
        self.calibration_map = None  # 校正映射
        self.collection_thread = None
        self.analyzer = None
        self.init_ui()
        
        # 导入分析器
        try:
            from consistency_analysis import ConsistencyAnalyzer, CalibrationSystem
            self.analyzer = ConsistencyAnalyzer()
            self.calibration_system = CalibrationSystem()
        except ImportError:
            print("⚠️ 一致性分析模块未找到")
    
    def init_ui(self):
        """初始化校正UI"""
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 标签页1: 数据收集
        collection_tab = self.create_collection_tab()
        tab_widget.addTab(collection_tab, "数据收集")
        
        # 标签页2: 校正分析
        analysis_tab = self.create_analysis_tab()
        tab_widget.addTab(analysis_tab, "校正分析")
        
        # 标签页3: 校正应用
        application_tab = self.create_application_tab()
        tab_widget.addTab(application_tab, "校正应用")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
    
    def create_collection_tab(self):
        """创建数据收集标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 收集参数设置
        params_group = QGroupBox("收集参数")
        params_layout = QVBoxLayout()
        
        # 参数控件
        param_row1 = QHBoxLayout()
        param_row1.addWidget(QLabel("起始压力:"))
        self.start_pressure_spin = QDoubleSpinBox()
        self.start_pressure_spin.setRange(0.1, 10.0)
        self.start_pressure_spin.setValue(0.5)
        self.start_pressure_spin.setSuffix(" kg")
        param_row1.addWidget(self.start_pressure_spin)
        
        param_row1.addWidget(QLabel("压力增量:"))
        self.pressure_increment_spin = QDoubleSpinBox()
        self.pressure_increment_spin.setRange(0.1, 2.0)
        self.pressure_increment_spin.setValue(0.5)
        self.pressure_increment_spin.setSuffix(" kg")
        param_row1.addWidget(self.pressure_increment_spin)
        
        param_row2 = QHBoxLayout()
        param_row2.addWidget(QLabel("步骤数:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(3, 20)
        self.steps_spin.setValue(5)
        param_row2.addWidget(self.steps_spin)
        
        param_row2.addWidget(QLabel("每步帧数:"))
        self.frames_per_step_spin = QSpinBox()
        self.frames_per_step_spin.setRange(10, 200)
        self.frames_per_step_spin.setValue(50)
        param_row2.addWidget(self.frames_per_step_spin)
        
        params_layout.addLayout(param_row1)
        params_layout.addLayout(param_row2)
        params_group.setLayout(params_layout)
        
        # 收集控制
        control_group = QGroupBox("收集控制")
        control_layout = QHBoxLayout()
        
        self.start_collection_btn = QPushButton("开始收集")
        self.start_collection_btn.clicked.connect(self.start_calibration_collection)
        
        self.stop_collection_btn = QPushButton("停止收集")
        self.stop_collection_btn.clicked.connect(self.stop_calibration_collection)
        self.stop_collection_btn.setEnabled(False)
        
        self.save_collection_btn = QPushButton("保存数据")
        self.save_collection_btn.clicked.connect(self.save_calibration_data)
        self.save_collection_btn.setEnabled(False)
        
        self.load_collection_btn = QPushButton("加载数据")
        self.load_collection_btn.clicked.connect(self.load_calibration_data)
        
        self.debug_btn = QPushButton("调试状态")
        self.debug_btn.clicked.connect(self.debug_data_handler_status)
        
        control_layout.addWidget(self.start_collection_btn)
        control_layout.addWidget(self.stop_collection_btn)
        control_layout.addWidget(self.save_collection_btn)
        control_layout.addWidget(self.load_collection_btn)
        control_layout.addWidget(self.debug_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        
        # 收集状态
        status_group = QGroupBox("收集状态")
        status_layout = QVBoxLayout()
        
        self.collection_status_label = QLabel("状态: 未开始")
        self.collection_progress_label = QLabel("进度: 0%")
        
        status_layout.addWidget(self.collection_status_label)
        status_layout.addWidget(self.collection_progress_label)
        
        status_group.setLayout(status_layout)
        
        # 数据预览
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["压力", "平均响应", "标准差", "帧数"])
        
        preview_layout.addWidget(self.data_table)
        preview_group.setLayout(preview_layout)
        
        # 组装布局
        layout.addWidget(params_group)
        layout.addWidget(control_group)
        layout.addWidget(status_group)
        layout.addWidget(preview_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_analysis_tab(self):
        """创建校正分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 分析控制
        analysis_control_group = QGroupBox("分析控制")
        analysis_control_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("执行分析")
        self.analyze_btn.clicked.connect(self.run_calibration_analysis)
        self.analyze_btn.setEnabled(False)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["线性校正", "多项式校正", "自适应校正"])
        
        analysis_control_layout.addWidget(QLabel("校正方法:"))
        analysis_control_layout.addWidget(self.method_combo)
        analysis_control_layout.addWidget(self.analyze_btn)
        analysis_control_layout.addStretch()
        
        analysis_control_group.setLayout(analysis_control_layout)
        
        # 分析结果显示
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        
        self.analysis_results_table = QTableWidget()
        self.analysis_results_table.setColumnCount(2)
        self.analysis_results_table.setHorizontalHeaderLabels(["指标", "数值"])
        
        results_layout.addWidget(self.analysis_results_table)
        results_group.setLayout(results_layout)
        
        # 校正参数
        calibration_params_group = QGroupBox("校正参数")
        calibration_params_layout = QVBoxLayout()
        
        param_row = QHBoxLayout()
        param_row.addWidget(QLabel("目标响应值:"))
        self.target_response_spin = QDoubleSpinBox()
        self.target_response_spin.setRange(0.1, 10.0)
        self.target_response_spin.setValue(1.0)
        param_row.addWidget(self.target_response_spin)
        
        self.auto_target_check = QCheckBox("自动计算目标值")
        self.auto_target_check.setChecked(True)
        param_row.addWidget(self.auto_target_check)
        param_row.addStretch()
        
        self.generate_map_btn = QPushButton("生成校正映射")
        self.generate_map_btn.clicked.connect(self.generate_calibration_map)
        self.generate_map_btn.setEnabled(False)
        
        calibration_params_layout.addLayout(param_row)
        calibration_params_layout.addWidget(self.generate_map_btn)
        
        calibration_params_group.setLayout(calibration_params_layout)
        
        # 组装布局
        layout.addWidget(analysis_control_group)
        layout.addWidget(results_group)
        layout.addWidget(calibration_params_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_application_tab(self):
        """创建校正应用标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 校正控制
        correction_control_group = QGroupBox("校正控制")
        correction_control_layout = QHBoxLayout()
        
        self.enable_correction_check = QCheckBox("启用实时校正")
        self.enable_correction_check.stateChanged.connect(self.toggle_correction)
        
        self.save_correction_btn = QPushButton("保存校正映射")
        self.save_correction_btn.clicked.connect(self.save_correction_map)
        self.save_correction_btn.setEnabled(False)
        
        self.load_correction_btn = QPushButton("加载校正映射")
        self.load_correction_btn.clicked.connect(self.load_correction_map)
        
        correction_control_layout.addWidget(self.enable_correction_check)
        correction_control_layout.addWidget(self.save_correction_btn)
        correction_control_layout.addWidget(self.load_correction_btn)
        correction_control_layout.addStretch()
        
        correction_control_group.setLayout(correction_control_layout)
        
        # 校正效果评估
        effect_group = QGroupBox("校正效果")
        effect_layout = QVBoxLayout()
        
        self.before_after_table = QTableWidget()
        self.before_after_table.setColumnCount(3)
        self.before_after_table.setHorizontalHeaderLabels(["指标", "校正前", "校正后"])
        
        effect_layout.addWidget(self.before_after_table)
        effect_group.setLayout(effect_layout)
        
        # 测试区域
        test_group = QGroupBox("校正测试")
        test_layout = QVBoxLayout()
        
        test_control_layout = QHBoxLayout()
        self.test_correction_btn = QPushButton("测试校正效果")
        self.test_correction_btn.clicked.connect(self.test_correction_effect)
        self.test_correction_btn.setEnabled(False)
        
        test_control_layout.addWidget(self.test_correction_btn)
        test_control_layout.addStretch()
        
        self.test_results_label = QLabel("测试结果: --")
        
        test_layout.addLayout(test_control_layout)
        test_layout.addWidget(self.test_results_label)
        
        test_group.setLayout(test_layout)
        
        # 组装布局
        layout.addWidget(correction_control_group)
        layout.addWidget(effect_group)
        layout.addWidget(test_group)
        
        widget.setLayout(layout)
        return widget
    
    def debug_data_handler_status(self):
        """调试数据处理器状态"""
        # 尝试多种方式获取主界面
        main_interface = None
        
        # 方式1: 通过parent获取
        if hasattr(self.parent(), 'get_data_handler_status'):
            main_interface = self.parent()
            
        # 方式2: 通过parent的parent获取
        elif hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'get_data_handler_status'):
            main_interface = self.parent().parent()
            
        # 方式3: 通过主窗口获取
        else:
            main_window = self.window()
            if hasattr(main_window, 'get_data_handler_status'):
                main_interface = main_window
        
        if main_interface:
            status = main_interface.get_data_handler_status()
            
            # 显示状态信息
            status_text = "数据处理器状态:\n"
            for key, value in status.items():
                status_text += f"{key}: {value}\n"
            
            QMessageBox.information(self, "调试信息", status_text)
        else:
            QMessageBox.warning(self, "调试失败", "无法找到主界面")
    
    def start_calibration_collection(self):
        """开始校正数据收集"""
        # 尝试多种方式获取data_handler
        data_handler = None
        
        # 方式1: 通过parent获取
        if hasattr(self.parent(), 'data_handler'):
            data_handler = self.parent().data_handler
            
        # 方式2: 通过parent的parent获取（如果当前组件在标签页中）
        if not data_handler and hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'data_handler'):
            data_handler = self.parent().parent().data_handler
            
        # 方式3: 通过主窗口获取
        if not data_handler:
            main_window = self.window()
            if hasattr(main_window, 'data_handler'):
                data_handler = main_window.data_handler
        
        if not data_handler:
            QMessageBox.warning(self, "警告", "无法找到传感器连接，请确保传感器已连接并运行")
            return
        
        # 检查传感器是否正在运行
        if hasattr(self.parent(), 'is_running') and not self.parent().is_running:
            QMessageBox.warning(self, "警告", "传感器未运行，请先启动传感器")
            return
        
        # 获取收集参数
        collection_settings = {
            'start_pressure': self.start_pressure_spin.value(),
            'pressure_increment': self.pressure_increment_spin.value(),
            'steps': self.steps_spin.value(),
            'frames_per_step': self.frames_per_step_spin.value()
        }
        
        # 创建进度对话框
        self.progress_dialog = QProgressDialog("收集校正数据...", "取消", 0, 100, self)
        self.progress_dialog.setWindowModality(True)
        self.progress_dialog.setMinimumDuration(0)
        
        # 创建收集线程
        self.collection_thread = CalibrationDataCollector(
            data_handler, collection_settings
        )
        
        # 连接信号
        self.collection_thread.progress_updated.connect(self.progress_dialog.setValue)
        self.collection_thread.data_collected.connect(self.on_calibration_data_collected)
        self.collection_thread.message_updated.connect(self.collection_status_label.setText)
        self.progress_dialog.canceled.connect(self.collection_thread.stop)
        
        # 更新UI状态
        self.start_collection_btn.setEnabled(False)
        self.stop_collection_btn.setEnabled(True)
        
        # 开始收集
        self.collection_thread.start()
    
    def stop_calibration_collection(self):
        """停止校正数据收集"""
        if self.collection_thread:
            self.collection_thread.stop()
            self.collection_thread.wait()
        
        self.start_collection_btn.setEnabled(True)
        self.stop_collection_btn.setEnabled(False)
        
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
    
    def on_calibration_data_collected(self, data):
        """处理收集到的校正数据"""
        self.calibration_data = data
        self.update_data_preview()
        
        # 更新UI状态
        self.start_collection_btn.setEnabled(True)
        self.stop_collection_btn.setEnabled(False)
        self.save_collection_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        QMessageBox.information(self, "完成", f"已收集 {len(data)} 个压力点的数据")
    
    def update_data_preview(self):
        """更新数据预览表格"""
        self.data_table.setRowCount(len(self.calibration_data))
        
        for row, (pressure, data) in enumerate(self.calibration_data.items()):
            self.data_table.setItem(row, 0, QTableWidgetItem(f"{pressure:.2f}"))
            
            avg_response = np.mean(data['average_response'])
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{avg_response:.4f}"))
            
            avg_std = np.mean(data['std_response'])
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{avg_std:.4f}"))
            
            self.data_table.setItem(row, 3, QTableWidgetItem(str(data['frame_count'])))
    
    def save_calibration_data(self):
        """保存校正数据"""
        if not self.calibration_data:
            QMessageBox.warning(self, "警告", "没有数据可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存校正数据", "", "Pickle文件 (*.pkl);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.pkl'):
                    with open(filename, 'wb') as f:
                        pickle.dump(self.calibration_data, f)
                else:
                    # 转换numpy数组为列表以支持JSON
                    json_data = {}
                    for pressure, data in self.calibration_data.items():
                        json_data[str(pressure)] = {
                            'average_response': data['average_response'].tolist(),
                            'std_response': data['std_response'].tolist(),
                            'frame_count': data['frame_count']
                        }
                    
                    with open(filename, 'w') as f:
                        json.dump(json_data, f, indent=2)
                
                QMessageBox.information(self, "成功", f"数据已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_calibration_data(self):
        """加载校正数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载校正数据", "", "Pickle文件 (*.pkl);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.pkl'):
                    with open(filename, 'rb') as f:
                        self.calibration_data = pickle.load(f)
                else:
                    with open(filename, 'r') as f:
                        json_data = json.load(f)
                    
                    # 转换回numpy数组
                    self.calibration_data = {}
                    for pressure_str, data in json_data.items():
                        pressure = float(pressure_str)
                        self.calibration_data[pressure] = {
                            'average_response': np.array(data['average_response']),
                            'std_response': np.array(data['std_response']),
                            'frame_count': data['frame_count']
                        }
                
                self.update_data_preview()
                self.analyze_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"数据已从 {filename} 加载")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def run_calibration_analysis(self):
        """运行校正分析"""
        if not self.calibration_data:
            QMessageBox.warning(self, "警告", "请先收集或加载校正数据")
            return
        
        if not self.analyzer:
            QMessageBox.warning(self, "警告", "分析器未可用")
            return
        
        try:
            # 选择一个参考压力点进行分析（通常选择中间的压力值）
            pressures = sorted(self.calibration_data.keys())
            ref_pressure = pressures[len(pressures)//2]
            ref_data = self.calibration_data[ref_pressure]['average_response']
            
            # 转换为一致性数据格式
            consistency_data = {}
            for i in range(ref_data.shape[0]):
                for j in range(ref_data.shape[1]):
                    consistency_data[(i, j)] = ref_data[i, j]
            
            # 执行分析
            analysis_results = self.analyzer.analyze_consistency(consistency_data, ref_pressure)
            
            if analysis_results:
                self.display_analysis_results(analysis_results)
                self.generate_map_btn.setEnabled(True)
                
                # 存储分析结果以供后续使用
                self.analysis_results = analysis_results
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {e}")
    
    def display_analysis_results(self, results):
        """显示分析结果"""
        # 准备显示的指标
        display_items = []
        
        # 基础统计
        if 'basic_stats' in results and results['basic_stats']:
            stats = results['basic_stats']
            display_items.extend([
                ("有效传感器比例", f"{stats['active_sensors']}/{stats['total_sensors']} ({stats['active_sensors']/stats['total_sensors']*100:.1f}%)"),
                ("平均响应", f"{stats['mean']:.4f}"),
                ("标准差", f"{stats['std']:.4f}"),
                ("变异系数", f"{stats['cv']*100:.1f}%"),
                ("响应范围", f"{stats['min']:.4f} - {stats['max']:.4f}")
            ])
        
        # 均匀性指标
        if 'uniformity_metrics' in results and results['uniformity_metrics']:
            uniformity = results['uniformity_metrics']
            display_items.extend([
                ("均匀性指数", f"{uniformity['uniformity_index']:.3f}"),
                ("响应比率", f"{uniformity['response_ratio']:.2f}"),
                ("离群值比例", f"{uniformity['outlier_ratio']:.1%}")
            ])
        
        # 空间一致性
        if 'spatial_consistency' in results and results['spatial_consistency']:
            spatial = results['spatial_consistency']
            display_items.extend([
                ("邻域一致性", f"{spatial['neighbor_consistency']:.3f}"),
                ("高变异点数", f"{spatial['high_variation_points']}")
            ])
        
        # 敏感度分析
        if 'sensitivity_mapping' in results and results['sensitivity_mapping']:
            sensitivity = results['sensitivity_mapping']
            display_items.extend([
                ("平均敏感度", f"{sensitivity['avg_sensitivity']:.3f}"),
                ("低敏感度比例", f"{sensitivity['low_sensitivity_ratio']:.1%}"),
                ("高敏感度比例", f"{sensitivity['high_sensitivity_ratio']:.1%}")
            ])
        
        # 更新表格
        self.analysis_results_table.setRowCount(len(display_items))
        for row, (metric, value) in enumerate(display_items):
            self.analysis_results_table.setItem(row, 0, QTableWidgetItem(metric))
            self.analysis_results_table.setItem(row, 1, QTableWidgetItem(value))
        
        self.analysis_results_table.resizeColumnsToContents()
    
    def generate_calibration_map(self):
        """生成校正映射"""
        if not hasattr(self, 'analysis_results'):
            QMessageBox.warning(self, "警告", "请先执行分析")
            return
        
        try:
            # 获取参考数据
            pressures = sorted(self.calibration_data.keys())
            ref_pressure = pressures[len(pressures)//2]
            ref_data = self.calibration_data[ref_pressure]['average_response']
            
            # 确定目标响应值
            if self.auto_target_check.isChecked():
                target_response = np.median(ref_data[ref_data > 0])
                self.target_response_spin.setValue(target_response)
            else:
                target_response = self.target_response_spin.value()
            
            # 生成校正映射
            calibration_result = self.analyzer.generate_calibration_map(ref_data, target_response)
            self.calibration_map = calibration_result['calibration_map']
            
            # 更新UI状态
            self.save_correction_btn.setEnabled(True)
            self.test_correction_btn.setEnabled(True)
            
            # 显示校正范围信息
            correction_range = calibration_result['correction_range']
            QMessageBox.information(
                self, "校正映射生成完成", 
                f"目标响应值: {target_response:.4f}\n"
                f"校正系数范围: {correction_range[0]:.3f} - {correction_range[1]:.3f}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成校正映射失败: {e}")
    
    def toggle_correction(self, enabled):
        """切换校正功能"""
        if enabled and self.calibration_map is None:
            QMessageBox.warning(self, "警告", "请先生成校正映射")
            self.enable_correction_check.setChecked(False)
            return
        
        # 尝试多种方式通知主界面启用/禁用校正
        main_interface = None
        
        # 方式1: 通过parent获取
        if hasattr(self.parent(), 'set_correction_enabled'):
            main_interface = self.parent()
            
        # 方式2: 通过parent的parent获取
        elif hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'set_correction_enabled'):
            main_interface = self.parent().parent()
            
        # 方式3: 通过主窗口获取
        else:
            main_window = self.window()
            if hasattr(main_window, 'set_correction_enabled'):
                main_interface = main_window
        
        if main_interface:
            main_interface.set_correction_enabled(enabled, self.calibration_map)
        else:
            print("⚠️ 无法找到主界面来设置校正状态")
    
    def save_correction_map(self):
        """保存校正映射"""
        if self.calibration_map is None:
            QMessageBox.warning(self, "警告", "没有校正映射可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存校正映射", "", "Numpy文件 (*.npy);;Pickle文件 (*.pkl)"
        )
        
        if filename:
            try:
                if filename.endswith('.npy'):
                    np.save(filename, self.calibration_map)
                else:
                    with open(filename, 'wb') as f:
                        pickle.dump(self.calibration_map, f)
                
                QMessageBox.information(self, "成功", f"校正映射已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_correction_map(self):
        """加载校正映射"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载校正映射", "", "Numpy文件 (*.npy);;Pickle文件 (*.pkl)"
        )
        
        if filename:
            try:
                if filename.endswith('.npy'):
                    self.calibration_map = np.load(filename)
                else:
                    with open(filename, 'rb') as f:
                        self.calibration_map = pickle.load(f)
                
                self.save_correction_btn.setEnabled(True)
                self.test_correction_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"校正映射已从 {filename} 加载")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def test_correction_effect(self):
        """测试校正效果"""
        if self.calibration_map is None:
            QMessageBox.warning(self, "警告", "请先生成或加载校正映射")
            return
        
        if not self.calibration_data:
            QMessageBox.warning(self, "警告", "需要校正数据进行测试")
            return
        
        try:
            # 选择测试数据
            pressures = sorted(self.calibration_data.keys())
            test_pressure = pressures[len(pressures)//2]
            test_data = self.calibration_data[test_pressure]['average_response']
            
            # 应用校正
            corrected_data = self.calibration_system.linear_calibration(test_data, self.calibration_map)
            
            # 计算校正前后的统计信息
            before_stats = self._calculate_test_stats(test_data)
            after_stats = self._calculate_test_stats(corrected_data)
            
            # 显示对比结果
            self.display_before_after_comparison(before_stats, after_stats)
            
            # 显示总体改善情况
            cv_improvement = ((before_stats['cv'] - after_stats['cv']) / before_stats['cv']) * 100
            uniformity_improvement = ((after_stats['uniformity'] - before_stats['uniformity']) / before_stats['uniformity']) * 100
            
            self.test_results_label.setText(
                f"测试结果: CV改善 {cv_improvement:.1f}%, 均匀性改善 {uniformity_improvement:.1f}%"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试失败: {e}")
    
    def _calculate_test_stats(self, data):
        """计算测试统计信息"""
        valid_data = data[data > 0]
        
        if len(valid_data) == 0:
            return {'mean': 0, 'std': 0, 'cv': 0, 'uniformity': 0}
        
        mean_val = np.mean(valid_data)
        std_val = np.std(valid_data)
        cv = std_val / mean_val if mean_val > 0 else 0
        uniformity = 1 - cv  # 简单的均匀性指标
        
        return {
            'mean': mean_val,
            'std': std_val,
            'cv': cv,
            'uniformity': uniformity,
            'min': np.min(valid_data),
            'max': np.max(valid_data)
        }
    
    def display_before_after_comparison(self, before_stats, after_stats):
        """显示校正前后对比"""
        comparison_items = [
            ("平均值", f"{before_stats['mean']:.4f}", f"{after_stats['mean']:.4f}"),
            ("标准差", f"{before_stats['std']:.4f}", f"{after_stats['std']:.4f}"),
            ("变异系数", f"{before_stats['cv']:.3f}", f"{after_stats['cv']:.3f}"),
            ("均匀性指数", f"{before_stats['uniformity']:.3f}", f"{after_stats['uniformity']:.3f}"),
            ("最小值", f"{before_stats['min']:.4f}", f"{after_stats['min']:.4f}"),
            ("最大值", f"{before_stats['max']:.4f}", f"{after_stats['max']:.4f}")
        ]
        
        self.before_after_table.setRowCount(len(comparison_items))
        for row, (metric, before, after) in enumerate(comparison_items):
            self.before_after_table.setItem(row, 0, QTableWidgetItem(metric))
            self.before_after_table.setItem(row, 1, QTableWidgetItem(before))
            self.before_after_table.setItem(row, 2, QTableWidgetItem(after))
        
        self.before_after_table.resizeColumnsToContents()
    
    def apply_correction(self, raw_data):
        """应用校正到原始数据"""
        if self.calibration_map is None or not self.enable_correction_check.isChecked():
            return raw_data
        
        try:
            method = self.method_combo.currentText()
            
            if method == "线性校正":
                return self.calibration_system.linear_calibration(raw_data, self.calibration_map)
            elif method == "多项式校正":
                # 这里需要预先训练的多项式系数
                return raw_data  # 临时返回原始数据
            elif method == "自适应校正":
                # 需要敏感度映射和死区映射
                if hasattr(self, 'analysis_results'):
                    sensitivity_map = self.analysis_results.get('sensitivity_mapping', {}).get('sensitivity_map')
                    dead_zone_map = self.analysis_results.get('dead_zone_analysis', {}).get('dead_zone_map')
                    
                    if sensitivity_map is not None and dead_zone_map is not None:
                        return self.calibration_system.adaptive_calibration(raw_data, sensitivity_map, dead_zone_map)
                
                return raw_data
            
        except Exception as e:
            print(f"校正应用失败: {e}")
            return raw_data
        
        return raw_data