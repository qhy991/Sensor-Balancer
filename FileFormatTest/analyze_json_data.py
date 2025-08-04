#!/usr/bin/env python3
"""
分析JSON格式的位置一致性数据
"""

import json
import os
import sys
import numpy as np
from datetime import datetime

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

def analyze_consistency_data(data):
    """分析一致性数据"""
    print("🔧 开始分析位置一致性数据")
    print("=" * 60)
    
    # 基本信息
    timestamp = data.get('timestamp', '未知')
    guide_positions = data.get('guide_positions', {})
    consistency_results = data.get('consistency_results', {})
    
    print(f"📅 数据时间: {timestamp}")
    print(f"📍 总位置数: {len(guide_positions)}")
    print(f"📊 有数据的位置数: {len(consistency_results)}")
    
    # 统计信息
    all_sensitivities = []
    all_cvs = []
    position_stats = {}
    
    print("\n🎯 位置详细分析:")
    print("-" * 40)
    
    for pos_id, pos_data in consistency_results.items():
        pos_name = guide_positions.get(pos_id, {}).get('name', pos_id)
        sensitivities = []
        cvs = []
        
        print(f"\n📍 {pos_name} ({pos_id}):")
        
        for weight_id, result in pos_data.items():
            sensitivity = result.get('sensitivity_total', 0)
            cv = result.get('cv', 0)
            mass = result.get('weight_info', {}).get('mass', 0)
            
            sensitivities.append(sensitivity)
            cvs.append(cv)
            all_sensitivities.append(sensitivity)
            all_cvs.append(cv)
            
            print(f"   砝码{weight_id} ({mass}g): 敏感性={sensitivity:.6f}, CV={cv:.6f}")
        
        # 位置统计
        if sensitivities:
            avg_sensitivity = np.mean(sensitivities)
            avg_cv = np.mean(cvs)
            position_stats[pos_id] = {
                'name': pos_name,
                'avg_sensitivity': avg_sensitivity,
                'avg_cv': avg_cv,
                'sensitivities': sensitivities,
                'cvs': cvs
            }
            print(f"   平均: 敏感性={avg_sensitivity:.6f}, CV={avg_cv:.6f}")
    
    # 总体统计
    print("\n📈 总体统计:")
    print("-" * 40)
    
    if all_sensitivities:
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        min_sensitivity = np.min(all_sensitivities)
        max_sensitivity = np.max(all_sensitivities)
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        
        print(f"平均敏感性: {avg_sensitivity:.6f} ± {std_sensitivity:.6f}")
        print(f"敏感性范围: [{min_sensitivity:.6f}, {max_sensitivity:.6f}]")
        print(f"平均变异系数: {avg_cv:.6f} ± {std_cv:.6f}")
        
        # 位置间一致性
        if len(position_stats) > 1:
            position_sensitivities = [stats['avg_sensitivity'] for stats in position_stats.values()]
            position_consistency_cv = np.std(position_sensitivities) / np.mean(position_sensitivities)
            print(f"位置间一致性CV: {position_consistency_cv:.3f}")
            
            # 一致性评估
            if position_consistency_cv < 0.05:
                consistency_level = "优秀 (<5%)"
            elif position_consistency_cv < 0.10:
                consistency_level = "良好 (5-10%)"
            elif position_consistency_cv < 0.20:
                consistency_level = "一般 (10-20%)"
            else:
                consistency_level = "需要改进 (>20%)"
            
            print(f"位置一致性: {consistency_level}")
    
    # 问题分析
    print("\n🔍 问题分析:")
    print("-" * 40)
    
    # 检查负敏感性
    negative_sensitivities = [s for s in all_sensitivities if s < -1e-6]
    if negative_sensitivities:
        print(f"⚠️ 发现 {len(negative_sensitivities)} 个负敏感性值")
        for pos_id, stats in position_stats.items():
            for i, sensitivity in enumerate(stats['sensitivities']):
                if sensitivity < -1e-6:
                    print(f"   {stats['name']} 砝码{i+1}: {sensitivity:.6f}")
    else:
        print("✅ 未发现负敏感性值")
    
    # 检查高CV值
    high_cv_threshold = 0.1
    high_cvs = [cv for cv in all_cvs if cv > high_cv_threshold]
    if high_cvs:
        print(f"⚠️ 发现 {len(high_cvs)} 个高CV值 (>10%)")
        for pos_id, stats in position_stats.items():
            for i, cv in enumerate(stats['cvs']):
                if cv > high_cv_threshold:
                    print(f"   {stats['name']} 砝码{i+1}: CV={cv:.6f}")
    else:
        print("✅ 所有CV值都在正常范围内")
    
    # 检查缺失位置
    missing_positions = set(guide_positions.keys()) - set(consistency_results.keys())
    if missing_positions:
        print(f"⚠️ 发现 {len(missing_positions)} 个缺失位置:")
        for pos_id in missing_positions:
            pos_name = guide_positions.get(pos_id, {}).get('name', pos_id)
            print(f"   {pos_name} ({pos_id})")
    else:
        print("✅ 所有位置都有数据")
    
    # 建议
    print("\n💡 建议:")
    print("-" * 40)
    
    if negative_sensitivities:
        print("• 负敏感性通常表示基线校正过度，建议检查基线数据记录过程")
        print("• 可能需要调整基线校正算法")
        print("• 考虑重新进行基线测量")
    
    if high_cvs:
        print("• 高CV值表示测量重复性差，建议检查测量环境稳定性")
        print("• 可能需要增加测量次数或改善测量条件")
    
    if missing_positions:
        print("• 建议补充缺失位置的测量数据以获得完整的传感器特性")
    
    if len(position_stats) > 1:
        if position_consistency_cv > 0.20:
            print("• 位置间一致性较差，建议检查传感器安装和校准")
        elif position_consistency_cv > 0.10:
            print("• 位置间一致性一般，可以考虑进一步优化")
        else:
            print("• 位置间一致性良好，传感器性能稳定")
    
    return {
        'timestamp': timestamp,
        'total_positions': len(guide_positions),
        'measured_positions': len(consistency_results),
        'total_measurements': len(all_sensitivities),
        'avg_sensitivity': avg_sensitivity if all_sensitivities else 0,
        'std_sensitivity': std_sensitivity if all_sensitivities else 0,
        'avg_cv': avg_cv if all_cvs else 0,
        'std_cv': std_cv if all_cvs else 0,
        'position_consistency_cv': position_consistency_cv if len(position_stats) > 1 else 0,
        'position_stats': position_stats,
        'negative_sensitivities': len(negative_sensitivities),
        'high_cvs': len(high_cvs),
        'missing_positions': len(missing_positions)
    }

def save_analysis_report(results, output_dir="analysis_results"):
    """保存分析报告"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"detailed_analysis_{timestamp}.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("详细位置一致性分析报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据时间: {results['timestamp']}\n\n")
        
        f.write("📊 数据概览\n")
        f.write("-" * 30 + "\n")
        f.write(f"总位置数: {results['total_positions']}\n")
        f.write(f"测量位置数: {results['measured_positions']}\n")
        f.write(f"总测量点: {results['total_measurements']}\n\n")
        
        f.write("📈 统计结果\n")
        f.write("-" * 30 + "\n")
        f.write(f"平均敏感性: {results['avg_sensitivity']:.6f} ± {results['std_sensitivity']:.6f}\n")
        f.write(f"平均变异系数: {results['avg_cv']:.6f} ± {results['std_cv']:.6f}\n")
        f.write(f"位置间一致性CV: {results['position_consistency_cv']:.3f}\n\n")
        
        f.write("🎯 位置详细分析\n")
        f.write("-" * 30 + "\n")
        for pos_id, stats in results['position_stats'].items():
            f.write(f"{stats['name']}: 敏感性={stats['avg_sensitivity']:.6f}, CV={stats['avg_cv']:.6f}\n")
        
        f.write(f"\n🔍 问题统计\n")
        f.write("-" * 30 + "\n")
        f.write(f"负敏感性数量: {results['negative_sensitivities']}\n")
        f.write(f"高CV值数量: {results['high_cvs']}\n")
        f.write(f"缺失位置数量: {results['missing_positions']}\n")
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    return report_file

def main():
    """主函数"""
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
    data = load_data_from_json(json_filepath)
    if data is None:
        return
    
    # 分析数据
    results = analyze_consistency_data(data)
    
    # 保存报告
    report_file = save_analysis_report(results)
    
    print(f"\n✅ 分析完成！详细报告: {report_file}")

if __name__ == "__main__":
    main() 