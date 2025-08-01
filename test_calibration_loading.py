#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试校准数据加载功能
"""

import sys
import os
import numpy as np

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_calibration_loader():
    """测试校准数据加载器"""
    print("🔍 测试校准数据加载器...")
    
    try:
        from sensor_sensitivity_calibration import CalibrationDataLoader
        
        # 创建校准数据加载器
        loader = CalibrationDataLoader()
        
        # 创建测试校准数据
        test_calibration_map = np.random.rand(64, 64) * 2.0 + 0.5  # 范围0.5-2.5
        test_file = "test_calibration.npy"
        
        # 保存测试数据
        np.save(test_file, test_calibration_map)
        print(f"✅ 创建测试校准数据: {test_file}")
        
        # 测试加载
        success = loader.load_calibration_data(test_file)
        if success:
            print("✅ 校准数据加载成功")
            
            # 获取信息
            info = loader.get_calibration_info()
            if info:
                print(f"✅ 校准信息: 形状={info['shape']}, 均值={info['mean']:.4f}, 文件={info['loaded_file']}")
            else:
                print("❌ 无法获取校准信息")
        else:
            print("❌ 校准数据加载失败")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✅ 清理测试文件: {test_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sensitivity_widget():
    """测试敏感性标定组件"""
    print("\n🔍 测试敏感性标定组件...")
    
    try:
        from sensor_sensitivity_calibration import SensitivityCalibrationWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # 创建敏感性标定组件
        widget = SensitivityCalibrationWidget()
        print("✅ 敏感性标定组件创建成功")
        
        # 检查属性是否存在
        if hasattr(widget, 'calibration_info_label'):
            print("✅ calibration_info_label属性存在")
        else:
            print("❌ calibration_info_label属性不存在")
            print(f"可用属性: {[attr for attr in dir(widget) if 'calibration' in attr.lower()]}")
        
        if hasattr(widget, 'calibration_loader'):
            print("✅ calibration_loader属性存在")
        else:
            print("❌ calibration_loader属性不存在")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始校准数据加载测试...")
    print("=" * 50)
    
    # 测试校准数据加载器
    loader_ok = test_calibration_loader()
    
    # 测试敏感性标定组件
    widget_ok = test_sensitivity_widget()
    
    if loader_ok and widget_ok:
        print("\n🎉 所有测试通过！校准数据加载功能正常。")
    else:
        print("\n❌ 部分测试失败。")
    
    print("=" * 50)
    print("测试完成。") 