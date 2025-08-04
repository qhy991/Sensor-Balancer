#!/usr/bin/env python3
"""
可视化校准位置分布和斜率信息
"""

import json
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def visualize_calibration_positions():
    """可视化校准位置分布"""
    print("🎯 可视化校准位置分布")
    print("=" * 50)
    
    # 加载位置校准数据
    with open('position_calibration_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    positions = data['positions']
    
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 图1: 位置分布图
    ax1.set_title('传感器校准位置分布', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X坐标', fontsize=12)
    ax1.set_ylabel('Y坐标', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 64)
    ax1.set_ylim(0, 64)
    ax1.invert_yaxis()  # 反转Y轴，使(0,0)在左上角
    
    # 绘制64x64传感器网格
    for i in range(0, 65, 8):
        ax1.axhline(y=i, color='lightgray', alpha=0.5, linewidth=0.5)
        ax1.axvline(x=i, color='lightgray', alpha=0.5, linewidth=0.5)
    
    # 绘制校准位置
    colors = plt.cm.Set3(np.linspace(0, 1, len(positions)))
    for i, (pos_id, pos_info) in enumerate(positions.items()):
        x, y = pos_info['x'], pos_info['y']
        slope = pos_info['calibration']['slope']
        r_squared = pos_info['calibration']['r_squared']
        
        # 绘制位置点
        ax1.scatter(x, y, s=200, c=[colors[i]], alpha=0.8, edgecolors='black', linewidth=2)
        
        # 添加标签
        ax1.annotate(f"{pos_info['name']}\n斜率: {slope:.1f}\nR²: {r_squared:.3f}", 
                    (x, y), xytext=(5, 5), textcoords='offset points',
                    fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # 图2: 斜率对比图
    pos_names = [pos_info['name'] for pos_info in positions.values()]
    slopes = [pos_info['calibration']['slope'] for pos_info in positions.values()]
    r_squared_values = [pos_info['calibration']['r_squared'] for pos_info in positions.values()]
    
    bars = ax2.bar(pos_names, slopes, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_title('各位置校准斜率对比', fontsize=14, fontweight='bold')
    ax2.set_ylabel('斜率 (g/N)', fontsize=12)
    ax2.set_xlabel('位置', fontsize=12)
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 在柱状图上添加R²值
    for i, (bar, r2) in enumerate(zip(bars, r_squared_values)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'R²={r2:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 添加统计信息
    avg_slope = np.mean(slopes)
    std_slope = np.std(slopes)
    ax2.axhline(y=avg_slope, color='red', linestyle='--', alpha=0.7, label=f'平均值: {avg_slope:.1f}')
    ax2.legend()
    
    # 添加统计信息文本框
    stats_text = f"统计信息:\n平均斜率: {avg_slope:.2f}\n标准差: {std_slope:.2f}\n变异系数: {std_slope/avg_slope:.3f}"
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('calibration_positions_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 打印详细信息
    print("\n📊 校准位置详细信息:")
    print("-" * 80)
    print(f"{'位置名称':<12} {'坐标':<10} {'斜率':<12} {'截距':<12} {'R²':<8} {'测量次数':<8}")
    print("-" * 80)
    
    for pos_id, pos_info in positions.items():
        cal = pos_info['calibration']
        print(f"{pos_info['name']:<12} ({pos_info['x']:2d},{pos_info['y']:2d})    "
              f"{cal['slope']:<12.2f} {cal['intercept']:<12.2f} {cal['r_squared']:<8.4f} {cal['measurement_count']:<8}")
    
    print("-" * 80)
    print(f"总位置数: {len(positions)}")
    print(f"平均斜率: {avg_slope:.2f}")
    print(f"斜率标准差: {std_slope:.2f}")
    print(f"斜率变异系数: {std_slope/avg_slope:.3f}")
    
    # 分析斜率差异
    print(f"\n📈 斜率差异分析:")
    max_slope = max(slopes)
    min_slope = min(slopes)
    max_pos = [pos_info['name'] for pos_info in positions.values() if pos_info['calibration']['slope'] == max_slope][0]
    min_pos = [pos_info['name'] for pos_info in positions.values() if pos_info['calibration']['slope'] == min_slope][0]
    
    print(f"最大斜率: {max_slope:.2f} ({max_pos})")
    print(f"最小斜率: {min_slope:.2f} ({min_pos})")
    print(f"斜率范围: {max_slope - min_slope:.2f}")
    print(f"相对差异: {(max_slope - min_slope) / avg_slope * 100:.1f}%")

if __name__ == "__main__":
    visualize_calibration_positions()