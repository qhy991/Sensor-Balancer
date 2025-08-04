#!/usr/bin/env python3
"""
简化的像素分布分析程序
展示每个像素点在100帧数据上的数值分布
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

class SimplePixelDistribution:
    """简化的像素分布分析器"""
    
    def __init__(self, data_file="consistency-test/原始-100.npz"):
        self.frames = None
        self.frame_count = 0
        self.frame_shape = None
        self.load_data(data_file)
        
    def load_data(self, data_file):
        """加载数据"""
        if os.path.exists(data_file):
            data = np.load(data_file)
            self.frames = [frame for frame in data['frames']]
            self.frame_count = len(self.frames)
            self.frame_shape = self.frames[0].shape
            print(f"✅ Loaded {self.frame_count} frames, shape: {self.frame_shape}")
        else:
            print(f"❌ Data file not found: {data_file}")
            self.create_demo_data()
    
    def create_demo_data(self):
        """创建演示数据"""
        print("📊 Creating demo data for visualization...")
        self.frame_count = 100
        self.frame_shape = (64, 64)
        
        # 创建模拟的传感器数据
        self.frames = []
        base_pressure = 0.0001
        
        for i in range(self.frame_count):
            frame = np.random.normal(base_pressure, base_pressure * 0.1, self.frame_shape)
            
            # 添加空间变化
            for row in range(self.frame_shape[0]):
                for col in range(self.frame_shape[1]):
                    distance_from_center = np.sqrt((row-32)**2 + (col-32)**2)
                    center_factor = 1.0 - (distance_from_center / 45) * 0.2
                    frame[row, col] *= center_factor
            
            # 添加时间变化
            time_factor = 1.0 + 0.1 * np.sin(i * 0.1)
            frame *= time_factor
            
            self.frames.append(frame)
        
        print(f"✅ Created demo data: {self.frame_count} frames, shape: {self.frame_shape}")
    
    def get_pixel_time_series(self, row, col):
        """获取指定像素的时间序列"""
        pixel_values = [frame[row, col] for frame in self.frames]
        return np.array(pixel_values)
    
    def calculate_pixel_statistics(self, row, col):
        """计算指定像素的统计信息"""
        pixel_values = self.get_pixel_time_series(row, col)
        
        stats = {
            'mean': np.mean(pixel_values),
            'std': np.std(pixel_values),
            'min': np.min(pixel_values),
            'max': np.max(pixel_values),
            'cv': np.std(pixel_values) / np.mean(pixel_values) if np.mean(pixel_values) > 0 else 0,
            'values': pixel_values
        }
        
        return stats
    
    def plot_pixel_distribution(self, row, col):
        """绘制单个像素的分布"""
        pixel_values = self.get_pixel_time_series(row, col)
        stats = self.calculate_pixel_statistics(row, col)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Pixel ({row}, {col}) Distribution Analysis', fontsize=16)
        
        # 1. 时间序列
        axes[0, 0].plot(pixel_values, 'b-', alpha=0.7, linewidth=1)
        axes[0, 0].axhline(y=stats['mean'], color='r', linestyle='--', 
                          label=f'Mean: {stats["mean"]:.8f}')
        axes[0, 0].fill_between(range(len(pixel_values)), 
                               stats['mean'] - stats['std'], 
                               stats['mean'] + stats['std'], 
                               alpha=0.2, color='r', label=f'±1σ: {stats["std"]:.8f}')
        axes[0, 0].set_title(f'Pixel ({row}, {col}) Time Series')
        axes[0, 0].set_xlabel('Frame')
        axes[0, 0].set_ylabel('Pixel Value')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 直方图
        axes[0, 1].hist(pixel_values, bins=20, alpha=0.7, color='skyblue', 
                       edgecolor='black', density=True)
        axes[0, 1].set_title(f'Pixel ({row}, {col}) Value Distribution')
        axes[0, 1].set_xlabel('Pixel Value')
        axes[0, 1].set_ylabel('Density')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 添加高斯拟合
        from scipy.stats import norm
        x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
        y = norm.pdf(x, stats['mean'], stats['std'])
        axes[0, 1].plot(x, y, 'r-', linewidth=2, 
                       label=f'Gaussian Fit (μ={stats["mean"]:.6f}, σ={stats["std"]:.6f})')
        axes[0, 1].legend()
        
        # 3. 箱线图
        axes[1, 0].boxplot(pixel_values, vert=True)
        axes[1, 0].set_title(f'Pixel ({row}, {col}) Box Plot')
        axes[1, 0].set_ylabel('Pixel Value')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 统计信息
        stats_text = f"""Pixel ({row}, {col}) Statistics:

Mean: {stats['mean']:.8f}
Std: {stats['std']:.8f}
CV: {stats['cv']:.2%}
Min: {stats['min']:.8f}
Max: {stats['max']:.8f}
Range: {stats['max'] - stats['min']:.8f}

Total Frames: {len(pixel_values)}
Non-zero values: {np.sum(pixel_values > 0)}"""
        
        axes[1, 1].text(0.1, 0.9, stats_text, transform=axes[1, 1].transAxes, 
                       fontsize=12, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        axes[1, 1].set_title('Statistics')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.show()
        
        return stats
    
    def plot_multiple_pixels(self, pixel_positions):
        """绘制多个像素的分布对比"""
        print(f"📊 Analyzing {len(pixel_positions)} pixels...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Multiple Pixel Distribution Comparison', fontsize=16)
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        # 1. 传感器阵列热力图
        mean_frame = np.mean(self.frames, axis=0)
        im1 = axes[0, 0].imshow(mean_frame, cmap='viridis')
        axes[0, 0].set_title('Mean Sensor Response')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 标记目标像素
        for i, (row, col) in enumerate(pixel_positions):
            axes[0, 0].plot(col, row, 'o', color=colors[i], markersize=8, 
                           label=f'Pixel {i+1} ({row}, {col})')
        axes[0, 0].legend()
        
        # 2-6. 每个像素的直方图
        hist_axes = [axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1], axes[1, 2]]
        
        for i, (row, col) in enumerate(pixel_positions):
            pixel_values = self.get_pixel_time_series(row, col)
            stats = self.calculate_pixel_statistics(row, col)
            
            hist_axes[i].hist(pixel_values, bins=15, alpha=0.7, 
                            color=colors[i], edgecolor='black', density=True)
            hist_axes[i].set_title(f'Pixel {i+1} ({row}, {col})\nCV: {stats["cv"]:.1%}')
            hist_axes[i].set_xlabel('Value')
            hist_axes[i].set_ylabel('Density')
            hist_axes[i].grid(True, alpha=0.3)
            
            # 添加高斯拟合
            from scipy.stats import norm
            x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
            y = norm.pdf(x, stats['mean'], stats['std'])
            hist_axes[i].plot(x, y, 'k-', linewidth=2, 
                            label=f'μ={stats["mean"]:.6f}\nσ={stats["std"]:.6f}')
            hist_axes[i].legend()
        
        plt.tight_layout()
        plt.show()
        
        # 打印统计信息
        print("\n📊 Pixel Statistics Summary:")
        print("=" * 60)
        for i, (row, col) in enumerate(pixel_positions):
            stats = self.calculate_pixel_statistics(row, col)
            print(f"Pixel {i+1} ({row}, {col}):")
            print(f"   Mean: {stats['mean']:.8f}")
            print(f"   Std: {stats['std']:.8f}")
            print(f"   CV: {stats['cv']:.2%}")
            print(f"   Range: {stats['min']:.8f} - {stats['max']:.8f}")
            print()
    
    def plot_spatial_distribution(self):
        """绘制空间分布分析"""
        print("🎯 Analyzing spatial distribution...")
        
        # 计算每个像素的统计信息
        mean_map = np.zeros(self.frame_shape)
        std_map = np.zeros(self.frame_shape)
        cv_map = np.zeros(self.frame_shape)
        
        for row in range(self.frame_shape[0]):
            for col in range(self.frame_shape[1]):
                stats = self.calculate_pixel_statistics(row, col)
                mean_map[row, col] = stats['mean']
                std_map[row, col] = stats['std']
                cv_map[row, col] = stats['cv']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Spatial Distribution Analysis', fontsize=16)
        
        # 1. 平均响应分布
        im1 = axes[0, 0].imshow(mean_map, cmap='viridis')
        axes[0, 0].set_title(f'Mean Response Distribution\n(Overall CV: {np.std(mean_map)/np.mean(mean_map):.2%})')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 标准差分布
        im2 = axes[0, 1].imshow(std_map, cmap='plasma')
        axes[0, 1].set_title('Standard Deviation Distribution')
        axes[0, 1].set_xlabel('Column')
        axes[0, 1].set_ylabel('Row')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 3. 变异系数分布
        im3 = axes[1, 0].imshow(cv_map, cmap='hot')
        axes[1, 0].set_title('Coefficient of Variation Distribution')
        axes[1, 0].set_xlabel('Column')
        axes[1, 0].set_ylabel('Row')
        plt.colorbar(im3, ax=axes[1, 0])
        
        # 4. CV分布直方图
        axes[1, 1].hist(cv_map.flatten(), bins=30, alpha=0.7, color='orange', edgecolor='black')
        axes[1, 1].set_title('CV Distribution Histogram')
        axes[1, 1].set_xlabel('Coefficient of Variation')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # 打印空间统计
        print(f"\n📈 Spatial Statistics:")
        print(f"   Overall mean: {np.mean(mean_map):.8f}")
        print(f"   Overall std: {np.std(mean_map):.8f}")
        print(f"   Overall CV: {np.std(mean_map)/np.mean(mean_map):.2%}")
        print(f"   CV range: {np.min(cv_map):.2%} - {np.max(cv_map):.2%}")
        print(f"   Average CV: {np.mean(cv_map):.2%}")

def main():
    """主函数"""
    print("📊 Simple Pixel Distribution Analysis")
    print("=" * 60)
    
    # 创建分析器
    analyzer = SimplePixelDistribution()
    
    # 分析单个像素
    print("\n🎯 Analyzing individual pixels...")
    target_pixels = [(32, 32), (16, 16), (48, 48), (32, 16), (16, 32)]
    
    for row, col in target_pixels:
        print(f"\n📊 Analyzing pixel ({row}, {col})...")
        stats = analyzer.plot_pixel_distribution(row, col)
        print(f"   CV: {stats['cv']:.2%}")
    
    # 分析多个像素对比
    print("\n📊 Comparing multiple pixels...")
    analyzer.plot_multiple_pixels(target_pixels)
    
    # 分析空间分布
    print("\n🎯 Analyzing spatial distribution...")
    analyzer.plot_spatial_distribution()
    
    print("\n✅ Analysis complete!")
    print("📋 Key observations:")
    print("   • Each pixel shows different distribution patterns")
    print("   • CV values indicate variability across pixels")
    print("   • Spatial analysis reveals sensor uniformity")

if __name__ == "__main__":
    main() 