"""
时间一致性分析模块
分析传感器在时间维度上的不一致性问题
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

class TemporalDriftAnalyzer:
    """时间漂移分析器"""
    
    def __init__(self):
        self.drift_data = {}  # 存储漂移数据
        self.analysis_results = {}
        
    def analyze_temporal_drift(self, time_series_data, time_stamps):
        """
        分析时间漂移
        
        Args:
            time_series_data: 时间序列数据，形状为 (time_points, height, width)
            time_stamps: 时间戳列表
            
        Returns:
            漂移分析结果
        """
        results = {}
        
        # 1. 计算每个传感器点的漂移率
        drift_rates = self._calculate_drift_rates(time_series_data, time_stamps)
        
        # 2. 分析漂移模式
        drift_patterns = self._analyze_drift_patterns(time_series_data, time_stamps)
        
        # 3. 检测异常漂移点
        anomaly_points = self._detect_drift_anomalies(time_series_data, time_stamps)
        
        # 4. 预测未来漂移趋势
        drift_prediction = self._predict_drift_trend(time_series_data, time_stamps)
        
        results = {
            'drift_rates': drift_rates,
            'drift_patterns': drift_patterns,
            'anomaly_points': anomaly_points,
            'drift_prediction': drift_prediction,
            'summary_stats': self._calculate_drift_summary(drift_rates)
        }
        
        return results
    
    def _calculate_drift_rates(self, time_series_data, time_stamps):
        """计算每个传感器点的漂移率"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        drift_rates = np.zeros((height, width))
        
        # 将时间戳转换为数值（秒）
        time_numeric = np.array([(ts - time_stamps[0]).total_seconds() for ts in time_stamps])
        
        for i in range(height):
            for j in range(width):
                # 获取该传感器点的时间序列
                sensor_data = time_series_data[:, i, j]
                
                # 使用线性回归计算漂移率
                if len(sensor_data) > 1:
                    slope, intercept, r_value, p_value, std_err = linregress(time_numeric, sensor_data)
                    drift_rates[i, j] = slope  # 漂移率（单位/秒）
        
        return drift_rates
    
    def _analyze_drift_patterns(self, time_series_data, time_stamps):
        """分析漂移模式"""
        patterns = {}
        
        # 1. 线性漂移检测
        patterns['linear_drift'] = self._detect_linear_drift(time_series_data, time_stamps)
        
        # 2. 周期性漂移检测
        patterns['periodic_drift'] = self._detect_periodic_drift(time_series_data, time_stamps)
        
        # 3. 突变点检测
        patterns['change_points'] = self._detect_change_points(time_series_data, time_stamps)
        
        return patterns
    
    def _detect_linear_drift(self, time_series_data, time_stamps):
        """检测线性漂移"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        linear_drift_mask = np.zeros((height, width), dtype=bool)
        
        time_numeric = np.array([(ts - time_stamps[0]).total_seconds() for ts in time_stamps])
        
        for i in range(height):
            for j in range(width):
                sensor_data = time_series_data[:, i, j]
                
                if len(sensor_data) > 2:
                    slope, intercept, r_value, p_value, std_err = linregress(time_numeric, sensor_data)
                    
                    # 判断是否为显著线性漂移
                    if abs(slope) > 1e-6 and p_value < 0.05:  # 可调整阈值
                        linear_drift_mask[i, j] = True
        
        return linear_drift_mask
    
    def _detect_periodic_drift(self, time_series_data, time_stamps):
        """检测周期性漂移"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        periodic_drift_mask = np.zeros((height, width), dtype=bool)
        
        for i in range(height):
            for j in range(width):
                sensor_data = time_series_data[:, i, j]
                
                if len(sensor_data) > 10:
                    # 使用FFT检测周期性
                    fft_result = np.fft.fft(sensor_data)
                    power_spectrum = np.abs(fft_result)**2
                    
                    # 寻找主要频率成分
                    main_freq_idx = np.argmax(power_spectrum[1:len(power_spectrum)//2]) + 1
                    main_power = power_spectrum[main_freq_idx]
                    total_power = np.sum(power_spectrum[1:len(power_spectrum)//2])
                    
                    # 如果主要频率成分占总功率的比例超过阈值，认为存在周期性
                    if main_power / total_power > 0.3:  # 可调整阈值
                        periodic_drift_mask[i, j] = True
        
        return periodic_drift_mask
    
    def _detect_change_points(self, time_series_data, time_stamps):
        """检测突变点"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        change_points = []
        
        for i in range(height):
            for j in range(width):
                sensor_data = time_series_data[:, i, j]
                
                if len(sensor_data) > 5:
                    # 使用滑动窗口检测突变
                    window_size = min(5, len(sensor_data) // 4)
                    
                    for k in range(window_size, len(sensor_data) - window_size):
                        before_mean = np.mean(sensor_data[k-window_size:k])
                        after_mean = np.mean(sensor_data[k:k+window_size])
                        
                        # 如果前后均值差异超过阈值，认为是突变点
                        if abs(after_mean - before_mean) > np.std(sensor_data) * 2:
                            change_points.append({
                                'position': (i, j),
                                'time_index': k,
                                'time_stamp': time_stamps[k],
                                'magnitude': abs(after_mean - before_mean)
                            })
        
        return change_points
    
    def _detect_drift_anomalies(self, time_series_data, time_stamps):
        """检测异常漂移点"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        anomaly_points = []
        
        for i in range(height):
            for j in range(width):
                sensor_data = time_series_data[:, i, j]
                
                if len(sensor_data) > 10:
                    # 计算统计异常值
                    mean_val = np.mean(sensor_data)
                    std_val = np.std(sensor_data)
                    
                    # 检测3σ异常值
                    anomaly_indices = np.where(np.abs(sensor_data - mean_val) > 3 * std_val)[0]
                    
                    for idx in anomaly_indices:
                        anomaly_points.append({
                            'position': (i, j),
                            'time_index': idx,
                            'time_stamp': time_stamps[idx],
                            'value': sensor_data[idx],
                            'deviation': (sensor_data[idx] - mean_val) / std_val
                        })
        
        return anomaly_points
    
    def _predict_drift_trend(self, time_series_data, time_stamps):
        """预测漂移趋势"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        predictions = {}
        
        time_numeric = np.array([(ts - time_stamps[0]).total_seconds() for ts in time_stamps])
        
        for i in range(height):
            for j in range(width):
                sensor_data = time_series_data[:, i, j]
                
                if len(sensor_data) > 5:
                    # 线性回归预测
                    slope, intercept, r_value, p_value, std_err = linregress(time_numeric, sensor_data)
                    
                    # 预测未来1小时的值
                    future_time = time_numeric[-1] + 3600  # 1小时后
                    predicted_value = slope * future_time + intercept
                    
                    predictions[(i, j)] = {
                        'current_slope': slope,
                        'predicted_value_1h': predicted_value,
                        'confidence': r_value**2,
                        'prediction_interval': (predicted_value - 2*std_err, predicted_value + 2*std_err)
                    }
        
        return predictions
    
    def _calculate_drift_summary(self, drift_rates):
        """计算漂移统计摘要"""
        valid_rates = drift_rates[drift_rates != 0]
        
        if len(valid_rates) == 0:
            return {}
        
        summary = {
            'mean_drift_rate': np.mean(valid_rates),
            'std_drift_rate': np.std(valid_rates),
            'max_drift_rate': np.max(valid_rates),
            'min_drift_rate': np.min(valid_rates),
            'drift_range': np.max(valid_rates) - np.min(valid_rates),
            'positive_drift_count': np.sum(valid_rates > 0),
            'negative_drift_count': np.sum(valid_rates < 0),
            'total_sensors': len(valid_rates)
        }
        
        return summary


class ResponseTimeAnalyzer:
    """响应时间分析器"""
    
    def __init__(self):
        self.response_data = {}
        
    def analyze_response_time(self, time_series_data, time_stamps, pressure_events):
        """
        分析响应时间
        
        Args:
            time_series_data: 时间序列数据
            time_stamps: 时间戳列表
            pressure_events: 压力事件列表，每个事件包含开始时间、结束时间、压力值
            
        Returns:
            响应时间分析结果
        """
        results = {}
        
        # 1. 计算上升时间
        rise_times = self._calculate_rise_times(time_series_data, time_stamps, pressure_events)
        
        # 2. 计算下降时间
        fall_times = self._calculate_fall_times(time_series_data, time_stamps, pressure_events)
        
        # 3. 分析响应一致性
        response_consistency = self._analyze_response_consistency(rise_times, fall_times)
        
        # 4. 检测响应异常
        response_anomalies = self._detect_response_anomalies(time_series_data, time_stamps, pressure_events)
        
        results = {
            'rise_times': rise_times,
            'fall_times': fall_times,
            'response_consistency': response_consistency,
            'response_anomalies': response_anomalies,
            'summary_stats': self._calculate_response_summary(rise_times, fall_times)
        }
        
        return results
    
    def _calculate_rise_times(self, time_series_data, time_stamps, pressure_events):
        """计算上升时间"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        rise_times = {}
        
        for event_idx, event in enumerate(pressure_events):
            # 找到事件开始和结束的时间索引
            start_idx = self._find_time_index(time_stamps, event['start_time'])
            end_idx = self._find_time_index(time_stamps, event['end_time'])
            
            if start_idx is None or end_idx is None:
                continue
            
            event_rise_times = np.zeros((height, width))
            
            for i in range(height):
                for j in range(width):
                    sensor_data = time_series_data[start_idx:end_idx+1, i, j]
                    
                    if len(sensor_data) > 1:
                        # 计算从10%到90%的上升时间
                        rise_time = self._calculate_rise_time_10_90(sensor_data, time_stamps[start_idx:end_idx+1])
                        event_rise_times[i, j] = rise_time
            
            rise_times[f'event_{event_idx}'] = event_rise_times
        
        return rise_times
    
    def _calculate_fall_times(self, time_series_data, time_stamps, pressure_events):
        """计算下降时间"""
        height, width = time_series_data.shape[1], time_series_data.shape[2]
        fall_times = {}
        
        for event_idx, event in enumerate(pressure_events):
            # 找到事件结束后的恢复期
            end_idx = self._find_time_index(time_stamps, event['end_time'])
            recovery_end_idx = min(end_idx + 50, len(time_stamps) - 1)  # 假设50个采样点的恢复期
            
            if end_idx is None:
                continue
            
            event_fall_times = np.zeros((height, width))
            
            for i in range(height):
                for j in range(width):
                    sensor_data = time_series_data[end_idx:recovery_end_idx+1, i, j]
                    
                    if len(sensor_data) > 1:
                        # 计算从90%到10%的下降时间
                        fall_time = self._calculate_fall_time_90_10(sensor_data, time_stamps[end_idx:recovery_end_idx+1])
                        event_fall_times[i, j] = fall_time
            
            fall_times[f'event_{event_idx}'] = event_fall_times
        
        return fall_times
    
    def _calculate_rise_time_10_90(self, sensor_data, time_stamps):
        """计算10%-90%上升时间"""
        if len(sensor_data) < 2:
            return 0.0
        
        # 找到10%和90%的值
        min_val = np.min(sensor_data)
        max_val = np.max(sensor_data)
        range_val = max_val - min_val
        
        if range_val == 0:
            return 0.0
        
        threshold_10 = min_val + 0.1 * range_val
        threshold_90 = min_val + 0.9 * range_val
        
        # 找到10%和90%对应的时间点
        time_10 = None
        time_90 = None
        
        for k, value in enumerate(sensor_data):
            if time_10 is None and value >= threshold_10:
                time_10 = time_stamps[k]
            if time_90 is None and value >= threshold_90:
                time_90 = time_stamps[k]
                break
        
        if time_10 is not None and time_90 is not None:
            return (time_90 - time_10).total_seconds()
        
        return 0.0
    
    def _calculate_fall_time_90_10(self, sensor_data, time_stamps):
        """计算90%-10%下降时间"""
        if len(sensor_data) < 2:
            return 0.0
        
        # 找到90%和10%的值
        min_val = np.min(sensor_data)
        max_val = np.max(sensor_data)
        range_val = max_val - min_val
        
        if range_val == 0:
            return 0.0
        
        threshold_90 = min_val + 0.9 * range_val
        threshold_10 = min_val + 0.1 * range_val
        
        # 找到90%和10%对应的时间点
        time_90 = None
        time_10 = None
        
        for k, value in enumerate(sensor_data):
            if time_90 is None and value <= threshold_90:
                time_90 = time_stamps[k]
            if time_10 is None and value <= threshold_10:
                time_10 = time_stamps[k]
                break
        
        if time_90 is not None and time_10 is not None:
            return (time_10 - time_90).total_seconds()
        
        return 0.0
    
    def _find_time_index(self, time_stamps, target_time):
        """找到最接近目标时间的时间索引"""
        if not time_stamps:
            return None
        
        # 找到最接近的时间戳
        time_diffs = [abs((ts - target_time).total_seconds()) for ts in time_stamps]
        min_idx = np.argmin(time_diffs)
        
        # 如果时间差太大，返回None
        if time_diffs[min_idx] > 1.0:  # 1秒阈值
            return None
        
        return min_idx
    
    def _analyze_response_consistency(self, rise_times, fall_times):
        """分析响应一致性"""
        consistency = {}
        
        # 计算所有事件的响应时间统计
        all_rise_times = []
        all_fall_times = []
        
        for event_key in rise_times:
            rise_data = rise_times[event_key]
            fall_data = fall_times[event_key]
            
            valid_rise = rise_data[rise_data > 0]
            valid_fall = fall_data[fall_data > 0]
            
            all_rise_times.extend(valid_rise.flatten())
            all_fall_times.extend(valid_fall.flatten())
        
        if all_rise_times:
            consistency['rise_time_stats'] = {
                'mean': np.mean(all_rise_times),
                'std': np.std(all_rise_times),
                'cv': np.std(all_rise_times) / np.mean(all_rise_times) if np.mean(all_rise_times) > 0 else 0
            }
        
        if all_fall_times:
            consistency['fall_time_stats'] = {
                'mean': np.mean(all_fall_times),
                'std': np.std(all_fall_times),
                'cv': np.std(all_fall_times) / np.mean(all_fall_times) if np.mean(all_fall_times) > 0 else 0
            }
        
        return consistency
    
    def _detect_response_anomalies(self, time_series_data, time_stamps, pressure_events):
        """检测响应异常"""
        anomalies = []
        
        for event_idx, event in enumerate(pressure_events):
            start_idx = self._find_time_index(time_stamps, event['start_time'])
            end_idx = self._find_time_index(time_stamps, event['end_time'])
            
            if start_idx is None or end_idx is None:
                continue
            
            # 检测响应延迟
            for i in range(time_series_data.shape[1]):
                for j in range(time_series_data.shape[2]):
                    sensor_data = time_series_data[start_idx:end_idx+1, i, j]
                    
                    if len(sensor_data) > 5:
                        # 检测响应延迟
                        response_delay = self._detect_response_delay(sensor_data, time_stamps[start_idx:end_idx+1])
                        
                        if response_delay > 0.1:  # 100ms阈值
                            anomalies.append({
                                'type': 'response_delay',
                                'position': (i, j),
                                'event': event_idx,
                                'delay': response_delay,
                                'severity': 'high' if response_delay > 0.5 else 'medium'
                            })
        
        return anomalies
    
    def _detect_response_delay(self, sensor_data, time_stamps):
        """检测响应延迟"""
        if len(sensor_data) < 2:
            return 0.0
        
        # 计算基线噪声
        baseline = np.mean(sensor_data[:min(5, len(sensor_data)//4)])
        noise_std = np.std(sensor_data[:min(5, len(sensor_data)//4)])
        
        # 寻找响应开始点（超过基线3σ）
        threshold = baseline + 3 * noise_std
        
        for k, value in enumerate(sensor_data):
            if value > threshold:
                return (time_stamps[k] - time_stamps[0]).total_seconds()
        
        return 0.0
    
    def _calculate_response_summary(self, rise_times, fall_times):
        """计算响应时间统计摘要"""
        summary = {}
        
        # 收集所有有效的响应时间
        all_rise = []
        all_fall = []
        
        for event_key in rise_times:
            rise_data = rise_times[event_key]
            fall_data = fall_times[event_key]
            
            valid_rise = rise_data[rise_data > 0]
            valid_fall = fall_data[fall_data > 0]
            
            all_rise.extend(valid_rise.flatten())
            all_fall.extend(valid_fall.flatten())
        
        if all_rise:
            summary['rise_time_summary'] = {
                'count': len(all_rise),
                'mean': np.mean(all_rise),
                'std': np.std(all_rise),
                'min': np.min(all_rise),
                'max': np.max(all_rise),
                'cv': np.std(all_rise) / np.mean(all_rise) if np.mean(all_rise) > 0 else 0
            }
        
        if all_fall:
            summary['fall_time_summary'] = {
                'count': len(all_fall),
                'mean': np.mean(all_fall),
                'std': np.std(all_fall),
                'min': np.min(all_fall),
                'max': np.max(all_fall),
                'cv': np.std(all_fall) / np.mean(all_fall) if np.mean(all_fall) > 0 else 0
            }
        
        return summary


class FatigueAnalyzer:
    """疲劳效应分析器"""
    
    def __init__(self):
        self.fatigue_data = {}
        
    def analyze_fatigue_effects(self, repeated_test_data, test_cycles):
        """
        分析疲劳效应
        
        Args:
            repeated_test_data: 重复测试数据，形状为 (cycles, time_points, height, width)
            test_cycles: 测试周期信息
            
        Returns:
            疲劳效应分析结果
        """
        results = {}
        
        # 1. 分析敏感度衰减
        sensitivity_decay = self._analyze_sensitivity_decay(repeated_test_data, test_cycles)
        
        # 2. 分析响应稳定性变化
        stability_changes = self._analyze_stability_changes(repeated_test_data, test_cycles)
        
        # 3. 检测疲劳阈值
        fatigue_thresholds = self._detect_fatigue_thresholds(repeated_test_data, test_cycles)
        
        # 4. 预测疲劳寿命
        fatigue_life_prediction = self._predict_fatigue_life(repeated_test_data, test_cycles)
        
        results = {
            'sensitivity_decay': sensitivity_decay,
            'stability_changes': stability_changes,
            'fatigue_thresholds': fatigue_thresholds,
            'fatigue_life_prediction': fatigue_life_prediction,
            'summary_stats': self._calculate_fatigue_summary(sensitivity_decay, stability_changes)
        }
        
        return results
    
    def _analyze_sensitivity_decay(self, repeated_test_data, test_cycles):
        """分析敏感度衰减"""
        num_cycles, time_points, height, width = repeated_test_data.shape
        sensitivity_decay = {}
        
        for i in range(height):
            for j in range(width):
                # 计算每个周期的峰值响应
                peak_responses = []
                
                for cycle in range(num_cycles):
                    cycle_data = repeated_test_data[cycle, :, i, j]
                    peak_response = np.max(cycle_data)
                    peak_responses.append(peak_response)
                
                # 分析敏感度衰减趋势
                if len(peak_responses) > 1:
                    # 计算衰减率
                    initial_sensitivity = peak_responses[0]
                    final_sensitivity = peak_responses[-1]
                    decay_rate = (initial_sensitivity - final_sensitivity) / initial_sensitivity
                    
                    # 拟合衰减曲线
                    cycles = np.arange(len(peak_responses))
                    if len(cycles) > 2:
                        slope, intercept, r_value, p_value, std_err = linregress(cycles, peak_responses)
                        
                        sensitivity_decay[(i, j)] = {
                            'initial_sensitivity': initial_sensitivity,
                            'final_sensitivity': final_sensitivity,
                            'decay_rate': decay_rate,
                            'decay_slope': slope,
                            'decay_confidence': r_value**2,
                            'peak_responses': peak_responses
                        }
        
        return sensitivity_decay
    
    def _analyze_stability_changes(self, repeated_test_data, test_cycles):
        """分析响应稳定性变化"""
        num_cycles, time_points, height, width = repeated_test_data.shape
        stability_changes = {}
        
        for i in range(height):
            for j in range(width):
                # 计算每个周期的响应稳定性指标
                stability_metrics = []
                
                for cycle in range(num_cycles):
                    cycle_data = repeated_test_data[cycle, :, i, j]
                    
                    # 计算稳定性指标（标准差/均值）
                    mean_response = np.mean(cycle_data)
                    std_response = np.std(cycle_data)
                    
                    if mean_response > 0:
                        stability_coefficient = std_response / mean_response
                        stability_metrics.append(stability_coefficient)
                
                # 分析稳定性变化趋势
                if len(stability_metrics) > 1:
                    cycles = np.arange(len(stability_metrics))
                    slope, intercept, r_value, p_value, std_err = linregress(cycles, stability_metrics)
                    
                    stability_changes[(i, j)] = {
                        'initial_stability': stability_metrics[0],
                        'final_stability': stability_metrics[-1],
                        'stability_trend': slope,
                        'stability_confidence': r_value**2,
                        'stability_metrics': stability_metrics
                    }
        
        return stability_changes
    
    def _detect_fatigue_thresholds(self, repeated_test_data, test_cycles):
        """检测疲劳阈值"""
        num_cycles, time_points, height, width = repeated_test_data.shape
        fatigue_thresholds = {}
        
        for i in range(height):
            for j in range(width):
                # 计算每个周期的峰值响应
                peak_responses = []
                
                for cycle in range(num_cycles):
                    cycle_data = repeated_test_data[cycle, :, i, j]
                    peak_response = np.max(cycle_data)
                    peak_responses.append(peak_response)
                
                # 检测疲劳阈值（响应下降超过10%的周期）
                if len(peak_responses) > 1:
                    initial_response = peak_responses[0]
                    fatigue_threshold_cycle = None
                    
                    for cycle, response in enumerate(peak_responses):
                        if response < initial_response * 0.9:  # 10%下降阈值
                            fatigue_threshold_cycle = cycle
                            break
                    
                    if fatigue_threshold_cycle is not None:
                        fatigue_thresholds[(i, j)] = {
                            'threshold_cycle': fatigue_threshold_cycle,
                            'threshold_response': peak_responses[fatigue_threshold_cycle],
                            'initial_response': initial_response,
                            'response_decline': (initial_response - peak_responses[fatigue_threshold_cycle]) / initial_response
                        }
        
        return fatigue_thresholds
    
    def _predict_fatigue_life(self, repeated_test_data, test_cycles):
        """预测疲劳寿命"""
        num_cycles, time_points, height, width = repeated_test_data.shape
        fatigue_life_prediction = {}
        
        for i in range(height):
            for j in range(width):
                # 计算每个周期的峰值响应
                peak_responses = []
                
                for cycle in range(num_cycles):
                    cycle_data = repeated_test_data[cycle, :, i, j]
                    peak_response = np.max(cycle_data)
                    peak_responses.append(peak_response)
                
                # 预测疲劳寿命
                if len(peak_responses) > 2:
                    cycles = np.arange(len(peak_responses))
                    
                    # 拟合衰减曲线
                    slope, intercept, r_value, p_value, std_err = linregress(cycles, peak_responses)
                    
                    if slope < 0:  # 只有在衰减时才预测
                        initial_response = peak_responses[0]
                        failure_threshold = initial_response * 0.5  # 50%下降作为失效标准
                        
                        # 预测达到失效阈值的周期数
                        if slope != 0:
                            failure_cycle = (failure_threshold - intercept) / slope
                            failure_cycle = max(0, failure_cycle)
                            
                            fatigue_life_prediction[(i, j)] = {
                                'predicted_life_cycles': failure_cycle,
                                'confidence': r_value**2,
                                'decay_rate': abs(slope),
                                'current_cycles': len(peak_responses)
                            }
        
        return fatigue_life_prediction
    
    def _calculate_fatigue_summary(self, sensitivity_decay, stability_changes):
        """计算疲劳效应统计摘要"""
        summary = {}
        
        # 敏感度衰减统计
        if sensitivity_decay:
            decay_rates = [data['decay_rate'] for data in sensitivity_decay.values()]
            summary['sensitivity_decay_summary'] = {
                'affected_sensors': len(decay_rates),
                'mean_decay_rate': np.mean(decay_rates),
                'max_decay_rate': np.max(decay_rates),
                'severe_decay_count': len([r for r in decay_rates if r > 0.2])
            }
        
        # 稳定性变化统计
        if stability_changes:
            stability_trends = [data['stability_trend'] for data in stability_changes.values()]
            summary['stability_changes_summary'] = {
                'affected_sensors': len(stability_trends),
                'mean_stability_trend': np.mean(stability_trends),
                'worsening_stability_count': len([t for t in stability_trends if t > 0])
            }
        
        return summary


class TemporalConsistencyWidget(QWidget):
    """时间一致性分析界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drift_analyzer = TemporalDriftAnalyzer()
        self.response_analyzer = ResponseTimeAnalyzer()
        self.fatigue_analyzer = FatigueAnalyzer()
        
        self.time_series_data = None
        self.time_stamps = []
        self.pressure_events = []
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 时间漂移分析标签页
        self.drift_tab = self.create_drift_tab()
        self.tab_widget.addTab(self.drift_tab, "时间漂移分析")
        
        # 响应时间分析标签页
        self.response_tab = self.create_response_tab()
        self.tab_widget.addTab(self.response_tab, "响应时间分析")
        
        # 疲劳效应分析标签页
        self.fatigue_tab = self.create_fatigue_tab()
        self.tab_widget.addTab(self.fatigue_tab, "疲劳效应分析")
        
        layout.addWidget(self.tab_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_analysis_btn = QPushButton("开始时间分析")
        self.start_analysis_btn.clicked.connect(self.start_temporal_analysis)
        
        self.save_results_btn = QPushButton("保存分析结果")
        self.save_results_btn.clicked.connect(self.save_analysis_results)
        self.save_results_btn.setEnabled(False)
        
        self.clear_data_btn = QPushButton("清空数据")
        self.clear_data_btn.clicked.connect(self.clear_data)
        
        button_layout.addWidget(self.start_analysis_btn)
        button_layout.addWidget(self.save_results_btn)
        button_layout.addWidget(self.clear_data_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_drift_tab(self):
        """创建时间漂移分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 控制组
        control_group = QGroupBox("漂移分析控制")
        control_layout = QHBoxLayout()
        
        self.drift_duration_spin = QSpinBox()
        self.drift_duration_spin.setRange(1, 24)
        self.drift_duration_spin.setValue(2)
        self.drift_duration_spin.setSuffix(" 小时")
        
        self.start_drift_analysis_btn = QPushButton("开始漂移监测")
        self.start_drift_analysis_btn.clicked.connect(self.start_drift_monitoring)
        
        self.stop_drift_analysis_btn = QPushButton("停止监测")
        self.stop_drift_analysis_btn.clicked.connect(self.stop_drift_monitoring)
        self.stop_drift_analysis_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("监测时长:"))
        control_layout.addWidget(self.drift_duration_spin)
        control_layout.addWidget(self.start_drift_analysis_btn)
        control_layout.addWidget(self.stop_drift_analysis_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 结果显示
        results_group = QGroupBox("漂移分析结果")
        results_layout = QVBoxLayout()
        
        self.drift_results_text = QTextEdit()
        self.drift_results_text.setReadOnly(True)
        
        results_layout.addWidget(self.drift_results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_response_tab(self):
        """创建响应时间分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 控制组
        control_group = QGroupBox("响应时间分析控制")
        control_layout = QHBoxLayout()
        
        self.response_test_count_spin = QSpinBox()
        self.response_test_count_spin.setRange(1, 50)
        self.response_test_count_spin.setValue(10)
        self.response_test_count_spin.setSuffix(" 次")
        
        self.start_response_test_btn = QPushButton("开始响应测试")
        self.start_response_test_btn.clicked.connect(self.start_response_test)
        
        self.stop_response_test_btn = QPushButton("停止测试")
        self.stop_response_test_btn.clicked.connect(self.stop_response_test)
        self.stop_response_test_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("测试次数:"))
        control_layout.addWidget(self.response_test_count_spin)
        control_layout.addWidget(self.start_response_test_btn)
        control_layout.addWidget(self.stop_response_test_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 结果显示
        results_group = QGroupBox("响应时间分析结果")
        results_layout = QVBoxLayout()
        
        self.response_results_text = QTextEdit()
        self.response_results_text.setReadOnly(True)
        
        results_layout.addWidget(self.response_results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_fatigue_tab(self):
        """创建疲劳效应分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 控制组
        control_group = QGroupBox("疲劳效应分析控制")
        control_layout = QHBoxLayout()
        
        self.fatigue_cycles_spin = QSpinBox()
        self.fatigue_cycles_spin.setRange(10, 1000)
        self.fatigue_cycles_spin.setValue(100)
        self.fatigue_cycles_spin.setSuffix(" 次")
        
        self.start_fatigue_test_btn = QPushButton("开始疲劳测试")
        self.start_fatigue_test_btn.clicked.connect(self.start_fatigue_test)
        
        self.stop_fatigue_test_btn = QPushButton("停止测试")
        self.stop_fatigue_test_btn.clicked.connect(self.stop_fatigue_test)
        self.stop_fatigue_test_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("测试周期:"))
        control_layout.addWidget(self.fatigue_cycles_spin)
        control_layout.addWidget(self.start_fatigue_test_btn)
        control_layout.addWidget(self.stop_fatigue_test_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 结果显示
        results_group = QGroupBox("疲劳效应分析结果")
        results_layout = QVBoxLayout()
        
        self.fatigue_results_text = QTextEdit()
        self.fatigue_results_text.setReadOnly(True)
        
        results_layout.addWidget(self.fatigue_results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab
    
    def start_temporal_analysis(self):
        """开始时间一致性分析"""
        if self.time_series_data is None:
            QMessageBox.warning(self, "警告", "没有时间序列数据")
            return
        
        try:
            # 执行时间漂移分析
            drift_results = self.drift_analyzer.analyze_temporal_drift(
                self.time_series_data, self.time_stamps
            )
            
            # 执行响应时间分析
            response_results = self.response_analyzer.analyze_response_time(
                self.time_series_data, self.time_stamps, self.pressure_events
            )
            
            # 显示分析结果
            self.display_drift_results(drift_results)
            self.display_response_results(response_results)
            
            self.save_results_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {e}")
    
    def display_drift_results(self, results):
        """显示漂移分析结果"""
        if not results:
            return
        
        summary = results.get('summary_stats', {})
        
        result_text = f"""
=== 时间漂移分析结果 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 漂移统计:
"""
        
        if summary:
            result_text += f"""
• 平均漂移率: {summary.get('mean_drift_rate', 0):.6f} 单位/秒
• 漂移率标准差: {summary.get('std_drift_rate', 0):.6f}
• 最大漂移率: {summary.get('max_drift_rate', 0):.6f}
• 最小漂移率: {summary.get('min_drift_rate', 0):.6f}
• 漂移范围: {summary.get('drift_range', 0):.6f}
• 正漂移传感器: {summary.get('positive_drift_count', 0)}
• 负漂移传感器: {summary.get('negative_drift_count', 0)}
• 总传感器数: {summary.get('total_sensors', 0)}
"""
        
        # 添加漂移模式信息
        patterns = results.get('drift_patterns', {})
        if patterns.get('linear_drift') is not None:
            linear_count = np.sum(patterns['linear_drift'])
            result_text += f"\n• 线性漂移传感器: {linear_count}"
        
        if patterns.get('periodic_drift') is not None:
            periodic_count = np.sum(patterns['periodic_drift'])
            result_text += f"\n• 周期性漂移传感器: {periodic_count}"
        
        # 添加异常点信息
        anomalies = results.get('anomaly_points', [])
        if anomalies:
            result_text += f"\n• 检测到异常点: {len(anomalies)} 个"
        
        self.drift_results_text.setText(result_text)
    
    def display_response_results(self, results):
        """显示响应时间分析结果"""
        if not results:
            return
        
        summary = results.get('summary_stats', {})
        
        result_text = f"""
=== 响应时间分析结果 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 响应时间统计:
"""
        
        rise_summary = summary.get('rise_time_summary', {})
        fall_summary = summary.get('fall_time_summary', {})
        
        if rise_summary:
            result_text += f"""
上升时间统计:
• 测试次数: {rise_summary.get('count', 0)}
• 平均上升时间: {rise_summary.get('mean', 0):.3f} 秒
• 上升时间标准差: {rise_summary.get('std', 0):.3f} 秒
• 上升时间范围: {rise_summary.get('min', 0):.3f} - {rise_summary.get('max', 0):.3f} 秒
• 上升时间变异系数: {rise_summary.get('cv', 0)*100:.1f}%
"""
        
        if fall_summary:
            result_text += f"""
下降时间统计:
• 测试次数: {fall_summary.get('count', 0)}
• 平均下降时间: {fall_summary.get('mean', 0):.3f} 秒
• 下降时间标准差: {fall_summary.get('std', 0):.3f} 秒
• 下降时间范围: {fall_summary.get('min', 0):.3f} - {fall_summary.get('max', 0):.3f} 秒
• 下降时间变异系数: {fall_summary.get('cv', 0)*100:.1f}%
"""
        
        # 添加响应一致性信息
        consistency = results.get('response_consistency', {})
        if consistency:
            result_text += f"\n响应一致性评估:\n"
            
            rise_stats = consistency.get('rise_time_stats', {})
            if rise_stats:
                result_text += f"• 上升时间一致性: {rise_stats.get('cv', 0)*100:.1f}%\n"
            
            fall_stats = consistency.get('fall_time_stats', {})
            if fall_stats:
                result_text += f"• 下降时间一致性: {fall_stats.get('cv', 0)*100:.1f}%\n"
        
        # 添加异常信息
        anomalies = results.get('response_anomalies', [])
        if anomalies:
            result_text += f"\n• 检测到响应异常: {len(anomalies)} 个"
        
        self.response_results_text.setText(result_text)
    
    def display_fatigue_results(self, results):
        """显示疲劳效应分析结果"""
        if not results:
            return
        
        summary = results.get('summary_stats', {})
        
        result_text = f"""
=== 疲劳效应分析结果 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 疲劳效应统计:
"""
        
        sensitivity_summary = summary.get('sensitivity_decay_summary', {})
        stability_summary = summary.get('stability_changes_summary', {})
        
        if sensitivity_summary:
            result_text += f"""
敏感度衰减统计:
• 受影响传感器: {sensitivity_summary.get('affected_sensors', 0)}
• 平均衰减率: {sensitivity_summary.get('mean_decay_rate', 0)*100:.1f}%
• 最大衰减率: {sensitivity_summary.get('max_decay_rate', 0)*100:.1f}%
• 严重衰减传感器: {sensitivity_summary.get('severe_decay_count', 0)}
"""
        
        if stability_summary:
            result_text += f"""
稳定性变化统计:
• 受影响传感器: {stability_summary.get('affected_sensors', 0)}
• 平均稳定性趋势: {stability_summary.get('mean_stability_trend', 0):.4f}
• 稳定性恶化传感器: {stability_summary.get('worsening_stability_count', 0)}
"""
        
        self.fatigue_results_text.setText(result_text)
    
    def start_drift_monitoring(self):
        """开始时间漂移监测"""
        duration_hours = self.drift_duration_spin.value()
        self.start_drift_analysis_btn.setEnabled(False)
        self.stop_drift_analysis_btn.setEnabled(True)
        
        # 初始化数据收集
        self.time_series_data = []
        self.time_stamps = []
        
        # 启动定时器收集数据
        self.drift_timer = QTimer()
        self.drift_timer.timeout.connect(self.collect_drift_data)
        self.drift_timer.start(1000)  # 每秒收集一次数据
        
        # 设置停止时间
        self.drift_end_time = datetime.now() + timedelta(hours=duration_hours)
        
        self.drift_results_text.setText(f"开始时间漂移监测...\n监测时长: {duration_hours} 小时\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop_drift_monitoring(self):
        """停止时间漂移监测"""
        if hasattr(self, 'drift_timer'):
            self.drift_timer.stop()
        
        self.start_drift_analysis_btn.setEnabled(True)
        self.stop_drift_analysis_btn.setEnabled(False)
        
        # 执行漂移分析
        if self.time_series_data and len(self.time_series_data) > 10:
            time_series_array = np.array(self.time_series_data)
            drift_results = self.drift_analyzer.analyze_temporal_drift(time_series_array, self.time_stamps)
            self.display_drift_results(drift_results)
        else:
            self.drift_results_text.setText("数据不足，无法进行漂移分析")
    
    def collect_drift_data(self):
        """收集漂移数据"""
        # 检查是否到达停止时间
        if datetime.now() >= self.drift_end_time:
            self.stop_drift_monitoring()
            return
        
        # 获取当前传感器数据（这里需要从主界面获取）
        if hasattr(self.parent(), 'get_current_sensor_data'):
            current_data = self.parent().get_current_sensor_data()
            if current_data is not None:
                self.time_series_data.append(current_data.copy())
                self.time_stamps.append(datetime.now())
        
        # 更新状态
        elapsed_time = datetime.now() - (self.drift_end_time - timedelta(hours=self.drift_duration_spin.value()))
        remaining_time = self.drift_end_time - datetime.now()
        
        status_text = f"监测进行中...\n已收集数据: {len(self.time_series_data)} 个\n已用时间: {elapsed_time}\n剩余时间: {remaining_time}"
        self.drift_results_text.setText(status_text)
    
    def start_response_test(self):
        """开始响应时间测试"""
        test_count = self.response_test_count_spin.value()
        self.start_response_test_btn.setEnabled(False)
        self.stop_response_test_btn.setEnabled(True)
        
        # 初始化测试数据
        self.pressure_events = []
        self.response_test_data = []
        self.response_test_timestamps = []
        
        # 启动响应测试
        self.response_test_timer = QTimer()
        self.response_test_timer.timeout.connect(self.perform_response_test)
        self.response_test_timer.start(2000)  # 每2秒进行一次测试
        
        self.current_test_count = 0
        self.max_test_count = test_count
        
        self.response_results_text.setText(f"开始响应时间测试...\n测试次数: {test_count}\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop_response_test(self):
        """停止响应时间测试"""
        if hasattr(self, 'response_test_timer'):
            self.response_test_timer.stop()
        
        self.start_response_test_btn.setEnabled(True)
        self.stop_response_test_btn.setEnabled(False)
        
        # 执行响应时间分析
        if self.response_test_data and len(self.response_test_data) > 5:
            response_array = np.array(self.response_test_data)
            response_results = self.response_analyzer.analyze_response_time(
                response_array, self.response_test_timestamps, self.pressure_events
            )
            self.display_response_results(response_results)
        else:
            self.response_results_text.setText("数据不足，无法进行响应时间分析")
    
    def perform_response_test(self):
        """执行响应时间测试"""
        if self.current_test_count >= self.max_test_count:
            self.stop_response_test()
            return
        
        # 记录测试开始时间
        test_start_time = datetime.now()
        
        # 模拟压力事件（在实际应用中，这里应该由用户触发或自动触发）
        pressure_event = {
            'start_time': test_start_time,
            'end_time': test_start_time + timedelta(seconds=1),
            'pressure_value': 0.5
        }
        self.pressure_events.append(pressure_event)
        
        # 收集响应数据
        self.collect_response_data(test_start_time, test_start_time + timedelta(seconds=2))
        
        self.current_test_count += 1
        
        # 更新状态
        status_text = f"响应测试进行中...\n已完成: {self.current_test_count}/{self.max_test_count}\n当前测试: {test_start_time.strftime('%H:%M:%S')}"
        self.response_results_text.setText(status_text)
    
    def collect_response_data(self, start_time, end_time):
        """收集响应数据"""
        # 模拟收集2秒的响应数据
        data_points = []
        timestamps = []
        
        current_time = start_time
        while current_time <= end_time:
            # 获取当前传感器数据
            if hasattr(self.parent(), 'get_current_sensor_data'):
                current_data = self.parent().get_current_sensor_data()
                if current_data is not None:
                    data_points.append(current_data.copy())
                    timestamps.append(current_time)
            
            current_time += timedelta(milliseconds=50)  # 50ms采样间隔
        
        if data_points:
            self.response_test_data.extend(data_points)
            self.response_test_timestamps.extend(timestamps)
    
    def start_fatigue_test(self):
        """开始疲劳效应测试"""
        test_cycles = self.fatigue_cycles_spin.value()
        self.start_fatigue_test_btn.setEnabled(False)
        self.stop_fatigue_test_btn.setEnabled(True)
        
        # 初始化疲劳测试数据
        self.fatigue_test_data = []
        self.fatigue_cycle_data = []
        self.current_fatigue_cycle = 0
        self.max_fatigue_cycles = test_cycles
        
        # 启动疲劳测试
        self.fatigue_test_timer = QTimer()
        self.fatigue_test_timer.timeout.connect(self.perform_fatigue_test)
        self.fatigue_test_timer.start(1000)  # 每秒进行一次测试
        
        self.fatigue_results_text.setText(f"开始疲劳效应测试...\n测试周期: {test_cycles}\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop_fatigue_test(self):
        """停止疲劳效应测试"""
        if hasattr(self, 'fatigue_test_timer'):
            self.fatigue_test_timer.stop()
        
        self.start_fatigue_test_btn.setEnabled(True)
        self.stop_fatigue_test_btn.setEnabled(False)
        
        # 执行疲劳效应分析
        if self.fatigue_cycle_data and len(self.fatigue_cycle_data) > 5:
            fatigue_array = np.array(self.fatigue_cycle_data)
            fatigue_results = self.fatigue_analyzer.analyze_fatigue_effects(fatigue_array, range(len(self.fatigue_cycle_data)))
            self.display_fatigue_results(fatigue_results)
        else:
            self.fatigue_results_text.setText("数据不足，无法进行疲劳效应分析")
    
    def perform_fatigue_test(self):
        """执行疲劳效应测试"""
        if self.current_fatigue_cycle >= self.max_fatigue_cycles:
            self.stop_fatigue_test()
            return
        
        # 收集一个周期的数据
        cycle_data = []
        cycle_start_time = datetime.now()
        
        # 模拟一个完整的加载-卸载周期
        for i in range(20):  # 20个数据点代表一个周期
            if hasattr(self.parent(), 'get_current_sensor_data'):
                current_data = self.parent().get_current_sensor_data()
                if current_data is not None:
                    cycle_data.append(current_data.copy())
            
            # 模拟时间延迟
            import time
            time.sleep(0.05)  # 50ms延迟
        
        if cycle_data:
            self.fatigue_cycle_data.append(cycle_data)
            self.current_fatigue_cycle += 1
        
        # 更新状态
        status_text = f"疲劳测试进行中...\n已完成周期: {self.current_fatigue_cycle}/{self.max_fatigue_cycles}\n当前周期: {cycle_start_time.strftime('%H:%M:%S')}"
        self.fatigue_results_text.setText(status_text)
    
    def save_analysis_results(self):
        """保存分析结果"""
        if not self.time_series_data and not self.response_test_data and not self.fatigue_cycle_data:
            QMessageBox.warning(self, "警告", "没有分析结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存时间一致性分析结果", "", "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if filename:
            try:
                results = {
                    'analysis_time': datetime.now().isoformat(),
                    'drift_analysis': {},
                    'response_analysis': {},
                    'fatigue_analysis': {}
                }
                
                # 保存漂移分析结果
                if self.time_series_data:
                    time_series_array = np.array(self.time_series_data)
                    drift_results = self.drift_analyzer.analyze_temporal_drift(time_series_array, self.time_stamps)
                    results['drift_analysis'] = {
                        'summary_stats': drift_results.get('summary_stats', {}),
                        'drift_rates': drift_results.get('drift_rates', {}).tolist() if isinstance(drift_results.get('drift_rates'), np.ndarray) else {},
                        'anomaly_count': len(drift_results.get('anomaly_points', []))
                    }
                
                # 保存响应时间分析结果
                if self.response_test_data:
                    response_array = np.array(self.response_test_data)
                    response_results = self.response_analyzer.analyze_response_time(
                        response_array, self.response_test_timestamps, self.pressure_events
                    )
                    results['response_analysis'] = {
                        'summary_stats': response_results.get('summary_stats', {}),
                        'response_consistency': response_results.get('response_consistency', {}),
                        'anomaly_count': len(response_results.get('response_anomalies', []))
                    }
                
                # 保存疲劳效应分析结果
                if self.fatigue_cycle_data:
                    fatigue_array = np.array(self.fatigue_cycle_data)
                    fatigue_results = self.fatigue_analyzer.analyze_fatigue_effects(fatigue_array, range(len(self.fatigue_cycle_data)))
                    results['fatigue_analysis'] = {
                        'summary_stats': fatigue_results.get('summary_stats', {}),
                        'sensitivity_decay_count': len(fatigue_results.get('sensitivity_decay', {})),
                        'stability_changes_count': len(fatigue_results.get('stability_changes', {}))
                    }
                
                # 保存到文件
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", f"分析结果已保存到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def clear_data(self):
        """清空数据"""
        self.time_series_data = None
        self.time_stamps = []
        self.pressure_events = []
        self.response_test_data = []
        self.response_test_timestamps = []
        self.fatigue_cycle_data = []
        
        # 清空显示
        self.drift_results_text.clear()
        self.response_results_text.clear()
        self.fatigue_results_text.clear()
        
        # 重置按钮状态
        self.save_results_btn.setEnabled(False)
        
        QMessageBox.information(self, "清空完成", "所有数据已清空")


class TemporalCalibrationSystem:
    """时间校正系统"""
    
    def __init__(self):
        self.drift_compensation = None
        self.response_compensation = None
        self.fatigue_compensation = None
        
    def generate_drift_compensation(self, drift_analysis_results):
        """生成漂移补偿"""
        drift_rates = drift_analysis_results.get('drift_rates')
        if drift_rates is None:
            return None
        
        # 创建漂移补偿映射
        compensation_map = np.ones_like(drift_rates)
        
        # 对每个传感器点应用漂移补偿
        for i in range(drift_rates.shape[0]):
            for j in range(drift_rates.shape[1]):
                drift_rate = drift_rates[i, j]
                
                # 如果漂移率显著，创建补偿函数
                if abs(drift_rate) > 1e-6:
                    # 线性补偿：compensation = 1 - drift_rate * time
                    compensation_map[i, j] = 1.0 - drift_rate * 3600  # 1小时后的补偿
        
        return compensation_map
    
    def generate_response_compensation(self, response_analysis_results):
        """生成响应时间补偿"""
        rise_times = response_analysis_results.get('rise_times', {})
        fall_times = response_analysis_results.get('fall_times', {})
        
        if not rise_times or not fall_times:
            return None
        
        # 计算平均响应时间
        all_rise_times = []
        all_fall_times = []
        
        for event_key in rise_times:
            rise_data = rise_times[event_key]
            fall_data = fall_times[event_key]
            
            valid_rise = rise_data[rise_data > 0]
            valid_fall = fall_data[fall_data > 0]
            
            all_rise_times.extend(valid_rise.flatten())
            all_fall_times.extend(valid_fall.flatten())
        
        if not all_rise_times or not all_fall_times:
            return None
        
        avg_rise_time = np.mean(all_rise_times)
        avg_fall_time = np.mean(all_fall_times)
        
        # 创建响应时间补偿参数
        compensation_params = {
            'avg_rise_time': avg_rise_time,
            'avg_fall_time': avg_fall_time,
            'rise_time_std': np.std(all_rise_times),
            'fall_time_std': np.std(all_fall_times)
        }
        
        return compensation_params
    
    def generate_fatigue_compensation(self, fatigue_analysis_results):
        """生成疲劳效应补偿"""
        sensitivity_decay = fatigue_analysis_results.get('sensitivity_decay', {})
        stability_changes = fatigue_analysis_results.get('stability_changes', {})
        
        if not sensitivity_decay and not stability_changes:
            return None
        
        # 创建疲劳补偿映射
        height, width = 64, 64  # 假设传感器尺寸
        fatigue_compensation = np.ones((height, width))
        
        # 应用敏感度衰减补偿
        for (i, j), decay_data in sensitivity_decay.items():
            decay_rate = decay_data.get('decay_rate', 0)
            if decay_rate > 0.05:  # 5%以上衰减才补偿
                fatigue_compensation[i, j] = 1.0 + decay_rate
        
        # 应用稳定性变化补偿
        for (i, j), stability_data in stability_changes.items():
            stability_trend = stability_data.get('stability_trend', 0)
            if stability_trend > 0.01:  # 稳定性恶化时补偿
                fatigue_compensation[i, j] *= (1.0 + stability_trend)
        
        return fatigue_compensation
    
    def apply_temporal_correction(self, raw_data, time_elapsed, pressure_event=None):
        """应用时间校正"""
        corrected_data = raw_data.copy()
        
        # 1. 应用漂移补偿
        if self.drift_compensation is not None:
            drift_factor = 1.0 - self.drift_compensation * time_elapsed
            corrected_data *= drift_factor
        
        # 2. 应用响应时间补偿
        if self.response_compensation is not None and pressure_event is not None:
            # 根据压力事件的时间调整响应
            event_duration = (pressure_event['end_time'] - pressure_event['start_time']).total_seconds()
            if event_duration < self.response_compensation['avg_rise_time']:
                # 响应时间补偿
                correction_factor = event_duration / self.response_compensation['avg_rise_time']
                corrected_data *= correction_factor
        
        # 3. 应用疲劳补偿
        if self.fatigue_compensation is not None:
            corrected_data *= self.fatigue_compensation
        
        return corrected_data


# 使用示例
def main():
    """主函数示例"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建时间一致性分析界面
    temporal_widget = TemporalConsistencyWidget()
    temporal_widget.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()