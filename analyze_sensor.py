import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# 设置 Matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

def load_data(filepath='data.json'):
    """加载并返回JSON数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件未找到 '{filepath}'")
        return None
    except json.JSONDecodeError:
        print(f"错误: 文件格式无效 '{filepath}'")
        return None

def plot_combined_linearity(data):
    """
    新增功能：将所有位置的所有数据点绘制在一张图上。
    - 使用不同颜色区分不同位置的点。
    - 对所有点进行一次总的线性回归。
    - 将聚合分析图表保存到文件。
    """
    print("\n" + "="*50)
    print("📊 3. 传感器整体线性度聚合分析")
    print("="*50)

    consistency_results = data.get("consistency_results", {})
    guide_positions = data.get("guide_positions", {})
    
    # 创建保存图像的目录
    output_dir = "C:/Users/84672/Documents/Research/balance-sensor/"
    os.makedirs(output_dir, exist_ok=True)
    
    # 聚合所有数据点
    all_masses = []
    all_pressures = []
    all_pos_names = [] # 用于图例

    for position, measurements in consistency_results.items():
        pos_name = guide_positions.get(position, {}).get("name", position)
        for details in measurements.values():
            all_masses.append(details["weight_info"]["mass"])
            all_pressures.append(details["avg_total_pressure"])
            all_pos_names.append(pos_name)

    if not all_masses:
        print("无数据可供聚合分析。")
        return
    
    # 对所有点进行一次总的线性回归
    all_masses_np = np.array(all_masses)
    all_pressures_np = np.array(all_pressures)
    slope, intercept, r_value, p_value, std_err = stats.linregress(all_masses_np, all_pressures_np)
    r_squared = r_value**2

    print("--- 传感器整体回归分析结果 ---")
    print(f"  - 总数据点数量: {len(all_masses)}")
    print(f"  - 整体回归斜率: {slope:.6f}")
    print(f"  - 整体回归截距: {intercept:.6f}")
    print(f"  - 整体 R² (决定系数): {r_squared:.4f}")
    if r_squared > 0.95:
         print("  - 结论: 整体数据点趋向于一条直线，但离散度可能较大。")
    else:
         print("  - 结论: 整体线性关系较差，说明位置一致性问题严重影响了总体性能。")

    # --- 绘图 ---
    plt.figure(figsize=(14, 9))
    
    # 使用Seaborn绘制散点图，并根据位置自动着色
    sns.scatterplot(x=all_masses, y=all_pressures, hue=all_pos_names, s=80, palette="tab10")

    # 绘制总的回归线
    line_x = np.array([0, max(all_masses)])
    line_y = slope * line_x + intercept
    plt.plot(line_x, line_y, color='black', linestyle='--', linewidth=2.5, label="整体回归线")
    
    # 设置图表标题和标签
    title_text = (
        f"传感器所有位置数据点聚合分析\n"
        f"整体回归方程: y = {slope:.4f}x + {intercept:.4f}\n"
        f"整体 $R^2$ = {r_squared:.4f}"
    )
    plt.title(title_text, fontsize=16)
    plt.xlabel("砝码质量 (g)", fontsize=12)
    plt.ylabel("平均总压力 (avg_total_pressure)", fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(title="传感器位置", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.88, 1]) # 调整布局为图例腾出空间

    # 保存图表
    filename = f"{output_dir}/combined_linearity_analysis.png"
    plt.savefig(filename)
    plt.close()
    
    print(f"\n聚合分析图表已生成并保存到: '{filename}'")


def analyze_and_plot_linearity(data):
    """
    对每个位置进行线性度分析和绘图。
    """
    print("\n" + "="*50)
    print("📊 1. 逐个位置的线性度分析与绘图")
    print("="*50)

    consistency_results = data.get("consistency_results", {})
    guide_positions = data.get("guide_positions", {})
    
    output_dir = "C:/Users/84672/Documents/Research/balance-sensor/linearity_analysis_plots"
    os.makedirs(output_dir, exist_ok=True)
    print(f"线性度分析图表将保存到 '{output_dir}' 目录中。\n")

    for position, measurements in consistency_results.items():
        pos_name = guide_positions.get(position, {}).get("name", position)
        
        masses = [d["weight_info"]["mass"] for d in measurements.values()]
        pressures = [d["avg_total_pressure"] for d in measurements.values()]
        
        if len(masses) < 3:
            print(f"位置 '{pos_name}' 数据点不足，跳过分析。")
            continue
            
        masses = np.array(masses)
        pressures = np.array(pressures)

        slope, intercept, r_value, p_value, std_err = stats.linregress(masses, pressures)
        r_squared = r_value**2

        print(f"--- 分析位置: {pos_name} ({position}) ---")
        print(f"  - 线性回归斜率: {slope:.6f}")
        print(f"  - 截距: {intercept:.6f}")
        print(f"  - R² (决定系数): {r_squared:.4f}")
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=masses, y=pressures, s=100, label="实际测量值")
        line_x = np.array([0, max(masses)])
        line_y = slope * line_x + intercept
        plt.plot(line_x, line_y, color='red', linestyle='--', label="线性回归线")
        
        title_text = (
            f"位置: {pos_name} 的线性度分析\n"
            f"回归方程: y = {slope:.4f}x + {intercept:.4f}\n"
            f"$R^2$ = {r_squared:.4f}"
        )
        plt.title(title_text)
        plt.xlabel("砝码质量 (g)")
        plt.ylabel("平均总压力 (avg_total_pressure)")
        plt.grid(True)
        plt.legend()
        
        filename = f"{output_dir}/{position}_linearity.png"
        plt.savefig(filename)
        plt.close()

    print("\n所有位置的线性度图表已生成。")


def analyze_and_plot_consistency(data):
    """
    对每个砝码进行位置一致性分析和绘图。
    """
    print("\n" + "="*50)
    print("📊 2. 逐个砝码的位置一致性分析与绘图")
    print("="*50)

    consistency_results = data.get("consistency_results", {})
    guide_positions = data.get("guide_positions", {})
    
    output_dir = "C:/Users/84672/Documents/Research/balance-sensor/consistency_analysis_plots"
    os.makedirs(output_dir, exist_ok=True)
    print(f"位置一致性分析图表将保存到 '{output_dir}' 目录中。\n")

    if not consistency_results:
        print("无数据可供分析。")
        return

    first_pos = list(consistency_results.keys())[0]
    weight_ids = list(consistency_results[first_pos].keys())

    for weight_id in weight_ids:
        positions_data = []
        mass = 0
        for pos_key, measurements in consistency_results.items():
            if weight_id in measurements:
                pos_name = guide_positions.get(pos_key, {}).get("name", pos_key)
                pressure = measurements[weight_id]["avg_total_pressure"]
                mass = measurements[weight_id]["weight_info"]["mass"]
                positions_data.append({"position": pos_name, "pressure": pressure})
        
        if not positions_data:
            continue

        pressures = [d['pressure'] for d in positions_data]
        pos_names = [d['position'] for d in positions_data]
        
        mean_pressure = np.mean(pressures)
        std_pressure = np.std(pressures)
        
        if abs(mean_pressure) < 1e-9:
            cv = float('inf') if std_pressure > 1e-9 else 0.0
        else:
            cv = std_pressure / abs(mean_pressure)

        print(f"--- 分析砝码: {weight_id} ({mass}g) ---")
        print(f"  - 平均压力: {mean_pressure:.6f}")
        print(f"  - 压力标准差: {std_pressure:.6f}")
        print(f"  - 变异系数 (CV): {cv:.4f}")
            
        plt.figure(figsize=(12, 7))
        # 修正了Seaborn的FutureWarning
        sns.barplot(x=pos_names, y=pressures, hue=pos_names, palette="viridis", legend=False)
        plt.axhline(y=mean_pressure, color='r', linestyle='--', label=f'平均值: {mean_pressure:.4f}')
        title_text = (
            f"砝码 {mass}g 在不同位置的压力一致性分析\n"
            f"变异系数 (CV) = {cv:.4f}"
        )
        plt.title(title_text)
        plt.xlabel("传感器位置")
        plt.ylabel("平均总压力 (avg_total_pressure)")
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        filename = f"{output_dir}/weight_{mass}g_consistency.png"
        plt.savefig(filename)
        plt.close()

    print("\n所有砝码的位置一致性图表已生成。")


def main():
    """主函数，执行所有分析"""
    # 注意：请确保这个路径是正确的，或者将JSON文件放在脚本同目录下并使用相对路径
    filepath = 'C:/Users/84672/Documents/Research/balance-sensor/consistency-test/0801-3-完整.json'
    sensor_data = load_data(filepath)
    if sensor_data:
        # 1. 执行逐个位置的线性度分析
        analyze_and_plot_linearity(sensor_data)
        
        # 2. 执行逐个砝码的位置一致性分析
        analyze_and_plot_consistency(sensor_data)

        # 3. 新增功能：执行所有数据点的聚合分析
        plot_combined_linearity(sensor_data)
        
        print("\n" + "="*50)
        print("✅ 分析完成。")
        print("="*50)

if __name__ == "__main__":
    main()