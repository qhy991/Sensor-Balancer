#!/usr/bin/env python3
"""
传感器空间一致性分析程序
专门分析均匀按压场景下传感器的空间响应一致性
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
import warnings

# 设置matplotlib使用英文
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')

class SpatialConsistencyAnalyzer:
    """空间一致性分析器"""
    
    def __init__(self, frames_data):
        """
        初始化分析器
        
        Args:
            frames_data: 帧数据，可以是文件路径或已加载的数据
        """
        self.frames = None
        self.frame_count = 0
        self.frame_shape = None
        
        # 加载数据
        self.load_data(frames_data)
        
        # 分析结果存储
        self.spatial_stats = {}  # 空间统计信息
        self.frame_consistency = {}  # 每帧的一致性分析
        
    def load_data(self, data_source):
        """加载帧数据"""
        if isinstance(data_source, str):
            if data_source.endswith('.npz'):
                data = np.load(data_source)
                self.frames = [frame for frame in data['frames']]
            elif data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    data_dict = json.load(f)
                self.frames = [np.array(frame) for frame in data_dict['frames']]
        else:
            self.frames = data_source
            
        self.frame_count = len(self.frames)
        if self.frames:
            self.frame_shape = self.frames[0].shape
            print(f"✅ Loaded {self.frame_count} frames, shape: {self.frame_shape}")
    
    def analyze_spatial_consistency(self):
        """分析空间一致性"""
        print("🔍 Analyzing spatial consistency for uniform pressure...")
        
        # 1. 分析每帧的空间一致性
        self.analyze_frame_by_frame_consistency()
        
        # 2. 分析整体空间一致性
        self.analyze_overall_spatial_consistency()
        
        # 3. 分析时间稳定性
        self.analyze_temporal_stability()
        
        # 4. 生成可视化结果
        self.plot_spatial_analysis()
        
        # 5. 打印详细报告
        self.print_detailed_report()
    
    def analyze_frame_by_frame_consistency(self):
        """逐帧分析空间一致性"""
        print("📊 Analyzing frame-by-frame spatial consistency...")
        
        for i, frame in enumerate(self.frames):
            # 计算每帧的统计信息
            mean_val = np.mean(frame)
            std_val = np.std(frame)
            cv_val = std_val / mean_val if mean_val > 0 else 0
            
            # 计算空间一致性指标
            # 1. 变异系数 (CV)
            # 2. 最大值与最小值之比
            # 3. 有效响应区域比例
            max_val = np.max(frame)
            min_val = np.min(frame)
            range_ratio = max_val / min_val if min_val > 0 else float('inf')
            
            # 计算有效响应区域（排除噪声）
            threshold = mean_val * 0.1  # 10%阈值
            active_pixels = np.sum(frame > threshold)
            active_ratio = active_pixels / frame.size
            
            # 计算空间均匀性（使用相邻像素差异）
            spatial_variation = self.calculate_spatial_variation(frame)
            
            self.frame_consistency[i] = {
                'mean': mean_val,
                'std': std_val,
                'cv': cv_val,
                'max': max_val,
                'min': min_val,
                'range_ratio': range_ratio,
                'active_pixels': active_pixels,
                'active_ratio': active_ratio,
                'spatial_variation': spatial_variation,
                'frame_data': frame
            }
    
    def calculate_spatial_variation(self, frame):
        """计算空间变化程度"""
        rows, cols = frame.shape
        variations = []
        
        # 计算相邻像素的差异
        for i in range(rows):
            for j in range(cols):
                # 检查四个方向的相邻像素
                neighbors = []
                if i > 0:  # 上
                    neighbors.append(frame[i-1, j])
                if i < rows-1:  # 下
                    neighbors.append(frame[i+1, j])
                if j > 0:  # 左
                    neighbors.append(frame[i, j-1])
                if j < cols-1:  # 右
                    neighbors.append(frame[i, j+1])
                
                if neighbors:
                    # 计算与邻居的平均差异
                    neighbor_mean = np.mean(neighbors)
                    variation = abs(frame[i, j] - neighbor_mean) / neighbor_mean if neighbor_mean > 0 else 0
                    variations.append(variation)
        
        return np.mean(variations) if variations else 0
    
    def analyze_overall_spatial_consistency(self):
        """分析整体空间一致性"""
        print("📈 Analyzing overall spatial consistency...")
        
        # 计算所有帧的平均响应
        all_frames_array = np.array(self.frames)
        mean_response_map = np.mean(all_frames_array, axis=0)
        std_response_map = np.std(all_frames_array, axis=0)
        
        # 整体统计
        overall_mean = np.mean(mean_response_map)
        overall_std = np.std(mean_response_map)
        overall_cv = overall_std / overall_mean if overall_mean > 0 else 0
        
        # 计算空间一致性指标
        spatial_uniformity = self.calculate_spatial_uniformity(mean_response_map)
        
        self.spatial_stats = {
            'mean_response_map': mean_response_map,
            'std_response_map': std_response_map,
            'overall_mean': overall_mean,
            'overall_std': overall_std,
            'overall_cv': overall_cv,
            'spatial_uniformity': spatial_uniformity,
            'frame_consistency_stats': {
                'mean_cv': np.mean([stats['cv'] for stats in self.frame_consistency.values()]),
                'mean_range_ratio': np.mean([stats['range_ratio'] for stats in self.frame_consistency.values()]),
                'mean_active_ratio': np.mean([stats['active_ratio'] for stats in self.frame_consistency.values()]),
                'mean_spatial_variation': np.mean([stats['spatial_variation'] for stats in self.frame_consistency.values()])
            }
        }
    
    def calculate_spatial_uniformity(self, response_map):
        """计算空间均匀性"""
        # 使用多种指标评估空间均匀性
        mean_val = np.mean(response_map)
        
        # 1. 变异系数
        cv = np.std(response_map) / mean_val if mean_val > 0 else 0
        
        # 2. 相对范围
        relative_range = (np.max(response_map) - np.min(response_map)) / mean_val if mean_val > 0 else 0
        
        # 3. 空间自相关（简化版本）
        spatial_correlation = self.calculate_spatial_correlation(response_map)
        
        return {
            'cv': cv,
            'relative_range': relative_range,
            'spatial_correlation': spatial_correlation,
            'uniformity_score': 1.0 / (1.0 + cv + relative_range)  # 综合评分
        }
    
    def calculate_spatial_correlation(self, response_map):
        """计算空间自相关"""
        rows, cols = response_map.shape
        correlations = []
        
        # 计算相邻像素的相关性
        for i in range(rows-1):
            for j in range(cols-1):
                # 计算2x2区域的相关性
                region = response_map[i:i+2, j:j+2]
                if np.std(region) > 0:
                    # 计算区域内像素的相关性
                    flat_region = region.flatten()
                    if len(flat_region) > 1:
                        corr_matrix = np.corrcoef(flat_region.reshape(-1, 1), rowvar=False)
                        if not np.isnan(corr_matrix).all():
                            correlations.append(np.mean(corr_matrix))
        
        return np.mean(correlations) if correlations else 0
    
    def analyze_temporal_stability(self):
        """分析时间稳定性"""
        print("⏰ Analyzing temporal stability...")
        
        # 分析每帧的一致性变化
        frame_cvs = [stats['cv'] for stats in self.frame_consistency.values()]
        frame_means = [stats['mean'] for stats in self.frame_consistency.values()]
        
        # 计算时间稳定性指标
        temporal_cv = np.std(frame_means) / np.mean(frame_means) if np.mean(frame_means) > 0 else 0
        consistency_trend = np.polyfit(range(len(frame_cvs)), frame_cvs, 1)[0]  # 趋势斜率
        
        self.temporal_stats = {
            'frame_cvs': frame_cvs,
            'frame_means': frame_means,
            'temporal_cv': temporal_cv,
            'consistency_trend': consistency_trend,
            'is_stable': temporal_cv < 0.1 and abs(consistency_trend) < 0.001
        }
    
    def plot_spatial_analysis(self):
        """绘制空间分析结果"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Spatial Consistency Analysis for Uniform Pressure', fontsize=16)
        
        # 1. 平均响应分布
        im1 = axes[0, 0].imshow(self.spatial_stats['mean_response_map'], cmap='viridis')
        axes[0, 0].set_title(f'Mean Response Distribution\n(CV: {self.spatial_stats["overall_cv"]:.2%})')
        axes[0, 0].set_xlabel('Column')
        axes[0, 0].set_ylabel('Row')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. 标准差分布
        im2 = axes[0, 1].imshow(self.spatial_stats['std_response_map'], cmap='plasma')
        axes[0, 1].set_title('Standard Deviation Distribution')
        axes[0, 1].set_xlabel('Column')
        axes[0, 1].set_ylabel('Row')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 3. 变异系数分布
        cv_map = self.spatial_stats['std_response_map'] / self.spatial_stats['mean_response_map']
        cv_map = np.where(self.spatial_stats['mean_response_map'] > 0, cv_map, 0)
        im3 = axes[0, 2].imshow(cv_map, cmap='hot')
        axes[0, 2].set_title('Coefficient of Variation Distribution')
        axes[0, 2].set_xlabel('Column')
        axes[0, 2].set_ylabel('Row')
        plt.colorbar(im3, ax=axes[0, 2])
        
        # 4. 时间序列一致性
        frame_cvs = [stats['cv'] for stats in self.frame_consistency.values()]
        axes[1, 0].plot(frame_cvs, 'b-', alpha=0.7)
        axes[1, 0].set_title(f'Temporal Consistency (CV over frames)\nMean: {np.mean(frame_cvs):.2%}')
        axes[1, 0].set_xlabel('Frame')
        axes[1, 0].set_ylabel('Coefficient of Variation')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. 平均响应时间序列
        frame_means = [stats['mean'] for stats in self.frame_consistency.values()]
        axes[1, 1].plot(frame_means, 'g-', alpha=0.7)
        axes[1, 1].set_title(f'Mean Response over Time\nCV: {self.temporal_stats["temporal_cv"]:.2%}')
        axes[1, 1].set_xlabel('Frame')
        axes[1, 1].set_ylabel('Mean Response')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. 空间均匀性评分
        uniformity_map = np.ones_like(self.spatial_stats['mean_response_map']) * self.spatial_stats['spatial_uniformity']['uniformity_score']
        im6 = axes[1, 2].imshow(uniformity_map, cmap='RdYlGn', vmin=0, vmax=1)
        axes[1, 2].set_title(f'Spatial Uniformity Score\n{self.spatial_stats["spatial_uniformity"]["uniformity_score"]:.3f}')
        axes[1, 2].set_xlabel('Column')
        axes[1, 2].set_ylabel('Row')
        plt.colorbar(im6, ax=axes[1, 2])
        
        plt.tight_layout()
        plt.show()
    
    def print_detailed_report(self):
        """打印详细分析报告"""
        print("\n📊 Spatial Consistency Analysis Report")
        print("=" * 60)
        
        # 基本信息
        print(f"📁 Analysis Info:")
        print(f"   Frame count: {self.frame_count}")
        print(f"   Sensor array: {self.frame_shape[0]}x{self.frame_shape[1]} = {self.frame_shape[0]*self.frame_shape[1]} pixels")
        
        # 整体空间一致性
        print(f"\n🎯 Overall Spatial Consistency:")
        print(f"   Mean response: {self.spatial_stats['overall_mean']:.8f}")
        print(f"   Spatial CV: {self.spatial_stats['overall_cv']:.2%}")
        print(f"   Spatial uniformity score: {self.spatial_stats['spatial_uniformity']['uniformity_score']:.3f}")
        print(f"   Relative range: {self.spatial_stats['spatial_uniformity']['relative_range']:.2%}")
        
        # 帧间一致性统计
        frame_stats = self.spatial_stats['frame_consistency_stats']
        print(f"\n📈 Frame-by-Frame Consistency:")
        print(f"   Average CV per frame: {frame_stats['mean_cv']:.2%}")
        print(f"   Average range ratio: {frame_stats['mean_range_ratio']:.2f}")
        print(f"   Average active pixel ratio: {frame_stats['mean_active_ratio']:.1%}")
        print(f"   Average spatial variation: {frame_stats['mean_spatial_variation']:.2%}")
        
        # 时间稳定性
        print(f"\n⏰ Temporal Stability:")
        print(f"   Temporal CV: {self.temporal_stats['temporal_cv']:.2%}")
        print(f"   Consistency trend: {self.temporal_stats['consistency_trend']:.6f}")
        print(f"   Is temporally stable: {'Yes' if self.temporal_stats['is_stable'] else 'No'}")
        
        # 评估结果
        print(f"\n💡 Assessment Results:")
        
        # 空间一致性评估
        spatial_cv = self.spatial_stats['overall_cv']
        if spatial_cv < 0.1:
            spatial_quality = "Excellent"
        elif spatial_cv < 0.2:
            spatial_quality = "Good"
        elif spatial_cv < 0.3:
            spatial_quality = "Fair"
        else:
            spatial_quality = "Poor"
        
        print(f"   1. Spatial Consistency: {spatial_quality} (CV: {spatial_cv:.2%})")
        
        # 时间稳定性评估
        temporal_cv = self.temporal_stats['temporal_cv']
        if temporal_cv < 0.05:
            temporal_quality = "Excellent"
        elif temporal_cv < 0.1:
            temporal_quality = "Good"
        elif temporal_cv < 0.2:
            temporal_quality = "Fair"
        else:
            temporal_quality = "Poor"
        
        print(f"   2. Temporal Stability: {temporal_quality} (CV: {temporal_cv:.2%})")
        
        # 综合评估
        uniformity_score = self.spatial_stats['spatial_uniformity']['uniformity_score']
        if uniformity_score > 0.8:
            overall_quality = "Excellent"
        elif uniformity_score > 0.6:
            overall_quality = "Good"
        elif uniformity_score > 0.4:
            overall_quality = "Fair"
        else:
            overall_quality = "Poor"
        
        print(f"   3. Overall Quality: {overall_quality} (Score: {uniformity_score:.3f})")
        
        # 建议
        print(f"\n🔧 Recommendations:")
        
        if spatial_cv > 0.2:
            print(f"   • Spatial consistency needs improvement")
            print(f"   • Check sensor calibration and mounting")
            print(f"   • Ensure uniform pressure application")
        
        if temporal_cv > 0.1:
            print(f"   • Temporal stability needs improvement")
            print(f"   • Maintain consistent pressure during measurement")
            print(f"   • Reduce environmental vibrations")
        
        if uniformity_score < 0.6:
            print(f"   • Overall sensor performance needs attention")
            print(f"   • Consider sensor replacement or recalibration")
            print(f"   • Improve measurement conditions")
        
        print(f"\n✅ Analysis complete! This analysis is specifically designed for uniform pressure scenarios.")
    
    def save_analysis_results(self, filename):
        """保存分析结果"""
        results = {
            'frame_count': self.frame_count,
            'frame_shape': self.frame_shape,
            'analysis_timestamp': datetime.now().isoformat(),
            'spatial_stats': self.spatial_stats,
            'temporal_stats': self.temporal_stats,
            'frame_consistency': {str(k): v for k, v in self.frame_consistency.items()}
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Spatial consistency analysis results saved to: {filename}")

def main():
    """主函数"""
    print("🔍 Spatial Consistency Analysis for Uniform Pressure")
    print("=" * 60)
    
    # 使用用户提供的原始帧数据文件
    data_file = "consistency-test/原始-100.npz"
    
    if os.path.exists(data_file):
        print(f"📁 Loading data file: {data_file}")
        
        # 创建分析器
        analyzer = SpatialConsistencyAnalyzer(data_file)
        
        # 进行空间一致性分析
        analyzer.analyze_spatial_consistency()
        
        # 保存分析结果
        analyzer.save_analysis_results("spatial_consistency_analysis.json")
        
    else:
        print(f"❌ Data file not found: {data_file}")
        print("Please ensure the original frame data file is available")

if __name__ == "__main__":
    main() 