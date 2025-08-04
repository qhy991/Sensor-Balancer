#!/usr/bin/env python3
"""
所有4096个像素的完整分析程序
分析每个像素的分布特征并生成快速播放的GIF动图
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

class AllPixelsAnalyzer:
    """所有像素分析器"""
    
    def __init__(self, data_file="consistency-test/原始-100.npz"):
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
        
        # 初始化统计数组
        mean_map = np.zeros(self.frame_shape)
        std_map = np.zeros(self.frame_shape)
        cv_map = np.zeros(self.frame_shape)
        min_map = np.zeros(self.frame_shape)
        max_map = np.zeros(self.frame_shape)
        
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
                
                # 存储到地图
                mean_map[row, col] = mean_val
                std_map[row, col] = std_val
                cv_map[row, col] = cv_val
                min_map[row, col] = min_val
                max_map[row, col] = max_val
                
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
        
        # 计算整体统计
        all_cvs = [stats['cv'] for stats in self.pixel_stats.values()]
        all_means = [stats['mean'] for stats in self.pixel_stats.values()]
        all_stds = [stats['std'] for stats in self.pixel_stats.values()]
        
        print(f"\n📊 All Pixels Analysis Complete!")
        print(f"   Total pixels analyzed: {len(self.pixel_stats)}")
        print(f"   Mean CV: {np.mean(all_cvs):.2%}")
        print(f"   CV range: {np.min(all_cvs):.2%} - {np.max(all_cvs):.2%}")
        print(f"   Mean response: {np.mean(all_means):.8f}")
        print(f"   Response range: {np.min(all_means):.8f} - {np.max(all_means):.8f}")
        
        return {
            'mean_map': mean_map,
            'std_map': std_map,
            'cv_map': cv_map,
            'min_map': min_map,
            'max_map': max_map,
            'overall_stats': {
                'mean_cv': np.mean(all_cvs),
                'std_cv': np.std(all_cvs),
                'min_cv': np.min(all_cvs),
                'max_cv': np.max(all_cvs),
                'mean_response': np.mean(all_means),
                'std_response': np.std(all_means)
            }
        }
    
    def find_extreme_pixels(self):
        """找出极值像素"""
        print("\n🎯 Finding extreme pixels...")
        
        # 找出CV最高和最低的像素
        cv_values = [(key, stats['cv']) for key, stats in self.pixel_stats.items()]
        cv_values.sort(key=lambda x: x[1], reverse=True)
        
        highest_cv = cv_values[:5]  # 前5个最高CV
        lowest_cv = cv_values[-5:]  # 后5个最低CV
        
        print(f"📈 Highest CV pixels:")
        for i, (pixel, cv) in enumerate(highest_cv):
            stats = self.pixel_stats[pixel]
            print(f"   {i+1}. {pixel}: CV={cv:.2%}, Mean={stats['mean']:.8f}")
        
        print(f"\n📉 Lowest CV pixels:")
        for i, (pixel, cv) in enumerate(lowest_cv):
            stats = self.pixel_stats[pixel]
            print(f"   {i+1}. {pixel}: CV={cv:.2%}, Mean={stats['mean']:.8f}")
        
        return highest_cv, lowest_cv
    
    def create_fast_animation(self, fps=10, save_gif=True):
        """创建快速播放的GIF动图"""
        print(f"🎬 Creating fast animation (fps={fps})...")
        
        # 分析所有像素
        analysis_results = self.analyze_all_pixels()
        
        # 设置图形
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('All Pixels Distribution Animation', fontsize=16)
        
        # 初始化子图
        # 1. 当前帧热力图
        im1 = axes[0, 0].imshow(self.frames[0], cmap='viridis')
        axes[0, 0].set_title('Current Frame')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 平均响应分布
        im2 = axes[0, 1].imshow(analysis_results['mean_map'], cmap='viridis')
        axes[0, 1].set_title(f'Mean Response Distribution\n(CV: {analysis_results["overall_stats"]["mean_cv"]:.2%})')
        axes[0, 1].set_xlabel('Column')
        axes[0, 1].set_ylabel('Row')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 3. CV分布
        im3 = axes[1, 0].imshow(analysis_results['cv_map'], cmap='hot')
        axes[1, 0].set_title('CV Distribution')
        axes[1, 0].set_xlabel('Column')
        axes[1, 0].set_ylabel('Row')
        plt.colorbar(im3, ax=axes[1, 0])
        
        # 4. 统计信息
        text1 = axes[1, 1].text(0.1, 0.9, '', transform=axes[1, 1].transAxes, 
                               fontsize=10, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        axes[1, 1].set_title('Animation Info')
        axes[1, 1].axis('off')
        
        # 创建动画函数
        def animate(frame_idx):
            # 更新当前帧
            current_frame = self.frames[frame_idx % self.frame_count]
            im1.set_array(current_frame)
            axes[0, 0].set_title(f'Frame {frame_idx + 1}/{self.frame_count}')
            
            # 更新统计信息
            stats_text = f"""Animation Progress:
            
Frame: {frame_idx + 1}/{self.frame_count}
Time: {frame_idx / fps:.1f}s

Overall Statistics:
Mean CV: {analysis_results['overall_stats']['mean_cv']:.2%}
CV Range: {analysis_results['overall_stats']['min_cv']:.2%} - {analysis_results['overall_stats']['max_cv']:.2%}
Mean Response: {analysis_results['overall_stats']['mean_response']:.8f}

Total Pixels: {self.frame_shape[0] * self.frame_shape[1]}
FPS: {fps}"""
            
            text1.set_text(stats_text)
            
            return im1, text1
        
        # 创建动画
        anim = animation.FuncAnimation(fig, animate, frames=self.frame_count, 
                                     interval=1000/fps, blit=False, repeat=True)
        
        plt.tight_layout()
        
        # 保存GIF
        if save_gif:
            print("💾 Saving GIF animation...")
            try:
                gif_filename = f'all_pixels_animation_{fps}fps.gif'
                anim.save(gif_filename, writer='pillow', fps=fps)
                print(f"✅ Animation saved as: {gif_filename}")
            except Exception as e:
                print(f"⚠️ Could not save animation: {e}")
                print("📺 Displaying animation in window...")
        
        plt.show()
        return anim
    
    def create_pixel_scan_animation(self, fps=20, save_gif=True):
        """创建像素扫描动画"""
        print(f"🔍 Creating pixel scan animation (fps={fps})...")
        
        # 设置图形
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Pixel Scan Animation', fontsize=16)
        
        # 初始化子图
        # 1. 传感器阵列（高亮当前像素）
        im1 = axes[0, 0].imshow(self.frames[0], cmap='viridis')
        axes[0, 0].set_title('Sensor Array (Current Pixel Highlighted)')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 当前像素的时间序列
        line1, = axes[0, 1].plot([], [], 'b-', linewidth=1)
        axes[0, 1].set_title('Current Pixel Time Series')
        axes[0, 1].set_xlabel('Frame')
        axes[0, 1].set_ylabel('Pixel Value')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 当前像素的直方图
        hist1 = axes[1, 0].hist([], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 0].set_title('Current Pixel Distribution')
        axes[1, 0].set_xlabel('Pixel Value')
        axes[1, 0].set_ylabel('Frequency')
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
        axes[0, 1].set_ylim(value_range)
        axes[1, 0].set_xlim(value_range)
        
        # 创建动画函数
        def animate(frame_idx):
            # 计算当前像素位置（快速扫描）
            total_pixels = self.frame_shape[0] * self.frame_shape[1]
            pixel_idx = frame_idx % total_pixels
            row = pixel_idx // self.frame_shape[1]
            col = pixel_idx % self.frame_shape[1]
            
            # 更新传感器阵列图
            current_frame = self.frames[frame_idx % self.frame_count]
            im1.set_array(current_frame)
            
            # 在热力图上标记当前像素
            for artist in axes[0, 0].findobj(Rectangle):
                artist.remove()
            rect = Rectangle((col-0.5, row-0.5), 1, 1, linewidth=2, 
                           edgecolor='red', facecolor='none')
            axes[0, 0].add_patch(rect)
            
            # 更新标题
            axes[0, 0].set_title(f'Pixel ({row}, {col}) - {pixel_idx + 1}/{total_pixels}')
            
            # 获取当前像素的时间序列
            pixel_values = [frame[row, col] for frame in self.frames]
            
            # 更新时间序列图
            frames_range = range(len(pixel_values))
            line1.set_data(frames_range, pixel_values)
            
            # 更新直方图
            axes[1, 0].clear()
            axes[1, 0].hist(pixel_values, bins=15, alpha=0.7, color='skyblue', 
                           edgecolor='black', density=True)
            axes[1, 0].set_title(f'Pixel ({row}, {col}) Distribution')
            axes[1, 0].set_xlabel('Pixel Value')
            axes[1, 0].set_ylabel('Density')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].set_xlim(value_range)
            
            # 添加高斯拟合
            if len(pixel_values) > 1:
                from scipy.stats import norm
                x = np.linspace(np.min(pixel_values), np.max(pixel_values), 100)
                mu, sigma = np.mean(pixel_values), np.std(pixel_values)
                y = norm.pdf(x, mu, sigma)
                axes[1, 0].plot(x, y, 'r-', linewidth=2, 
                               label=f'μ={mu:.6f}, σ={sigma:.6f}')
                axes[1, 0].legend()
            
            # 更新统计信息
            stats = self.pixel_stats.get(f"({row}, {col})", {})
            if stats:
                stats_text = f"""Pixel ({row}, {col}):

Mean: {stats['mean']:.8f}
Std: {stats['std']:.8f}
CV: {stats['cv']:.2%}
Range: {stats['min']:.8f} - {stats['max']:.8f}

Progress: {pixel_idx + 1}/{total_pixels}
Scan Speed: {fps} pixels/sec"""
            else:
                stats_text = f"Pixel ({row}, {col}):\nAnalyzing..."
            
            text1.set_text(stats_text)
            
            return im1, line1, text1
        
        # 创建动画
        total_frames = self.frame_shape[0] * self.frame_shape[1]
        anim = animation.FuncAnimation(fig, animate, frames=total_frames, 
                                     interval=1000/fps, blit=False, repeat=True)
        
        plt.tight_layout()
        
        # 保存GIF
        if save_gif:
            print("💾 Saving pixel scan GIF...")
            try:
                gif_filename = f'pixel_scan_animation_{fps}fps.gif'
                anim.save(gif_filename, writer='pillow', fps=fps)
                print(f"✅ Pixel scan animation saved as: {gif_filename}")
            except Exception as e:
                print(f"⚠️ Could not save animation: {e}")
                print("📺 Displaying animation in window...")
        
        plt.show()
        return anim

def main():
    """主函数"""
    print("🔍 All 4096 Pixels Analysis")
    print("=" * 60)
    
    # 创建分析器
    analyzer = AllPixelsAnalyzer()
    
    # 分析所有像素
    print("\n📊 Analyzing all pixels...")
    analysis_results = analyzer.analyze_all_pixels()
    
    # 找出极值像素
    analyzer.find_extreme_pixels()
    
    # 创建快速动画
    print("\n🎬 Creating fast animation...")
    analyzer.create_fast_animation(fps=15, save_gif=True)
    
    # 创建像素扫描动画
    print("\n🔍 Creating pixel scan animation...")
    analyzer.create_pixel_scan_animation(fps=30, save_gif=True)
    
    print("\n✅ All pixels analysis complete!")
    print("📋 Generated files:")
    print("   • all_pixels_animation_15fps.gif (快速帧动画)")
    print("   • pixel_scan_animation_30fps.gif (像素扫描动画)")

if __name__ == "__main__":
    main() 