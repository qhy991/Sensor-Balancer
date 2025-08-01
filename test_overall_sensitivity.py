#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试整体敏感性计算方法
"""

import sys
import os
import numpy as np

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_overall_sensitivity():
    """测试整体敏感性计算"""
    print("🔍 测试整体敏感性计算...")
    
    try:
        from sensor_sensitivity_calibration import WeightCalibration
        
        # 创建砝码校准实例
        calibration = WeightCalibration()
        
        # 添加测试砝码
        calibration.add_weight("1", 50.0, "g")
        calibration.add_weight("2", 100.0, "g")
        calibration.add_weight("3", 150.0, "g")
        
        # 添加测试测量数据
        test_data1 = np.random.rand(64, 64) * 0.01
        test_data2 = np.random.rand(64, 64) * 0.01
        test_data3 = np.random.rand(64, 64) * 0.01
        
        # 记录多次测量
        for i in range(5):
            calibration.record_measurement("1", test_data1 + np.random.rand(64, 64) * 0.001)
            calibration.record_measurement("2", test_data2 + np.random.rand(64, 64) * 0.001)
            calibration.record_measurement("3", test_data3 + np.random.rand(64, 64) * 0.001)
        
        # 计算敏感性
        results = calibration.calculate_sensitivity()
        print(f"✅ 敏感性计算成功，结果数量: {len(results)}")
        
        # 获取整体敏感性
        overall = calibration.get_overall_sensitivity()
        if overall:
            print("✅ 整体敏感性计算成功")
            print(f"平均敏感性(总): {overall['avg_sensitivity_total']:.6f}")
            print(f"敏感性标准差: {overall['std_sensitivity_total']:.6f}")
            print(f"敏感性变异系数: {overall['cv_sensitivity_total']:.3f}")
            print(f"测量点数量: {overall['measurement_points']}")
            print(f"总测量次数: {overall['total_measurements']}")
            
            # 检查所有必需的键是否存在
            required_keys = [
                'avg_sensitivity_total', 'avg_sensitivity_mean', 'avg_sensitivity_max',
                'std_sensitivity_total', 'std_sensitivity_mean', 'std_sensitivity_max',
                'cv_sensitivity_total', 'measurement_points', 'total_measurements'
            ]
            
            missing_keys = [key for key in required_keys if key not in overall]
            if missing_keys:
                print(f"❌ 缺少键: {missing_keys}")
                return False
            else:
                print("✅ 所有必需的键都存在")
                return True
        else:
            print("❌ 整体敏感性计算失败")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始整体敏感性计算测试...")
    print("=" * 50)
    
    success = test_overall_sensitivity()
    
    if success:
        print("\n🎉 测试通过！整体敏感性计算功能正常。")
    else:
        print("\n❌ 测试失败。")
    
    print("=" * 50)
    print("测试完成。") 