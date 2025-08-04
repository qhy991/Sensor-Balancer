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

def analyze_calibration_model(data):
    """
    新增功能: 以总压力为X，砝码重量为Y，进行回归分析。
    这用于建立一个“校准模型”，即通过压力读数预测重量。
    """
    print("\n" + "="*50)
    print("📊 新增: 校准模型分析 (总压力 -> 砝码重量)")
    print("="*50)

    consistency_results = data.get("consistency_results", {})
    guide_positions = data.get("guide_positions", {})
    
    # --- 1. 逐个位置的校准模型 ---
    output_dir_individual = "calibration_model_plots"
    os.makedirs(output_dir_individual, exist_ok=True)
    print(f"独立的校准模型图表将保存到 '{output_dir_individual}' 目录中。\n")

    for position, measurements in consistency_results.items():
        pos_name = guide_positions.get(position, {}).get("name", position)
        
        # 提取数据点，X为压力，Y为质量
        pressures = np.array([d["avg_total_pressure"] for d in measurements.values()])
        masses = np.array([d["weight_info"]["mass"] for d in measurements.values()])
        
        if len(masses) < 3:
            continue
            
        # 进行线性回归: y = slope * x + intercept  (Mass = slope * Pressure + intercept)
        slope, intercept, r_value, p_value, std_err = stats.linregress(pressures, masses)
        r_squared = r_value**2

        print(f"--- 位置: {pos_name} 的校准模型 ---")
        print(f"  - 校准斜率 (g/pressure_unit): {slope:.4f}")
        print(f"  - 校准截距 (g): {intercept:.4f}")
        print(f"  - R²: {r_squared:.4f}")

        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=pressures, y=masses, s=100, label="测量数据")
        line_x = np.array([min(pressures), max(pressures)])
        line_y = slope * line_x + intercept
        plt.plot(line_x, line_y, color='green', linestyle='--', label="校准模型回归线")
        
        title_text = (
            f"位置: {pos_name} 的校准模型 (压力->重量)\n"
            f"校准方程: 重量 = {slope:.2f} * 压力 + {intercept:.2f}\n"
            f"$R^2$ = {r_squared:.4f}"
        )
        plt.title(title_text)
        plt.xlabel("平均总压力 (avg_total_pressure)")
        plt.ylabel("砝码质量 (g)")
        plt.grid(True)
        plt.legend()
        
        filename = f"{output_dir_individual}/{position}_calibration_model.png"
        plt.savefig(filename)
        plt.close()
    
    print("\n已为每个位置生成独立的校准模型图表。")
    
    # --- 2. 整体的校准模型 ---
    all_masses = []
    all_pressures = []
    all_pos_names = []

    for position, measurements in consistency_results.items():
        pos_name = guide_positions.get(position, {}).get("name", position)
        for details in measurements.values():
            all_pressures.append(details["avg_total_pressure"])
            all_masses.append(details["weight_info"]["mass"])
            all_pos_names.append(pos_name)

    # 进行总回归
    slope_all, intercept_all, r_value_all, _, _ = stats.linregress(all_pressures, all_masses)
    r_squared_all = r_value_all**2

    print("\n" + "-"*50)
    print("--- 传感器整体校准模型 (所有点聚合) ---")
    print(f"  - 整体校准斜率 (g/pressure_unit): {slope_all:.4f}")
    print(f"  - 整体校准截距 (g): {intercept_all:.4f}")
    print(f"  - 整体 R²: {r_squared_all:.4f}")
    if r_squared_all < 0.9:
        print("  - 结论: 整体 R² 值较低，说明如果使用单一模型对所有位置进行预测，误差会非常大。这再次证明了位置一致性是主要问题。")
    else:
        print("  - 结论: 整体数据点高度相关，但仍需关注离散情况。")

    plt.figure(figsize=(14, 9))
    sns.scatterplot(x=all_pressures, y=all_masses, hue=all_pos_names, s=80, palette="tab10")
    
    line_x_all = np.array([min(all_pressures), max(all_pressures)])
    line_y_all = slope_all * line_x_all + intercept_all
    plt.plot(line_x_all, line_y_all, color='black', linestyle='--', linewidth=2.5, label="整体校准回归线")
    
    title_text = (
        f"传感器整体校准模型 (所有位置聚合)\n"
        f"整体校准方程: 重量 = {slope_all:.2f} * 压力 + {intercept_all:.2f}\n"
        f"整体 $R^2$ = {r_squared_all:.4f}"
    )
    plt.title(title_text, fontsize=16)
    plt.xlabel("平均总压力 (avg_total_pressure)", fontsize=12)
    plt.ylabel("砝码质量 (g)", fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(title="传感器位置", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.88, 1])

    output_dir_combined = "." # 保存到主目录
    filename = f"{output_dir_combined}/combined_calibration_model.png"
    plt.savefig(filename)
    plt.close()
    
    print(f"\n整体校准模型图表已生成并保存到: '{filename}'")

def main():
    """主函数，执行所有分析"""
    # 假设您的JSON文件与脚本在同一目录下
    filepath = 'C:/Users/84672/Documents/Research/balance-sensor/consistency-test/0801-3-完整.json' 
    sensor_data = load_data(filepath)
    
    if sensor_data:
        # 新增的校准模型分析 (压力 -> 重量)
        analyze_calibration_model(sensor_data)
        
        # 这里可以注释掉之前的分析，如果不想重复生成
        # print("\n\n" + "#"*60)
        # print("以下为原始分析 (重量 -> 压力)")
        # print("#"*60)
        # analyze_and_plot_linearity(sensor_data)
        # analyze_and_plot_consistency(sensor_data)
        # plot_combined_linearity(sensor_data)
        
        print("\n" + "="*50)
        print("✅ 分析完成。")
        print("="*50)

if __name__ == "__main__":
    # 在运行前，请确保 'data.json' 文件存在于脚本所在的目录中
    # 如果文件不存在，我们先创建一个
    if not os.path.exists('C:/Users/84672/Documents/Research/balance-sensor/consistency-test/0801-3-完整.json'):
        print("未找到 'data.json'，正在根据之前的对话创建示例文件...")
        # (此处应填入之前对话中的完整JSON数据)
        # 为简洁起见，这里假设文件已存在。在实际环境中，请确保文件就位。
        # 如果您在本地运行，请将您的JSON数据保存为 data.json
        print("请确保 'data.json' 文件已准备好，然后重新运行脚本。")
    else:
        main()