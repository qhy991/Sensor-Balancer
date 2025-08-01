"""
帧间一致性分析模块
分析传感器在连续帧之间的数据不一致性问题
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QGroupBox, QTextEdit, QProgressBar, 
                            QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget,
                            QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from datetime import datetime, timedelta
import json
import logging
import traceback

class FrameConsistencyAnalyzer:
    """帧间一致性分析器"""
    
    def __init__(self, config=None):
        # 配置日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 默认配置
        self.default_config = {
            'max_history_size': 100,
            'anomaly_threshold': 3.0,  # 异常检测阈值
            'stability_threshold': 0.1,  # 稳定性阈值
            'noise_threshold': 0.3,  # 噪声检测阈值
            'min_frames_for_analysis': 2,
            'min_frames_for_stability': 3,
            'min_frames_for_anomaly': 5,
            'min_frames_for_noise': 3,
            'consistency_weights': {
                'frame_difference': 0.4,
                'stability': 0.3,
                'noise': 0.2,
                'anomaly': 0.1
            }
        }
        
        # 合并用户配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
        
        self.frame_history = []  # 存储历史帧数据
        self.analysis_results = {}
        
        self.logger.info("FrameConsistencyAnalyzer initialized with config: %s", self.config)
    
    def add_frame(self, frame_data):
        """添加新帧数据"""
        try:
            if frame_data is None:
                self.logger.warning("Received None frame data, skipping")
                return
            
            # 确保数据格式正确
            if isinstance(frame_data, list):
                frame_data = np.array(frame_data)
            
            # 验证数据形状
            if not isinstance(frame_data, np.ndarray):
                raise ValueError("Frame data must be numpy array or list")
            
            if frame_data.ndim != 2:
                raise ValueError(f"Frame data must be 2D array, got {frame_data.ndim}D")
            
            # 添加到历史记录
            self.frame_history.append(frame_data.copy())
            
            # 保持历史记录大小
            if len(self.frame_history) > self.config['max_history_size']:
                removed_frame = self.frame_history.pop(0)
                self.logger.debug("Removed oldest frame from history")
            
            self.logger.debug("Added frame to history, current size: %d", len(self.frame_history))
            
        except Exception as e:
            self.logger.error("Error adding frame: %s", str(e))
            self.logger.error("Traceback: %s", traceback.format_exc())
            raise
    
    def analyze_frame_consistency(self, current_frame=None):
        """
        分析帧间一致性
        
        Args:
            current_frame: 当前帧数据（可选，如果不提供则使用最新帧）
            
        Returns:
            帧间一致性分析结果
        """
        if len(self.frame_history) < self.config['min_frames_for_analysis']:
            return {}
        
        if current_frame is not None:
            self.add_frame(current_frame)
        
        results = {}
        
        # 1. 计算帧间差异
        frame_differences = self._calculate_frame_differences()
        
        # 2. 分析稳定性指标
        stability_metrics = self._analyze_stability_metrics()
        
        # 3. 检测异常帧
        anomaly_frames = self._detect_anomaly_frames()
        
        # 4. 分析噪声特性
        noise_characteristics = self._analyze_noise_characteristics()
        
        # 5. 计算一致性评分
        consistency_score = self._calculate_consistency_score()
        
        results = {
            'frame_differences': frame_differences,
            'stability_metrics': stability_metrics,
            'anomaly_frames': anomaly_frames,
            'noise_characteristics': noise_characteristics,
            'consistency_score': consistency_score,
            'summary_stats': self._calculate_summary_stats(results)
        }
        
        return results
    
    def _calculate_frame_differences(self):
        """计算帧间差异"""
        if len(self.frame_history) < 2:
            return {}
        
        differences = []
        relative_differences = []
        
        for i in range(1, len(self.frame_history)):
            prev_frame = self.frame_history[i-1]
            curr_frame = self.frame_history[i]
            
            # 绝对差异
            abs_diff = np.abs(curr_frame - prev_frame)
            differences.append(abs_diff)
            
            # 相对差异（避免除零）
            mask = prev_frame > 0.001  # 避免除以很小的值
            rel_diff = np.zeros_like(curr_frame)
            rel_diff[mask] = abs_diff[mask] / prev_frame[mask]
            relative_differences.append(rel_diff)
        
        return {
            'absolute_differences': differences,
            'relative_differences': relative_differences,
            'mean_abs_diff': np.mean([np.mean(diff) for diff in differences]),
            'max_abs_diff': np.max([np.max(diff) for diff in differences]),
            'mean_rel_diff': np.mean([np.mean(rel_diff) for rel_diff in relative_differences]),
            'max_rel_diff': np.max([np.max(rel_diff) for rel_diff in relative_differences])
        }
    
    def _analyze_stability_metrics_vectorized(self):
        """向量化分析稳定性指标（性能优化版本）"""
        if len(self.frame_history) < self.config['min_frames_for_stability']:
            return {}
        
        # 将历史帧堆叠成3D数组
        frame_stack = np.array(self.frame_history)
        
        # 向量化计算
        std_map = np.std(frame_stack, axis=0)
        mean_map = np.mean(frame_stack, axis=0)
        
        # 避免除零
        cv_map = np.divide(std_map, mean_map, out=np.zeros_like(std_map), where=mean_map > 0.001)
        stability_map = np.maximum(0, 1 - cv_map)
        
        return {
            'stability_map': stability_map,
            'variance_map': std_map**2,
            'cv_map': cv_map,
            'mean_stability': np.mean(stability_map),
            'mean_variance': np.mean(std_map**2),
            'mean_cv': np.mean(cv_map),
            'unstable_sensors': np.sum(cv_map > self.config['stability_threshold'])
        }
    
    def _analyze_stability_metrics(self):
        """分析稳定性指标"""
        # 使用向量化版本以提高性能
        return self._analyze_stability_metrics_vectorized()
    
    def _detect_anomaly_frames(self):
        """检测异常帧"""
        if len(self.frame_history) < self.config['min_frames_for_anomaly']:
            return []
        
        anomalies = []
        frame_stack = np.array(self.frame_history)
        
        for frame_idx in range(len(frame_stack)):
            frame_data = frame_stack[frame_idx]
            
            # 计算该帧与历史帧的差异
            if frame_idx > 0:
                prev_frame = frame_stack[frame_idx-1]
                diff = np.abs(frame_data - prev_frame)
                
                # 检测异常：差异超过历史平均差异的3倍
                mean_diff = np.mean(diff)
                std_diff = np.std(diff)
                
                if mean_diff > 0:
                    anomaly_score = mean_diff / (std_diff + 1e-6)
                    
                    if anomaly_score > self.config['anomaly_threshold']:  # 使用配置的阈值
                        anomalies.append({
                            'frame_index': frame_idx,
                            'anomaly_score': anomaly_score,
                            'mean_difference': mean_diff,
                            'max_difference': np.max(diff),
                            'timestamp': datetime.now() - timedelta(seconds=len(frame_stack)-frame_idx)
                        })
        
        return anomalies
    
    def _analyze_noise_characteristics(self):
        """分析噪声特性"""
        if len(self.frame_history) < self.config['min_frames_for_noise']:
            return {}
        
        frame_stack = np.array(self.frame_history)
        height, width = frame_stack[0].shape
        
        # 计算每个传感器点的噪声特性
        noise_power = np.zeros((height, width))
        noise_frequency = np.zeros((height, width))
        
        for i in range(height):
            for j in range(width):
                time_series = frame_stack[:, i, j]
                
                if len(time_series) > 2:
                    # 计算噪声功率（方差）
                    noise_power[i, j] = np.var(time_series)
                    
                    # 计算噪声频率特性（使用FFT）
                    if len(time_series) > 10:
                        fft_result = np.fft.fft(time_series)
                        power_spectrum = np.abs(fft_result)**2
                        
                        # 找到主要频率成分
                        main_freq_idx = np.argmax(power_spectrum[1:len(power_spectrum)//2]) + 1
                        noise_frequency[i, j] = main_freq_idx / len(time_series)
        
        return {
            'noise_power_map': noise_power,
            'noise_frequency_map': noise_frequency,
            'mean_noise_power': np.mean(noise_power),
            'mean_noise_frequency': np.mean(noise_frequency),
            'high_noise_sensors': np.sum(noise_power > np.mean(noise_power) * self.config['noise_threshold']) # 噪声功率>均值*阈值的传感器
        }
    
    def _calculate_consistency_score(self):
        """计算一致性评分（0-10分）"""
        if len(self.frame_history) < self.config['min_frames_for_analysis']:
            return 0.0
        
        # 获取分析结果
        frame_diffs = self._calculate_frame_differences()
        stability_metrics = self._analyze_stability_metrics()
        noise_chars = self._analyze_noise_characteristics()
        
        score = 10.0  # 满分10分
        weights = self.config['consistency_weights']
        
        # 1. 帧间差异评分
        if 'mean_abs_diff' in frame_diffs:
            mean_diff = frame_diffs['mean_abs_diff']
            # 差异越小，得分越高
            diff_score = max(0, weights['frame_difference'] * 10 - mean_diff * 1000)
            score = score - weights['frame_difference'] * 10 + diff_score
        
        # 2. 稳定性评分
        if 'mean_stability' in stability_metrics:
            stability = stability_metrics['mean_stability']
            stability_score = stability * weights['stability'] * 10
            score = score - weights['stability'] * 10 + stability_score
        
        # 3. 噪声评分
        if 'mean_noise_power' in noise_chars:
            noise_power = noise_chars['mean_noise_power']
            # 噪声越小，得分越高
            noise_score = max(0, weights['noise'] * 10 - noise_power * 1000)
            score = score - weights['noise'] * 10 + noise_score
        
        # 4. 异常帧惩罚
        anomalies = self._detect_anomaly_frames()
        anomaly_penalty = min(weights['anomaly'] * 10, len(anomalies) * 0.2)
        score = score - anomaly_penalty
        
        return max(0.0, min(10.0, score))
    
    def _calculate_summary_stats(self, results):
        """计算统计摘要"""
        if not results:
            return {}
        
        summary = {
            'total_frames': len(self.frame_history),
            'consistency_score': results.get('consistency_score', 0),
            'analysis_time': datetime.now().isoformat()
        }
        
        # 添加帧间差异统计
        if 'frame_differences' in results:
            frame_diffs = results['frame_differences']
            summary.update({
                'mean_frame_difference': frame_diffs.get('mean_abs_diff', 0),
                'max_frame_difference': frame_diffs.get('max_abs_diff', 0),
                'mean_relative_difference': frame_diffs.get('mean_rel_diff', 0)
            })
        
        # 添加稳定性统计
        if 'stability_metrics' in results:
            stability = results['stability_metrics']
            summary.update({
                'mean_stability': stability.get('mean_stability', 0),
                'mean_variance': stability.get('mean_variance', 0),
                'unstable_sensors': stability.get('unstable_sensors', 0)
            })
        
        # 添加噪声统计
        if 'noise_characteristics' in results:
            noise = results['noise_characteristics']
            summary.update({
                'mean_noise_power': noise.get('mean_noise_power', 0),
                'high_noise_sensors': noise.get('high_noise_sensors', 0)
            })
        
        # 添加异常统计
        if 'anomaly_frames' in results:
            anomalies = results['anomaly_frames']
            summary.update({
                'anomaly_frame_count': len(anomalies),
                'anomaly_rate': len(anomalies) / max(1, len(self.frame_history))
            })
        
        return summary

    def get_performance_stats(self):
        """获取性能统计信息"""
        stats = {
            'frame_history_size': len(self.frame_history),
            'memory_usage_estimate': len(self.frame_history) * 64 * 64 * 8,  # 假设64x64 float64
            'analysis_count': len(self.analysis_results),
            'last_analysis_time': self.analysis_results.get('last_analysis_time', None)
        }
        
        if self.frame_history:
            stats['frame_shape'] = self.frame_history[0].shape
            stats['data_type'] = str(self.frame_history[0].dtype)
        
        return stats
    
    def clear_history(self):
        """清空历史数据"""
        self.frame_history.clear()
        self.analysis_results.clear()
        self.logger.info("Cleared frame history and analysis results")
    
    def get_config(self):
        """获取当前配置"""
        return self.config.copy()
    
    def update_config(self, new_config):
        """更新配置"""
        self.config.update(new_config)
        self.logger.info("Updated config: %s", new_config)


class FrameConsistencyWidget(QWidget):
    """帧间一致性分析界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = FrameConsistencyAnalyzer()
        self.is_monitoring = False
        self.monitor_timer = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("帧间一致性分析")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 控制面板
        control_group = QGroupBox("分析控制")
        control_layout = QHBoxLayout()
        
        self.start_monitoring_btn = QPushButton("开始监测")
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        
        self.stop_monitoring_btn = QPushButton("停止监测")
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitoring_btn.setEnabled(False)
        
        self.analyze_current_btn = QPushButton("分析当前数据")
        self.analyze_current_btn.clicked.connect(self.analyze_current_data)
        
        self.clear_data_btn = QPushButton("清空数据")
        self.clear_data_btn.clicked.connect(self.clear_data)
        
        self.diagnose_btn = QPushButton("诊断问题")
        self.diagnose_btn.clicked.connect(self.show_diagnosis)
        self.diagnose_btn.setToolTip("诊断数据收集问题")
        
        self.help_btn = QPushButton("使用指南")
        self.help_btn.clicked.connect(self.show_usage_guide)
        self.help_btn.setToolTip("查看使用指南")
        
        control_layout.addWidget(self.start_monitoring_btn)
        control_layout.addWidget(self.stop_monitoring_btn)
        control_layout.addWidget(self.analyze_current_btn)
        control_layout.addWidget(self.clear_data_btn)
        control_layout.addWidget(self.diagnose_btn)
        control_layout.addWidget(self.help_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 实时状态
        status_group = QGroupBox("实时状态")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 未开始监测")
        self.frame_count_label = QLabel("已收集帧数: 0")
        self.consistency_score_label = QLabel("一致性评分: --")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.frame_count_label)
        status_layout.addWidget(self.consistency_score_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 分析结果
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(300)
        
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_results_btn = QPushButton("保存分析结果")
        self.save_results_btn.clicked.connect(self.save_results)
        self.save_results_btn.setEnabled(False)
        
        save_layout.addWidget(self.save_results_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        self.setLayout(layout)
    
    def test_data_collection(self):
        """测试数据收集功能"""
        self.log_message("开始测试数据收集...")
        
        # 测试1: 检查父窗口
        if not self.parent():
            self.log_message("❌ 错误: 没有父窗口")
            return False
        
        # 测试2: 检查父窗口方法
        if not hasattr(self.parent(), 'get_current_sensor_data'):
            self.log_message("❌ 错误: 父窗口没有get_current_sensor_data方法")
            return False
        
        # 测试3: 检查传感器运行状态
        if hasattr(self.parent(), 'is_running') and not self.parent().is_running:
            self.log_message("❌ 错误: 传感器未运行")
            return False
        
        # 测试4: 尝试获取数据
        try:
            test_data = self.parent().get_current_sensor_data()
            if test_data is None:
                self.log_message("❌ 错误: get_current_sensor_data返回None")
                return False
            
            self.log_message(f"✅ 成功获取测试数据，形状: {test_data.shape}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ 错误: 获取数据时异常: {e}")
            return False
    
    def start_monitoring(self):
        """开始监测"""
        # 先进行测试
        if not self.test_data_collection():
            QMessageBox.warning(self, "警告", "数据收集测试失败，请检查传感器状态")
            return
        
        self.is_monitoring = True
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        
        # 启动定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.collect_frame_data)
        self.monitor_timer.start(100)  # 每100ms收集一次数据
        
        self.status_label.setText("状态: 正在监测")
        self.log_message("开始帧间一致性监测")
    
    def stop_monitoring(self):
        """停止监测"""
        self.is_monitoring = False
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)
        
        if self.monitor_timer:
            self.monitor_timer.stop()
        
        self.status_label.setText("状态: 监测已停止")
        self.log_message("停止帧间一致性监测")
        
        # 自动分析收集到的数据
        if len(self.analyzer.frame_history) > 1:
            self.analyze_current_data()
    
    def collect_frame_data(self):
        """收集帧数据"""
        if not self.is_monitoring:
            return
        
        # 从主界面获取当前传感器数据
        if hasattr(self.parent(), 'get_current_sensor_data'):
            current_data = self.parent().get_current_sensor_data()
            if current_data is not None:
                self.analyzer.add_frame(current_data)
                
                # 更新状态
                frame_count = len(self.analyzer.frame_history)
                self.frame_count_label.setText(f"已收集帧数: {frame_count}")
                
                # 实时计算一致性评分
                if frame_count > 1:
                    consistency_score = self.analyzer._calculate_consistency_score()
                    self.consistency_score_label.setText(f"一致性评分: {consistency_score:.2f}/10")
                
                # 添加调试信息
                if frame_count % 10 == 0:  # 每10帧记录一次
                    self.log_message(f"已收集 {frame_count} 帧数据，最新数据形状: {current_data.shape}")
            else:
                # 添加调试信息
                self.log_message("警告: 无法获取传感器数据")
        else:
            # 添加调试信息
            self.log_message("警告: 父窗口没有 get_current_sensor_data 方法")
    
    def analyze_current_data(self):
        """分析当前数据"""
        if len(self.analyzer.frame_history) < 2:
            QMessageBox.warning(self, "警告", "数据不足，至少需要2帧数据")
            return
        
        try:
            # 执行分析
            results = self.analyzer.analyze_frame_consistency()
            
            # 显示结果
            self.display_results(results)
            
            # 启用保存按钮
            self.save_results_btn.setEnabled(True)
            
            self.log_message("帧间一致性分析完成")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {e}")
            self.log_message(f"分析失败: {e}")
    
    def display_results(self, results):
        """显示分析结果"""
        if not results:
            return
        
        summary = results.get('summary_stats', {})
        
        result_text = f"""
=== 帧间一致性分析结果 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 基本统计:
• 总帧数: {summary.get('total_frames', 0)}
• 一致性评分: {summary.get('consistency_score', 0):.2f}/10

📈 帧间差异分析:
• 平均帧间差异: {summary.get('mean_frame_difference', 0):.6f}
• 最大帧间差异: {summary.get('max_frame_difference', 0):.6f}
• 平均相对差异: {summary.get('mean_relative_difference', 0)*100:.2f}%

🔍 稳定性分析:
• 平均稳定性: {summary.get('mean_stability', 0):.3f}
• 平均方差: {summary.get('mean_variance', 0):.6f}
• 不稳定传感器: {summary.get('unstable_sensors', 0)} 个

📊 噪声特性:
• 平均噪声功率: {summary.get('mean_noise_power', 0):.6f}
• 高噪声传感器: {summary.get('high_noise_sensors', 0)} 个

⚠️ 异常检测:
• 异常帧数量: {summary.get('anomaly_frame_count', 0)} 个
• 异常率: {summary.get('anomaly_rate', 0)*100:.1f}%

🎯 评估结果:
"""
        
        # 根据一致性评分给出评估
        consistency_score = summary.get('consistency_score', 0)
        if consistency_score >= 8.0:
            result_text += "• 一致性状态: 优秀 ✅\n"
        elif consistency_score >= 6.0:
            result_text += "• 一致性状态: 良好 ✅\n"
        elif consistency_score >= 4.0:
            result_text += "• 一致性状态: 一般 ⚠️\n"
        else:
            result_text += "• 一致性状态: 较差 ❌\n"
        
        # 给出改进建议
        result_text += "\n💡 改进建议:\n"
        
        if summary.get('mean_frame_difference', 0) > 0.001:
            result_text += "• 帧间差异较大，建议检查传感器稳定性\n"
        
        if summary.get('unstable_sensors', 0) > 100:
            result_text += "• 不稳定传感器较多，建议进行传感器校准\n"
        
        if summary.get('anomaly_rate', 0) > 0.1:
            result_text += "• 异常帧率较高，建议检查数据采集系统\n"
        
        if summary.get('high_noise_sensors', 0) > 200:
            result_text += "• 高噪声传感器较多，建议改善信号质量\n"
        
        self.results_text.setText(result_text)
    
    def save_results(self):
        """保存分析结果"""
        if len(self.analyzer.frame_history) < 2:
            QMessageBox.warning(self, "警告", "没有分析结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存帧间一致性分析结果", "", "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if filename:
            try:
                # 执行分析
                results = self.analyzer.analyze_frame_consistency()
                
                # 准备保存数据
                save_data = {
                    'analysis_time': datetime.now().isoformat(),
                    'frame_count': len(self.analyzer.frame_history),
                    'summary_stats': results.get('summary_stats', {}),
                    'frame_differences': {
                        'mean_abs_diff': results.get('frame_differences', {}).get('mean_abs_diff', 0),
                        'max_abs_diff': results.get('frame_differences', {}).get('max_abs_diff', 0),
                        'mean_rel_diff': results.get('frame_differences', {}).get('mean_rel_diff', 0)
                    },
                    'stability_metrics': {
                        'mean_stability': results.get('stability_metrics', {}).get('mean_stability', 0),
                        'unstable_sensors': results.get('stability_metrics', {}).get('unstable_sensors', 0)
                    },
                    'anomaly_info': {
                        'anomaly_count': len(results.get('anomaly_frames', [])),
                        'anomaly_rate': len(results.get('anomaly_frames', [])) / len(self.analyzer.frame_history)
                    }
                }
                
                # 保存到文件
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", f"分析结果已保存到: {filename}")
                self.log_message(f"分析结果已保存: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
                self.log_message(f"保存失败: {e}")
    
    def clear_data(self):
        """清空数据"""
        self.analyzer.frame_history.clear()
        self.frame_count_label.setText("已收集帧数: 0")
        self.consistency_score_label.setText("一致性评分: --")
        self.results_text.clear()
        self.save_results_btn.setEnabled(False)
        
        QMessageBox.information(self, "清空完成", "所有数据已清空")
        self.log_message("数据已清空")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 帧间一致性分析: {message}")
    
    def diagnose_data_collection(self):
        """诊断数据收集问题"""
        diagnosis_info = {
            'monitoring_active': self.is_monitoring,
            'parent_window': self.parent() is not None,
            'parent_has_method': hasattr(self.parent(), 'get_current_sensor_data') if self.parent() else False,
            'sensor_running': False,
            'data_handler_status': 'Unknown',
            'frame_history_size': len(self.analyzer.frame_history)
        }
        
        # 检查传感器运行状态
        if self.parent() and hasattr(self.parent(), 'is_running'):
            diagnosis_info['sensor_running'] = self.parent().is_running
        
        # 检查数据处理器状态
        if self.parent() and hasattr(self.parent(), 'get_data_handler_status'):
            try:
                status = self.parent().get_data_handler_status()
                diagnosis_info['data_handler_status'] = status
            except Exception as e:
                diagnosis_info['data_handler_status'] = f"Error: {e}"
        
        # 生成诊断报告
        report = f"""
=== 帧间一致性分析数据收集诊断报告 ===

📊 基本状态:
• 监测状态: {'✅ 活跃' if diagnosis_info['monitoring_active'] else '❌ 未激活'}
• 父窗口: {'✅ 已设置' if diagnosis_info['parent_window'] else '❌ 未设置'}
• 父窗口方法: {'✅ 可用' if diagnosis_info['parent_has_method'] else '❌ 不可用'}
• 传感器运行: {'✅ 运行中' if diagnosis_info['sensor_running'] else '❌ 未运行'}
• 历史帧数: {diagnosis_info['frame_history_size']}

🔧 数据处理器状态:
{diagnosis_info['data_handler_status']}

💡 建议解决方案:
"""
        
        if not diagnosis_info['monitoring_active']:
            report += "1. 点击'开始监测'按钮激活数据收集\n"
        
        if not diagnosis_info['parent_window']:
            report += "2. 检查组件是否正确添加到主界面\n"
        
        if not diagnosis_info['parent_has_method']:
            report += "3. 检查主界面是否实现了get_current_sensor_data方法\n"
        
        if not diagnosis_info['sensor_running']:
            report += "4. 请先启动传感器连接\n"
        
        if diagnosis_info['frame_history_size'] == 0:
            report += "5. 数据收集可能存在问题，请检查上述项目\n"
        
        return report
    
    def show_diagnosis(self):
        """显示诊断信息"""
        report = self.diagnose_data_collection()
        QMessageBox.information(self, "数据收集诊断", report)

    def show_usage_guide(self):
        """显示使用指南"""
        guide_text = """
=== 帧间一致性分析使用指南 ===

📋 使用步骤:
1. 确保传感器已连接并运行
2. 点击"开始监测"按钮开始收集数据
3. 在传感器上进行各种操作（按压、移动等）
4. 观察实时状态中的帧数增长
5. 点击"停止监测"结束收集
6. 点击"分析当前数据"查看分析结果

🔧 故障排除:
• 如果帧数一直为0，请点击"诊断问题"按钮
• 确保传感器已启动（主界面显示"已连接"）
• 检查日志信息了解详细错误

📊 分析指标:
• 帧间差异: 连续帧之间的数据变化
• 稳定性指标: 传感器响应的稳定性
• 异常检测: 检测异常的帧数据
• 噪声特性: 分析数据噪声特征
• 一致性评分: 综合评分（0-10分）

💡 使用建议:
• 建议收集至少50帧数据进行有效分析
• 在分析期间保持传感器稳定
• 可以多次收集数据进行比较
• 使用"清空数据"重新开始收集

⚠️ 注意事项:
• 传感器必须处于运行状态
• 数据收集会消耗系统资源
• 长时间监测建议定期停止和重新开始
"""
        QMessageBox.information(self, "使用指南", guide_text)


class FrameCorrectionSystem:
    """帧间校正系统"""
    
    def __init__(self):
        self.correction_enabled = False
        self.smoothing_factor = 0.7  # 平滑因子
        self.previous_frame = None
        self.correction_threshold = 0.001  # 校正阈值
        
    def enable_correction(self, enabled=True):
        """启用/禁用校正"""
        self.correction_enabled = enabled
    
    def set_smoothing_factor(self, factor):
        """设置平滑因子"""
        self.smoothing_factor = max(0.0, min(1.0, factor))
    
    def set_correction_threshold(self, threshold):
        """设置校正阈值"""
        self.correction_threshold = max(0.0, threshold)
    
    def correct_frame(self, current_frame):
        """校正当前帧"""
        if not self.correction_enabled or self.previous_frame is None:
            self.previous_frame = current_frame.copy()
            return current_frame
        
        # 计算帧间差异
        frame_diff = np.abs(current_frame - self.previous_frame)
        
        # 如果差异超过阈值，进行校正
        if np.mean(frame_diff) > self.correction_threshold:
            # 使用指数平滑
            corrected_frame = (self.smoothing_factor * self.previous_frame + 
                             (1 - self.smoothing_factor) * current_frame)
        else:
            corrected_frame = current_frame
        
        # 更新前一帧
        self.previous_frame = corrected_frame.copy()
        
        return corrected_frame
    
    def get_correction_stats(self):
        """获取校正统计信息"""
        return {
            'correction_enabled': self.correction_enabled,
            'smoothing_factor': self.smoothing_factor,
            'correction_threshold': self.correction_threshold
        }


# 使用示例
def main():
    """主函数示例"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建帧间一致性分析界面
    frame_widget = FrameConsistencyWidget()
    frame_widget.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 