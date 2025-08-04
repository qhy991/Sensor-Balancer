#!/usr/bin/env python3
"""
测试指标详细解释程序
解释各种传感器测试指标的含义、计算方法和物理意义
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

class MetricsExplanation:
    """测试指标解释器"""
    
    def __init__(self):
        self.metrics = {}
    
    def explain_basic_statistics(self):
        """解释基础统计指标"""
        print("📊 Basic Statistical Metrics")
        print("=" * 60)
        
        print("1. 平均值 (Mean)")
        print("   📝 定义: 所有数值的总和除以数值个数")
        print("   🧮 公式: μ = (Σxᵢ) / n")
        print("   💡 物理意义: 代表传感器响应的中心趋势")
        print("   📈 在传感器测试中: 反映平均压力水平")
        print("   ⚠️ 注意事项: 对异常值敏感")
        
        print("\n2. 标准差 (Standard Deviation)")
        print("   📝 定义: 数据偏离平均值的平均程度")
        print("   🧮 公式: σ = √(Σ(xᵢ - μ)² / n)")
        print("   💡 物理意义: 衡量数据的离散程度")
        print("   📈 在传感器测试中: 反映响应的波动性")
        print("   ⚠️ 注意事项: 单位与原始数据相同")
        
        print("\n3. 变异系数 (Coefficient of Variation, CV)")
        print("   📝 定义: 标准差与平均值的比值")
        print("   🧮 公式: CV = σ / μ")
        print("   💡 物理意义: 相对离散程度，无量纲")
        print("   📈 在传感器测试中: 标准化的波动性指标")
        print("   ✅ 优点: 可以比较不同量级的数据")
        print("   🎯 目标值: < 20% (良好), < 10% (优秀)")
    
    def explain_spatial_metrics(self):
        """解释空间一致性指标"""
        print("\n🎯 Spatial Consistency Metrics")
        print("=" * 60)
        
        print("1. 空间变异系数 (Spatial CV)")
        print("   📝 定义: 传感器阵列中不同位置响应的变异程度")
        print("   🧮 计算方法:")
        print("      a) 计算每个像素的平均响应")
        print("      b) 计算所有像素响应的标准差")
        print("      c) CV = 标准差 / 平均值")
        print("   💡 物理意义: 传感器在空间上的均匀性")
        print("   📈 理想情况: 均匀按压时所有像素响应相同")
        print("   🎯 目标值: < 20% (良好), < 10% (优秀)")
        print("   ⚠️ 问题: 值过大表示传感器校准或安装有问题")
        
        print("\n2. 空间均匀性评分 (Spatial Uniformity Score)")
        print("   📝 定义: 综合评估空间一致性的指标")
        print("   🧮 公式: Score = 1 / (1 + CV + relative_range)")
        print("   💡 物理意义: 0-1之间的评分，越高越好")
        print("   📈 评分标准:")
        print("      > 0.8: 优秀")
        print("      > 0.6: 良好")
        print("      > 0.4: 一般")
        print("      ≤ 0.4: 差")
        
        print("\n3. 相对范围 (Relative Range)")
        print("   📝 定义: 最大值与最小值的差除以平均值")
        print("   🧮 公式: (max - min) / mean")
        print("   💡 物理意义: 响应范围的相对大小")
        print("   📈 理想情况: 均匀按压时范围应该很小")
    
    def explain_temporal_metrics(self):
        """解释时间稳定性指标"""
        print("\n⏰ Temporal Stability Metrics")
        print("=" * 60)
        
        print("1. 时间变异系数 (Temporal CV)")
        print("   📝 定义: 传感器响应随时间变化的程度")
        print("   🧮 计算方法:")
        print("      a) 计算每帧的平均响应")
        print("      b) 计算所有帧响应的标准差")
        print("      c) CV = 标准差 / 平均值")
        print("   💡 物理意义: 传感器在时间上的稳定性")
        print("   📈 理想情况: 稳定压力下响应应该恒定")
        print("   🎯 目标值: < 10% (良好), < 5% (优秀)")
        print("   ⚠️ 问题: 值过大表示压力不稳定或环境干扰")
        
        print("\n2. 一致性趋势 (Consistency Trend)")
        print("   📝 定义: 一致性指标随时间的变化趋势")
        print("   🧮 计算方法: 线性回归的斜率")
        print("   💡 物理意义: 正斜率表示一致性在恶化")
        print("   📈 理想情况: 斜率为0或接近0")
        print("   ⚠️ 问题: 显著的正斜率表示传感器性能在下降")
        
        print("\n3. 稳定性评估 (Stability Assessment)")
        print("   📝 定义: 综合评估时间稳定性的指标")
        print("   🧮 判断条件: temporal_cv < 0.1 AND |trend| < 0.001")
        print("   💡 物理意义: 是否满足稳定性要求")
        print("   📈 结果: True (稳定) / False (不稳定)")
    
    def explain_gaussian_fit_metrics(self):
        """解释高斯拟合指标"""
        print("\n📈 Gaussian Fit Quality Metrics")
        print("=" * 60)
        
        print("1. R² (决定系数)")
        print("   📝 定义: 拟合优度，表示模型解释数据变异的比例")
        print("   🧮 公式: R² = 1 - (SS_res / SS_tot)")
        print("   💡 物理意义: 0-1之间，越接近1拟合越好")
        print("   📈 评分标准:")
        print("      > 0.9: 优秀")
        print("      > 0.7: 良好")
        print("      > 0.5: 一般")
        print("      ≤ 0.5: 差")
        print("   ⚠️ 注意: 仅表示拟合程度，不表示数据质量")
        
        print("\n2. Kolmogorov-Smirnov检验 (KS Test)")
        print("   📝 定义: 检验数据是否来自指定分布的统计检验")
        print("   🧮 输出: KS统计量和p值")
        print("   💡 物理意义: p值 > 0.05表示数据符合高斯分布")
        print("   📈 判断标准:")
        print("      p > 0.05: 符合高斯分布")
        print("      p ≤ 0.05: 不符合高斯分布")
        print("   ⚠️ 注意: 样本量越大，检验越严格")
        
        print("\n3. 拟合质量评估 (Goodness of Fit)")
        print("   📝 定义: 综合R²和KS检验的评估结果")
        print("   🧮 判断标准:")
        print("      Excellent: R² > 0.9 AND p > 0.05")
        print("      Good: R² > 0.7 AND p > 0.01")
        print("      Fair: R² > 0.5")
        print("      Poor: R² ≤ 0.5")
    
    def demonstrate_calculations(self):
        """演示指标计算过程"""
        print("\n🧮 Calculation Demonstrations")
        print("=" * 60)
        
        # 创建示例数据
        print("📊 Example Data:")
        sample_data = np.array([0.0001, 0.00012, 0.00008, 0.00011, 0.00009])
        print(f"   Sample values: {sample_data}")
        
        # 计算基础统计
        mean_val = np.mean(sample_data)
        std_val = np.std(sample_data)
        cv_val = std_val / mean_val
        
        print(f"\n📈 Basic Statistics:")
        print(f"   Mean: {mean_val:.8f}")
        print(f"   Std: {std_val:.8f}")
        print(f"   CV: {cv_val:.2%}")
        
        # 演示空间一致性计算
        print(f"\n🎯 Spatial Consistency Example:")
        spatial_data = np.array([
            [0.0001, 0.00012, 0.00011],
            [0.00009, 0.0001, 0.00012],
            [0.00011, 0.00008, 0.0001]
        ])
        print(f"   Spatial array:\n{spatial_data}")
        
        spatial_mean = np.mean(spatial_data)
        spatial_std = np.std(spatial_data)
        spatial_cv = spatial_std / spatial_mean
        
        print(f"   Spatial mean: {spatial_mean:.8f}")
        print(f"   Spatial std: {spatial_std:.8f}")
        print(f"   Spatial CV: {spatial_cv:.2%}")
        
        # 演示时间稳定性计算
        print(f"\n⏰ Temporal Stability Example:")
        temporal_data = np.array([0.0001, 0.00011, 0.00009, 0.00012, 0.0001])
        print(f"   Temporal values: {temporal_data}")
        
        temporal_mean = np.mean(temporal_data)
        temporal_std = np.std(temporal_data)
        temporal_cv = temporal_std / temporal_mean
        
        print(f"   Temporal mean: {temporal_mean:.8f}")
        print(f"   Temporal std: {temporal_std:.8f}")
        print(f"   Temporal CV: {temporal_cv:.2%}")
    
    def explain_interpretation_guide(self):
        """解释结果解读指南"""
        print("\n📋 Results Interpretation Guide")
        print("=" * 60)
        
        print("🎯 优秀性能指标:")
        print("   • 空间CV < 10%")
        print("   • 时间CV < 5%")
        print("   • 均匀性评分 > 0.8")
        print("   • 高斯拟合R² > 0.9")
        print("   • KS检验p值 > 0.05")
        
        print("\n⚠️ 需要改进的指标:")
        print("   • 空间CV > 20%")
        print("   • 时间CV > 10%")
        print("   • 均匀性评分 < 0.6")
        print("   • 高斯拟合R² < 0.7")
        print("   • KS检验p值 < 0.01")
        
        print("\n🔧 常见问题诊断:")
        print("   1. 空间CV过高:")
        print("      → 检查传感器校准")
        print("      → 检查压力施加均匀性")
        print("      → 检查传感器表面平整度")
        
        print("   2. 时间CV过高:")
        print("      → 检查压力稳定性")
        print("      → 减少环境振动")
        print("      → 使用固定装置")
        
        print("   3. 高斯拟合差:")
        print("      → 数据可能不符合高斯分布")
        print("      → 考虑使用其他分布模型")
        print("      → 检查数据质量")
    
    def create_visual_examples(self):
        """创建可视化示例"""
        print("\n📊 Creating Visual Examples")
        print("=" * 60)
        
        # 创建示例数据
        np.random.seed(42)
        
        # 好的传感器数据
        good_data = np.random.normal(0.0001, 0.00001, (64, 64))
        good_cv = np.std(good_data) / np.mean(good_data)
        
        # 差的传感器数据
        bad_data = np.random.normal(0.0001, 0.00005, (64, 64))
        bad_cv = np.std(bad_data) / np.mean(bad_data)
        
        # 创建对比图
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Metrics Visualization Examples', fontsize=16)
        
        # 好的空间一致性
        im1 = axes[0, 0].imshow(good_data, cmap='viridis')
        axes[0, 0].set_title(f'Good Spatial Consistency\n(CV: {good_cv:.2%})')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 差的空间一致性
        im2 = axes[0, 1].imshow(bad_data, cmap='viridis')
        axes[0, 1].set_title(f'Poor Spatial Consistency\n(CV: {bad_cv:.2%})')
        axes[0, 1].set_xlabel('Column')
        axes[0, 1].set_ylabel('Row')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 好的时间稳定性
        good_temporal = np.random.normal(0.0001, 0.000005, 100)
        axes[1, 0].plot(good_temporal, 'g-', alpha=0.7)
        axes[1, 0].set_title(f'Good Temporal Stability\n(CV: {np.std(good_temporal)/np.mean(good_temporal):.2%})')
        axes[1, 0].set_xlabel('Frame')
        axes[1, 0].set_ylabel('Mean Response')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 差的时间稳定性
        bad_temporal = np.random.normal(0.0001, 0.00002, 100)
        axes[1, 1].plot(bad_temporal, 'r-', alpha=0.7)
        axes[1, 1].set_title(f'Poor Temporal Stability\n(CV: {np.std(bad_temporal)/np.mean(bad_temporal):.2%})')
        axes[1, 1].set_xlabel('Frame')
        axes[1, 1].set_ylabel('Mean Response')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        print("✅ Visual examples created!")
        print("📊 The plots show:")
        print("   • Good vs Poor spatial consistency")
        print("   • Good vs Poor temporal stability")
        print("   • CV values for comparison")

def main():
    """主函数"""
    print("📚 Sensor Testing Metrics Explanation")
    print("=" * 80)
    
    explainer = MetricsExplanation()
    
    # 解释各种指标
    explainer.explain_basic_statistics()
    explainer.explain_spatial_metrics()
    explainer.explain_temporal_metrics()
    explainer.explain_gaussian_fit_metrics()
    
    # 演示计算过程
    explainer.demonstrate_calculations()
    
    # 提供解读指南
    explainer.explain_interpretation_guide()
    
    # 创建可视化示例
    explainer.create_visual_examples()
    
    print("\n✅ Explanation complete!")
    print("📋 Key takeaways:")
    print("   • CV是标准化的波动性指标")
    print("   • 空间CV反映传感器均匀性")
    print("   • 时间CV反映测量稳定性")
    print("   • 目标值: 空间CV < 20%, 时间CV < 10%")

if __name__ == "__main__":
    main() 