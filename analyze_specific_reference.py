#!/usr/bin/env python3
"""
专门分析指定参考数据文件的脚本
"""

import numpy as np
import json
import os
import matplotlib.pyplot as plt

def analyze_specific_reference_data(filepath):
    """详细分析指定的参考数据文件"""
    print(f"🔍 详细分析参考数据文件: {filepath}")
    print("=" * 60)
    
    try:
        # 加载数据
        data = np.load(filepath)
        
        print(f"📊 基础信息:")
        print(f"  数据类型: {type(data)}")
        print(f"  数据形状: {data.shape}")
        print(f"  数据类型: {data.dtype}")
        print(f"  数据大小: {data.size} 个元素")
        print(f"  文件大小: {os.path.getsize(filepath)} 字节")
        
        # 数值统计
        print(f"\n📈 数值统计:")
        print(f"  最小值: {data.min():.8f}")
        print(f"  最大值: {data.max():.8f}")
        print(f"  平均值: {data.mean():.8f}")
        print(f"  标准差: {data.std():.8f}")
        print(f"  中位数: {np.median(data):.8f}")
        print(f"  变异系数: {data.std()/data.mean():.2%}")
        
        # 传感器阵列信息
        if len(data.shape) == 2:
            print(f"\n🔧 传感器阵列信息:")
            print(f"  行数: {data.shape[0]}")
            print(f"  列数: {data.shape[1]}")
            print(f"  总传感器数: {data.shape[0] * data.shape[1]}")
            
            if data.shape == (64, 64):
                print("  ✅ 这是标准的64x64传感器阵列数据")
            else:
                print(f"  ⚠️ 非标准阵列大小: {data.shape}")
        
        # 数据分布分析
        print(f"\n📊 数据分布分析:")
        
        # 计算有效数据（排除噪声）
        threshold = data.mean() * 0.1
        valid_data = data[data > threshold]
        noise_data = data[data <= threshold]
        
        print(f"  有效数据阈值: {threshold:.8f}")
        print(f"  有效数据点数: {len(valid_data)} ({len(valid_data)/data.size:.1%})")
        print(f"  噪声数据点数: {len(noise_data)} ({len(noise_data)/data.size:.1%})")
        
        if len(valid_data) > 0:
            print(f"  有效数据平均值: {valid_data.mean():.8f}")
            print(f"  有效数据标准差: {valid_data.std():.8f}")
            print(f"  有效数据变异系数: {valid_data.std()/valid_data.mean():.2%}")
        
        # 一致性分析
        if len(valid_data) > 0:
            print(f"\n🎯 一致性分析:")
            mean_response = valid_data.mean()
            low_response = np.sum(data < mean_response * 0.7)
            high_response = np.sum(data > mean_response * 1.3)
            normal_response = data.size - low_response - high_response
            
            print(f"  低响应区域 (<70%): {low_response} 点 ({low_response/data.size:.1%})")
            print(f"  正常响应区域: {normal_response} 点 ({normal_response/data.size:.1%})")
            print(f"  高响应区域 (>130%): {high_response} 点 ({high_response/data.size:.1%})")
        
        # 显示数据预览
        print(f"\n👀 数据预览 (左上角 8x8 区域):")
        if len(data.shape) == 2:
            print(data[:8, :8])
        else:
            print(data[:8])
        
        # 检查是否为校正映射
        if data.min() >= 0.2 and data.max() <= 5.0 and np.median(data) > 0.5:
            print(f"\n🔧 这可能是校正映射文件:")
            print(f"  校正系数范围: {data.min():.3f} - {data.max():.3f}")
            print(f"  平均校正系数: {data.mean():.3f}")
            print(f"  中位校正系数: {np.median(data):.3f}")
            
            # 分析校正强度
            strong_correction = np.sum((data < 0.5) | (data > 2.0))
            print(f"  强校正区域 (>2x 或 <0.5x): {strong_correction} 点 ({strong_correction/data.size:.1%})")
        else:
            print(f"\n📊 这是原始传感器数据:")
            print(f"  数据范围: {data.min():.8f} - {data.max():.8f}")
            print(f"  典型压力值范围: 10^-5 到 10^-4 量级")
        
        return data
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def main():
    """主函数"""
    # 分析指定的参考数据文件
    filepath = "consistency-test/参考数据-200帧.npy"
    
    if os.path.exists(filepath):
        data = analyze_specific_reference_data(filepath)
        
        if data is not None:
            print(f"\n💡 总结:")
            print(f"这个文件包含了一个64x64传感器阵列的参考数据，")
            print(f"数据范围在 {data.min():.8f} 到 {data.max():.8f} 之间，")
            print(f"平均值为 {data.mean():.8f}，变异系数为 {data.std()/data.mean():.2%}。")
            print(f"这应该是通过均匀物体压测收集的200帧数据的平均值，")
            print(f"用于生成传感器校正映射。")
    else:
        print(f"❌ 文件不存在: {filepath}")

if __name__ == "__main__":
    main() 