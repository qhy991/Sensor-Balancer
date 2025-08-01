#!/usr/bin/env python3
"""
分析您提供的位置一致性数据
"""

import json
import os
import sys
from consistency_data_analyzer import ConsistencyDataAnalyzer

def load_data_from_json(filepath):
    """从JSON文件加载数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 成功加载数据文件: {filepath}")
        return data
    except FileNotFoundError:
        print(f"❌ 文件未找到: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return None

def main():
    """分析您的数据"""
    print("🔧 分析位置一致性数据")
    print("=" * 60)
    
    # 从命令行参数或默认路径获取文件路径
    if len(sys.argv) > 1:
        json_filepath = sys.argv[1]
    else:
        # 默认文件路径
        json_filepath = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\0801-2.json"
    
    print(f"📁 数据文件路径: {json_filepath}")
    
    # 检查文件是否存在
    if not os.path.exists(json_filepath):
        print(f"❌ 文件不存在: {json_filepath}")
        print("请确保文件路径正确，或通过命令行参数指定文件路径")
        return
    
    # 加载数据
    your_data = load_data_from_json(json_filepath)
    if your_data is None:
        return
    
    # 创建分析器
    analyzer = ConsistencyDataAnalyzer(data_dict=your_data)
    
    # 运行完整分析
    results = analyzer.run_full_analysis("your_analysis_results")
    
    print("\n" + "=" * 60)
    print("📋 您的数据分析结果摘要:")
    print("=" * 60)
    print(f"数据有效性: {'✅ 通过' if results['is_valid'] else '❌ 失败'}")
    print(f"总测量点: {results['summary']['total_measurements']}")
    print(f"有效测量点: {results['summary']['valid_measurements']} ({results['summary']['valid_measurements']/results['summary']['total_measurements']*100:.1f}%)")
    print(f"平均敏感性: {results['summary']['avg_sensitivity']:.6f} ± {results['summary']['std_sensitivity']:.6f}")
    print(f"平均变异系数: {results['summary']['avg_cv']:.3f} ± {results['summary']['std_cv']:.3f}")
    print(f"位置间一致性CV: {results['consistency_analysis']['position_consistency_cv']:.3f}")
    print(f"问题位置数: {len(results['problematic_positions'])}")
    
    print(f"\n📊 图表文件: {results['plot_path']}")
    print(f"📄 报告文件: {results['report_path']}")
    
    # 特别分析负敏感性问题
    print("\n🔍 负敏感性分析:")
    negative_count = 0
    total_count = 0
    
    for pos_id, pos_results in your_data['consistency_results'].items():
        for weight_id, result in pos_results.items():
            total_count += 1
            sensitivity = result.get('sensitivity_total', 0)
            if sensitivity < -1e-6:
                negative_count += 1
                pos_name = your_data['guide_positions'][pos_id]['name']
                print(f"   ⚠️ {pos_name} 砝码{weight_id}: {sensitivity:.6f}")
    
    print(f"   负敏感性比例: {negative_count}/{total_count} ({negative_count/total_count*100:.1f}%)")
    
    if negative_count > 0:
        print("\n💡 关于负敏感性的建议:")
        print("   - 负敏感性通常表示基线校正过度")
        print("   - 建议检查基线数据的记录过程")
        print("   - 可能需要调整基线校正算法")
        print("   - 考虑重新进行基线测量")

if __name__ == "__main__":
    main() 