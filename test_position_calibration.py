#!/usr/bin/env python3
"""
测试位置校准管理器功能
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from position_calibration_manager import PositionCalibrationManager

def test_position_calibration():
    """测试位置校准管理器"""
    print("🧪 测试位置校准管理器功能")
    print("=" * 50)
    
    # 初始化管理器
    calibration_file = 'position_calibration_data.json'
    manager = PositionCalibrationManager(calibration_file)
    
    # 测试1: 计算压力重心
    print("\n📄 测试1: 压力重心计算")
    
    # 创建模拟压力数据 - 中心位置
    center_pressure = np.zeros((64, 64))
    center_x, center_y = 32, 32
    for i in range(64):
        for j in range(64):
            distance = np.sqrt((i - center_y)**2 + (j - center_x)**2)
            if distance < 10:
                center_pressure[i, j] = 1.0 * np.exp(-distance / 5)
    
    pressure_center = manager.calculate_pressure_center(center_pressure)
    print(f"✅ 中心压力重心: {pressure_center}")
    
    # 创建模拟压力数据 - 左上角位置
    top_left_pressure = np.zeros((64, 64))
    for i in range(64):
        for j in range(64):
            distance = np.sqrt((i - 16)**2 + (j - 16)**2)
            if distance < 8:
                top_left_pressure[i, j] = 1.0 * np.exp(-distance / 4)
    
    pressure_center_tl = manager.calculate_pressure_center(top_left_pressure)
    print(f"✅ 左上角压力重心: {pressure_center_tl}")
    
    # 测试2: 距离计算
    print("\n📄 测试2: 距离计算")
    point1 = (32, 32)
    point2 = (16, 16)
    
    euclidean_dist = manager.calculate_distance(point1, point2, 'euclidean')
    manhattan_dist = manager.calculate_distance(point1, point2, 'manhattan')
    chebyshev_dist = manager.calculate_distance(point1, point2, 'chebyshev')
    
    print(f"✅ 欧几里得距离: {euclidean_dist:.2f}")
    print(f"✅ 曼哈顿距离: {manhattan_dist:.2f}")
    print(f"✅ 切比雪夫距离: {chebyshev_dist:.2f}")
    
    # 测试3: 最近位置查找
    print("\n📄 测试3: 最近位置查找")
    
    # 测试中心位置
    nearest_id, nearest_info, distance = manager.find_nearest_position(pressure_center)
    print(f"✅ 中心压力 -> 最近位置: {nearest_id} (距离: {distance:.2f})")
    
    # 测试左上角位置
    nearest_id_tl, nearest_info_tl, distance_tl = manager.find_nearest_position(pressure_center_tl)
    print(f"✅ 左上角压力 -> 最近位置: {nearest_id_tl} (距离: {distance_tl:.2f})")
    
    # 测试4: 校准参数获取
    print("\n📄 测试4: 校准参数获取")
    
    cal_params_center = manager.get_calibration_parameters(center_pressure)
    print(f"✅ 中心位置校准参数:")
    print(f"   位置: {cal_params_center['position_name']}")
    print(f"   斜率: {cal_params_center['slope']:.4f}")
    print(f"   截距: {cal_params_center['intercept']:.4f}")
    print(f"   距离: {cal_params_center['distance']:.2f}")
    print(f"   R²: {cal_params_center['r_squared']:.4f}")
    
    cal_params_tl = manager.get_calibration_parameters(top_left_pressure)
    print(f"✅ 左上角位置校准参数:")
    print(f"   位置: {cal_params_tl['position_name']}")
    print(f"   斜率: {cal_params_tl['slope']:.4f}")
    print(f"   截距: {cal_params_tl['intercept']:.4f}")
    print(f"   距离: {cal_params_tl['distance']:.2f}")
    print(f"   R²: {cal_params_tl['r_squared']:.4f}")
    
    # 测试5: 重量计算
    print("\n📄 测试5: 重量计算")
    
    # 模拟不同重量的压力数据
    test_weights = [100, 200, 500, 1000]  # 克
    
    for target_weight in test_weights:
        # 使用中心位置的校准参数反向计算压力
        center_slope = manager.get_position_info('center')['calibration']['slope']
        center_intercept = manager.get_position_info('center')['calibration']['intercept']
        
        # 反向计算：压力 = (重量 - 截距) / 斜率
        target_pressure = (target_weight - center_intercept) / center_slope
        
        # 创建对应的压力数据
        test_pressure = center_pressure * target_pressure / np.sum(center_pressure)
        
        # 计算重量
        result = manager.calculate_weight(test_pressure, zero_pressure=0.0)
        
        print(f"✅ 目标重量: {target_weight}g -> 计算重量: {result['weight']:.2f}g")
        print(f"   使用位置: {result['calibration_params']['position_name']}")
        print(f"   距离: {result['calibration_params']['distance']:.2f}")
        print(f"   误差: {abs(result['weight'] - target_weight):.2f}g")
    
    # 测试6: 校准数据摘要
    print("\n📄 测试6: 校准数据摘要")
    summary = manager.get_calibration_summary()
    print(f"✅ 总位置数: {summary['total_positions']}")
    
    for position_id, info in summary['positions'].items():
        print(f"   {info['name']}: 斜率={info['slope']:.2f}, R²={info['r_squared']:.4f}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_position_calibration() 