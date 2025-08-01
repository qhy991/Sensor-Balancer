"""
帧间一致性分析演示程序
演示如何使用帧间一致性分析模块
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from frame_consistency_analysis import FrameConsistencyAnalyzer, FrameCorrectionSystem

def demonstrate_frame_consistency():
    """演示帧间一致性分析"""
    
    print("=== 帧间一致性分析演示 ===")
    
    # 创建分析器
    analyzer = FrameConsistencyAnalyzer()
    
    # 生成模拟的帧数据（模拟相同压力下的数据）
    print("生成模拟帧数据...")
    frames = generate_simulated_frames()
    
    # 添加帧数据到分析器
    for i, frame in enumerate(frames):
        analyzer.add_frame(frame)
        print(f"添加第 {i+1} 帧数据")
    
    # 执行分析
    print("\n执行帧间一致性分析...")
    results = analyzer.analyze_frame_consistency()
    
    # 显示分析结果
    display_analysis_results(results)
    
    # 演示校正系统
    demonstrate_correction_system(frames)
    
    return results

def generate_simulated_frames():
    """生成模拟的帧数据"""
    num_frames = 20
    height, width = 64, 64
    
    # 基础压力模式（模拟手指按压）
    base_pressure = np.zeros((height, width))
    center_x, center_y = 32, 32
    
    # 创建高斯分布的压力模式
    for i in range(height):
        for j in range(width):
            distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
            base_pressure[i, j] = 0.005 * np.exp(-distance**2 / 100)
    
    frames = []
    
    for frame_idx in range(num_frames):
        # 添加随机噪声（模拟传感器噪声）
        noise_level = 0.0001 + 0.0001 * np.sin(frame_idx * 0.5)  # 变化的噪声水平
        noise = np.random.normal(0, noise_level, (height, width))
        
        # 添加一些异常帧
        if frame_idx in [5, 12, 18]:  # 第5、12、18帧为异常帧
            # 添加较大的噪声
            noise += np.random.normal(0, 0.001, (height, width))
            # 添加位置偏移
            offset_x = np.random.randint(-2, 3)
            offset_y = np.random.randint(-2, 3)
            shifted_pressure = np.roll(np.roll(base_pressure, offset_x, axis=0), offset_y, axis=1)
            frame = shifted_pressure + noise
        else:
            frame = base_pressure + noise
        
        # 确保数据在合理范围内
        frame = np.clip(frame, 0, 0.01)
        frames.append(frame)
    
    return frames

def display_analysis_results(results):
    """显示分析结果"""
    if not results:
        print("没有分析结果")
        return
    
    summary = results.get('summary_stats', {})
    
    print(f"\n=== 分析结果 ===")
    print(f"总帧数: {summary.get('total_frames', 0)}")
    print(f"一致性评分: {summary.get('consistency_score', 0):.2f}/10")
    
    # 帧间差异
    frame_diffs = results.get('frame_differences', {})
    if frame_diffs:
        print(f"\n帧间差异分析:")
        print(f"  平均绝对差异: {frame_diffs.get('mean_abs_diff', 0):.6f}")
        print(f"  最大绝对差异: {frame_diffs.get('max_abs_diff', 0):.6f}")
        print(f"  平均相对差异: {frame_diffs.get('mean_rel_diff', 0)*100:.2f}%")
    
    # 稳定性分析
    stability = results.get('stability_metrics', {})
    if stability:
        print(f"\n稳定性分析:")
        print(f"  平均稳定性: {stability.get('mean_stability', 0):.3f}")
        print(f"  平均方差: {stability.get('mean_variance', 0):.6f}")
        print(f"  不稳定传感器: {stability.get('unstable_sensors', 0)} 个")
    
    # 噪声特性
    noise = results.get('noise_characteristics', {})
    if noise:
        print(f"\n噪声特性:")
        print(f"  平均噪声功率: {noise.get('mean_noise_power', 0):.6f}")
        print(f"  高噪声传感器: {noise.get('high_noise_sensors', 0)} 个")
    
    # 异常检测
    anomalies = results.get('anomaly_frames', [])
    print(f"\n异常检测:")
    print(f"  异常帧数量: {len(anomalies)} 个")
    if anomalies:
        print(f"  异常帧索引: {[a['frame_index'] for a in anomalies]}")
    
    # 评估结果
    consistency_score = summary.get('consistency_score', 0)
    print(f"\n评估结果:")
    if consistency_score >= 8.0:
        print("  一致性状态: 优秀 ✅")
    elif consistency_score >= 6.0:
        print("  一致性状态: 良好 ✅")
    elif consistency_score >= 4.0:
        print("  一致性状态: 一般 ⚠️")
    else:
        print("  一致性状态: 较差 ❌")

def demonstrate_correction_system(frames):
    """演示校正系统"""
    print(f"\n=== 帧间校正系统演示 ===")
    
    # 创建校正系统
    correction_system = FrameCorrectionSystem()
    correction_system.enable_correction(True)
    correction_system.set_smoothing_factor(0.7)
    correction_system.set_correction_threshold(0.0005)
    
    print("校正参数:")
    stats = correction_system.get_correction_stats()
    print(f"  校正启用: {stats['correction_enabled']}")
    print(f"  平滑因子: {stats['smoothing_factor']}")
    print(f"  校正阈值: {stats['correction_threshold']}")
    
    # 应用校正
    print("\n应用校正...")
    corrected_frames = []
    original_differences = []
    corrected_differences = []
    
    for i, frame in enumerate(frames):
        corrected_frame = correction_system.correct_frame(frame)
        corrected_frames.append(corrected_frame)
        
        # 计算帧间差异
        if i > 0:
            orig_diff = np.mean(np.abs(frame - frames[i-1]))
            corr_diff = np.mean(np.abs(corrected_frame - corrected_frames[i-1]))
            original_differences.append(orig_diff)
            corrected_differences.append(corr_diff)
    
    # 显示校正效果
    if original_differences and corrected_differences:
        print(f"\n校正效果:")
        print(f"  原始平均帧间差异: {np.mean(original_differences):.6f}")
        print(f"  校正后平均帧间差异: {np.mean(corrected_differences):.6f}")
        improvement = (np.mean(original_differences) - np.mean(corrected_differences)) / np.mean(original_differences) * 100
        print(f"  改善程度: {improvement:.1f}%")
    
    return corrected_frames

def visualize_frame_consistency(frames, corrected_frames=None):
    """可视化帧间一致性"""
    if not frames:
        return
    
    # 选择几个关键帧进行可视化
    key_frames = [0, 5, 10, 15, 19]  # 包括正常帧和异常帧
    
    fig, axes = plt.subplots(2, len(key_frames), figsize=(15, 6))
    fig.suptitle('帧间一致性可视化', fontsize=16)
    
    for i, frame_idx in enumerate(key_frames):
        if frame_idx < len(frames):
            # 原始帧
            im1 = axes[0, i].imshow(frames[frame_idx], cmap='viridis', aspect='auto')
            axes[0, i].set_title(f'原始帧 {frame_idx+1}')
            axes[0, i].set_xlabel('X轴')
            axes[0, i].set_ylabel('Y轴')
            plt.colorbar(im1, ax=axes[0, i])
            
            # 校正后帧（如果有）
            if corrected_frames and frame_idx < len(corrected_frames):
                im2 = axes[1, i].imshow(corrected_frames[frame_idx], cmap='viridis', aspect='auto')
                axes[1, i].set_title(f'校正帧 {frame_idx+1}')
                axes[1, i].set_xlabel('X轴')
                axes[1, i].set_ylabel('Y轴')
                plt.colorbar(im2, ax=axes[1, i])
    
    plt.tight_layout()
    plt.show()

def demonstrate_real_time_monitoring():
    """演示实时监测"""
    print(f"\n=== 实时监测演示 ===")
    
    # 创建分析器
    analyzer = FrameConsistencyAnalyzer()
    
    # 模拟实时数据流
    print("模拟实时数据流...")
    for i in range(30):
        # 生成当前帧数据
        current_frame = generate_simulated_frames()[i % 20]  # 循环使用20帧数据
        
        # 添加到分析器
        analyzer.add_frame(current_frame)
        
        # 实时计算一致性评分
        if len(analyzer.frame_history) > 1:
            consistency_score = analyzer._calculate_consistency_score()
            print(f"帧 {i+1}: 一致性评分 = {consistency_score:.2f}/10")
            
            # 如果评分过低，发出警告
            if consistency_score < 6.0:
                print(f"  ⚠️ 警告：帧间一致性较差")
        
        # 模拟时间延迟
        import time
        time.sleep(0.1)
    
    print("实时监测完成")

def main():
    """主函数"""
    print("帧间一致性分析演示程序")
    print("=" * 50)
    
    # 1. 基本分析演示
    results = demonstrate_frame_consistency()
    
    # 2. 生成可视化
    frames = generate_simulated_frames()
    corrected_frames = demonstrate_correction_system(frames)
    visualize_frame_consistency(frames, corrected_frames)
    
    # 3. 实时监测演示
    demonstrate_real_time_monitoring()
    
    print("\n演示完成！")

if __name__ == "__main__":
    main() 