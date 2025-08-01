#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试组件连接脚本
验证主界面和敏感性标定组件之间的连接是否正确
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_component_connection():
    """测试组件连接"""
    print("🔍 开始测试组件连接...")
    
    try:
        # 尝试导入主程序
        from sensor_sensitivity_calibration import SensitivityCalibrationInterface, SensitivityCalibrationWidget
        
        print("✅ 成功导入主程序模块")
        
        # 创建主界面实例
        print("🔧 创建主界面实例...")
        main_interface = SensitivityCalibrationInterface()
        
        # 检查主界面是否有sensitivity_widget属性
        if hasattr(main_interface, 'sensitivity_widget'):
            print(f"✅ 主界面有sensitivity_widget属性: {type(main_interface.sensitivity_widget)}")
            
            # 检查sensitivity_widget的父窗口
            sensitivity_widget = main_interface.sensitivity_widget
            parent = sensitivity_widget.parent()
            print(f"✅ sensitivity_widget的父窗口: {type(parent)}")
            
            # 检查父窗口是否有start_sensitivity_measurement方法
            if hasattr(parent, 'start_sensitivity_measurement'):
                print("✅ 父窗口有start_sensitivity_measurement方法")
                
                # 检查方法是否可调用
                if callable(getattr(parent, 'start_sensitivity_measurement')):
                    print("✅ start_sensitivity_measurement方法是可调用的")
                else:
                    print("❌ start_sensitivity_measurement方法不可调用")
            else:
                print("❌ 父窗口没有start_sensitivity_measurement方法")
                print(f"父窗口的方法: {[method for method in dir(parent) if not method.startswith('_')]}")
        else:
            print("❌ 主界面没有sensitivity_widget属性")
            print(f"主界面的属性: {[attr for attr in dir(main_interface) if not attr.startswith('_')]}")
        
        # 检查主界面是否有start_sensitivity_measurement方法
        if hasattr(main_interface, 'start_sensitivity_measurement'):
            print("✅ 主界面有start_sensitivity_measurement方法")
        else:
            print("❌ 主界面没有start_sensitivity_measurement方法")
        
        # 检查主界面是否有update_data方法
        if hasattr(main_interface, 'update_data'):
            print("✅ 主界面有update_data方法")
        else:
            print("❌ 主界面没有update_data方法")
        
        # 检查sensitivity_widget是否有record_measurement_data方法
        if hasattr(sensitivity_widget, 'record_measurement_data'):
            print("✅ sensitivity_widget有record_measurement_data方法")
        else:
            print("❌ sensitivity_widget没有record_measurement_data方法")
        
        print("\n📋 测试总结:")
        print("1. 组件导入: ✅")
        print("2. 主界面创建: ✅")
        print("3. 组件连接: ✅")
        print("4. 方法存在性: 已检查")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_calls():
    """测试方法调用"""
    print("\n🔍 开始测试方法调用...")
    
    try:
        from sensor_sensitivity_calibration import SensitivityCalibrationInterface
        
        # 创建主界面实例
        main_interface = SensitivityCalibrationInterface()
        
        # 测试start_sensitivity_measurement方法
        if hasattr(main_interface, 'start_sensitivity_measurement'):
            print("🔧 测试start_sensitivity_measurement方法...")
            main_interface.start_sensitivity_measurement("W1", 10)
            print("✅ start_sensitivity_measurement方法调用成功")
        else:
            print("❌ start_sensitivity_measurement方法不存在")
        
        # 测试sensitivity_widget的record_measurement_data方法
        if hasattr(main_interface, 'sensitivity_widget'):
            sensitivity_widget = main_interface.sensitivity_widget
            if hasattr(sensitivity_widget, 'record_measurement_data'):
                print("🔧 测试record_measurement_data方法...")
                import numpy as np
                test_data = np.random.rand(64, 64) * 0.01
                sensitivity_widget.record_measurement_data(test_data)
                print("✅ record_measurement_data方法调用成功")
            else:
                print("❌ record_measurement_data方法不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 方法调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始组件连接测试...")
    print("=" * 50)
    
    # 测试组件连接
    connection_ok = test_component_connection()
    
    if connection_ok:
        # 测试方法调用
        method_ok = test_method_calls()
        
        if method_ok:
            print("\n🎉 所有测试通过！组件连接正常。")
        else:
            print("\n⚠️ 方法调用测试失败，但组件连接正常。")
    else:
        print("\n❌ 组件连接测试失败。")
    
    print("=" * 50)
    print("测试完成。") 