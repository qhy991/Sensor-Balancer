"""
时间校正系统示例
展示如何使用时间一致性分析结果进行校正
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from temporal_consistency_analysis import TemporalDriftAnalyzer, ResponseTimeAnalyzer, FatigueAnalyzer, TemporalCalibrationSystem

def demonstrate_temporal_calibration():
    """演示时间校正系统"""
    
    # 1. 生成模拟的时间序列数据
    print("=== 生成模拟时间序列数据 ===")
    time_series_data, time_stamps = generate_simulated_time_series()
    print(f"生成了 {len(time_series_data)} 个时间点的数据")
    print(f"时间跨度: {time_stamps[0]} 到 {time_stamps[-1]}")
    
    # 2. 执行时间漂移分析
    print("\n=== 执行时间漂移分析 ===")
    drift_analyzer = TemporalDriftAnalyzer()
    drift_results = drift_analyzer.analyze_temporal_drift(time_series_data, time_stamps)
    
    # 显示漂移分析结果
    summary = drift_results.get('summary_stats', {})
    if summary:
        print(f"平均漂移率: {summary.get('mean_drift_rate', 0):.6f} 单位/秒")
        print(f"漂移率标准差: {summary.get('std_drift_rate', 0):.6f}")
        print(f"正漂移传感器: {summary.get('positive_drift_count', 0)}")
        print(f"负漂移传感器: {summary.get('negative_drift_count', 0)}")
    
    # 3. 执行响应时间分析
    print("\n=== 执行响应时间分析 ===")
    response_analyzer = ResponseTimeAnalyzer()
    
    # 创建模拟压力事件
    pressure_events = [
        {
            'start_time': time_stamps[100],
            'end_time': time_stamps[120],
            'pressure_value': 0.5
        },
        {
            'start_time': time_stamps[200],
            'end_time': time_stamps[220],
            'pressure_value': 0.7
        }
    ]
    
    response_results = response_analyzer.analyze_response_time(time_series_data, time_stamps, pressure_events)
    
    # 显示响应时间分析结果
    response_summary = response_results.get('summary_stats', {})
    rise_summary = response_summary.get('rise_time_summary', {})
    fall_summary = response_summary.get('fall_time_summary', {})
    
    if rise_summary:
        print(f"平均上升时间: {rise_summary.get('mean', 0):.3f} 秒")
        print(f"上升时间变异系数: {rise_summary.get('cv', 0)*100:.1f}%")
    
    if fall_summary:
        print(f"平均下降时间: {fall_summary.get('mean', 0):.3f} 秒")
        print(f"下降时间变异系数: {fall_summary.get('cv', 0)*100:.1f}%")
    
    # 4. 执行疲劳效应分析
    print("\n=== 执行疲劳效应分析 ===")
    fatigue_analyzer = FatigueAnalyzer()
    
    # 生成重复测试数据
    repeated_test_data = generate_repeated_test_data()
    test_cycles = list(range(len(repeated_test_data)))
    
    fatigue_results = fatigue_analyzer.analyze_fatigue_effects(repeated_test_data, test_cycles)
    
    # 显示疲劳效应分析结果
    fatigue_summary = fatigue_results.get('summary_stats', {})
    sensitivity_summary = fatigue_summary.get('sensitivity_decay_summary', {})
    
    if sensitivity_summary:
        print(f"受影响传感器: {sensitivity_summary.get('affected_sensors', 0)}")
        print(f"平均衰减率: {sensitivity_summary.get('mean_decay_rate', 0)*100:.1f}%")
        print(f"严重衰减传感器: {sensitivity_summary.get('severe_decay_count', 0)}")
    
    # 5. 创建时间校正系统
    print("\n=== 创建时间校正系统 ===")
    temporal_calibration = TemporalCalibrationSystem()
    
    # 生成各种补偿
    drift_compensation = temporal_calibration.generate_drift_compensation(drift_results)
    response_compensation = temporal_calibration.generate_response_compensation(response_results)
    fatigue_compensation = temporal_calibration.generate_fatigue_compensation(fatigue_results)
    
    print(f"漂移补偿: {'已生成' if drift_compensation is not None else '未生成'}")
    print(f"响应时间补偿: {'已生成' if response_compensation is not None else '未生成'}")
    print(f"疲劳补偿: {'已生成' if fatigue_compensation is not None else '未生成'}")
    
    # 6. 应用时间校正
    print("\n=== 应用时间校正 ===")
    
    # 设置补偿参数
    temporal_calibration.drift_compensation = drift_compensation
    temporal_calibration.response_compensation = response_compensation
    temporal_calibration.fatigue_compensation = fatigue_compensation
    
    # 获取最新的传感器数据
    latest_data = time_series_data[-1]
    time_elapsed = (time_stamps[-1] - time_stamps[0]).total_seconds()
    
    # 应用校正
    corrected_data = temporal_calibration.apply_temporal_correction(
        latest_data, time_elapsed, pressure_events[-1] if pressure_events else None
    )
    
    # 比较校正前后的数据
    print(f"原始数据统计:")
    print(f"  均值: {np.mean(latest_data):.4f}")
    print(f"  标准差: {np.std(latest_data):.4f}")
    print(f"  范围: {np.min(latest_data):.4f} - {np.max(latest_data):.4f}")
    
    print(f"校正后数据统计:")
    print(f"  均值: {np.mean(corrected_data):.4f}")
    print(f"  标准差: {np.std(corrected_data):.4f}")
    print(f"  范围: {np.min(corrected_data):.4f} - {np.max(corrected_data):.4f}")
    
    # 7. 可视化校正效果
    print("\n=== 可视化校正效果 ===")
    visualize_calibration_effect(latest_data, corrected_data, drift_results, response_results, fatigue_results)
    
    return {
        'drift_results': drift_results,
        'response_results': response_results,
        'fatigue_results': fatigue_results,
        'original_data': latest_data,
        'corrected_data': corrected_data,
        'temporal_calibration': temporal_calibration
    }


def generate_simulated_time_series():
    """生成模拟时间序列数据"""
    # 生成2小时的时间序列，每秒一个数据点
    start_time = datetime.now()
    time_stamps = [start_time + timedelta(seconds=i) for i in range(7200)]  # 2小时
    
    # 生成64x64传感器阵列的时间序列数据
    height, width = 64, 64
    time_series_data = []
    
    for t in range(len(time_stamps)):
        # 基础数据
        data = np.random.rand(height, width) * 0.01
        
        # 添加时间漂移
        drift_factor = 1.0 + 0.0001 * t  # 线性漂移
        data *= drift_factor
        
        # 添加周期性变化
        periodic_factor = 1.0 + 0.1 * np.sin(2 * np.pi * t / 3600)  # 1小时周期
        data *= periodic_factor
        
        # 添加随机噪声
        noise = np.random.normal(0, 0.001, (height, width))
        data += noise
        
        # 添加一些压力事件
        if t % 1000 == 0:  # 每1000秒添加一个压力事件
            center_x, center_y = np.random.randint(20, 44, 2)
            for i in range(max(0, center_x-10), min(height, center_x+10)):
                for j in range(max(0, center_y-10), min(width, center_y+10)):
                    distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if distance < 10:
                        data[i, j] += 0.3 * np.exp(-distance / 5)
        
        time_series_data.append(data)
    
    return np.array(time_series_data), time_stamps


def generate_repeated_test_data():
    """生成重复测试数据"""
    # 生成10个周期的重复测试数据
    num_cycles = 10
    time_points = 50
    height, width = 64, 64
    
    repeated_data = []
    
    for cycle in range(num_cycles):
        cycle_data = []
        
        for t in range(time_points):
            # 基础数据
            data = np.random.rand(height, width) * 0.01
            
            # 添加疲劳效应（敏感度衰减）
            fatigue_factor = 1.0 - 0.02 * cycle  # 每个周期衰减2%
            data *= fatigue_factor
            
            # 添加压力事件
            if 20 <= t <= 30:  # 中间10个时间点有压力
                center_x, center_y = 32, 32
                for i in range(max(0, center_x-8), min(height, center_x+8)):
                    for j in range(max(0, center_y-8), min(width, center_y+8)):
                        distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                        if distance < 8:
                            data[i, j] += 0.4 * np.exp(-distance / 4)
            
            cycle_data.append(data)
        
        repeated_data.append(cycle_data)
    
    return np.array(repeated_data)


def visualize_calibration_effect(original_data, corrected_data, drift_results, response_results, fatigue_results):
    """可视化校正效果"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('时间校正效果可视化', fontsize=16)
    
    # 1. 原始数据热力图
    im1 = axes[0, 0].imshow(original_data, cmap='viridis', aspect='auto')
    axes[0, 0].set_title('原始数据')
    axes[0, 0].set_xlabel('X轴')
    axes[0, 0].set_ylabel('Y轴')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # 2. 校正后数据热力图
    im2 = axes[0, 1].imshow(corrected_data, cmap='viridis', aspect='auto')
    axes[0, 1].set_title('校正后数据')
    axes[0, 1].set_xlabel('X轴')
    axes[0, 1].set_ylabel('Y轴')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # 3. 校正差异热力图
    difference = corrected_data - original_data
    im3 = axes[0, 2].imshow(difference, cmap='RdBu_r', aspect='auto')
    axes[0, 2].set_title('校正差异')
    axes[0, 2].set_xlabel('X轴')
    axes[0, 2].set_ylabel('Y轴')
    plt.colorbar(im3, ax=axes[0, 2])
    
    # 4. 漂移率分布
    if 'drift_rates' in drift_results:
        drift_rates = drift_results['drift_rates']
        axes[1, 0].hist(drift_rates.flatten(), bins=50, alpha=0.7, color='blue')
        axes[1, 0].set_title('漂移率分布')
        axes[1, 0].set_xlabel('漂移率')
        axes[1, 0].set_ylabel('频次')
    
    # 5. 响应时间统计
    if 'summary_stats' in response_results:
        response_summary = response_results['summary_stats']
        rise_summary = response_summary.get('rise_time_summary', {})
        fall_summary = response_summary.get('fall_time_summary', {})
        
        if rise_summary and fall_summary:
            categories = ['上升时间', '下降时间']
            means = [rise_summary.get('mean', 0), fall_summary.get('mean', 0)]
            stds = [rise_summary.get('std', 0), fall_summary.get('std', 0)]
            
            x_pos = np.arange(len(categories))
            axes[1, 1].bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
            axes[1, 1].set_title('响应时间统计')
            axes[1, 1].set_ylabel('时间 (秒)')
            axes[1, 1].set_xticks(x_pos)
            axes[1, 1].set_xticklabels(categories)
    
    # 6. 疲劳效应趋势
    if 'summary_stats' in fatigue_results:
        fatigue_summary = fatigue_results['summary_stats']
        sensitivity_summary = fatigue_summary.get('sensitivity_decay_summary', {})
        
        if sensitivity_summary:
            axes[1, 2].text(0.1, 0.5, f"受影响传感器: {sensitivity_summary.get('affected_sensors', 0)}\n"
                                      f"平均衰减率: {sensitivity_summary.get('mean_decay_rate', 0)*100:.1f}%\n"
                                      f"严重衰减: {sensitivity_summary.get('severe_decay_count', 0)}",
                           transform=axes[1, 2].transAxes, fontsize=12,
                           verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue'))
            axes[1, 2].set_title('疲劳效应统计')
            axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()


def demonstrate_real_time_calibration():
    """演示实时时间校正"""
    print("=== 实时时间校正演示 ===")
    
    # 创建时间校正系统
    temporal_calibration = TemporalCalibrationSystem()
    
    # 模拟实时数据流
    start_time = datetime.now()
    
    for i in range(10):
        # 模拟获取实时数据
        current_time = start_time + timedelta(seconds=i*10)
        time_elapsed = (current_time - start_time).total_seconds()
        
        # 生成模拟传感器数据
        raw_data = np.random.rand(64, 64) * 0.01
        
        # 应用时间校正
        corrected_data = temporal_calibration.apply_temporal_correction(
            raw_data, time_elapsed, None
        )
        
        print(f"时间点 {i+1}: {current_time.strftime('%H:%M:%S')}")
        print(f"  原始数据均值: {np.mean(raw_data):.4f}")
        print(f"  校正后数据均值: {np.mean(corrected_data):.4f}")
        print(f"  校正差异: {np.mean(corrected_data) - np.mean(raw_data):.4f}")
        print()


if __name__ == "__main__":
    # 运行时间校正演示
    results = demonstrate_temporal_calibration()
    
    # 运行实时校正演示
    demonstrate_real_time_calibration()
    
    print("=== 时间校正系统演示完成 ===") 