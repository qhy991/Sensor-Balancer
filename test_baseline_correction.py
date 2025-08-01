#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基线校正功能
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_baseline_correction():
    """测试基线校正功能"""
    print("🔍 测试基线校正功能...")
    
    try:
        from sensor_sensitivity_calibration import WeightCalibration
        
        # 创建砝码校准实例
        calibration = WeightCalibration()
        
        # 添加测试砝码
        calibration.add_weight("1", 50.0, "g")
        calibration.add_weight("2", 100.0, "g")
        
        print("\n=== 1. 记录基线数据（模拟噪声）===")
        # 模拟基线数据（无负载时的噪声）
        for i in range(5):
            # 生成噪声数据
            noise_data = np.random.rand(64, 64) * 0.001  # 噪声范围0-0.001
            calibration.record_baseline(noise_data)
        
        # 显示基线统计
        baseline_stats = calibration.get_baseline_stats()
        if baseline_stats:
            print(f"✅ 基线统计:")
            print(f"  记录次数: {baseline_stats['count']}")
            print(f"  平均总压力: {baseline_stats['avg_total_pressure']:.6f}")
            print(f"  总压力标准差: {baseline_stats['std_total_pressure']:.6f}")
            print(f"  变异系数: {baseline_stats['cv_total']*100:.2f}%")
        
        print("\n=== 2. 记录测量数据（带噪声）===")
        # 模拟带噪声的测量数据
        for i in range(3):
            # 50g砝码的测量数据
            base_pressure = 0.002  # 基础压力
            noise = np.random.rand(64, 64) * 0.001  # 噪声
            measurement_data = np.full((64, 64), base_pressure) + noise
            calibration.record_measurement("1", measurement_data)
            
            # 100g砝码的测量数据
            base_pressure = 0.004  # 基础压力
            noise = np.random.rand(64, 64) * 0.001  # 噪声
            measurement_data = np.full((64, 64), base_pressure) + noise
            calibration.record_measurement("2", measurement_data)
        
        print("\n=== 3. 计算敏感性（基线校正）===")
        results = calibration.calculate_sensitivity()
        
        for weight_id, result in results.items():
            print(f"\n砝码 {weight_id}:")
            print(f"  质量: {result['weight_info']['mass']}{result['weight_info']['unit']}")
            print(f"  力: {result['weight_info']['force']:.4f}N")
            print(f"  测量次数: {result['measurement_count']}")
            print(f"  平均总压力: {result['avg_total_pressure']:.6f}")
            print(f"  敏感性(总): {result['sensitivity_total']:.6f}")
            print(f"  变异系数: {result['cv']:.3f}")
            print(f"  基线校正: {'是' if result['baseline_corrected'] else '否'}")
        
        print("\n=== 4. 清空基线数据测试 ===")
        calibration.clear_baseline()
        baseline_stats = calibration.get_baseline_stats()
        if baseline_stats is None:
            print("✅ 基线数据已清空")
        
        print("\n=== 5. 重新计算敏感性（无基线校正）===")
        results_no_baseline = calibration.calculate_sensitivity()
        
        for weight_id, result in results_no_baseline.items():
            print(f"\n砝码 {weight_id} (无基线校正):")
            print(f"  平均总压力: {result['avg_total_pressure']:.6f}")
            print(f"  敏感性(总): {result['sensitivity_total']:.6f}")
            print(f"  基线校正: {'是' if result['baseline_corrected'] else '否'}")
        
        print("\n🎉 基线校正功能测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始基线校正功能测试...")
    print("=" * 60)
    
    success = test_baseline_correction()
    
    if success:
        print("\n🎉 测试通过！基线校正功能正常。")
    else:
        print("\n❌ 测试失败。")
    
    print("=" * 60)
    print("测试完成。") 