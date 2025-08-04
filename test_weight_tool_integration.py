#!/usr/bin/env python3
"""
测试位置校准管理器与称重工具的集成
"""

import sys
import os
import numpy as np

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_integration():
    """测试集成功能"""
    print("🧪 测试位置校准管理器与称重工具集成")
    print("=" * 50)
    
    # 测试1: 导入模块
    print("\n📄 测试1: 模块导入")
    try:
        from position_calibration_manager import PositionCalibrationManager
        print("✅ 位置校准管理器导入成功")
    except ImportError as e:
        print(f"❌ 位置校准管理器导入失败: {e}")
        return
    
    try:
        # 测试2: 初始化管理器
        print("\n📄 测试2: 初始化位置校准管理器")
        manager = PositionCalibrationManager('position_calibration_data.json')
        print(f"✅ 位置校准管理器初始化成功，包含 {len(manager.position_data)} 个位置")
        
        # 测试3: 创建模拟压力数据
        print("\n📄 测试3: 模拟压力数据")
        
        # 中心位置压力数据
        center_pressure = np.zeros((64, 64))
        center_x, center_y = 32, 32
        for i in range(64):
            for j in range(64):
                distance = np.sqrt((i - center_y)**2 + (j - center_x)**2)
                if distance < 10:
                    center_pressure[i, j] = 1.0 * np.exp(-distance / 5)
        
        print(f"✅ 中心位置压力数据创建成功，总压力: {np.sum(center_pressure):.4f}")
        
        # 测试4: 计算重量
        print("\n📄 测试4: 重量计算")
        result = manager.calculate_weight(center_pressure, zero_pressure=0.0)
        
        print(f"✅ 计算重量: {result['weight']:.2f}g")
        print(f"   总压力: {result['total_pressure']:.4f}N")
        print(f"   净压力: {result['net_pressure']:.4f}N")
        print(f"   使用位置: {result['calibration_params']['position_name']}")
        print(f"   距离: {result['calibration_params']['distance']:.2f}")
        print(f"   R²: {result['calibration_params']['r_squared']:.4f}")
        
        # 测试5: 不同位置的重量计算
        print("\n📄 测试5: 不同位置的重量计算")
        
        # 左上角位置压力数据
        top_left_pressure = np.zeros((64, 64))
        for i in range(64):
            for j in range(64):
                distance = np.sqrt((i - 16)**2 + (j - 16)**2)
                if distance < 8:
                    top_left_pressure[i, j] = 1.0 * np.exp(-distance / 4)
        
        result_tl = manager.calculate_weight(top_left_pressure, zero_pressure=0.0)
        print(f"✅ 左上角位置重量: {result_tl['weight']:.2f}g")
        print(f"   使用位置: {result_tl['calibration_params']['position_name']}")
        print(f"   距离: {result_tl['calibration_params']['distance']:.2f}")
        
        # 测试6: 校准数据摘要
        print("\n📄 测试6: 校准数据摘要")
        summary = manager.get_calibration_summary()
        print(f"✅ 总位置数: {summary['total_positions']}")
        
        for position_id, info in summary['positions'].items():
            print(f"   {info['name']}: 斜率={info['slope']:.2f}, R²={info['r_squared']:.4f}")
        
        print("\n🎉 集成测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration() 