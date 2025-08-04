#!/usr/bin/env python3
"""
像素点数值分布动态直方图分析
展示每个像素点在100帧数据上的数值分布变化
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import json
import os
from datetime import datetime

class PixelDistributionAnimation:
    """像素分布动态分析器"""
    
    def __init__(self, data_file="consistency-test/原始-100.npz"):
        self.frames = None
        self.frame_count = 0
        self.frame_shape = None
        self.current_pixel = [0, 0]  # 当前显示的像素位置
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
            # 创建模拟数据用于演示
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
            # 创建基础压力分布
            frame = np.random.normal(base_pressure, base_pressure * 0.1, self.frame_shape)
            
            # 添加空间变化（中心到边缘的渐变）
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
    
    def create_animation(self, save_animation=True):
        """创建动态直方图动画"""
        print("🎬 Creating pixel distribution animation...")
        
        # 设置图形
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Pixel Distribution Analysis Animation', fontsize=16)
        
        # 初始化子图
        # 1. 传感器阵列热力图（显示当前像素位置）
        im1 = axes[0, 0].imshow(self.frames[0], cmap='viridis')
        axes[0, 0].set_title('Sensor Array (Current Pixel Highlighted)')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 当前像素的时间序列
        line1, = axes[0, 1].plot([], [], 'b-', linewidth=1)
        axes[0, 1].set_title('Pixel Time Series')
        axes[0, 1].set_xlabel('Frame')
        axes[0, 1].set_ylabel('Pixel Value')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 当前像素的直方图
        hist1 = axes[1, 0].hist([], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 0].set_title('Pixel Value Distribution')
        axes[1, 0].set_xlabel('Pixel Value')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 统计信息文本
        text1 = axes[1, 1].text(0.1, 0.9, '', transform=axes[1, 1].transAxes, 
                               fontsize=12, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        axes[1, 1].set_title('Pixel Statistics')
        axes[1, 1].axis('off')
        
        # 设置坐标轴范围
        all_values = np.array(self.frames).flatten()
        value_range = [np.min(all_values), np.max(all_values)]
        axes[0, 1].set_ylim(value_range)
        axes[1, 0].set_xlim(value_range)
        
        # 创建动画函数
        def animate(frame_idx):
            # 计算当前像素位置（遍历整个阵列）
            total_pixels = self.frame_shape[0] * self.frame_shape[1]
            pixel_idx = frame_idx % total_pixels
            row = pixel_idx // self.frame_shape[1]
            col = pixel_idx % self.frame_shape[1]
            
            self.current_pixel = [row, col]
            
            # 更新传感器阵列图（高亮当前像素）
            current_frame = self.frames[frame_idx % self.frame_count]
            im1.set_array(current_frame)
            
            # 在热力图上标记当前像素
            for artist in axes[0, 0].findobj(Rectangle):
                artist.remove()
            rect = Rectangle((col-0.5, row-0.5), 1, 1, linewidth=3, 
                           edgecolor='red', facecolor='none')
            axes[0, 0].add_patch(rect)
            
            # 更新标题显示当前像素位置
            axes[0, 0].set_title(f'Sensor Array - Pixel ({row}, {col})')
            
            # 获取当前像素的时间序列
            pixel_values = self.get_pixel_time_series(row, col)
            
            # 更新时间序列图
            frames_range = range(len(pixel_values))
            line1.set_data(frames_range, pixel_values)
            axes[0, 1].set_title(f'Pixel ({row}, {col}) Time Series')
            
            # 更新直方图
            axes[1, 0].clear()
            axes[1, 0].hist(pixel_values, bins=20, alpha=0.7, color='skyblue', 
                           edgecolor='black', density=True)
            axes[1, 0].set_title(f'Pixel ({row}, {col}) Value Distribution')
            axes[1, 0].set_xlabel('Pixel Value')
            axes[1, 0].set_ylabel('Density')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].set_xlim(value_range)
            
            # 添加高斯拟合曲线
            if len(pixel_values) > 1:
                from scipy.stats import norm
                x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
                mu, sigma = np.mean(pixel_values), np.std(pixel_values)
                y = norm.pdf(x, mu, sigma)
                axes[1, 0].plot(x, y, 'r-', linewidth=2, label=f'Gaussian Fit (μ={mu:.6f}, σ={sigma:.6f})')
                axes[1, 0].legend()
            
            # 更新统计信息
            stats = self.calculate_pixel_statistics(row, col)
            stats_text = f"""Pixel ({row}, {col}) Statistics:
            
Mean: {stats['mean']:.8f}
Std: {stats['std']:.8f}
CV: {stats['cv']:.2%}
Min: {stats['min']:.8f}
Max: {stats['max']:.8f}
Range: {stats['max'] - stats['min']:.8f}

Frame: {frame_idx + 1}/{self.frame_count}
Pixel: {pixel_idx + 1}/{total_pixels}"""
            
            text1.set_text(stats_text)
            
            return im1, line1, text1
        
        # 创建动画
        total_frames = self.frame_shape[0] * self.frame_shape[1]
        anim = animation.FuncAnimation(fig, animate, frames=total_frames, 
                                     interval=500, blit=False, repeat=True)
        
        plt.tight_layout()
        
        # 保存动画
        if save_animation:
            print("💾 Saving animation...")
            try:
                anim.save('pixel_distribution_animation.gif', writer='pillow', fps=2)
                print("✅ Animation saved as: pixel_distribution_animation.gif")
            except Exception as e:
                print(f"⚠️ Could not save animation: {e}")
                print("📺 Displaying animation in window...")
        
        plt.show()
        return anim
    
    def create_focused_animation(self, target_pixels=None, save_animation=True):
        """创建聚焦于特定像素的动画"""
        if target_pixels is None:
            # 选择一些有代表性的像素
            target_pixels = [
                (32, 32),  # 中心
                (16, 16),  # 左上角
                (48, 48),  # 右下角
                (32, 16),  # 左中
                (16, 32),  # 上中
            ]
        
        print(f"🎯 Creating focused animation for {len(target_pixels)} pixels...")
        
        # 设置图形
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Focused Pixel Distribution Analysis', fontsize=16)
        
        # 初始化子图
        # 1. 传感器阵列热力图
        im1 = axes[0, 0].imshow(self.frames[0], cmap='viridis')
        axes[0, 0].set_title('Sensor Array (Target Pixels Highlighted)')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 标记目标像素
        for i, (row, col) in enumerate(target_pixels):
            rect = Rectangle((col-0.5, row-0.5), 1, 1, linewidth=2, 
                           edgecolor=['red', 'blue', 'green', 'orange', 'purple'][i], 
                           facecolor='none')
            axes[0, 0].add_patch(rect)
            axes[0, 0].text(col, row, f'{i+1}', ha='center', va='center', 
                           color='white', fontweight='bold')
        
        # 2-6. 每个目标像素的直方图
        hist_axes = [axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1], axes[1, 2]]
        hist_plots = []
        
        for i, (row, col) in enumerate(target_pixels):
            pixel_values = self.get_pixel_time_series(row, col)
            hist, bins, _ = hist_axes[i].hist(pixel_values, bins=15, alpha=0.7, 
                                            color=['red', 'blue', 'green', 'orange', 'purple'][i],
                                            edgecolor='black', density=True)
            hist_axes[i].set_title(f'Pixel ({row}, {col}) Distribution')
            hist_axes[i].set_xlabel('Value')
            hist_axes[i].set_ylabel('Density')
            hist_axes[i].grid(True, alpha=0.3)
            
            # 添加高斯拟合
            if len(pixel_values) > 1:
                from scipy.stats import norm
                x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
                mu, sigma = np.mean(pixel_values), np.std(pixel_values)
                y = norm.pdf(x, mu, sigma)
                hist_axes[i].plot(x, y, 'k-', linewidth=2, 
                                label=f'μ={mu:.6f}\nσ={sigma:.6f}\nCV={sigma/mu:.1%}')
                hist_axes[i].legend()
            
            hist_plots.append((hist, bins))
        
        plt.tight_layout()
        plt.show()
        
        # 打印统计信息
        print("\n📊 Target Pixel Statistics:")
        print("=" * 60)
        for i, (row, col) in enumerate(target_pixels):
            stats = self.calculate_pixel_statistics(row, col)
            print(f"Pixel {i+1} ({row}, {col}):")
            print(f"   Mean: {stats['mean']:.8f}")
            print(f"   Std: {stats['std']:.8f}")
            print(f"   CV: {stats['cv']:.2%}")
            print(f"   Range: {stats['min']:.8f} - {stats['max']:.8f}")
            print()

def main():
    """主函数"""
    print("🎬 Pixel Distribution Animation Analysis")
    print("=" * 60)
    
    # 创建分析器
    analyzer = PixelDistributionAnimation()
    
    # 创建完整动画
    print("\n🎬 Creating full animation (all pixels)...")
    analyzer.create_animation(save_animation=True)
    
    # 创建聚焦动画
    print("\n🎯 Creating focused animation (target pixels)...")
    analyzer.create_focused_animation(save_animation=True)
    
    print("\n✅ Animation analysis complete!")
    print("📋 Generated files:")
    print("   • pixel_distribution_animation.gif (完整动画)")
    print("   • 聚焦分析图 (显示在窗口中)")

if __name__ == "__main__":
    main() 