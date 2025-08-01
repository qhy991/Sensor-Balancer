#!/usr/bin/env python3
"""
位置一致性和线性度分析器
分析同一个砝码在不同位置的压力，以及不同砝码在同一个位置的压力线性关系
"""

import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

class PositionLinearityAnalyzer:
    """位置一致性和线性度分析器"""
    
    def __init__(self, data_dict=None):
        self.data = data_dict
        self.guide_positions = {}
        self.consistency_results = {}
        self.position_analysis = {}
        self.linearity_analysis = {}
        
        if data_dict:
            self.load_data(data_dict)
    
    def load_data(self, data_dict):
        """加载数据"""
        self.data = data_dict
        self.guide_positions = data_dict.get('guide_positions', {})
        self.consistency_results = data_dict.get('consistency_results', {})
        print(f"✅ 数据加载完成: {len(self.guide_positions)} 个位置, {len(self.consistency_results)} 个结果")
    
    def analyze_position_consistency(self):
        """任务1：分析同一个砝码在不同位置的压力（位置一致性）"""
        print("\n🔍 开始位置一致性分析...")
        
        # 收集所有砝码ID
        weight_ids = set()
        for position_results in self.consistency_results.values():
            weight_ids.update(position_results.keys())
        weight_ids = sorted(list(weight_ids))
        
        position_analysis = {}
        
        for weight_id in weight_ids:
            print(f"\n📊 分析砝码 {weight_id} 在不同位置的一致性:")
            
            # 收集该砝码在所有位置的数据
            weight_data = {}
            for position_id, position_results in self.consistency_results.items():
                if weight_id in position_results:
                    result = position_results[weight_id]
                    sensitivity = result.get('sensitivity_total', 0)
                    cv = result.get('cv', 0)
                    avg_pressure = result.get('avg_total_pressure', 0)
                    
                    weight_data[position_id] = {
                        'sensitivity': sensitivity,
                        'cv': cv,
                        'avg_pressure': avg_pressure,
                        'position_name': self.guide_positions.get(position_id, {}).get('name', position_id)
                    }
            
            if len(weight_data) > 1:
                # 计算统计信息
                sensitivities = [data['sensitivity'] for data in weight_data.values()]
                pressures = [data['avg_pressure'] for data in weight_data.values()]
                cvs = [data['cv'] for data in weight_data.values()]
                
                # 位置一致性指标
                mean_sensitivity = np.mean(sensitivities)
                std_sensitivity = np.std(sensitivities)
                cv_sensitivity = std_sensitivity / mean_sensitivity if mean_sensitivity > 0 else 0
                
                mean_pressure = np.mean(pressures)
                std_pressure = np.std(pressures)
                cv_pressure = std_pressure / mean_pressure if mean_pressure > 0 else 0
                
                # 位置间变异系数
                position_consistency_cv = cv_sensitivity
                
                # 评估一致性等级
                if position_consistency_cv < 0.05:
                    consistency_grade = "优秀"
                elif position_consistency_cv < 0.1:
                    consistency_grade = "良好"
                elif position_consistency_cv < 0.2:
                    consistency_grade = "一般"
                else:
                    consistency_grade = "较差"
                
                position_analysis[weight_id] = {
                    'weight_data': weight_data,
                    'statistics': {
                        'mean_sensitivity': mean_sensitivity,
                        'std_sensitivity': std_sensitivity,
                        'cv_sensitivity': cv_sensitivity,
                        'mean_pressure': mean_pressure,
                        'std_pressure': std_pressure,
                        'cv_pressure': cv_pressure,
                        'position_consistency_cv': position_consistency_cv,
                        'consistency_grade': consistency_grade
                    },
                    'positions_count': len(weight_data)
                }
                
                print(f"  位置数量: {len(weight_data)}")
                print(f"  平均敏感性: {mean_sensitivity:.6f} ± {std_sensitivity:.6f}")
                print(f"  位置一致性CV: {position_consistency_cv:.3f} ({consistency_grade})")
                print(f"  位置列表: {list(weight_data.keys())}")
            else:
                print(f"  警告: 砝码 {weight_id} 只有一个位置的数据，无法进行一致性分析")
        
        self.position_analysis = position_analysis
        return position_analysis
    
    def analyze_linearity(self):
        """任务2：分析不同砝码在同一个位置的压力线性关系"""
        print("\n🔍 开始线性度分析...")
        
        linearity_analysis = {}
        
        for position_id, position_results in self.consistency_results.items():
            position_name = self.guide_positions.get(position_id, {}).get('name', position_id)
            print(f"\n📊 分析位置 {position_name} ({position_id}) 的线性关系:")
            
            # 收集该位置所有砝码的数据
            position_data = {}
            for weight_id, result in position_results.items():
                sensitivity = result.get('sensitivity_total', 0)
                avg_pressure = result.get('avg_total_pressure', 0)
                weight_info = result.get('weight_info', {})
                mass = weight_info.get('mass', 0)
                force = weight_info.get('force', 0)
                
                position_data[weight_id] = {
                    'sensitivity': sensitivity,
                    'avg_pressure': avg_pressure,
                    'mass': mass,
                    'force': force
                }
            
            if len(position_data) > 2:  # 至少需要3个点才能分析线性关系
                # 准备数据
                weights = [data['mass'] for data in position_data.values()]
                pressures = [data['avg_pressure'] for data in position_data.values()]
                forces = [data['force'] for data in position_data.values()]
                
                # 线性回归分析（质量 vs 压力）
                slope_mass, intercept_mass, r_value_mass, p_value_mass, std_err_mass = stats.linregress(weights, pressures)
                r_squared_mass = r_value_mass ** 2
                
                # 线性回归分析（力 vs 压力）
                slope_force, intercept_force, r_value_force, p_value_force, std_err_force = stats.linregress(forces, pressures)
                r_squared_force = r_value_force ** 2
                
                # 计算理论斜率（基于重力加速度）
                theoretical_slope = 0.0098  # g = 9.8 m/s²
                
                # 计算线性度误差
                linearity_error_mass = abs(slope_mass - theoretical_slope) / theoretical_slope * 100
                linearity_error_force = abs(slope_force - 1.0) * 100  # 理想情况下力与压力应该1:1
                
                # 评估线性度等级
                if linearity_error_mass < 5:
                    linearity_grade = "优秀"
                elif linearity_error_mass < 10:
                    linearity_grade = "良好"
                elif linearity_error_mass < 20:
                    linearity_grade = "一般"
                else:
                    linearity_grade = "较差"
                
                # 计算残差
                predicted_pressures_mass = [slope_mass * w + intercept_mass for w in weights]
                residuals_mass = [p - pred for p, pred in zip(pressures, predicted_pressures_mass)]
                
                predicted_pressures_force = [slope_force * f + intercept_force for f in forces]
                residuals_force = [p - pred for p, pred in zip(pressures, predicted_pressures_force)]
                
                linearity_analysis[position_id] = {
                    'position_name': position_name,
                    'position_data': position_data,
                    'mass_analysis': {
                        'weights': weights,
                        'pressures': pressures,
                        'slope': slope_mass,
                        'intercept': intercept_mass,
                        'r_squared': r_squared_mass,
                        'p_value': p_value_mass,
                        'std_err': std_err_mass,
                        'linearity_error': linearity_error_mass,
                        'predicted': predicted_pressures_mass,
                        'residuals': residuals_mass
                    },
                    'force_analysis': {
                        'forces': forces,
                        'pressures': pressures,
                        'slope': slope_force,
                        'intercept': intercept_force,
                        'r_squared': r_squared_force,
                        'p_value': p_value_force,
                        'std_err': std_err_force,
                        'linearity_error': linearity_error_force,
                        'predicted': predicted_pressures_force,
                        'residuals': residuals_force
                    },
                    'linearity_grade': linearity_grade,
                    'weights_count': len(position_data)
                }
                
                print(f"  砝码数量: {len(position_data)}")
                print(f"  质量-压力线性度: R² = {r_squared_mass:.4f}, 斜率 = {slope_mass:.6f}")
                print(f"  线性度误差: {linearity_error_mass:.2f}% ({linearity_grade})")
                print(f"  砝码列表: {list(position_data.keys())}")
            else:
                print(f"  警告: 位置 {position_name} 只有 {len(position_data)} 个砝码的数据，无法进行线性分析")
        
        self.linearity_analysis = linearity_analysis
        return linearity_analysis
    
    def create_analysis_plots(self, save_path=None):
        """创建分析图表"""
        print("\n📊 创建分析图表...")
        
        # 创建2x2的子图布局
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('位置一致性和线性度分析', fontsize=16, fontweight='bold')
        
        # 1. 位置一致性分析图（左上）
        ax1 = axes[0, 0]
        if self.position_analysis:
            weight_ids = list(self.position_analysis.keys())
            consistency_cvs = [self.position_analysis[wid]['statistics']['position_consistency_cv'] for wid in weight_ids]
            grades = [self.position_analysis[wid]['statistics']['consistency_grade'] for wid in weight_ids]
            
            # 颜色映射
            colors = []
            for grade in grades:
                if grade == "优秀":
                    colors.append('green')
                elif grade == "良好":
                    colors.append('blue')
                elif grade == "一般":
                    colors.append('orange')
                else:
                    colors.append('red')
            
            bars = ax1.bar(weight_ids, consistency_cvs, color=colors, alpha=0.7)
            ax1.set_title('位置一致性分析（同一砝码在不同位置）')
            ax1.set_xlabel('砝码ID')
            ax1.set_ylabel('位置一致性CV')
            ax1.grid(True, alpha=0.3)
            
            # 添加数值标签
            for i, (bar, cv, grade) in enumerate(zip(bars, consistency_cvs, grades)):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(consistency_cvs)*0.01,
                        f'{cv:.3f}\n({grade})', ha='center', va='bottom', fontsize=9)
        
        # 2. 线性度分析图（右上）
        ax2 = axes[0, 1]
        if self.linearity_analysis:
            position_ids = list(self.linearity_analysis.keys())
            linearity_errors = [self.linearity_analysis[pid]['linearity_grade'] for pid in position_ids]
            r_squared_values = [self.linearity_analysis[pid]['mass_analysis']['r_squared'] for pid in position_ids]
            
            # 颜色映射
            colors = []
            for grade in linearity_errors:
                if grade == "优秀":
                    colors.append('green')
                elif grade == "良好":
                    colors.append('blue')
                elif grade == "一般":
                    colors.append('orange')
                else:
                    colors.append('red')
            
            bars = ax2.bar(range(len(position_ids)), r_squared_values, color=colors, alpha=0.7)
            ax2.set_title('线性度分析（不同砝码在同一位置）')
            ax2.set_xlabel('位置')
            ax2.set_ylabel('R²值')
            ax2.set_xticks(range(len(position_ids)))
            ax2.set_xticklabels([self.linearity_analysis[pid]['position_name'] for pid in position_ids], rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # 添加数值标签
            for i, (bar, r2, grade) in enumerate(zip(bars, r_squared_values, linearity_errors)):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(r_squared_values)*0.01,
                        f'{r2:.3f}\n({grade})', ha='center', va='bottom', fontsize=9)
        
        # 3. 详细线性关系图（左下）- 选择一个位置进行详细分析
        ax3 = axes[1, 0]
        if self.linearity_analysis:
            # 选择第一个有数据的位置
            selected_position = list(self.linearity_analysis.keys())[0]
            pos_data = self.linearity_analysis[selected_position]
            position_name = pos_data['position_name']
            
            weights = pos_data['mass_analysis']['weights']
            pressures = pos_data['mass_analysis']['pressures']
            predicted = pos_data['mass_analysis']['predicted']
            
            # 绘制散点图和拟合线
            ax3.scatter(weights, pressures, color='blue', s=50, alpha=0.7, label='实测数据')
            ax3.plot(weights, predicted, color='red', linewidth=2, label=f'拟合线 (R²={pos_data["mass_analysis"]["r_squared"]:.3f})')
            
            ax3.set_title(f'质量-压力线性关系 ({position_name})')
            ax3.set_xlabel('质量 (g)')
            ax3.set_ylabel('压力')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. 残差分析图（右下）
        ax4 = axes[1, 1]
        if self.linearity_analysis:
            selected_position = list(self.linearity_analysis.keys())[0]
            pos_data = self.linearity_analysis[selected_position]
            weights = pos_data['mass_analysis']['weights']
            residuals = pos_data['mass_analysis']['residuals']
            
            ax4.scatter(weights, residuals, color='green', s=50, alpha=0.7)
            ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax4.set_title(f'残差分析 ({pos_data["position_name"]})')
            ax4.set_xlabel('质量 (g)')
            ax4.set_ylabel('残差')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 分析图表已保存到: {save_path}")
        
        plt.show()
    
    def generate_analysis_report(self, output_path):
        """生成分析报告"""
        print(f"\n📄 生成分析报告...")
        
        report = []
        report.append("=" * 80)
        report.append("传感器位置一致性和线性度分析报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据时间: {self.data.get('timestamp', '未知')}")
        report.append("")
        
        # 任务1：位置一致性分析
        report.append("📊 任务1：位置一致性分析（同一砝码在不同位置）")
        report.append("-" * 60)
        
        if self.position_analysis:
            for weight_id, analysis in self.position_analysis.items():
                stats = analysis['statistics']
                report.append(f"\n砝码 {weight_id}:")
                report.append(f"  位置数量: {analysis['positions_count']}")
                report.append(f"  平均敏感性: {stats['mean_sensitivity']:.6f} ± {stats['std_sensitivity']:.6f}")
                report.append(f"  位置一致性CV: {stats['position_consistency_cv']:.3f} ({stats['consistency_grade']})")
                report.append(f"  位置列表: {list(analysis['weight_data'].keys())}")
        else:
            report.append("  无位置一致性数据")
        
        # 任务2：线性度分析
        report.append("\n\n📊 任务2：线性度分析（不同砝码在同一位置）")
        report.append("-" * 60)
        
        if self.linearity_analysis:
            for position_id, analysis in self.linearity_analysis.items():
                position_name = analysis['position_name']
                mass_analysis = analysis['mass_analysis']
                force_analysis = analysis['force_analysis']
                
                report.append(f"\n位置 {position_name} ({position_id}):")
                report.append(f"  砝码数量: {analysis['weights_count']}")
                report.append(f"  质量-压力线性度:")
                report.append(f"    斜率: {mass_analysis['slope']:.6f}")
                report.append(f"    截距: {mass_analysis['intercept']:.6f}")
                report.append(f"    R²: {mass_analysis['r_squared']:.4f}")
                report.append(f"    线性度误差: {mass_analysis['linearity_error']:.2f}%")
                report.append(f"  力-压力线性度:")
                report.append(f"    斜率: {force_analysis['slope']:.6f}")
                report.append(f"    截距: {force_analysis['intercept']:.6f}")
                report.append(f"    R²: {force_analysis['r_squared']:.4f}")
                report.append(f"    线性度误差: {force_analysis['linearity_error']:.2f}%")
                report.append(f"  综合评估: {analysis['linearity_grade']}")
        else:
            report.append("  无线性度数据")
        
        # 总结和建议
        report.append("\n\n💡 总结和建议")
        report.append("-" * 60)
        
        if self.position_analysis:
            avg_consistency_cv = np.mean([analysis['statistics']['position_consistency_cv'] 
                                        for analysis in self.position_analysis.values()])
            report.append(f"平均位置一致性CV: {avg_consistency_cv:.3f}")
            
            if avg_consistency_cv < 0.05:
                report.append("✅ 位置一致性优秀，传感器在不同位置的响应一致")
            elif avg_consistency_cv < 0.1:
                report.append("✅ 位置一致性良好，建议进一步优化")
            elif avg_consistency_cv < 0.2:
                report.append("⚠️ 位置一致性一般，建议检查传感器校准")
            else:
                report.append("❌ 位置一致性较差，需要重新校准传感器")
        
        if self.linearity_analysis:
            avg_r_squared = np.mean([analysis['mass_analysis']['r_squared'] 
                                   for analysis in self.linearity_analysis.values()])
            avg_linearity_error = np.mean([analysis['mass_analysis']['linearity_error'] 
                                         for analysis in self.linearity_analysis.values()])
            
            report.append(f"平均线性度R²: {avg_r_squared:.4f}")
            report.append(f"平均线性度误差: {avg_linearity_error:.2f}%")
            
            if avg_r_squared > 0.99 and avg_linearity_error < 5:
                report.append("✅ 线性度优秀，传感器响应线性良好")
            elif avg_r_squared > 0.95 and avg_linearity_error < 10:
                report.append("✅ 线性度良好，建议微调校准参数")
            elif avg_r_squared > 0.9 and avg_linearity_error < 20:
                report.append("⚠️ 线性度一般，建议检查测量过程")
            else:
                report.append("❌ 线性度较差，需要重新校准或检查硬件")
        
        # 写入报告文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"✅ 分析报告已保存到: {output_path}")
        return report
    
    def run_full_analysis(self, output_dir="analysis_results"):
        """运行完整分析"""
        print("🚀 开始完整的位置一致性和线性度分析")
        print("=" * 60)
        
        # 创建输出目录
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 运行分析
        position_results = self.analyze_position_consistency()
        linearity_results = self.analyze_linearity()
        
        # 生成时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存结果
        results = {
            'timestamp': timestamp,
            'position_analysis': position_results,
            'linearity_analysis': linearity_results,
            'summary': {
                'total_positions': len(self.guide_positions),
                'total_weights': len(set().union(*[set(pos.keys()) for pos in self.consistency_results.values()])),
                'position_analysis_count': len(position_results),
                'linearity_analysis_count': len(linearity_results)
            }
        }
        
        # 保存JSON结果
        json_path = os.path.join(output_dir, f"position_linearity_analysis_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 生成报告
        report_path = os.path.join(output_dir, f"position_linearity_report_{timestamp}.txt")
        self.generate_analysis_report(report_path)
        
        # 创建图表
        plot_path = os.path.join(output_dir, f"position_linearity_plots_{timestamp}.png")
        self.create_analysis_plots(plot_path)
        
        print(f"\n✅ 分析完成！")
        print(f"📄 报告文件: {report_path}")
        print(f"📊 图表文件: {plot_path}")
        print(f"📋 JSON结果: {json_path}")
        
        return results


def main():
    """主函数 - 测试分析器"""
    # 加载测试数据
    test_data_path = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\0801-2.json"
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 成功加载测试数据: {test_data_path}")
        
        # 创建分析器
        analyzer = PositionLinearityAnalyzer(data)
        
        # 运行完整分析
        results = analyzer.run_full_analysis()
        
        print("\n📋 分析结果摘要:")
        print(f"位置一致性分析: {results['summary']['position_analysis_count']} 个砝码")
        print(f"线性度分析: {results['summary']['linearity_analysis_count']} 个位置")
        
    except FileNotFoundError:
        print(f"❌ 测试数据文件未找到: {test_data_path}")
        print("请确保数据文件存在，或修改main函数中的文件路径")
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()