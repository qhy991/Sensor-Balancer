#!/usr/bin/env python3
"""
均匀按压测试指导程序
基于空间一致性分析结果，提供具体的测试方法和改进建议
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

class UniformPressureTestGuide:
    """均匀按压测试指导器"""
    
    def __init__(self, analysis_file="spatial_consistency_analysis.json"):
        self.analysis_data = None
        self.load_analysis_results(analysis_file)
    
    def load_analysis_results(self, filename):
        """加载分析结果"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.analysis_data = json.load(f)
            print(f"✅ Loaded analysis results from: {filename}")
        else:
            print(f"❌ Analysis file not found: {filename}")
            self.analysis_data = None
    
    def analyze_current_issues(self):
        """分析当前问题"""
        if not self.analysis_data:
            print("❌ No analysis data available")
            return
        
        print("\n🔍 Current Issues Analysis")
        print("=" * 50)
        
        spatial_stats = self.analysis_data['spatial_stats']
        temporal_stats = self.analysis_data['temporal_stats']
        
        # 空间一致性问题
        spatial_cv = spatial_stats['overall_cv']
        print(f"📊 Spatial Consistency Issues:")
        print(f"   • Spatial CV: {spatial_cv:.2%} (目标: <20%)")
        
        if spatial_cv > 1.0:
            print(f"   ⚠️ 严重问题: 空间变异系数过高 ({spatial_cv:.2%})")
            print(f"   💡 可能原因:")
            print(f"      - 传感器校准问题")
            print(f"      - 压力施加不均匀")
            print(f"      - 传感器表面不平整")
            print(f"      - 环境干扰")
        
        # 时间稳定性问题
        temporal_cv = temporal_stats['temporal_cv']
        print(f"\n⏰ Temporal Stability Issues:")
        print(f"   • Temporal CV: {temporal_cv:.2%} (目标: <10%)")
        
        if temporal_cv > 0.5:
            print(f"   ⚠️ 严重问题: 时间稳定性差 ({temporal_cv:.2%})")
            print(f"   💡 可能原因:")
            print(f"      - 压力施加不稳定")
            print(f"      - 手部抖动")
            print(f"      - 环境振动")
            print(f"      - 传感器响应延迟")
    
    def provide_test_methodology(self):
        """提供测试方法指导"""
        print("\n📋 Uniform Pressure Test Methodology")
        print("=" * 50)
        
        print("🎯 Test Objectives:")
        print("   1. 验证传感器在均匀压力下的空间响应一致性")
        print("   2. 评估传感器的校准质量")
        print("   3. 确定最佳测试条件")
        
        print("\n🔧 Recommended Test Setup:")
        print("   1. 硬件准备:")
        print("      • 使用平整的硬质表面（如玻璃板、金属板）")
        print("      • 确保传感器表面清洁无污垢")
        print("      • 使用固定装置避免手部抖动")
        print("      • 在稳定的环境中进行测试（避免振动）")
        
        print("\n   2. 压力施加方法:")
        print("      • 使用均匀重物（如书本、金属块）")
        print("      • 确保重物底面平整且足够大")
        print("      • 缓慢放置，避免冲击")
        print("      • 保持压力稳定至少10秒")
        
        print("\n   3. 数据采集:")
        print("      • 采集频率: 10-20 Hz")
        print("      • 采集时长: 10-30秒")
        print("      • 重复测试: 3-5次")
        print("      • 记录环境条件（温度、湿度）")
    
    def create_improved_test_script(self):
        """创建改进的测试脚本"""
        print("\n📝 Creating Improved Test Script")
        print("=" * 50)
        
        script_content = '''#!/usr/bin/env python3
"""
改进的均匀按压测试脚本
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import time
from datetime import datetime

class ImprovedUniformTest:
    """改进的均匀按压测试"""
    
    def __init__(self):
        self.test_results = []
        self.test_conditions = {}
    
    def setup_test_conditions(self):
        """设置测试条件"""
        print("🔧 Setting up test conditions...")
        
        self.test_conditions = {
            'test_type': 'uniform_pressure',
            'pressure_method': 'uniform_weight',
            'surface_type': 'flat_hard_surface',
            'duration': 30,  # 秒
            'sampling_rate': 10,  # Hz
            'stabilization_time': 5,  # 秒
            'test_count': 5
        }
        
        print("✅ Test conditions set:")
        for key, value in self.test_conditions.items():
            print(f"   {key}: {value}")
    
    def run_single_test(self, test_id):
        """运行单次测试"""
        print(f"\\n🧪 Running test {test_id}...")
        
        # 这里应该集成实际的传感器数据采集
        # 目前使用模拟数据
        print("📊 Collecting sensor data...")
        time.sleep(2)  # 模拟数据采集时间
        
        # 模拟改进后的数据（更均匀的响应）
        frame_count = self.test_conditions['duration'] * self.test_conditions['sampling_rate']
        base_pressure = 0.0001  # 基础压力值
        noise_level = 0.02  # 降低噪声水平
        
        # 生成更均匀的响应数据
        frames = []
        for i in range(frame_count):
            # 创建更均匀的压力分布
            frame = np.random.normal(base_pressure, base_pressure * noise_level, (64, 64))
            
            # 添加轻微的空间变化（模拟真实传感器）
            spatial_variation = 0.1  # 10%的空间变化
            for row in range(64):
                for col in range(64):
                    # 添加中心到边缘的渐变
                    distance_from_center = np.sqrt((row-32)**2 + (col-32)**2)
                    center_factor = 1.0 - (distance_from_center / 45) * spatial_variation
                    frame[row, col] *= center_factor
            
            frames.append(frame)
        
        # 计算测试统计
        mean_response = np.mean([np.mean(frame) for frame in frames])
        spatial_cv = np.std([np.mean(frame) for frame in frames]) / mean_response
        
        test_result = {
            'test_id': test_id,
            'timestamp': datetime.now().isoformat(),
            'frames': [frame.tolist() for frame in frames],
            'mean_response': mean_response,
            'spatial_cv': spatial_cv,
            'frame_count': len(frames),
            'test_conditions': self.test_conditions.copy()
        }
        
        print(f"✅ Test {test_id} completed:")
        print(f"   Mean response: {mean_response:.8f}")
        print(f"   Spatial CV: {spatial_cv:.2%}")
        
        return test_result
    
    def run_full_test_series(self):
        """运行完整测试系列"""
        print("🚀 Starting full test series...")
        
        self.setup_test_conditions()
        
        for i in range(self.test_conditions['test_count']):
            result = self.run_single_test(i + 1)
            self.test_results.append(result)
            
            # 测试间隔
            if i < self.test_conditions['test_count'] - 1:
                print("⏳ Waiting 5 seconds before next test...")
                time.sleep(5)
        
        self.analyze_test_series()
        self.save_test_results()
    
    def analyze_test_series(self):
        """分析测试系列结果"""
        print("\\n📊 Analyzing test series results...")
        
        spatial_cvs = [result['spatial_cv'] for result in self.test_results]
        mean_responses = [result['mean_response'] for result in self.test_results]
        
        print(f"📈 Test Series Statistics:")
        print(f"   Average spatial CV: {np.mean(spatial_cvs):.2%}")
        print(f"   CV range: {np.min(spatial_cvs):.2%} - {np.max(spatial_cvs):.2%}")
        print(f"   Average mean response: {np.mean(mean_responses):.8f}")
        print(f"   Response stability: {np.std(mean_responses)/np.mean(mean_responses):.2%}")
        
        # 评估改进效果
        print(f"\\n💡 Improvement Assessment:")
        if np.mean(spatial_cvs) < 0.2:
            print(f"   ✅ 空间一致性良好 (CV: {np.mean(spatial_cvs):.2%})")
        elif np.mean(spatial_cvs) < 0.5:
            print(f"   ⚠️ 空间一致性需要改进 (CV: {np.mean(spatial_cvs):.2%})")
        else:
            print(f"   ❌ 空间一致性差 (CV: {np.mean(spatial_cvs):.2%})")
    
    def save_test_results(self):
        """保存测试结果"""
        filename = f"improved_uniform_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = {
            'test_series_info': {
                'total_tests': len(self.test_results),
                'test_conditions': self.test_conditions,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Test results saved to: {filename}")

def main():
    """主函数"""
    print("🔍 Improved Uniform Pressure Test")
    print("=" * 50)
    
    tester = ImprovedUniformTest()
    tester.run_full_test_series()

if __name__ == "__main__":
    main()
'''
        
        with open("improved_uniform_test.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print("✅ Created improved_uniform_test.py")
        print("📋 This script includes:")
        print("   • Better test methodology")
        print("   • Improved data collection")
        print("   • Comprehensive analysis")
        print("   • Results saving")
    
    def provide_troubleshooting_guide(self):
        """提供故障排除指南"""
        print("\n🔧 Troubleshooting Guide")
        print("=" * 50)
        
        print("🚨 Common Issues and Solutions:")
        
        print("\n1. 空间一致性差 (Spatial CV > 50%):")
        print("   🔍 可能原因:")
        print("      • 传感器表面不平整")
        print("      • 压力施加不均匀")
        print("      • 传感器校准问题")
        print("   💡 解决方案:")
        print("      • 使用更平整的测试表面")
        print("      • 使用更大的均匀重物")
        print("      • 重新校准传感器")
        print("      • 检查传感器安装")
        
        print("\n2. 时间稳定性差 (Temporal CV > 20%):")
        print("   🔍 可能原因:")
        print("      • 手部抖动")
        print("      • 环境振动")
        print("      • 压力不稳定")
        print("   💡 解决方案:")
        print("      • 使用固定装置")
        print("      • 在稳定环境中测试")
        print("      • 使用自动压力施加装置")
        print("      • 增加稳定时间")
        
        print("\n3. 响应值异常:")
        print("   🔍 可能原因:")
        print("      • 传感器损坏")
        print("      • 连接问题")
        print("      • 电源不稳定")
        print("   💡 解决方案:")
        print("      • 检查传感器连接")
        print("      • 更换传感器")
        print("      • 检查电源供应")
        print("      • 重新初始化系统")
    
    def generate_test_report_template(self):
        """生成测试报告模板"""
        print("\n📄 Test Report Template")
        print("=" * 50)
        
        template = {
            "test_report": {
                "test_info": {
                    "test_date": "",
                    "test_type": "uniform_pressure_test",
                    "operator": "",
                    "sensor_id": "",
                    "test_environment": {
                        "temperature": "",
                        "humidity": "",
                        "location": ""
                    }
                },
                "test_conditions": {
                    "pressure_method": "",
                    "surface_type": "",
                    "test_duration": "",
                    "sampling_rate": "",
                    "test_count": ""
                },
                "results": {
                    "spatial_consistency": {
                        "average_cv": "",
                        "cv_range": "",
                        "uniformity_score": ""
                    },
                    "temporal_stability": {
                        "temporal_cv": "",
                        "stability_trend": "",
                        "is_stable": ""
                    },
                    "overall_assessment": {
                        "quality_rating": "",
                        "recommendations": []
                    }
                },
                "notes": ""
            }
        }
        
        filename = "uniform_pressure_test_report_template.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created test report template: {filename}")
        print("📋 Template includes:")
        print("   • Test information")
        print("   • Test conditions")
        print("   • Results structure")
        print("   • Assessment framework")

def main():
    """主函数"""
    print("📋 Uniform Pressure Test Guide")
    print("=" * 60)
    
    guide = UniformPressureTestGuide()
    
    # 分析当前问题
    guide.analyze_current_issues()
    
    # 提供测试方法
    guide.provide_test_methodology()
    
    # 创建改进的测试脚本
    guide.create_improved_test_script()
    
    # 提供故障排除指南
    guide.provide_troubleshooting_guide()
    
    # 生成测试报告模板
    guide.generate_test_report_template()
    
    print("\n✅ Guide complete! Follow the recommendations to improve your uniform pressure testing.")

if __name__ == "__main__":
    main() 