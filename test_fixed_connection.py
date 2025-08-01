#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的组件连接
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parent_connection():
    """测试父窗口连接修复"""
    print("🔍 测试父窗口连接修复...")
    
    try:
        from sensor_sensitivity_calibration import SensitivityCalibrationWidget
        
        # 创建一个模拟的标签页结构
        from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget
        
        app = QApplication(sys.argv)
        
        # 创建主界面（模拟）
        class MockMainInterface(QWidget):
            def __init__(self):
                super().__init__()
                self.is_running = True
                
            def start_sensitivity_measurement(self, weight_id, count):
                print(f"✅ 主界面收到测量请求: {weight_id}, {count}")
                
            def set_calibration_data(self, calibration_map):
                print(f"✅ 主界面收到校准数据: {calibration_map.shape if calibration_map is not None else 'None'}")
        
        # 创建标签页控件
        tab_widget = QTabWidget()
        main_interface = MockMainInterface()
        
        # 创建敏感性标定组件
        sensitivity_widget = SensitivityCalibrationWidget()
        
        # 模拟标签页结构
        tab_widget.addTab(sensitivity_widget, "敏感性标定")
        main_interface.layout = tab_widget
        
        # 测试父窗口查找
        parent = sensitivity_widget.parent()
        print(f"直接父窗口: {type(parent)}")
        
        if parent and hasattr(parent, 'parent'):
            tab_widget_parent = parent.parent()
            print(f"标签页父窗口: {type(tab_widget_parent)}")
            
            if tab_widget_parent and hasattr(tab_widget_parent, 'parent'):
                main_interface_found = tab_widget_parent.parent()
                print(f"找到的主界面: {type(main_interface_found)}")
                
                if main_interface_found and hasattr(main_interface_found, 'start_sensitivity_measurement'):
                    print("✅ 成功找到主界面的start_sensitivity_measurement方法")
                    main_interface_found.start_sensitivity_measurement("W1", 10)
                else:
                    print("❌ 未找到主界面的start_sensitivity_measurement方法")
            else:
                print("❌ 无法找到标签页的父窗口")
        else:
            print("❌ 无法找到敏感性组件的父窗口")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 测试修复后的组件连接...")
    print("=" * 50)
    
    success = test_parent_connection()
    
    if success:
        print("\n🎉 测试通过！父窗口连接修复成功。")
    else:
        print("\n❌ 测试失败。")
    
    print("=" * 50)
    print("测试完成。") 