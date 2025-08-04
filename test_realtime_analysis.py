#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实时校正数据分析功能
"""

import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from weight_measurement_tool import WeightMeasurementInterface, CalibrationAnalysisDialog

class TestRealtimeAnalysis:
    """测试实时校正数据分析"""
    
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
        # 创建主窗口
        self.main_window = WeightMeasurementInterface()
        self.main_window.show()
        
        # 创建测试数据
        self.test_data = np.random.rand(64, 64) * 0.1
        
        # 设置定时器来模拟数据更新
        self.data_timer = QtCore.QTimer()
        self.data_timer.timeout.connect(self.update_test_data)
        self.data_timer.start(1000)  # 每秒更新一次
        
        print("✅ 测试环境已启动")
        print("📋 使用说明:")
        print("1. 点击'连接传感器'按钮启动模拟数据")
        print("2. 点击'校正数据分析'按钮打开分析窗口")
        print("3. 观察分析窗口是否实时更新")
        print("4. 使用'暂停更新'按钮测试暂停功能")
    
    def update_test_data(self):
        """更新测试数据"""
        try:
            # 生成新的测试数据
            self.test_data = np.random.rand(64, 64) * 0.1
            
            # 模拟一个移动的压力点
            import time
            t = time.time()
            center_x = 32 + 10 * np.sin(t * 0.5)
            center_y = 32 + 10 * np.cos(t * 0.3)
            
            for i in range(64):
                for j in range(64):
                    distance = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if distance < 8:
                        weight = 1.0 + 0.5 * np.sin(t)
                        self.test_data[i, j] += weight * np.exp(-distance / 4)
            
            # 更新主窗口的数据
            if hasattr(self.main_window, 'current_raw_data'):
                self.main_window.current_raw_data = self.test_data.copy()
                self.main_window.current_calibrated_data = self.test_data.copy() * 1.1  # 模拟校正效果
                
                # 更新压力显示
                pressure_sum = np.sum(self.test_data)
                if hasattr(self.main_window, 'total_pressure_label'):
                    self.main_window.total_pressure_label.setText(f"总压力: {pressure_sum:.4f} N")
                
                print(f"📊 数据已更新 - 总压力: {pressure_sum:.4f} N")
                
        except Exception as e:
            print(f"⚠️ 更新测试数据失败: {e}")
    
    def run(self):
        """运行测试"""
        try:
            sys.exit(self.app.exec_())
        except KeyboardInterrupt:
            print("\n🛑 测试被用户中断")
        except Exception as e:
            print(f"❌ 测试运行失败: {e}")

def main():
    """主函数"""
    print("🚀 启动实时校正数据分析测试")
    test = TestRealtimeAnalysis()
    test.run()

if __name__ == "__main__":
    main() 