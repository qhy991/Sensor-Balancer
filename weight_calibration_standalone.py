#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的WeightCalibration类，不依赖PyQt5
"""

import numpy as np
from datetime import datetime

class WeightCalibration:
    """砝码校准类"""
    
    def __init__(self):
        self.weights = {}  # 存储砝码信息 {weight_id: {mass, unit, force}}
        self.measurements = {}  # 存储测量数据 {weight_id: [measurements]}
        self.calibration_results = {}  # 存储校准结果
        self.baseline_data = []  # 存储基线数据（无负载时的噪声）
        self.baseline_corrected = False  # 是否已进行基线校正
        
    def add_weight(self, weight_id, mass, unit='g'):
        """添加砝码"""
        # 单位转换
        if unit.lower() == 'g':
            force = mass * 0.0098  # 转换为牛顿
        elif unit.lower() == 'kg':
            force = mass * 9.8
        elif unit.lower() == 'n':
            force = mass
        else:
            force = mass * 0.0098  # 默认按克处理
        
        self.weights[weight_id] = {
            'mass': mass,
            'unit': unit,
            'force': force
        }
        self.measurements[weight_id] = []
        print(f"✅ 添加砝码: {weight_id}, 质量: {mass}{unit}, 力: {force:.4f}N")
    
    def record_baseline(self, pressure_data):
        """记录基线数据（无负载时的噪声）"""
        total_pressure = np.sum(pressure_data)
        mean_pressure = np.mean(pressure_data)
        max_pressure = np.max(pressure_data)
        
        self.baseline_data.append({
            'timestamp': datetime.now(),
            'total_pressure': total_pressure,
            'mean_pressure': mean_pressure,
            'max_pressure': max_pressure,
            'raw_data': pressure_data.copy()
        })
        
        print(f"📊 记录基线数据: 总压力={total_pressure:.6f}, 平均压力={mean_pressure:.6f}")
    
    def get_baseline_stats(self):
        """获取基线统计信息"""
        if not self.baseline_data:
            return None
        
        total_pressures = [d['total_pressure'] for d in self.baseline_data]
        mean_pressures = [d['mean_pressure'] for d in self.baseline_data]
        max_pressures = [d['max_pressure'] for d in self.baseline_data]
        
        return {
            'count': len(self.baseline_data),
            'avg_total_pressure': np.mean(total_pressures),
            'std_total_pressure': np.std(total_pressures),
            'avg_mean_pressure': np.mean(mean_pressures),
            'std_mean_pressure': np.std(mean_pressures),
            'avg_max_pressure': np.mean(max_pressures),
            'std_max_pressure': np.std(max_pressures),
            'cv_total': np.std(total_pressures) / np.mean(total_pressures) if np.mean(total_pressures) > 0 else 0
        }
    
    def clear_baseline(self):
        """清空基线数据"""
        self.baseline_data.clear()
        self.baseline_corrected = False
        print("🗑️ 基线数据已清空")
    
    def record_measurement(self, weight_id, pressure_data):
        """记录测量数据（支持基线校正）"""
        if weight_id not in self.weights:
            print(f"❌ 砝码 {weight_id} 不存在")
            return
        
        total_pressure = np.sum(pressure_data)
        mean_pressure = np.mean(pressure_data)
        max_pressure = np.max(pressure_data)
        
        # 基线校正
        corrected_total = total_pressure
        corrected_mean = mean_pressure
        corrected_max = max_pressure
        
        if self.baseline_data:
            baseline_stats = self.get_baseline_stats()
            corrected_total = total_pressure - baseline_stats['avg_total_pressure']
            corrected_mean = mean_pressure - baseline_stats['avg_mean_pressure']
            corrected_max = max_pressure - baseline_stats['avg_max_pressure']
            self.baseline_corrected = True
            
            # 添加调试信息
            print(f"🔍 基线校正: 原始={total_pressure:.6f}, 基线={baseline_stats['avg_total_pressure']:.6f}, 校正后={corrected_total:.6f}")
        else:
            print(f"⚠️ 无基线数据，跳过校正")
        
        measurement = {
            'timestamp': datetime.now(),
            'total_pressure': total_pressure,
            'mean_pressure': mean_pressure,
            'max_pressure': max_pressure,
            'corrected_total_pressure': corrected_total,
            'corrected_mean_pressure': corrected_mean,
            'corrected_max_pressure': corrected_max,
            'raw_data': pressure_data.copy()
        }
        
        self.measurements[weight_id].append(measurement)
        
        print(f"📊 记录测量: 砝码={weight_id}, 原始总压力={total_pressure:.6f}, 校正后总压力={corrected_total:.6f}")
    
    def calculate_sensitivity(self):
        """计算敏感性（支持基线校正）"""
        if not self.measurements:
            print("❌ 没有测量数据")
            return {}
        
        results = {}
        
        for weight_id, measurements in self.measurements.items():
            if not measurements:
                continue
            
            weight_info = self.weights[weight_id]
            force = weight_info['force']
            
            # 使用校正后的数据计算敏感性
            if self.baseline_corrected:
                total_pressures = [m['corrected_total_pressure'] for m in measurements]
                mean_pressures = [m['corrected_mean_pressure'] for m in measurements]
                max_pressures = [m['corrected_max_pressure'] for m in measurements]
            else:
                total_pressures = [m['total_pressure'] for m in measurements]
                mean_pressures = [m['mean_pressure'] for m in measurements]
                max_pressures = [m['max_pressure'] for m in measurements]
            
            # 计算统计信息
            avg_total_pressure = np.mean(total_pressures)
            std_total_pressure = np.std(total_pressures)
            avg_mean_pressure = np.mean(mean_pressures)
            std_mean_pressure = np.std(mean_pressures)
            avg_max_pressure = np.mean(max_pressures)
            std_max_pressure = np.std(max_pressures)
            
            # 计算敏感性
            sensitivity_total = avg_total_pressure / force if force > 0 else 0
            sensitivity_mean = avg_mean_pressure / force if force > 0 else 0
            sensitivity_max = avg_max_pressure / force if force > 0 else 0
            
            # 计算变异系数
            cv = std_total_pressure / avg_total_pressure if avg_total_pressure > 0 else 0
            
            results[weight_id] = {
                'weight_info': weight_info,
                'measurement_count': len(measurements),
                'avg_total_pressure': avg_total_pressure,
                'std_total_pressure': std_total_pressure,
                'avg_mean_pressure': avg_mean_pressure,
                'std_mean_pressure': std_mean_pressure,
                'avg_max_pressure': avg_max_pressure,
                'std_max_pressure': std_max_pressure,
                'sensitivity_total': sensitivity_total,
                'sensitivity_mean': sensitivity_mean,
                'sensitivity_max': sensitivity_max,
                'cv': cv,
                'baseline_corrected': self.baseline_corrected
            }
        
        self.calibration_results = results
        return results
    
    def get_overall_sensitivity(self):
        """获取整体敏感性统计"""
        if not self.calibration_results:
            return None
        
        sensitivities_total = [r['sensitivity_total'] for r in self.calibration_results.values()]
        sensitivities_mean = [r['sensitivity_mean'] for r in self.calibration_results.values()]
        sensitivities_max = [r['sensitivity_max'] for r in self.calibration_results.values()]
        
        # 计算统计信息
        avg_sensitivity_total = np.mean(sensitivities_total)
        std_sensitivity_total = np.std(sensitivities_total)
        cv_sensitivity_total = std_sensitivity_total / avg_sensitivity_total if avg_sensitivity_total > 0 else 0
        
        # 计算测量点数量和总测量次数
        measurement_points = len(self.calibration_results)
        total_measurements = sum(r['measurement_count'] for r in self.calibration_results.values())
        
        return {
            'avg_sensitivity_total': avg_sensitivity_total,
            'avg_sensitivity_mean': np.mean(sensitivities_mean),
            'avg_sensitivity_max': np.mean(sensitivities_max),
            'std_sensitivity_total': std_sensitivity_total,
            'std_sensitivity_mean': np.std(sensitivities_mean),
            'std_sensitivity_max': np.std(sensitivities_max),
            'cv_sensitivity_total': cv_sensitivity_total,
            'measurement_points': measurement_points,
            'total_measurements': total_measurements
        }

def test_weight_calibration():
    """测试WeightCalibration类"""
    print("🔍 测试WeightCalibration类...")
    
    try:
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
        
        print("\n🎉 WeightCalibration类测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始WeightCalibration类测试...")
    print("=" * 60)
    
    success = test_weight_calibration()
    
    if success:
        print("\n🎉 测试通过！WeightCalibration类功能正常。")
    else:
        print("\n❌ 测试失败。")
    
    print("=" * 60)
    print("测试完成。") 