#!/usr/bin/env python3
"""
单像素直方图动画程序
每一帧显示一个像素的压力值分布直方图，快速扫描所有4096个像素
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class SinglePixelHistogramAnimation:
    """单像素直方图动画器"""
    
    def __init__(self, data_file="C:/Users/84672/Documents/Research/balance-sensor/consistency-test/原始-100.npz"):
        self.frames = None
        self.frame_count = 0
        self.frame_shape = None
        self.pixel_stats = {}  # 存储所有像素的统计信息
        self.load_data(data_file)
        
    def load_data(self, data_file):
        """加载数据"""
        if os.path.exists(data_file):
            data = np.load(data_file)
            self.frames = [frame for frame in data['frames']]
            self.frame_count = len(self.frames)
            self.frame_shape = self.frames[0].shape
            print(f"✅ Loaded {self.frame_count} frames, shape: {self.frame_shape}")
            print(f"📊 Total pixels: {self.frame_shape[0] * self.frame_shape[1]} = {self.frame_shape[0] * self.frame_shape[1]}")
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
    
    def analyze_all_pixels(self):
        """分析所有像素"""
        print("🔍 Analyzing all pixels...")
        
        rows, cols = self.frame_shape
        total_pixels = rows * cols
        
        # 分析每个像素
        for row in range(rows):
            for col in range(cols):
                # 获取像素时间序列
                pixel_values = [frame[row, col] for frame in self.frames]
                pixel_values = np.array(pixel_values)
                
                # 计算统计信息
                mean_val = np.mean(pixel_values)
                std_val = np.std(pixel_values)
                cv_val = std_val / mean_val if mean_val > 0 else 0
                min_val = np.min(pixel_values)
                max_val = np.max(pixel_values)
                
                # 存储详细信息
                pixel_key = f"({row}, {col})"
                self.pixel_stats[pixel_key] = {
                    'mean': mean_val,
                    'std': std_val,
                    'cv': cv_val,
                    'min': min_val,
                    'max': max_val,
                    'range': max_val - min_val,
                    'values': pixel_values
                }
                
                # 显示进度
                pixel_idx = row * cols + col + 1
                if pixel_idx % 500 == 0:
                    print(f"   Progress: {pixel_idx}/{total_pixels} ({pixel_idx/total_pixels:.1%})")
        
        print(f"✅ All pixels analyzed: {len(self.pixel_stats)}")
    
    def create_histogram_animation(self, fps=30, save_gif=True):
        """创建单像素直方图动画"""
        print(f"📊 Creating single pixel histogram animation (fps={fps})...")
        
        # 分析所有像素
        self.analyze_all_pixels()
        
        # 设置图形
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Single Pixel Histogram Animation', fontsize=16)
        
        # 初始化子图
        # 1. 传感器阵列（高亮当前像素）
        im1 = axes[0, 0].imshow(self.frames[0], cmap='viridis')
        axes[0, 0].set_title('Sensor Array (Current Pixel Highlighted)')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 当前像素的直方图（主要显示）
        hist1 = axes[0, 1].hist([], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 1].set_title('Current Pixel Pressure Distribution')
        axes[0, 1].set_xlabel('Pressure Value')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 当前像素的时间序列
        line1, = axes[1, 0].plot([], [], 'b-', linewidth=1)
        axes[1, 0].set_title('Current Pixel Time Series')
        axes[1, 0].set_xlabel('Frame')
        axes[1, 0].set_ylabel('Pressure Value')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 统计信息
        text1 = axes[1, 1].text(0.1, 0.9, '', transform=axes[1, 1].transAxes, 
                               fontsize=10, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        axes[1, 1].set_title('Pixel Statistics')
        axes[1, 1].axis('off')
        
        # 设置坐标轴范围
        all_values = np.array(self.frames).flatten()
        value_range = [np.min(all_values), np.max(all_values)]
        axes[1, 0].set_ylim(value_range)
        axes[0, 1].set_xlim(value_range)
        
        # 存储当前高亮矩形
        current_rect = None
        
        # 创建动画函数
        def animate(frame_idx):
            nonlocal current_rect
            
            # 计算当前像素位置（快速扫描）
            total_pixels = self.frame_shape[0] * self.frame_shape[1]
            pixel_idx = frame_idx % total_pixels
            row = pixel_idx // self.frame_shape[1]
            col = pixel_idx % self.frame_shape[1]
            
            # 更新传感器阵列图
            current_frame = self.frames[frame_idx % self.frame_count]
            im1.set_array(current_frame)
            
            # 在热力图上标记当前像素 - 修复Rectangle删除问题
            if current_rect is not None:
                current_rect.remove()
            current_rect = Rectangle((col-0.5, row-0.5), 1, 1, linewidth=3, 
                                   edgecolor='red', facecolor='none')
            axes[0, 0].add_patch(current_rect)
            
            # 更新标题
            axes[0, 0].set_title(f'Pixel ({row}, {col}) - {pixel_idx + 1}/{total_pixels}')
            
            # 获取当前像素的数据
            pixel_values = [frame[row, col] for frame in self.frames]
            stats = self.pixel_stats.get(f"({row}, {col})", {})
            
            # 更新直方图（主要显示）
            axes[0, 1].clear()
            axes[0, 1].hist(pixel_values, bins=20, alpha=0.7, color='skyblue', 
                           edgecolor='black', density=True)
            axes[0, 1].set_title(f'Pixel ({row}, {col}) Pressure Distribution\nCV: {stats.get("cv", 0):.1%}')
            axes[0, 1].set_xlabel('Pressure Value')
            axes[0, 1].set_ylabel('Density')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].set_xlim(value_range)
            
            # 添加高斯拟合曲线
            if len(pixel_values) > 1 and stats:
                from scipy.stats import norm
                x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
                mu, sigma = stats['mean'], stats['std']
                y = norm.pdf(x, mu, sigma)
                axes[0, 1].plot(x, y, 'r-', linewidth=2, 
                               label=f'Gaussian Fit (μ={mu:.6f}, σ={sigma:.6f})')
                axes[0, 1].legend()
            
            # 更新时间序列图
            frames_range = range(len(pixel_values))
            line1.set_data(frames_range, pixel_values)
            axes[1, 0].set_title(f'Pixel ({row}, {col}) Time Series')
            
            # 更新统计信息
            if stats:
                stats_text = f"""Pixel ({row}, {col}) Statistics:

Mean: {stats['mean']:.8f}
Std: {stats['std']:.8f}
CV: {stats['cv']:.2%}
Min: {stats['min']:.8f}
Max: {stats['max']:.8f}
Range: {stats['range']:.8f}

Progress: {pixel_idx + 1}/{total_pixels}
Scan Speed: {fps} pixels/sec
Total Frames: {len(pixel_values)}"""
            else:
                stats_text = f"Pixel ({row}, {col}):\nAnalyzing..."
            
            text1.set_text(stats_text)
            
            return im1, line1, text1, current_rect
        
        # 创建动画
        total_frames = self.frame_shape[0] * self.frame_shape[1]
        anim = animation.FuncAnimation(fig, animate, frames=total_frames, 
                                     interval=1000/fps, blit=False, repeat=True)
        
        plt.tight_layout()
        
        # 保存GIF
        if save_gif:
            print("💾 Saving histogram GIF...")
            try:
                gif_filename = f'C:/Users/84672/Documents/Research/balance-sensor/single_pixel_histogram_{fps}fps.gif'
                # 减少帧数以加快保存速度
                save_frames = min(total_frames, 100)  # 最多保存100帧
                anim.save(gif_filename, writer='pillow', fps=fps, 
                         savefig_kwargs={'bbox_inches': 'tight', 'pad_inches': 0.1})
                print(f"✅ Histogram animation saved as: {gif_filename}")
            except Exception as e:
                print(f"⚠️ Could not save animation: {e}")
                print("📺 Displaying animation in window...")
        
        plt.show()
        return anim
    
    def create_focused_histogram_animation(self, target_pixels=None, fps=10, save_gif=True):
        """创建聚焦于特定像素的直方图动画"""
        if target_pixels is None:
            # 选择一些有代表性的像素
            target_pixels = [
                (32, 32),  # 中心
                (16, 16),  # 左上角
                (48, 48),  # 右下角
                (32, 16),  # 左中
                (16, 32),  # 上中
            ]
        
        print(f"🎯 Creating focused histogram animation for {len(target_pixels)} pixels...")
        
        # 分析所有像素
        self.analyze_all_pixels()
        
        # 设置图形
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Focused Pixel Histogram Analysis', fontsize=16)
        
        # 初始化子图
        # 1. 传感器阵列热力图
        mean_frame = np.mean(self.frames, axis=0)
        im1 = axes[0, 0].imshow(mean_frame, cmap='viridis')
        axes[0, 0].set_title('Mean Sensor Response')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 标记目标像素
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        for i, (row, col) in enumerate(target_pixels):
            axes[0, 0].plot(col, row, 'o', color=colors[i], markersize=8, 
                           label=f'Pixel {i+1} ({row}, {col})')
        axes[0, 0].legend()
        
        # 2-6. 每个目标像素的直方图
        hist_axes = [axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1], axes[1, 2]]
        
        for i, (row, col) in enumerate(target_pixels):
            pixel_values = [frame[row, col] for frame in self.frames]
            stats = self.pixel_stats.get(f"({row}, {col})", {})
            
            hist_axes[i].hist(pixel_values, bins=15, alpha=0.7, 
                            color=colors[i], edgecolor='black', density=True)
            hist_axes[i].set_title(f'Pixel {i+1} ({row}, {col})\nCV: {stats.get("cv", 0):.1%}')
            hist_axes[i].set_xlabel('Pressure Value')
            hist_axes[i].set_ylabel('Density')
            hist_axes[i].grid(True, alpha=0.3)
            
            # 添加高斯拟合
            if len(pixel_values) > 1 and stats:
                from scipy.stats import norm
                x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
                mu, sigma = stats['mean'], stats['std']
                y = norm.pdf(x, mu, sigma)
                hist_axes[i].plot(x, y, 'k-', linewidth=2, 
                                label=f'μ={mu:.6f}\nσ={sigma:.6f}')
                hist_axes[i].legend()
        
        plt.tight_layout()
        plt.show()
        
        # 打印统计信息
        print("\n📊 Target Pixel Statistics:")
        print("=" * 60)
        for i, (row, col) in enumerate(target_pixels):
            stats = self.pixel_stats.get(f"({row}, {col})", {})
            print(f"Pixel {i+1} ({row}, {col}):")
            print(f"   Mean: {stats.get('mean', 0):.8f}")
            print(f"   Std: {stats.get('std', 0):.8f}")
            print(f"   CV: {stats.get('cv', 0):.2%}")
            print(f"   Range: {stats.get('min', 0):.8f} - {stats.get('max', 0):.8f}")
            print()

def main():
    """主函数"""
    print("📊 Single Pixel Histogram Animation")
    print("=" * 60)
    
    # 创建分析器
    analyzer = SinglePixelHistogramAnimation()
    
    # 创建单像素直方图动画
    print("\n📊 Creating single pixel histogram animation...")
    analyzer.create_histogram_animation(fps=50, save_gif=True)
    
    # 创建聚焦直方图动画
    print("\n🎯 Creating focused histogram animation...")
    analyzer.create_focused_histogram_animation(save_gif=True)
    
    print("\n✅ Histogram animation complete!")
    print("📋 Generated files:")
    print("   • single_pixel_histogram_50fps.gif (单像素直方图动画)")
    print("   • 聚焦直方图分析 (显示在窗口中)")

if __name__ == "__main__":
    main() 