#!/usr/bin/env python3
"""
分析原始帧数据中每个像素点压力分布的程序
分析每个像素点在连续帧中的压力分布，并使用高斯分布进行近似
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.optimize import curve_fit
import json
import os
from datetime import datetime
import seaborn as sns
from matplotlib.patches import Rectangle

class PixelDistributionAnalyzer:
    """像素点分布分析器"""
    
    def __init__(self, frames_data):
        """
        初始化分析器
        
        Args:
            frames_data: 帧数据，可以是文件路径或已加载的数据
        """
        self.frames = None
        self.reference_data = None
        self.frame_count = 0
        self.frame_shape = None
        
        # 加载数据
        self.load_data(frames_data)
        
        # 分析结果存储
        self.pixel_stats = {}  # 每个像素的统计信息
        self.gaussian_fits = {}  # 每个像素的高斯拟合结果
        self.fit_quality = {}  # 拟合质量评估
        
    def load_data(self, data_source):
        """加载帧数据"""
        if isinstance(data_source, str):
            # 从文件加载
            if data_source.endswith('.npz'):
                data = np.load(data_source)
                self.frames = [frame for frame in data['frames']]
                if 'reference_data' in data:
                    self.reference_data = data['reference_data']
            elif data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    data_dict = json.load(f)
                self.frames = [np.array(frame) for frame in data_dict['frames']]
                if 'reference_data' in data_dict:
                    self.reference_data = np.array(data_dict['reference_data'])
        else:
            # 直接使用数据
            self.frames = data_source
            
        self.frame_count = len(self.frames)
        if self.frames:
            self.frame_shape = self.frames[0].shape
            print(f"✅ 加载了 {self.frame_count} 帧数据，形状: {self.frame_shape}")
    
    def analyze_pixel_distribution(self, pixel_pos=None, plot=True):
        """
        分析指定像素点的压力分布
        
        Args:
            pixel_pos: 像素位置 (row, col)，None表示分析所有像素
            plot: 是否绘制分布图
        """
        if pixel_pos is None:
            # 分析所有像素
            print("🔍 分析所有像素点的压力分布...")
            self.analyze_all_pixels()
        else:
            # 分析指定像素
            row, col = pixel_pos
            print(f"🔍 分析像素点 ({row}, {col}) 的压力分布...")
            self.analyze_single_pixel(row, col, plot)
    
    def analyze_single_pixel(self, row, col, plot=True):
        """分析单个像素点的分布"""
        # 提取该像素在所有帧中的值
        pixel_values = [frame[row, col] for frame in self.frames]
        pixel_values = np.array(pixel_values)
        
        # 基础统计
        mean_val = np.mean(pixel_values)
        std_val = np.std(pixel_values)
        min_val = np.min(pixel_values)
        max_val = np.max(pixel_values)
        
        # 存储统计信息
        pixel_key = f"({row}, {col})"
        self.pixel_stats[pixel_key] = {
            'mean': mean_val,
            'std': std_val,
            'min': min_val,
            'max': max_val,
            'cv': std_val / mean_val if mean_val > 0 else 0,
            'values': pixel_values
        }
        
        # 高斯分布拟合
        fit_result = self.fit_gaussian_distribution(pixel_values)
        self.gaussian_fits[pixel_key] = fit_result
        
        # 评估拟合质量
        quality = self.evaluate_fit_quality(pixel_values, fit_result)
        self.fit_quality[pixel_key] = quality
        
        # 打印结果
        print(f"📊 像素 ({row}, {col}) 统计结果:")
        print(f"   平均值: {mean_val:.8f}")
        print(f"   标准差: {std_val:.8f}")
        print(f"   变异系数: {std_val/mean_val:.2%}")
        print(f"   数值范围: {min_val:.8f} - {max_val:.8f}")
        print(f"   高斯拟合参数: μ={fit_result['mu']:.8f}, σ={fit_result['sigma']:.8f}")
        print(f"   拟合质量: R²={quality['r_squared']:.4f}, KS检验p值={quality['ks_pvalue']:.4f}")
        
        # 绘制分布图
        if plot:
            self.plot_pixel_distribution(row, col, pixel_values, fit_result, quality)
        
        return {
            'stats': self.pixel_stats[pixel_key],
            'fit': fit_result,
            'quality': quality
        }
    
    def analyze_all_pixels(self):
        """分析所有像素点"""
        rows, cols = self.frame_shape
        
        # 初始化结果数组
        mean_map = np.zeros(self.frame_shape)
        std_map = np.zeros(self.frame_shape)
        cv_map = np.zeros(self.frame_shape)
        r_squared_map = np.zeros(self.frame_shape)
        ks_pvalue_map = np.zeros(self.frame_shape)
        
        print(f"📊 分析 {rows}x{cols} = {rows*cols} 个像素点...")
        
        for row in range(rows):
            for col in range(cols):
                # 提取像素值
                pixel_values = [frame[row, col] for frame in self.frames]
                pixel_values = np.array(pixel_values)
                
                # 基础统计
                mean_val = np.mean(pixel_values)
                std_val = np.std(pixel_values)
                cv_val = std_val / mean_val if mean_val > 0 else 0
                
                # 存储到地图
                mean_map[row, col] = mean_val
                std_map[row, col] = std_val
                cv_map[row, col] = cv_val
                
                # 高斯拟合
                fit_result = self.fit_gaussian_distribution(pixel_values)
                quality = self.evaluate_fit_quality(pixel_values, fit_result)
                
                r_squared_map[row, col] = quality['r_squared']
                ks_pvalue_map[row, col] = quality['ks_pvalue']
                
                # 存储详细信息
                pixel_key = f"({row}, {col})"
                self.pixel_stats[pixel_key] = {
                    'mean': mean_val,
                    'std': std_val,
                    'cv': cv_val,
                    'values': pixel_values
                }
                self.gaussian_fits[pixel_key] = fit_result
                self.fit_quality[pixel_key] = quality
        
        # 绘制整体分析结果
        self.plot_overall_analysis(mean_map, std_map, cv_map, r_squared_map, ks_pvalue_map)
        
        # 打印整体统计
        self.print_overall_statistics()
    
    def fit_gaussian_distribution(self, values):
        """对数据进行高斯分布拟合"""
        # 使用最大似然估计
        mu = np.mean(values)
        sigma = np.std(values)
        
        # 使用scipy进行更精确的拟合
        try:
            # 定义高斯函数
            def gaussian(x, mu, sigma, amplitude):
                return amplitude * np.exp(-(x - mu)**2 / (2 * sigma**2))
            
            # 创建直方图数据
            hist, bin_edges = np.histogram(values, bins=30, density=True)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # 拟合
            popt, _ = curve_fit(gaussian, bin_centers, hist, p0=[mu, sigma, 1.0])
            mu_fit, sigma_fit, amplitude_fit = popt
            
        except:
            # 如果拟合失败，使用MLE结果
            mu_fit, sigma_fit = mu, sigma
        
        return {
            'mu': mu_fit,
            'sigma': sigma_fit,
            'original_mu': mu,
            'original_sigma': sigma
        }
    
    def evaluate_fit_quality(self, values, fit_result):
        """评估高斯拟合的质量"""
        mu, sigma = fit_result['mu'], fit_result['sigma']
        
        # 计算R² (决定系数)
        # 创建理论高斯分布
        x = np.linspace(values.min(), values.max(), 100)
        theoretical_pdf = stats.norm.pdf(x, mu, sigma)
        
        # 创建实际数据的直方图
        hist, bin_edges = np.histogram(values, bins=30, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # 插值到相同点进行比较
        from scipy.interpolate import interp1d
        try:
            interp_hist = interp1d(bin_centers, hist, bounds_error=False, fill_value=0)
            hist_interp = interp_hist(x)
            
            # 计算R²
            ss_res = np.sum((hist_interp - theoretical_pdf) ** 2)
            ss_tot = np.sum((hist_interp - np.mean(hist_interp)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        except:
            r_squared = 0
        
        # Kolmogorov-Smirnov检验
        try:
            ks_statistic, ks_pvalue = stats.kstest(values, 'norm', args=(mu, sigma))
        except:
            ks_statistic, ks_pvalue = 0, 0
        
        return {
            'r_squared': r_squared,
            'ks_statistic': ks_statistic,
            'ks_pvalue': ks_pvalue,
            'goodness_of_fit': 'Excellent' if r_squared > 0.9 and ks_pvalue > 0.05 else
                              'Good' if r_squared > 0.7 and ks_pvalue > 0.01 else
                              'Fair' if r_squared > 0.5 else 'Poor'
        }
    
    def plot_pixel_distribution(self, row, col, values, fit_result, quality):
        """绘制单个像素点的分布图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 时间序列图
        ax1.plot(values, 'b-', alpha=0.7, linewidth=0.8)
        ax1.axhline(y=fit_result['mu'], color='r', linestyle='--', label=f'均值: {fit_result["mu"]:.6f}')
        ax1.fill_between(range(len(values)), 
                        fit_result['mu'] - fit_result['sigma'], 
                        fit_result['mu'] + fit_result['sigma'], 
                        alpha=0.2, color='r', label=f'±1σ: {fit_result["sigma"]:.6f}')
        ax1.set_title(f'像素 ({row}, {col}) 压力时间序列')
        ax1.set_xlabel('帧数')
        ax1.set_ylabel('压力值')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 分布直方图和高斯拟合
        ax2.hist(values, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='black')
        
        # 绘制拟合的高斯分布
        x = np.linspace(values.min(), values.max(), 100)
        y = stats.norm.pdf(x, fit_result['mu'], fit_result['sigma'])
        ax2.plot(x, y, 'r-', linewidth=2, label=f'高斯拟合 (μ={fit_result["mu"]:.6f}, σ={fit_result["sigma"]:.6f})')
        
        ax2.set_title(f'压力分布直方图 (R²={quality["r_squared"]:.4f}, KS p={quality["ks_pvalue"]:.4f})')
        ax2.set_xlabel('压力值')
        ax2.set_ylabel('密度')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_overall_analysis(self, mean_map, std_map, cv_map, r_squared_map, ks_pvalue_map):
        """绘制整体分析结果"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('像素点压力分布整体分析', fontsize=16)
        
        # 平均值分布
        im1 = axes[0, 0].imshow(mean_map, cmap='viridis')
        axes[0, 0].set_title('平均压力分布')
        axes[0, 0].set_xlabel('列')
        axes[0, 0].set_ylabel('行')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 标准差分布
        im2 = axes[0, 1].imshow(std_map, cmap='plasma')
        axes[0, 1].set_title('标准差分布')
        axes[0, 1].set_xlabel('列')
        axes[0, 1].set_ylabel('行')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 变异系数分布
        im3 = axes[0, 2].imshow(cv_map, cmap='hot')
        axes[0, 2].set_title('变异系数分布 (CV)')
        axes[0, 2].set_xlabel('列')
        axes[0, 2].set_ylabel('行')
        plt.colorbar(im3, ax=axes[0, 2])
        
        # R²分布
        im4 = axes[1, 0].imshow(r_squared_map, cmap='RdYlBu', vmin=0, vmax=1)
        axes[1, 0].set_title('高斯拟合 R² 分布')
        axes[1, 0].set_xlabel('列')
        axes[1, 0].set_ylabel('行')
        plt.colorbar(im4, ax=axes[1, 0])
        
        # KS检验p值分布
        im5 = axes[1, 1].imshow(ks_pvalue_map, cmap='RdYlGn', vmin=0, vmax=1)
        axes[1, 1].set_title('KS检验 p值分布')
        axes[1, 1].set_xlabel('列')
        axes[1, 1].set_ylabel('行')
        plt.colorbar(im5, ax=axes[1, 1])
        
        # 拟合质量评估
        quality_map = np.zeros_like(r_squared_map)
        quality_map[(r_squared_map > 0.9) & (ks_pvalue_map > 0.05)] = 3  # Excellent
        quality_map[(r_squared_map > 0.7) & (ks_pvalue_map > 0.01)] = 2  # Good
        quality_map[(r_squared_map > 0.5)] = 1  # Fair
        quality_map[(r_squared_map <= 0.5)] = 0  # Poor
        
        im6 = axes[1, 2].imshow(quality_map, cmap='RdYlGn', vmin=0, vmax=3)
        axes[1, 2].set_title('拟合质量评估\n(3=Excellent, 2=Good, 1=Fair, 0=Poor)')
        axes[1, 2].set_xlabel('列')
        axes[1, 2].set_ylabel('行')
        plt.colorbar(im6, ax=axes[1, 2])
        
        plt.tight_layout()
        plt.show()
    
    def print_overall_statistics(self):
        """打印整体统计信息"""
        print("\n📊 整体分析结果:")
        print("=" * 50)
        
        # 收集所有像素的统计信息
        all_means = [stats['mean'] for stats in self.pixel_stats.values()]
        all_stds = [stats['std'] for stats in self.pixel_stats.values()]
        all_cvs = [stats['cv'] for stats in self.pixel_stats.values()]
        all_r_squared = [quality['r_squared'] for quality in self.fit_quality.values()]
        all_ks_pvalues = [quality['ks_pvalue'] for quality in self.fit_quality.values()]
        
        print(f"📈 压力值统计:")
        print(f"   平均压力范围: {np.min(all_means):.8f} - {np.max(all_means):.8f}")
        print(f"   平均压力均值: {np.mean(all_means):.8f}")
        print(f"   标准差范围: {np.min(all_stds):.8f} - {np.max(all_stds):.8f}")
        print(f"   变异系数范围: {np.min(all_cvs):.2%} - {np.max(all_cvs):.2%}")
        print(f"   变异系数均值: {np.mean(all_cvs):.2%}")
        
        print(f"\n🎯 高斯拟合质量:")
        print(f"   R² 范围: {np.min(all_r_squared):.4f} - {np.max(all_r_squared):.4f}")
        print(f"   R² 均值: {np.mean(all_r_squared):.4f}")
        print(f"   KS p值范围: {np.min(all_ks_pvalues):.4f} - {np.max(all_ks_pvalues):.4f}")
        print(f"   KS p值均值: {np.mean(all_ks_pvalues):.4f}")
        
        # 拟合质量统计
        excellent_count = sum(1 for q in self.fit_quality.values() if q['goodness_of_fit'] == 'Excellent')
        good_count = sum(1 for q in self.fit_quality.values() if q['goodness_of_fit'] == 'Good')
        fair_count = sum(1 for q in self.fit_quality.values() if q['goodness_of_fit'] == 'Fair')
        poor_count = sum(1 for q in self.fit_quality.values() if q['goodness_of_fit'] == 'Poor')
        total_pixels = len(self.fit_quality)
        
        print(f"\n📊 拟合质量分布:")
        print(f"   Excellent (R²>0.9, p>0.05): {excellent_count} ({excellent_count/total_pixels:.1%})")
        print(f"   Good (R²>0.7, p>0.01): {good_count} ({good_count/total_pixels:.1%})")
        print(f"   Fair (R²>0.5): {fair_count} ({fair_count/total_pixels:.1%})")
        print(f"   Poor (R²≤0.5): {poor_count} ({poor_count/total_pixels:.1%})")
        
        # 找出拟合最好的像素
        best_pixel = max(self.fit_quality.items(), key=lambda x: x[1]['r_squared'])
        worst_pixel = min(self.fit_quality.items(), key=lambda x: x[1]['r_squared'])
        
        print(f"\n🏆 最佳拟合像素: {best_pixel[0]}")
        print(f"   R² = {best_pixel[1]['r_squared']:.4f}, KS p = {best_pixel[1]['ks_pvalue']:.4f}")
        
        print(f"⚠️ 最差拟合像素: {worst_pixel[0]}")
        print(f"   R² = {worst_pixel[1]['r_squared']:.4f}, KS p = {worst_pixel[1]['ks_pvalue']:.4f}")
    
    def save_analysis_results(self, filename):
        """保存分析结果"""
        results = {
            'frame_count': self.frame_count,
            'frame_shape': self.frame_shape,
            'analysis_timestamp': datetime.now().isoformat(),
            'pixel_stats': self.pixel_stats,
            'gaussian_fits': self.gaussian_fits,
            'fit_quality': self.fit_quality
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ 分析结果已保存到: {filename}")

def main():
    """主函数"""
    print("🔍 像素点压力分布分析程序")
    print("=" * 50)
    
    # 示例：分析指定的参考数据文件
    data_file = "C:\Users\84672\Documents\Research\balance-sensor\consistency-test\原始-100.npz"
    
    if os.path.exists(data_file):
        print(f"📁 加载数据文件: {data_file}")
        
        # 创建分析器
        analyzer = PixelDistributionAnalyzer(data_file)
        
        # 分析所有像素
        analyzer.analyze_pixel_distribution()
        
        # 分析特定像素点（可选）
        # analyzer.analyze_pixel_distribution(pixel_pos=(32, 32))
        
        # 保存分析结果
        analyzer.save_analysis_results("pixel_distribution_analysis.json")
        
    else:
        print(f"❌ 数据文件不存在: {data_file}")
        print("请确保有可用的参考数据文件")

if __name__ == "__main__":
    main()