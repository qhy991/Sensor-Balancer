#!/usr/bin/env python3
"""
测试校准数据加载器功能
"""

import sys
import os
import numpy as np
import json
import csv
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weight_measurement_tool import CalibrationDataLoader

def test_calibration_loader():
    """测试校准数据加载器"""
    print("🧪 测试校准数据加载器功能")
    print("=" * 50)
    
    # 创建测试数据
    test_coefficient = 1730.6905
    test_bias = 126.1741
    test_zero_pressure = 100.0
    test_is_zeroed = True
    
    # 测试JSON格式
    print("\n📄 测试JSON格式:")
    json_data = {
        'timestamp': datetime.now().isoformat(),
        'coefficient': test_coefficient,
        'bias': test_bias,
        'zero_pressure': test_zero_pressure,
        'is_zeroed': test_is_zeroed,
        'description': '测试校准数据'
    }
    
    json_filename = 'test_calibration.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    loader = CalibrationDataLoader()
    if loader.load_calibration_data(json_filename):
        info = loader.get_calibration_info()
        print(f"✅ JSON加载成功: {info}")
    else:
        print("❌ JSON加载失败")
    
    # 测试CSV格式
    print("\n📄 测试CSV格式:")
    csv_filename = 'test_calibration.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:  # 使用utf-8编码
        writer = csv.writer(f)
        writer.writerow(['参数', '数值', '单位', '说明'])
        writer.writerow(['coefficient', f'{test_coefficient:.6f}', '', '校准系数'])
        writer.writerow(['bias', f'{test_bias:.6f}', 'g', '校准偏置'])
        writer.writerow(['zero_pressure', f'{test_zero_pressure:.6f}', 'N', '归零压力'])
        writer.writerow(['is_zeroed', '1' if test_is_zeroed else '0', '', '是否已归零'])
    
    loader2 = CalibrationDataLoader()
    if loader2.load_calibration_data(csv_filename):
        info = loader2.get_calibration_info()
        print(f"✅ CSV加载成功: {info}")
    else:
        print("❌ CSV加载失败")
    
    # 测试NumPy格式
    print("\n📄 测试NumPy格式:")
    numpy_data = {
        'coefficient': test_coefficient,
        'bias': test_bias,
        'zero_pressure': test_zero_pressure,
        'is_zeroed': test_is_zeroed,
        'timestamp': datetime.now().isoformat(),
        'description': 'NumPy测试校准数据'
    }
    
    numpy_filename = 'test_calibration.npy'
    np.save(numpy_filename, numpy_data)
    
    loader3 = CalibrationDataLoader()
    if loader3.load_calibration_data(numpy_filename):
        info = loader3.get_calibration_info()
        print(f"✅ NumPy加载成功: {info}")
    else:
        print("❌ NumPy加载失败")
    
    # 测试校准映射格式
    print("\n📄 测试校准映射格式:")
    calibration_map = np.random.rand(64, 64) * 0.1
    map_data = {
        'calibration_map': calibration_map,
        'coefficient': test_coefficient,
        'bias': test_bias,
        'zero_pressure': test_zero_pressure,
        'is_zeroed': test_is_zeroed,
        'timestamp': datetime.now().isoformat(),
        'description': '校准映射测试数据'
    }
    
    map_filename = 'test_calibration_map.json'
    with open(map_filename, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, ensure_ascii=False, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
    
    loader4 = CalibrationDataLoader()
    if loader4.load_calibration_data(map_filename):
        info = loader4.get_calibration_info()
        print(f"✅ 校准映射加载成功: {info}")
    else:
        print("❌ 校准映射加载失败")
    
    # 清理测试文件
    print("\n🧹 清理测试文件:")
    test_files = [json_filename, csv_filename, numpy_filename, map_filename]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ 删除: {file}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_calibration_loader() 