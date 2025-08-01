#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试默认砝码功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_default_weights():
    """测试默认砝码功能"""
    print("🔍 测试默认砝码功能...")
    
    try:
        from sensor_sensitivity_calibration import SensitivityCalibrationWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # 创建敏感性标定组件
        widget = SensitivityCalibrationWidget()
        print("✅ 敏感性标定组件创建成功")
        
        # 检查默认砝码是否加载
        weights = widget.weight_calibration.weights
        print(f"✅ 默认砝码数量: {len(weights)}")
        
        # 显示默认砝码信息
        print("默认砝码列表:")
        for weight_id, weight_info in weights.items():
            mass = weight_info['mass']
            unit = weight_info['unit']
            force = weight_info['force']
            print(f"  {weight_id}: {mass}{unit} (力: {force:.4f}N)")
        
        # 检查UI更新
        if hasattr(widget, 'weight_table'):
            row_count = widget.weight_table.rowCount()
            print(f"✅ 砝码表格行数: {row_count}")
            
            if row_count == len(weights):
                print("✅ 砝码表格更新正确")
            else:
                print("❌ 砝码表格更新异常")
        
        # 检查砝码选择下拉框
        if hasattr(widget, 'weight_select_combo'):
            item_count = widget.weight_select_combo.count()
            print(f"✅ 砝码选择下拉框项目数: {item_count}")
            
            if item_count == len(weights) + 1:  # +1 for "选择砝码"
                print("✅ 砝码选择下拉框更新正确")
            else:
                print("❌ 砝码选择下拉框更新异常")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_weight_management():
    """测试砝码管理功能"""
    print("\n🔍 测试砝码管理功能...")
    
    try:
        from sensor_sensitivity_calibration import SensitivityCalibrationWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # 创建敏感性标定组件
        widget = SensitivityCalibrationWidget()
        
        # 检查管理按钮是否存在
        if hasattr(widget, 'reset_default_btn'):
            print("✅ 重置默认砝码按钮存在")
        else:
            print("❌ 重置默认砝码按钮不存在")
        
        if hasattr(widget, 'custom_default_btn'):
            print("✅ 自定义默认砝码按钮存在")
        else:
            print("❌ 自定义默认砝码按钮不存在")
        
        # 检查方法是否存在
        if hasattr(widget, 'reset_default_weights'):
            print("✅ reset_default_weights方法存在")
        else:
            print("❌ reset_default_weights方法不存在")
        
        if hasattr(widget, 'customize_default_weights'):
            print("✅ customize_default_weights方法存在")
        else:
            print("❌ customize_default_weights方法不存在")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始默认砝码功能测试...")
    print("=" * 50)
    
    # 测试默认砝码功能
    default_ok = test_default_weights()
    
    # 测试砝码管理功能
    management_ok = test_weight_management()
    
    if default_ok and management_ok:
        print("\n🎉 所有测试通过！默认砝码功能正常。")
    else:
        print("\n❌ 部分测试失败。")
    
    print("=" * 50)
    print("测试完成。") 