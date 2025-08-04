#!/usr/bin/env python3
"""
分析参考数据文件格式的脚本
"""

import numpy as np
import json
import os

def analyze_reference_data_file(filepath):
    """分析参考数据文件"""
    print(f"=== 分析文件: {filepath} ===")
    
    try:
        # 加载数据
        data = np.load(filepath)
        
        print(f"数据类型: {type(data)}")
        print(f"数据形状: {data.shape}")
        print(f"数据类型: {data.dtype}")
        print(f"数据大小: {data.size}")
        print(f"文件大小: {os.path.getsize(filepath)} 字节")
        
        # 数值统计
        print(f"\n数值统计:")
        print(f"最小值: {data.min():.6f}")
        print(f"最大值: {data.max():.6f}")
        print(f"平均值: {data.mean():.6f}")
        print(f"标准差: {data.std():.6f}")
        print(f"中位数: {np.median(data):.6f}")
        
        # 检查是否为2D数组（传感器阵列）
        if len(data.shape) == 2:
            print(f"\n传感器阵列信息:")
            print(f"行数: {data.shape[0]}")
            print(f"列数: {data.shape[1]}")
            
            # 检查是否为64x64阵列
            if data.shape == (64, 64):
                print("✅ 这是标准的64x64传感器阵列数据")
            else:
                print(f"⚠️ 非标准阵列大小: {data.shape}")
        
        # 显示部分数据
        print(f"\n数据预览 (左上角 8x8 区域):")
        if len(data.shape) == 2:
            print(data[:8, :8])
        else:
            print(data[:8])
            
        return data
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def analyze_json_reference_data(filepath):
    """分析JSON格式的参考数据"""
    print(f"=== 分析JSON文件: {filepath} ===")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"数据类型: {type(data)}")
        
        if isinstance(data, dict):
            print(f"字典键: {list(data.keys())}")
            
            # 检查是否包含参考数据
            if 'reference_data' in data:
                ref_data = np.array(data['reference_data'])
                print(f"参考数据形状: {ref_data.shape}")
                print(f"参考数据类型: {ref_data.dtype}")
                
                # 数值统计
                print(f"\n参考数据统计:")
                print(f"最小值: {ref_data.min():.6f}")
                print(f"最大值: {ref_data.max():.6f}")
                print(f"平均值: {ref_data.mean():.6f}")
                print(f"标准差: {ref_data.std():.6f}")
            
            # 显示元数据
            for key, value in data.items():
                if key != 'reference_data':
                    print(f"{key}: {value}")
        
        return data
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def main():
    """主函数"""
    print("🔍 参考数据格式分析")
    print("=" * 50)
    
    # 分析NPY文件
    npy_files = [
        "consistency-test/参考数据-500帧.npy",
        "consistency-test/参考数据-300帧.npy", 
        "consistency-test/参考数据-200帧.npy",
        "consistency-test/校正数据-200帧.npy"
    ]
    
    for filepath in npy_files:
        if os.path.exists(filepath):
            analyze_reference_data_file(filepath)
            print("\n" + "-" * 50 + "\n")
    
    # 分析JSON文件
    json_files = [
        "consistency-test/0731-1.json",
        "consistency-test/0731-2.json"
    ]
    
    for filepath in json_files:
        if os.path.exists(filepath):
            analyze_json_reference_data(filepath)
            print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main() 