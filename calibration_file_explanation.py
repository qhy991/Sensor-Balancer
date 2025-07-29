#!/usr/bin/env python3
"""
校正文件格式和实现原理说明
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

def explain_calibration_file():
    """解释校正文件的格式和内容"""
    
    print("=== 校正文件格式说明 ===\n")
    
    # 模拟一个64x64的传感器阵列
    sensor_shape = (64, 64)
    
    # 模拟原始传感器响应（包含不一致性）
    print("1. 原始传感器响应（模拟数据）:")
    original_response = np.random.rand(*sensor_shape) * 0.5 + 0.3
    
    # 模拟传感器敏感度不均匀
    sensitivity_gradient = np.linspace(0.7, 1.3, 64)
    for i in range(64):
        original_response[i, :] *= sensitivity_gradient[i]
    
    # 模拟几个死区
    dead_zones = [(10, 15, 5), (40, 50, 3)]
    for x, y, r in dead_zones:
        for i in range(max(0, x-r), min(64, x+r)):
            for j in range(max(0, y-r), min(64, y+r)):
                if (i-x)**2 + (j-y)**2 <= r**2:
                    original_response[i, j] *= 0.1
    
    print(f"   - 形状: {original_response.shape}")
    print(f"   - 数值范围: {original_response.min():.4f} - {original_response.max():.4f}")
    print(f"   - 平均值: {original_response.mean():.4f}")
    print(f"   - 标准差: {original_response.std():.4f}")
    print(f"   - 变异系数: {original_response.std()/original_response.mean():.1%}")
    
    # 计算目标响应值（理想情况下的均匀响应）
    valid_data = original_response[original_response > np.mean(original_response) * 0.1]
    target_response = np.median(valid_data)
    print(f"   - 目标响应值: {target_response:.4f}")
    
    # 生成校正映射
    print("\n2. 校正映射:")
    calibration_map = np.ones_like(original_response)
    
    # 只对有效响应的区域进行校正
    valid_mask = original_response > np.mean(original_response) * 0.1
    calibration_map[valid_mask] = target_response / original_response[valid_mask]
    
    # 限制校正系数范围，避免过度校正
    calibration_map = np.clip(calibration_map, 0.2, 5.0)
    
    print(f"   - 形状: {calibration_map.shape}")
    print(f"   - 校正系数范围: {calibration_map.min():.3f} - {calibration_map.max():.3f}")
    print(f"   - 平均校正系数: {calibration_map.mean():.3f}")
    
    # 应用校正
    print("\n3. 校正后的响应:")
    corrected_response = original_response * calibration_map
    
    print(f"   - 数值范围: {corrected_response.min():.4f} - {corrected_response.max():.4f}")
    print(f"   - 平均值: {corrected_response.mean():.4f}")
    print(f"   - 标准差: {corrected_response.std():.4f}")
    print(f"   - 变异系数: {corrected_response.std()/corrected_response.mean():.1%}")
    
    # 计算改善程度
    original_cv = original_response.std() / original_response.mean()
    corrected_cv = corrected_response.std() / corrected_response.mean()
    improvement = (original_cv - corrected_cv) / original_cv * 100
    
    print(f"   - 一致性改善: {improvement:.1f}%")
    
    # 保存示例文件
    np.save("example_calibration_map.npy", calibration_map)
    print(f"\n4. 文件保存:")
    print(f"   - 校正映射已保存为: example_calibration_map.npy")
    print(f"   - 文件大小: {calibration_map.nbytes} 字节")
    
    return original_response, calibration_map, corrected_response

def visualize_calibration_process():
    """可视化校正过程"""
    
    original, calibration_map, corrected = explain_calibration_file()
    
    # 创建可视化
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('传感器校正过程可视化', fontsize=16)
    
    # 原始响应
    im1 = axes[0,0].imshow(original, cmap='viridis', aspect='equal')
    axes[0,0].set_title('原始传感器响应')
    axes[0,0].set_xlabel('X轴 (传感器列)')
    axes[0,0].set_ylabel('Y轴 (传感器行)')
    plt.colorbar(im1, ax=axes[0,0])
    
    # 校正映射
    im2 = axes[0,1].imshow(calibration_map, cmap='RdBu_r', aspect='equal')
    axes[0,1].set_title('校正系数映射')
    axes[0,1].set_xlabel('X轴 (传感器列)')
    axes[0,1].set_ylabel('Y轴 (传感器行)')
    plt.colorbar(im2, ax=axes[0,1])
    
    # 校正后响应
    im3 = axes[1,0].imshow(corrected, cmap='viridis', aspect='equal')
    axes[1,0].set_title('校正后传感器响应')
    axes[1,0].set_xlabel('X轴 (传感器列)')
    axes[1,0].set_ylabel('Y轴 (传感器行)')
    plt.colorbar(im3, ax=axes[1,0])
    
    # 响应分布对比
    axes[1,1].hist(original.flatten(), bins=50, alpha=0.7, label='校正前', color='red')
    axes[1,1].hist(corrected.flatten(), bins=50, alpha=0.7, label='校正后', color='blue')
    axes[1,1].set_title('响应值分布对比')
    axes[1,1].set_xlabel('响应值')
    axes[1,1].set_ylabel('频次')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig('calibration_visualization.png', dpi=300, bbox_inches='tight')
    print(f"\n5. 可视化结果:")
    print(f"   - 校正过程可视化已保存为: calibration_visualization.png")
    
    plt.show()

def demonstrate_calibration_usage():
    """演示校正文件的使用方法"""
    
    print("\n=== 校正文件使用方法 ===\n")
    
    # 加载校正映射
    try:
        calibration_map = np.load("example_calibration_map.npy")
        print("✅ 成功加载校正映射文件")
    except FileNotFoundError:
        print("❌ 校正映射文件不存在，请先运行校正过程")
        return
    
    # 模拟实时数据
    print("\n1. 模拟实时传感器数据:")
    real_time_data = np.random.rand(64, 64) * 0.5 + 0.3
    
    # 应用相同的敏感度模式
    sensitivity_gradient = np.linspace(0.7, 1.3, 64)
    for i in range(64):
        real_time_data[i, :] *= sensitivity_gradient[i]
    
    print(f"   - 原始数据范围: {real_time_data.min():.4f} - {real_time_data.max():.4f}")
    print(f"   - 原始数据CV: {real_time_data.std()/real_time_data.mean():.1%}")
    
    # 应用校正
    print("\n2. 应用校正:")
    corrected_data = real_time_data * calibration_map
    
    print(f"   - 校正后数据范围: {corrected_data.min():.4f} - {corrected_data.max():.4f}")
    print(f"   - 校正后数据CV: {corrected_data.std()/corrected_data.mean():.1%}")
    
    # 计算改善
    original_cv = real_time_data.std() / real_time_data.mean()
    corrected_cv = corrected_data.std() / corrected_data.mean()
    improvement = (original_cv - corrected_cv) / original_cv * 100
    
    print(f"   - 一致性改善: {improvement:.1f}%")
    
    print("\n3. 校正效果评估:")
    if improvement > 20:
        print("   ✅ 校正效果显著")
    elif improvement > 10:
        print("   ⚠️ 校正效果一般")
    else:
        print("   ❌ 校正效果不明显")

if __name__ == "__main__":
    print("校正文件格式和实现原理演示\n")
    print("=" * 50)
    
    # 演示校正过程
    visualize_calibration_process()
    
    # 演示使用方法
    demonstrate_calibration_usage()
    
    print("\n" + "=" * 50)
    print("演示完成！") 