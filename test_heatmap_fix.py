#!/usr/bin/env python3
"""
测试热力图修复效果
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from consistency_data_analyzer import ConsistencyDataAnalyzer

def test_heatmap_visualization():
    """测试热力图可视化"""
    
    # 加载数据
    json_filepath = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\0801-2.json"
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 成功加载数据文件: {json_filepath}")
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return
    
    # 创建分析器
    analyzer = ConsistencyDataAnalyzer(data_dict=data)
    
    # 创建修复后的可视化
    print("🔧 创建修复后的热力图...")
    analyzer.create_visualization("test_heatmap_fixed.png")
    
    # 创建对比图
    create_comparison_heatmap(data)

def create_comparison_heatmap(data):
    """创建对比热力图"""
    print("📊 创建对比热力图...")
    
    guide_positions = data.get('guide_positions', {})
    consistency_results = data.get('consistency_results', {})
    
    # 准备数据
    positions = []
    position_names = []
    weight_ids = set()
    
    for pos_id, pos_results in consistency_results.items():
        positions.append(pos_id)
        position_names.append(guide_positions.get(pos_id, {}).get('name', pos_id))
        weight_ids.update(pos_results.keys())
    
    weight_ids = sorted(list(weight_ids))
    
    # 创建数据矩阵
    consistency_matrix = np.zeros((len(positions), len(weight_ids)))
    
    for i, pos_id in enumerate(positions):
        for j, weight_id in enumerate(weight_ids):
            if (pos_id in consistency_results and 
                weight_id in consistency_results[pos_id]):
                consistency_matrix[i, j] = consistency_results[pos_id][weight_id].get('sensitivity_total', 0)
    
    # 创建对比图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('热力图对比 - 修复前后', fontsize=16, fontweight='bold')
    
    # 原始版本（可能有问题）
    im1 = ax1.imshow(consistency_matrix, cmap='plasma', aspect='auto')
    ax1.set_title('原始版本 (可能颠倒)')
    ax1.set_xlabel('Weight ID')
    ax1.set_ylabel('Position')
    ax1.set_xticks(range(len(weight_ids)))
    ax1.set_xticklabels(weight_ids)
    ax1.set_yticks(range(len(positions)))
    ax1.set_yticklabels(position_names)
    
    # 添加数值标签
    for i in range(len(positions)):
        for j in range(len(weight_ids)):
            value = consistency_matrix[i, j]
            if abs(value) > 1e-6:
                text_color = 'white' if value < np.mean(consistency_matrix) else 'black'
                ax1.text(j, i, f'{value:.3f}', ha='center', va='center', 
                        color=text_color, fontsize=8, fontweight='bold')
    
    # 修复版本
    consistency_matrix_fixed = consistency_matrix.T  # 转置
    im2 = ax2.imshow(consistency_matrix_fixed, cmap='plasma', aspect='auto', origin='lower')
    ax2.set_title('修复版本 (正确方向)')
    ax2.set_xlabel('Position')
    ax2.set_ylabel('Weight ID')
    ax2.set_xticks(range(len(positions)))
    ax2.set_xticklabels(position_names, rotation=45, ha='right')
    ax2.set_yticks(range(len(weight_ids)))
    ax2.set_yticklabels(weight_ids)
    
    # 添加数值标签
    for i in range(len(weight_ids)):
        for j in range(len(positions)):
            value = consistency_matrix_fixed[i, j]
            if abs(value) > 1e-6:
                text_color = 'white' if value < np.mean(consistency_matrix_fixed) else 'black'
                ax2.text(j, i, f'{value:.3f}', ha='center', va='center', 
                        color=text_color, fontsize=8, fontweight='bold')
    
    # 添加颜色条
    plt.colorbar(im1, ax=ax1, label='Sensitivity')
    plt.colorbar(im2, ax=ax2, label='Sensitivity')
    
    plt.tight_layout()
    plt.savefig('heatmap_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ 对比图已保存到: heatmap_comparison.png")
    plt.show()

def create_detailed_heatmap_analysis(data):
    """创建详细的热力图分析"""
    print("🔍 创建详细热力图分析...")
    
    guide_positions = data.get('guide_positions', {})
    consistency_results = data.get('consistency_results', {})
    
    # 准备数据
    positions = []
    position_names = []
    weight_ids = set()
    
    for pos_id, pos_results in consistency_results.items():
        positions.append(pos_id)
        position_names.append(guide_positions.get(pos_id, {}).get('name', pos_id))
        weight_ids.update(pos_results.keys())
    
    weight_ids = sorted(list(weight_ids))
    
    # 创建数据矩阵
    consistency_matrix = np.zeros((len(positions), len(weight_ids)))
    
    for i, pos_id in enumerate(positions):
        for j, weight_id in enumerate(weight_ids):
            if (pos_id in consistency_results and 
                weight_id in consistency_results[pos_id]):
                consistency_matrix[i, j] = consistency_results[pos_id][weight_id].get('sensitivity_total', 0)
    
    # 创建详细分析图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('热力图详细分析', fontsize=16, fontweight='bold')
    
    # 1. 原始矩阵
    im1 = ax1.imshow(consistency_matrix, cmap='plasma', aspect='auto')
    ax1.set_title('原始数据矩阵')
    ax1.set_xlabel('Weight ID')
    ax1.set_ylabel('Position')
    ax1.set_xticks(range(len(weight_ids)))
    ax1.set_xticklabels(weight_ids)
    ax1.set_yticks(range(len(positions)))
    ax1.set_yticklabels(position_names)
    
    # 2. 转置矩阵
    consistency_matrix_T = consistency_matrix.T
    im2 = ax2.imshow(consistency_matrix_T, cmap='plasma', aspect='auto')
    ax2.set_title('转置矩阵')
    ax2.set_xlabel('Position')
    ax2.set_ylabel('Weight ID')
    ax2.set_xticks(range(len(positions)))
    ax2.set_xticklabels(position_names, rotation=45, ha='right')
    ax2.set_yticks(range(len(weight_ids)))
    ax2.set_yticklabels(weight_ids)
    
    # 3. 修复版本（转置 + origin='lower'）
    im3 = ax3.imshow(consistency_matrix_T, cmap='plasma', aspect='auto', origin='lower')
    ax3.set_title('修复版本 (转置 + origin=lower)')
    ax3.set_xlabel('Position')
    ax3.set_ylabel('Weight ID')
    ax3.set_xticks(range(len(positions)))
    ax3.set_xticklabels(position_names, rotation=45, ha='right')
    ax3.set_yticks(range(len(weight_ids)))
    ax3.set_yticklabels(weight_ids)
    
    # 4. 数据统计
    ax4.axis('off')
    ax4.text(0.1, 0.9, '数据统计信息:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    stats_text = f"""
矩阵形状: {consistency_matrix.shape}
位置数量: {len(positions)}
砝码数量: {len(weight_ids)}

位置列表:
{chr(10).join([f"  {i+1}. {name}" for i, name in enumerate(position_names)])}

砝码列表:
{chr(10).join([f"  {i+1}. {wid}" for i, wid in enumerate(weight_ids)])}

数据范围:
  最小值: {consistency_matrix.min():.6f}
  最大值: {consistency_matrix.max():.6f}
  平均值: {consistency_matrix.mean():.6f}
  标准差: {consistency_matrix.std():.6f}

非零数据点: {np.count_nonzero(consistency_matrix)}/{consistency_matrix.size}
    """
    
    ax4.text(0.1, 0.8, stats_text, fontsize=10, transform=ax4.transAxes, 
             verticalalignment='top', fontfamily='monospace')
    
    # 添加颜色条
    plt.colorbar(im1, ax=ax1, label='Sensitivity')
    plt.colorbar(im2, ax=ax2, label='Sensitivity')
    plt.colorbar(im3, ax=ax3, label='Sensitivity')
    
    plt.tight_layout()
    plt.savefig('heatmap_detailed_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 详细分析图已保存到: heatmap_detailed_analysis.png")
    plt.show()

def main():
    """主函数"""
    print("🔧 测试热力图修复效果")
    print("=" * 50)
    
    # 测试修复后的可视化
    test_heatmap_visualization()
    
    # 加载数据用于对比分析
    json_filepath = r"C:\Users\84672\Documents\Research\balance-sensor\consistency-test\0801-2.json"
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建对比图
        create_comparison_heatmap(data)
        
        # 创建详细分析
        create_detailed_heatmap_analysis(data)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    main() 