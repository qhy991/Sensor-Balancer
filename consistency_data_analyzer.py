#!/usr/bin/env python3
"""
位置一致性数据分析脚本
用于处理和分析传感器位置一致性测试数据
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# 设置中文字体支持
def setup_chinese_font():
    """设置中文字体支持"""
    try:
        # 尝试设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        print("✅ 中文字体设置成功")
    except Exception as e:
        print(f"⚠️ 中文字体设置失败: {e}")
        print("将使用英文标签")

# 初始化时设置字体
setup_chinese_font()

class ConsistencyDataAnalyzer:
    """位置一致性数据分析器"""
    
    def __init__(self, data_file=None, data_dict=None):
        """
        初始化分析器
        
        参数:
            data_file: JSON数据文件路径
            data_dict: 直接传入的数据字典
        """
        self.data = None
        self.guide_positions = {}
        self.consistency_results = {}
        self.analysis_summary = {}
        
        if data_dict:
            self.load_data_from_dict(data_dict)
        elif data_file:
            self.load_data_from_file(data_file)
        else:
            raise ValueError("必须提供data_file或data_dict参数")
    
    def load_data_from_file(self, file_path):
        """从文件加载数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self._extract_data()
            print(f"✅ 成功加载数据文件: {file_path}")
        except Exception as e:
            print(f"❌ 加载数据文件失败: {e}")
            raise
    
    def load_data_from_dict(self, data_dict):
        """从字典加载数据"""
        try:
            self.data = data_dict
            self._extract_data()
            print(f"✅ 成功加载数据字典")
        except Exception as e:
            print(f"❌ 加载数据字典失败: {e}")
            raise
    
    def _extract_data(self):
        """提取数据"""
        if not self.data:
            raise ValueError("没有数据可提取")
        
        self.guide_positions = self.data.get('guide_positions', {})
        self.consistency_results = self.data.get('consistency_results', {})
        self.analysis_summary = self.data.get('analysis_summary', {})
        
        print(f"📊 数据概览:")
        print(f"   - 位置数量: {len(self.guide_positions)}")
        print(f"   - 有数据的位置: {len(self.consistency_results)}")
        print(f"   - 时间戳: {self.data.get('timestamp', '未知')}")
    
    def validate_data(self):
        """验证数据完整性"""
        print("\n🔍 数据验证:")
        
        issues = []
        
        # 检查位置数据
        for pos_id, pos_info in self.guide_positions.items():
            if pos_id not in self.consistency_results:
                issues.append(f"位置 {pos_id} 没有测量数据")
        
        # 检查测量数据
        for pos_id, pos_results in self.consistency_results.items():
            if not pos_results:
                issues.append(f"位置 {pos_id} 的测量结果为空")
                continue
            
            for weight_id, result in pos_results.items():
                if 'sensitivity_total' not in result:
                    issues.append(f"位置 {pos_id} 砝码 {weight_id} 缺少敏感性数据")
                
                if 'cv' not in result:
                    issues.append(f"位置 {pos_id} 砝码 {weight_id} 缺少变异系数数据")
        
        if issues:
            print("⚠️ 发现以下问题:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 数据验证通过")
        
        return len(issues) == 0
    
    def get_data_summary(self):
        """获取数据摘要"""
        print("\n📈 数据摘要:")
        
        # 统计基本信息
        total_positions = len(self.guide_positions)
        measured_positions = len(self.consistency_results)
        total_measurements = 0
        valid_measurements = 0
        
        # 收集所有敏感性数据
        all_sensitivities = []
        all_cvs = []
        position_sensitivities = {}
        
        for pos_id, pos_results in self.consistency_results.items():
            position_sensitivities[pos_id] = []
            
            for weight_id, result in pos_results.items():
                total_measurements += 1
                
                sensitivity = result.get('sensitivity_total', 0)
                cv = result.get('cv', 0)
                
                all_sensitivities.append(sensitivity)
                all_cvs.append(cv)
                position_sensitivities[pos_id].append(sensitivity)
                
                if abs(sensitivity) > 1e-6:  # 有效数据阈值
                    valid_measurements += 1
        
        # 计算统计信息
        if all_sensitivities:
            avg_sensitivity = np.mean(all_sensitivities)
            std_sensitivity = np.std(all_sensitivities)
            min_sensitivity = np.min(all_sensitivities)
            max_sensitivity = np.max(all_sensitivities)
            
            avg_cv = np.mean(all_cvs)
            std_cv = np.std(all_cvs)
            
            print(f"   - 总测量点: {total_measurements}")
            print(f"   - 有效测量点: {valid_measurements} ({valid_measurements/total_measurements*100:.1f}%)")
            print(f"   - 平均敏感性: {avg_sensitivity:.6f} ± {std_sensitivity:.6f}")
            print(f"   - 敏感性范围: [{min_sensitivity:.6f}, {max_sensitivity:.6f}]")
            print(f"   - 平均变异系数: {avg_cv:.3f} ± {std_cv:.3f}")
        
        return {
            'total_positions': total_positions,
            'measured_positions': measured_positions,
            'total_measurements': total_measurements,
            'valid_measurements': valid_measurements,
            'avg_sensitivity': avg_sensitivity if all_sensitivities else 0,
            'std_sensitivity': std_sensitivity if all_sensitivities else 0,
            'avg_cv': avg_cv if all_cvs else 0,
            'std_cv': std_cv if all_cvs else 0
        }
    
    def analyze_position_consistency(self):
        """分析位置一致性"""
        print("\n🎯 位置一致性分析:")
        
        # 计算每个位置的平均敏感性
        position_avg_sensitivities = {}
        position_avg_cvs = {}
        
        for pos_id, pos_results in self.consistency_results.items():
            sensitivities = []
            cvs = []
            
            for result in pos_results.values():
                sensitivity = result.get('sensitivity_total', 0)
                cv = result.get('cv', 0)
                
                if abs(sensitivity) > 1e-6:  # 只考虑有效数据
                    sensitivities.append(sensitivity)
                    cvs.append(cv)
            
            if sensitivities:
                position_avg_sensitivities[pos_id] = np.mean(sensitivities)
                position_avg_cvs[pos_id] = np.mean(cvs)
                
                pos_name = self.guide_positions.get(pos_id, {}).get('name', pos_id)
                print(f"   - {pos_name}: 敏感性={position_avg_sensitivities[pos_id]:.6f}, CV={position_avg_cvs[pos_id]:.3f}")
        
        # 计算位置间一致性
        if position_avg_sensitivities:
            sensitivity_values = list(position_avg_sensitivities.values())
            position_consistency_cv = np.std(sensitivity_values) / abs(np.mean(sensitivity_values)) if np.mean(sensitivity_values) != 0 else 0
            
            print(f"\n   📊 位置间一致性CV: {position_consistency_cv:.3f}")
            
            if position_consistency_cv < 0.05:
                print("   ✅ 位置一致性: 优秀 (<5%)")
            elif position_consistency_cv < 0.1:
                print("   ✅ 位置一致性: 良好 (5-10%)")
            elif position_consistency_cv < 0.2:
                print("   ⚠️ 位置一致性: 一般 (10-20%)")
            else:
                print("   ❌ 位置一致性: 较差 (>20%)")
        
        return {
            'position_avg_sensitivities': position_avg_sensitivities,
            'position_avg_cvs': position_avg_cvs,
            'position_consistency_cv': position_consistency_cv if position_avg_sensitivities else 0
        }
    
    def identify_problematic_positions(self):
        """识别问题位置"""
        print("\n🔍 问题位置识别:")
        
        problematic_positions = []
        
        for pos_id, pos_results in self.consistency_results.items():
            pos_name = self.guide_positions.get(pos_id, {}).get('name', pos_id)
            issues = []
            
            # 检查是否有负敏感性
            negative_sensitivities = []
            for weight_id, result in pos_results.items():
                sensitivity = result.get('sensitivity_total', 0)
                if sensitivity < -1e-6:
                    negative_sensitivities.append((weight_id, sensitivity))
            
            if negative_sensitivities:
                issues.append(f"存在负敏感性: {negative_sensitivities}")
            
            # 检查变异系数
            high_cv_count = 0
            for result in pos_results.values():
                cv = result.get('cv', 0)
                if cv > 0.1:  # CV > 10%
                    high_cv_count += 1
            
            if high_cv_count > 0:
                issues.append(f"高变异系数测量点: {high_cv_count}/{len(pos_results)}")
            
            # 检查数据一致性
            sensitivities = [result.get('sensitivity_total', 0) for result in pos_results.values()]
            if len(sensitivities) > 1:
                sensitivity_cv = np.std(sensitivities) / abs(np.mean(sensitivities)) if np.mean(sensitivities) != 0 else 0
                if sensitivity_cv > 0.5:  # 敏感性CV > 50%
                    issues.append(f"敏感性不一致: CV={sensitivity_cv:.3f}")
            
            if issues:
                problematic_positions.append((pos_id, pos_name, issues))
                print(f"   ⚠️ {pos_name} ({pos_id}):")
                for issue in issues:
                    print(f"      - {issue}")
        
        if not problematic_positions:
            print("   ✅ 未发现明显问题位置")
        
        return problematic_positions
    
    def create_visualization(self, save_path=None):
        """创建可视化图表"""
        print("\n📊 创建可视化图表...")
        
        # 准备数据
        positions = []
        position_names = []
        avg_sensitivities = []
        avg_cvs = []
        
        for pos_id, pos_results in self.consistency_results.items():
            sensitivities = []
            cvs = []
            
            for result in pos_results.values():
                sensitivity = result.get('sensitivity_total', 0)
                cv = result.get('cv', 0)
                
                if abs(sensitivity) > 1e-6:
                    sensitivities.append(sensitivity)
                    cvs.append(cv)
            
            if sensitivities:
                positions.append(pos_id)
                position_names.append(self.guide_positions.get(pos_id, {}).get('name', pos_id))
                avg_sensitivities.append(np.mean(sensitivities))
                avg_cvs.append(np.mean(cvs))
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Position Consistency Analysis Results', fontsize=16, fontweight='bold')
        
        # 1. 位置敏感性对比
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(positions)), avg_sensitivities, color='skyblue', alpha=0.7)
        ax1.set_title('Average Sensitivity by Position')
        ax1.set_xlabel('Position')
        ax1.set_ylabel('Average Sensitivity')
        ax1.set_xticks(range(len(positions)))
        ax1.set_xticklabels(position_names, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars1, avg_sensitivities)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_sensitivities)*0.01,
                    f'{value:.4f}', ha='center', va='bottom', fontsize=9)
        
        # 2. 位置变异系数对比
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(positions)), avg_cvs, color='lightcoral', alpha=0.7)
        ax2.set_title('Average Coefficient of Variation by Position')
        ax2.set_xlabel('Position')
        ax2.set_ylabel('Average CV')
        ax2.set_xticks(range(len(positions)))
        ax2.set_xticklabels(position_names, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (bar, value) in enumerate(zip(bars2, avg_cvs)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_cvs)*0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=9)
        
        # 3. 敏感性分布直方图
        ax3 = axes[1, 0]
        all_sensitivities = []
        for pos_results in self.consistency_results.values():
            for result in pos_results.values():
                sensitivity = result.get('sensitivity_total', 0)
                if abs(sensitivity) > 1e-6:
                    all_sensitivities.append(sensitivity)
        
        if all_sensitivities:
            ax3.hist(all_sensitivities, bins=20, color='lightgreen', alpha=0.7, edgecolor='black')
            ax3.set_title('Sensitivity Distribution (All Positions)')
            ax3.set_xlabel('Sensitivity')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)
            
            # 添加标准差信息
            std_val = np.std(all_sensitivities)
            ax3.text(0.02, 0.98, f'Std: {std_val:.4f}', transform=ax3.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 4. 位置-砝码热力图 - 修复版本
        ax4 = axes[1, 1]
        
        # 创建位置-砝码矩阵
        weight_ids = set()
        for pos_results in self.consistency_results.values():
            weight_ids.update(pos_results.keys())
        weight_ids = sorted(list(weight_ids))
        
        if positions and weight_ids:
            consistency_matrix = np.zeros((len(positions), len(weight_ids)))
            
            for i, pos_id in enumerate(positions):
                for j, weight_id in enumerate(weight_ids):
                    if (pos_id in self.consistency_results and 
                        weight_id in self.consistency_results[pos_id]):
                        consistency_matrix[i, j] = self.consistency_results[pos_id][weight_id].get('sensitivity_total', 0)
            
            # 修复：转置矩阵并反转Y轴，使位置在Y轴从下到上显示
            consistency_matrix = consistency_matrix.T  # 转置矩阵
            
            # 创建热力图，使用origin='lower'确保Y轴从下到上
            im = ax4.imshow(consistency_matrix, cmap='plasma', aspect='auto', origin='lower')
            ax4.set_title('Position-Weight Sensitivity Heatmap')
            ax4.set_xlabel('Position')
            ax4.set_ylabel('Weight ID')
            ax4.set_xticks(range(len(positions)))
            ax4.set_xticklabels(position_names, rotation=45, ha='right')
            ax4.set_yticks(range(len(weight_ids)))
            ax4.set_yticklabels(weight_ids)
            
            # 添加数值标签 - 注意坐标已经转置
            for i in range(len(weight_ids)):
                for j in range(len(positions)):
                    value = consistency_matrix[i, j]
                    if abs(value) > 1e-6:
                        text_color = 'white' if value < np.mean(consistency_matrix) else 'black'
                        ax4.text(j, i, f'{value:.3f}', ha='center', va='center', 
                                color=text_color, fontsize=8, fontweight='bold')
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax4)
            cbar.set_label('Sensitivity')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 图表已保存到: {save_path}")
        
        plt.show()
    
    def export_analysis_report(self, output_path):
        """导出分析报告"""
        print(f"\n📄 导出分析报告到: {output_path}")
        
        # 获取分析结果
        summary = self.get_data_summary()
        consistency_analysis = self.analyze_position_consistency()
        problematic_positions = self.identify_problematic_positions()
        
        # 创建报告
        report = []
        report.append("=" * 60)
        report.append("传感器位置一致性分析报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"数据时间: {self.data.get('timestamp', '未知')}")
        report.append("")
        
        # 数据概览
        report.append("📊 数据概览")
        report.append("-" * 30)
        report.append(f"总位置数: {summary['total_positions']}")
        report.append(f"测量位置数: {summary['measured_positions']}")
        report.append(f"总测量点: {summary['total_measurements']}")
        report.append(f"有效测量点: {summary['valid_measurements']} ({summary['valid_measurements']/summary['total_measurements']*100:.1f}%)")
        report.append("")
        
        # 统计结果
        report.append("📈 统计结果")
        report.append("-" * 30)
        report.append(f"平均敏感性: {summary['avg_sensitivity']:.6f} ± {summary['std_sensitivity']:.6f}")
        report.append(f"平均变异系数: {summary['avg_cv']:.3f} ± {summary['std_cv']:.3f}")
        report.append(f"位置间一致性CV: {consistency_analysis['position_consistency_cv']:.3f}")
        report.append("")
        
        # 位置详细分析
        report.append("🎯 位置详细分析")
        report.append("-" * 30)
        for pos_id, avg_sens in consistency_analysis['position_avg_sensitivities'].items():
            pos_name = self.guide_positions.get(pos_id, {}).get('name', pos_id)
            avg_cv = consistency_analysis['position_avg_cvs'].get(pos_id, 0)
            report.append(f"{pos_name}: 敏感性={avg_sens:.6f}, CV={avg_cv:.3f}")
        report.append("")
        
        # 问题位置
        if problematic_positions:
            report.append("⚠️ 问题位置")
            report.append("-" * 30)
            for pos_id, pos_name, issues in problematic_positions:
                report.append(f"{pos_name} ({pos_id}):")
                for issue in issues:
                    report.append(f"  - {issue}")
            report.append("")
        
        # 建议
        report.append("💡 建议")
        report.append("-" * 30)
        if consistency_analysis['position_consistency_cv'] > 0.2:
            report.append("- 位置一致性较差，建议检查传感器校准")
        if summary['valid_measurements'] / summary['total_measurements'] < 0.8:
            report.append("- 有效数据比例较低，建议重新测量")
        if problematic_positions:
            report.append("- 存在负敏感性数据，建议检查基线校正")
        if not problematic_positions and consistency_analysis['position_consistency_cv'] < 0.1:
            report.append("- 位置一致性良好，传感器性能稳定")
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"✅ 分析报告已保存到: {output_path}")
    
    def run_full_analysis(self, output_dir="analysis_results"):
        """运行完整分析"""
        print("🚀 开始完整分析...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 数据验证
        is_valid = self.validate_data()
        
        # 获取分析结果
        summary = self.get_data_summary()
        consistency_analysis = self.analyze_position_consistency()
        problematic_positions = self.identify_problematic_positions()
        
        # 创建可视化
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_path = os.path.join(output_dir, f"consistency_analysis_{timestamp}.png")
        self.create_visualization(plot_path)
        
        # 导出报告
        report_path = os.path.join(output_dir, f"analysis_report_{timestamp}.txt")
        self.export_analysis_report(report_path)
        
        print(f"\n✅ 完整分析完成！")
        print(f"📊 图表: {plot_path}")
        print(f"📄 报告: {report_path}")
        
        return {
            'is_valid': is_valid,
            'summary': summary,
            'consistency_analysis': consistency_analysis,
            'problematic_positions': problematic_positions,
            'plot_path': plot_path,
            'report_path': report_path
        }


def main():
    """主函数 - 示例用法"""
    # 示例数据（您可以将您的数据粘贴在这里）
    sample_data = {
        "timestamp": "2025-08-01T09:34:55.048622",
        "guide_positions": {
            "center": {"name": "中心位置", "x": 32, "y": 32, "description": "传感器中心位置"}
        },
        "consistency_results": {
            "center": {
                "1": {
                    "weight_info": {"mass": 50.0, "unit": "g", "force": 0.49},
                    "measurement_count": 10,
                    "avg_total_pressure": 0.005066163004057334,
                    "std_total_pressure": 0.00019036257213867988,
                    "cv": 0.03757529554146291,
                    "sensitivity_total": 0.01033910817154558
                }
            }
        },
        "analysis_summary": {
            "avg_cv": 0.029305598248228797,
            "std_cv": 0.07440675621285253,
            "avg_sensitivity": -0.02002797769033922,
            "std_sensitivity": 0.04060561137120782,
            "position_consistency_cv": 0
        }
    }
    
    print("🔧 位置一致性数据分析工具")
    print("=" * 50)
    
    # 创建分析器
    analyzer = ConsistencyDataAnalyzer(data_dict=sample_data)
    
    # 运行完整分析
    results = analyzer.run_full_analysis()
    
    print("\n📋 分析结果摘要:")
    print(f"数据有效性: {'✅ 通过' if results['is_valid'] else '❌ 失败'}")
    print(f"有效测量点: {results['summary']['valid_measurements']}/{results['summary']['total_measurements']}")
    print(f"位置一致性CV: {results['consistency_analysis']['position_consistency_cv']:.3f}")
    print(f"问题位置数: {len(results['problematic_positions'])}")


if __name__ == "__main__":
    main() 