"""
基于均匀物体压测的简化校正系统
适用于使用书本、平板等均匀物体进行测试的场景
"""

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QGroupBox, QTextEdit, QProgressBar,
                            QMessageBox, QFileDialog, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer
import json
from datetime import datetime
import os # Added for file size calculation

class UniformObjectCalibration(QWidget):
    """基于均匀物体的校正系统"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_interface = parent
        self.reference_data = None  # 参考数据（理想的均匀响应）
        self.calibration_map = None  # 校正映射
        self.collection_active = False
        self.collected_frames = []
        self.collection_timer = QTimer()
        self.collection_timer.timeout.connect(self.collect_frame)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化简化的校正界面"""
        layout = QVBoxLayout()
        
        # 使用说明
        instruction_group = QGroupBox("使用说明")
        instruction_layout = QVBoxLayout()
        
        instruction_text = """
📋 简单校正流程：
1. 准备一个均匀的物体（如书本、平板、托盘等）
2. 将物体平稳地压在传感器表面
3. 点击"开始收集参考数据"，保持压力稳定
4. 收集完成后，点击"分析并生成校正"
5. 启用"实时校正"即可使用

💡 提示：物体越大越平整，校正效果越好
        """
        
        instruction_label = QLabel(instruction_text)
        instruction_label.setStyleSheet("font-size: 12px; color: #555;")
        instruction_layout.addWidget(instruction_label)
        instruction_group.setLayout(instruction_layout)
        
        # 数据收集控制
        collection_group = QGroupBox("参考数据收集")
        collection_layout = QVBoxLayout()
        
        # 收集参数
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("收集帧数:"))
        self.frame_count_spin = QSpinBox()
        self.frame_count_spin.setRange(50, 500)
        self.frame_count_spin.setValue(100)
        self.frame_count_spin.setSuffix(" 帧")
        param_layout.addWidget(self.frame_count_spin)
        param_layout.addStretch()
        
        # 收集控制按钮
        button_layout = QHBoxLayout()
        self.start_collection_btn = QPushButton("开始收集参考数据")
        self.start_collection_btn.clicked.connect(self.start_reference_collection)
        
        self.stop_collection_btn = QPushButton("停止收集")
        self.stop_collection_btn.clicked.connect(self.stop_collection)
        self.stop_collection_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_collection_btn)
        button_layout.addWidget(self.stop_collection_btn)
        button_layout.addStretch()
        
        # 收集状态
        self.collection_status = QLabel("状态: 未开始")
        self.collection_progress = QProgressBar()
        self.collection_progress.setVisible(False)
        
        collection_layout.addLayout(param_layout)
        collection_layout.addLayout(button_layout)
        collection_layout.addWidget(self.collection_status)
        collection_layout.addWidget(self.collection_progress)
        
        collection_group.setLayout(collection_layout)
        
        # 分析和校正
        analysis_group = QGroupBox("校正分析")
        analysis_layout = QVBoxLayout()
        
        # 分析控制
        analysis_control_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("分析并生成校正")
        self.analyze_btn.clicked.connect(self.analyze_and_generate_correction)
        self.analyze_btn.setEnabled(False)
        
        # 保存和加载控制
        save_load_layout = QHBoxLayout()
        
        self.save_reference_btn = QPushButton("保存参考数据")
        self.save_reference_btn.clicked.connect(self.save_reference_data)
        self.save_reference_btn.setEnabled(False)
        
        self.save_raw_frames_btn = QPushButton("保存原始帧数据")
        self.save_raw_frames_btn.clicked.connect(self.save_raw_frames_data)
        self.save_raw_frames_btn.setEnabled(False)
        
        self.load_reference_btn = QPushButton("加载参考数据")
        self.load_reference_btn.clicked.connect(self.load_reference_data)
        
        self.load_raw_frames_btn = QPushButton("加载原始帧数据")
        self.load_raw_frames_btn.clicked.connect(self.load_raw_frames_data)
        
        save_load_layout.addWidget(self.save_reference_btn)
        save_load_layout.addWidget(self.save_raw_frames_btn)
        save_load_layout.addWidget(self.load_reference_btn)
        save_load_layout.addWidget(self.load_raw_frames_btn)
        save_load_layout.addStretch()
        
        analysis_control_layout.addWidget(self.analyze_btn)
        analysis_control_layout.addLayout(save_load_layout)
        
        # 分析结果显示
        self.analysis_results = QTextEdit()
        self.analysis_results.setMaximumHeight(150)
        self.analysis_results.setReadOnly(True)
        
        analysis_layout.addLayout(analysis_control_layout)
        analysis_layout.addWidget(QLabel("分析结果:"))
        analysis_layout.addWidget(self.analysis_results)
        
        analysis_group.setLayout(analysis_layout)
        
        # 校正应用
        application_group = QGroupBox("校正应用")
        application_layout = QVBoxLayout()
        
        # 校正控制
        correction_control_layout = QHBoxLayout()
        self.enable_correction_check = QCheckBox("启用实时校正")
        self.enable_correction_check.stateChanged.connect(self.toggle_correction)
        
        self.save_calibration_btn = QPushButton("保存校正文件")
        self.save_calibration_btn.clicked.connect(self.save_calibration_map)
        self.save_calibration_btn.setEnabled(False)
        
        self.load_calibration_btn = QPushButton("加载校正文件")
        self.load_calibration_btn.clicked.connect(self.load_calibration_map)
        
        correction_control_layout.addWidget(self.enable_correction_check)
        correction_control_layout.addWidget(self.save_calibration_btn)
        correction_control_layout.addWidget(self.load_calibration_btn)
        correction_control_layout.addStretch()
        
        # 校正效果显示
        self.correction_effect = QLabel("校正效果: --")
        self.correction_effect.setStyleSheet("font-weight: bold; color: #2196F3;")
        
        application_layout.addLayout(correction_control_layout)
        application_layout.addWidget(self.correction_effect)
        
        application_group.setLayout(application_layout)
        
        # 组装主布局
        layout.addWidget(instruction_group)
        layout.addWidget(collection_group)
        layout.addWidget(analysis_group)
        layout.addWidget(application_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def start_reference_collection(self):
        """开始收集参考数据"""
        if not self.parent_interface or not self.parent_interface.is_running:
            QMessageBox.warning(self, "警告", "请先连接传感器并开始采集")
            return
        
        # 提示用户准备
        msg = QMessageBox(self)
        msg.setWindowTitle("准备收集参考数据")
        msg.setText("请将均匀的物体（如书本、平板）平稳地压在传感器表面，\n保持压力稳定，然后点击确定开始收集。")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        if msg.exec_() != QMessageBox.Ok:
            return
        
        # 开始收集
        self.collection_active = True
        self.collected_frames = []
        target_frames = self.frame_count_spin.value()
        
        # 更新UI状态
        self.start_collection_btn.setEnabled(False)
        self.stop_collection_btn.setEnabled(True)
        self.collection_progress.setVisible(True)
        self.collection_progress.setMaximum(target_frames)
        self.collection_progress.setValue(0)
        self.collection_status.setText("状态: 正在收集数据...")
        
        # 开始定时收集
        self.collection_timer.start(100)  # 每100ms收集一帧
    
    def collect_frame(self):
        """收集一帧数据"""
        if not self.collection_active:
            return
        
        try:
            # 获取当前传感器数据
            current_data = None
            if hasattr(self.parent_interface, 'data_handler') and self.parent_interface.data_handler:
                self.parent_interface.data_handler.trigger()
                with self.parent_interface.data_handler.lock:
                    if self.parent_interface.data_handler.value:
                        current_data = np.array(self.parent_interface.data_handler.value[-1])
            else:
                # 使用模拟数据进行测试
                current_data = self.parent_interface.generate_simulated_data()
            
            if current_data is not None:
                self.collected_frames.append(current_data.copy())
                
                # 更新进度
                progress = len(self.collected_frames)
                self.collection_progress.setValue(progress)
                self.collection_status.setText(f"状态: 已收集 {progress}/{self.frame_count_spin.value()} 帧")
                
                # 检查是否完成
                if progress >= self.frame_count_spin.value():
                    self.finish_collection()
                    
        except Exception as e:
            print(f"⚠️ 收集数据时出错: {e}")
            self.stop_collection()
    
    def stop_collection(self):
        """停止收集"""
        self.collection_active = False
        self.collection_timer.stop()
        
        # 更新UI状态
        self.start_collection_btn.setEnabled(True)
        self.stop_collection_btn.setEnabled(False)
        self.collection_progress.setVisible(False)
        
        if len(self.collected_frames) > 0:
            self.collection_status.setText(f"状态: 已收集 {len(self.collected_frames)} 帧数据")
        else:
            self.collection_status.setText("状态: 收集已取消")
    
    def finish_collection(self):
        """完成数据收集"""
        self.stop_collection()
        
        if len(self.collected_frames) == 0:
            return
        
        # 计算平均数据作为参考
        self.reference_data = np.mean(self.collected_frames, axis=0)
        
        # 更新UI状态
        self.analyze_btn.setEnabled(True)
        self.save_reference_btn.setEnabled(True)
        self.save_raw_frames_btn.setEnabled(True)  # 启用保存原始帧数据按钮
        self.collection_status.setText(f"状态: 参考数据收集完成 ({len(self.collected_frames)} 帧)")
        
        QMessageBox.information(self, "收集完成", f"已成功收集 {len(self.collected_frames)} 帧参考数据")
    
    def analyze_and_generate_correction(self):
        """分析参考数据并生成校正映射"""
        if self.reference_data is None:
            QMessageBox.warning(self, "警告", "请先收集参考数据")
            return
        
        try:
            # 分析参考数据的特性
            analysis_result = self.analyze_reference_data()
            
            # 生成校正映射
            self.calibration_map = self.generate_simple_calibration_map()
            
            # 显示分析结果
            self.display_analysis_results(analysis_result)
            
            # 更新UI状态
            self.save_calibration_btn.setEnabled(True)
            
            QMessageBox.information(self, "分析完成", "校正映射已生成，可以启用实时校正")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {e}")
    
    def analyze_reference_data(self):
        """分析参考数据"""
        data = self.reference_data
        
        # 过滤有效数据（排除很小的噪声值）
        threshold = np.mean(data) * 0.1
        valid_data = data[data > threshold]
        
        # 基础统计
        stats = {
            'total_points': data.size,
            'active_points': len(valid_data),
            'active_ratio': len(valid_data) / data.size,
            'mean_response': np.mean(valid_data) if len(valid_data) > 0 else 0,
            'std_response': np.std(valid_data) if len(valid_data) > 0 else 0,
            'cv': np.std(valid_data) / np.mean(valid_data) if len(valid_data) > 0 and np.mean(valid_data) > 0 else 0,
            'min_response': np.min(valid_data) if len(valid_data) > 0 else 0,
            'max_response': np.max(valid_data) if len(valid_data) > 0 else 0
        }
        
        # 一致性分析
        if len(valid_data) > 0:
            # 计算响应范围
            response_range = stats['max_response'] - stats['min_response']
            stats['response_range'] = response_range
            stats['relative_range'] = response_range / stats['mean_response'] if stats['mean_response'] > 0 else 0
            
            # 计算不一致性区域
            mean_response = stats['mean_response']
            low_response_threshold = mean_response * 0.7  # 低于平均值30%
            high_response_threshold = mean_response * 1.3  # 高于平均值30%
            
            low_response_count = np.sum(data < low_response_threshold)
            high_response_count = np.sum(data > high_response_threshold)
            
            stats['low_response_ratio'] = low_response_count / data.size
            stats['high_response_ratio'] = high_response_count / data.size
        
        return stats
    
    def generate_simple_calibration_map(self):
        """生成简单的校正映射"""
        data = self.reference_data
        
        # 计算目标响应值（使用中位数，更稳定）
        valid_data = data[data > np.mean(data) * 0.1]
        target_response = np.median(valid_data) if len(valid_data) > 0 else 1.0
        
        # 生成校正映射
        calibration_map = np.ones_like(data)
        
        # 只对有效响应的区域进行校正
        valid_mask = data > np.mean(data) * 0.1
        calibration_map[valid_mask] = target_response / data[valid_mask]
        
        # 限制校正系数范围，避免过度校正
        calibration_map = np.clip(calibration_map, 0.2, 5.0)
        
        return calibration_map
    
    def display_analysis_results(self, stats):
        """显示分析结果"""
        result_text = f"""
=== 传感器一致性分析结果 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 基础统计:
• 总传感器数: {stats['total_points']}
• 有效传感器数: {stats['active_points']} ({stats['active_ratio']:.1%})
• 平均响应: {stats['mean_response']:.4f}
• 标准差: {stats['std_response']:.4f}
• 变异系数: {stats['cv']:.1%}

📈 响应范围:
• 最小响应: {stats['min_response']:.4f}
• 最大响应: {stats['max_response']:.4f}
• 响应范围: {stats.get('response_range', 0):.4f}
• 相对范围: {stats.get('relative_range', 0):.1%}

⚠️ 不一致性分析:
• 低响应区域: {stats.get('low_response_ratio', 0):.1%}
• 高响应区域: {stats.get('high_response_ratio', 0):.1%}

💡 建议:
"""
        
        # 根据变异系数给出建议
        cv = stats['cv']
        if cv < 0.1:
            result_text += "• 传感器一致性很好，校正可选"
        elif cv < 0.2:
            result_text += "• 传感器一致性良好，轻微校正可提升精度"
        elif cv < 0.3:
            result_text += "• 传感器一致性中等，建议进行校正"
        else:
            result_text += "• 传感器一致性较差，强烈建议进行校正"
        
        self.analysis_results.setText(result_text)
    
    def toggle_correction(self, enabled):
        """切换校正功能"""
        if enabled and self.calibration_map is None:
            QMessageBox.warning(self, "警告", "请先分析并生成校正映射")
            self.enable_correction_check.setChecked(False)
            return
        
        # 通知父界面启用/禁用校正
        if hasattr(self.parent_interface, 'set_correction_enabled'):
            self.parent_interface.set_correction_enabled(enabled, self.calibration_map)
        
        # 更新效果显示
        if enabled:
            self.correction_effect.setText("校正效果: 实时校正已启用")
            self.correction_effect.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.correction_effect.setText("校正效果: 校正已关闭")
            self.correction_effect.setStyleSheet("font-weight: bold; color: gray;")
    
    def save_reference_data(self):
        """保存参考数据"""
        if self.reference_data is None:
            QMessageBox.warning(self, "警告", "没有参考数据可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存参考数据", "", "Numpy文件 (*.npy);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.npy'):
                    np.save(filename, self.reference_data)
                else:
                    data_dict = {
                        'reference_data': self.reference_data.tolist(),
                        'timestamp': datetime.now().isoformat(),
                        'frame_count': len(self.collected_frames) if self.collected_frames else 0
                    }
                    with open(filename, 'w') as f:
                        json.dump(data_dict, f, indent=2)
                
                QMessageBox.information(self, "成功", f"参考数据已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_raw_frames_data(self):
        """保存所有原始帧数据"""
        if not self.collected_frames:
            QMessageBox.warning(self, "警告", "没有原始帧数据可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存原始帧数据", "", "Numpy压缩文件 (*.npz);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.npz'):
                    # 保存为NumPy压缩格式，包含所有帧数据
                    frames_array = np.array(self.collected_frames)
                    np.savez_compressed(
                        filename,
                        frames=frames_array,
                        reference_data=self.reference_data if self.reference_data is not None else np.array([]),
                        timestamp=datetime.now().isoformat(),
                        frame_count=len(self.collected_frames),
                        frame_shape=frames_array.shape[1:] if len(frames_array.shape) > 1 else frames_array.shape
                    )
                else:
                    # 保存为JSON格式
                    data_dict = {
                        'frames': [frame.tolist() for frame in self.collected_frames],
                        'reference_data': self.reference_data.tolist() if self.reference_data is not None else [],
                        'timestamp': datetime.now().isoformat(),
                        'frame_count': len(self.collected_frames),
                        'frame_shape': list(self.collected_frames[0].shape) if self.collected_frames else []
                    }
                    with open(filename, 'w') as f:
                        json.dump(data_dict, f, indent=2)
                
                file_size = os.path.getsize(filename)
                QMessageBox.information(
                    self, "成功", 
                    f"原始帧数据已保存到: {filename}\n"
                    f"包含 {len(self.collected_frames)} 帧数据\n"
                    f"文件大小: {file_size/1024:.1f} KB"
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_reference_data(self):
        """加载参考数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载参考数据", "", "Numpy文件 (*.npy);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.npy'):
                    self.reference_data = np.load(filename)
                else:
                    with open(filename, 'r') as f:
                        data_dict = json.load(f)
                    self.reference_data = np.array(data_dict['reference_data'])
                
                self.analyze_btn.setEnabled(True)
                self.save_reference_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"参考数据已从 {filename} 加载")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def load_raw_frames_data(self):
        """加载原始帧数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载原始帧数据", "", "Numpy压缩文件 (*.npz);;JSON文件 (*.json)"
        )
        
        if filename:
            try:
                if filename.endswith('.npz'):
                    # 加载NumPy压缩格式
                    data = np.load(filename)
                    self.collected_frames = [frame for frame in data['frames']]
                    if 'reference_data' in data and len(data['reference_data']) > 0:
                        self.reference_data = data['reference_data']
                    else:
                        # 重新计算参考数据
                        self.reference_data = np.mean(self.collected_frames, axis=0)
                else:
                    # 加载JSON格式
                    with open(filename, 'r') as f:
                        data_dict = json.load(f)
                    self.collected_frames = [np.array(frame) for frame in data_dict['frames']]
                    if data_dict.get('reference_data'):
                        self.reference_data = np.array(data_dict['reference_data'])
                    else:
                        # 重新计算参考数据
                        self.reference_data = np.mean(self.collected_frames, axis=0)
                
                # 更新UI状态
                self.analyze_btn.setEnabled(True)
                self.save_reference_btn.setEnabled(True)
                self.save_raw_frames_btn.setEnabled(True)
                self.collection_status.setText(f"状态: 已加载 {len(self.collected_frames)} 帧原始数据")
                
                QMessageBox.information(
                    self, "成功", 
                    f"原始帧数据已从 {filename} 加载\n"
                    f"包含 {len(self.collected_frames)} 帧数据"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def save_calibration_map(self):
        """保存校正映射"""
        if self.calibration_map is None:
            QMessageBox.warning(self, "警告", "没有校正映射可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存校正映射", "", "Numpy文件 (*.npy)"
        )
        
        if filename:
            try:
                np.save(filename, self.calibration_map)
                QMessageBox.information(self, "成功", f"校正映射已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_calibration_map(self):
        """加载校正映射"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载校正映射", "", "Numpy文件 (*.npy)"
        )
        
        if filename:
            try:
                self.calibration_map = np.load(filename)
                self.save_calibration_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"校正映射已从 {filename} 加载")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def apply_correction(self, raw_data):
        """应用校正到原始数据"""
        if self.calibration_map is None or not self.enable_correction_check.isChecked():
            return raw_data
        
        try:
            # 简单的线性校正
            corrected_data = raw_data * self.calibration_map
            return corrected_data
        except Exception as e:
            print(f"校正应用失败: {e}")
            return raw_data 