#!/usr/bin/env python3
"""
测试校准映射功能
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weight_measurement_tool import CalibrationDataLoader

def test_calibration_mapping():
    """测试校准映射功能"""
    print("🧪 测试校准映射功能")
    print("=" * 50)
    
    # 创建测试数据
    print("\n📄 创建测试数据:")
    
    # 创建64x64的校准映射（模拟传感器校正数据）
    calibration_map = np.random.rand(64, 64) * 0.5 + 0.5  # 范围在0.5-1.0之间
    print(f"✅ 创建64x64校准映射")
    print(f"  映射统计: 均值={np.mean(calibration_map):.6f}, 标准差={np.std(calibration_map):.6f}")
    print(f"  映射范围: [{np.min(calibration_map):.6f}, {np.max(calibration_map):.6f}]")
    
    # 创建原始传感器数据（模拟有问题的传感器）
    raw_data = np.random.rand(64, 64) * 0.01
    # 模拟一些传感器响应不一致
    raw_data[20:30, 20:30] *= 1.5  # 某些区域响应过强
    raw_data[40:50, 40:50] *= 0.7  # 某些区域响应过弱
    
    print(f"✅ 创建原始传感器数据")
    print(f"  原始数据统计: 均值={np.mean(raw_data):.6f}, 标准差={np.std(raw_data):.6f}")
    print(f"  原始数据范围: [{np.min(raw_data):.6f}, {np.max(raw_data):.6f}]")
    
    # 保存校准映射
    map_filename = 'test_calibration_map.npy'
    np.save(map_filename, calibration_map)
    print(f"✅ 保存校准映射到: {map_filename}")
    
    # 测试校准数据加载器
    print("\n📄 测试校准数据加载:")
    loader = CalibrationDataLoader()
    if loader.load_calibration_data(map_filename):
        print("✅ 校准映射加载成功")
        
        # 获取校准映射信息
        map_info = loader.get_calibration_map_info()
        if map_info:
            print(f"✅ 校准映射信息:")
            print(f"  形状: {map_info['shape']}")
            print(f"  平均值: {map_info['mean']:.6f}")
            print(f"  标准差: {map_info['std']:.6f}")
            print(f"  变异系数: {map_info['cv']:.6f}")
        
        # 测试应用校准映射
        print("\n📄 测试应用校准映射:")
        calibrated_data = loader.apply_calibration_map(raw_data)
        
        print(f"✅ 校准后数据统计:")
        print(f"  校准后均值: {np.mean(calibrated_data):.6f}")
        print(f"  校准后标准差: {np.std(calibrated_data):.6f}")
        print(f"  校准后范围: [{np.min(calibrated_data):.6f}, {np.max(calibrated_data):.6f}]")
        
        # 计算压力总和对比
        raw_pressure_sum = np.sum(raw_data)
        calibrated_pressure_sum = np.sum(calibrated_data)
        
        print(f"\n📊 压力总和对比:")
        print(f"  原始压力总和: {raw_pressure_sum:.6f} N")
        print(f"  校准后压力总和: {calibrated_pressure_sum:.6f} N")
        print(f"  校正比例: {calibrated_pressure_sum/raw_pressure_sum:.6f}")
        
        # 测试形状不匹配的情况
        print("\n📄 测试形状不匹配:")
        wrong_shape_data = np.random.rand(32, 32) * 0.01
        result = loader.apply_calibration_map(wrong_shape_data)
        if result is wrong_shape_data:
            print("✅ 形状不匹配时正确返回原始数据")
        else:
            print("❌ 形状不匹配处理错误")
        
    else:
        print("❌ 校准映射加载失败")
    
    # 清理测试文件
    print("\n🧹 清理测试文件:")
    if os.path.exists(map_filename):
        os.remove(map_filename)
        print(f"✅ 删除: {map_filename}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_calibration_mapping() 