#!/usr/bin/env python3
"""
总结像素分布分析结果
"""

import json
import numpy as np
import matplotlib.pyplot as plt

def summarize_analysis(filename="pixel_distribution_analysis.json"):
    """总结分析结果"""
    print("📊 Pixel Distribution Analysis Summary")
    print("=" * 50)
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # 基本信息
    print(f"📁 Analysis Info:")
    print(f"   Frame count: {data['frame_count']}")
    print(f"   Frame shape: {data['frame_shape']}")
    print(f"   Analysis time: {data['analysis_timestamp']}")
    
    # 统计信息
    pixel_stats = data['pixel_stats']
    fit_quality = data['fit_quality']
    
    # 收集所有数据
    all_means = [stats['mean'] for stats in pixel_stats.values()]
    all_stds = [stats['std'] for stats in pixel_stats.values()]
    all_cvs = [stats['cv'] for stats in pixel_stats.values()]
    all_r_squared = [quality['r_squared'] for quality in fit_quality.values()]
    all_ks_pvalues = [quality['ks_pvalue'] for quality in fit_quality.values()]
    
    print(f"\n📈 Pressure Statistics:")
    print(f"   Mean pressure range: {np.min(all_means):.8f} - {np.max(all_means):.8f}")
    print(f"   Average mean pressure: {np.mean(all_means):.8f}")
    print(f"   Standard deviation range: {np.min(all_stds):.8f} - {np.max(all_stds):.8f}")
    print(f"   Coefficient of variation range: {np.min(all_cvs):.2%} - {np.max(all_cvs):.2%}")
    print(f"   Average coefficient of variation: {np.mean(all_cvs):.2%}")
    
    print(f"\n🎯 Gaussian Fit Quality:")
    print(f"   R² range: {np.min(all_r_squared):.4f} - {np.max(all_r_squared):.4f}")
    print(f"   Average R²: {np.mean(all_r_squared):.4f}")
    print(f"   KS p-value range: {np.min(all_ks_pvalues):.4f} - {np.max(all_ks_pvalues):.4f}")
    print(f"   Average KS p-value: {np.mean(all_ks_pvalues):.4f}")
    
    # 拟合质量分布
    excellent_count = sum(1 for q in fit_quality.values() if q['goodness_of_fit'] == 'Excellent')
    good_count = sum(1 for q in fit_quality.values() if q['goodness_of_fit'] == 'Good')
    fair_count = sum(1 for q in fit_quality.values() if q['goodness_of_fit'] == 'Fair')
    poor_count = sum(1 for q in fit_quality.values() if q['goodness_of_fit'] == 'Poor')
    total_pixels = len(fit_quality)
    
    print(f"\n📊 Fit Quality Distribution:")
    print(f"   Excellent (R²>0.9, p>0.05): {excellent_count} ({excellent_count/total_pixels:.1%})")
    print(f"   Good (R²>0.7, p>0.01): {good_count} ({good_count/total_pixels:.1%})")
    print(f"   Fair (R²>0.5): {fair_count} ({fair_count/total_pixels:.1%})")
    print(f"   Poor (R²≤0.5): {poor_count} ({poor_count/total_pixels:.1%})")
    
    # 找出最佳和最差拟合的像素
    best_pixel = max(fit_quality.items(), key=lambda x: x[1]['r_squared'])
    worst_pixel = min(fit_quality.items(), key=lambda x: x[1]['r_squared'])
    
    print(f"\n🏆 Best fit pixel: {best_pixel[0]}")
    print(f"   R² = {best_pixel[1]['r_squared']:.4f}")
    print(f"   KS p = {best_pixel[1]['ks_pvalue']:.4f}")
    print(f"   Mean = {pixel_stats[best_pixel[0]]['mean']:.8f}")
    print(f"   Std = {pixel_stats[best_pixel[0]]['std']:.8f}")
    
    print(f"\n⚠️ Worst fit pixel: {worst_pixel[0]}")
    print(f"   R² = {worst_pixel[1]['r_squared']:.4f}")
    print(f"   KS p = {worst_pixel[1]['ks_pvalue']:.4f}")
    print(f"   Mean = {pixel_stats[worst_pixel[0]]['mean']:.8f}")
    print(f"   Std = {pixel_stats[worst_pixel[0]]['std']:.8f}")
    
    # 分析结论
    print(f"\n💡 Analysis Conclusions:")
    print(f"   1. Data Quality: {total_pixels} pixels analyzed from {data['frame_count']} frames")
    print(f"   2. Pressure Range: Values range from {np.min(all_means):.8f} to {np.max(all_means):.8f}")
    print(f"   3. Variability: Average CV is {np.mean(all_cvs):.1%}, indicating high variability")
    print(f"   4. Gaussian Fit: Only {fair_count + good_count + excellent_count} pixels ({((fair_count + good_count + excellent_count)/total_pixels):.1%}) have reasonable Gaussian fits")
    print(f"   5. Best Fit: Pixel {best_pixel[0]} shows excellent Gaussian fit (R²={best_pixel[1]['r_squared']:.4f})")
    print(f"   6. Worst Fit: Pixel {worst_pixel[0]} shows poor Gaussian fit (R²={worst_pixel[1]['r_squared']:.4f})")
    
    # 建议
    print(f"\n🔧 Recommendations:")
    if np.mean(all_r_squared) < 0.3:
        print(f"   • Most pixels do not follow Gaussian distribution well")
        print(f"   • Consider using non-parametric methods for analysis")
        print(f"   • Check for systematic errors or sensor issues")
    else:
        print(f"   • Gaussian approximation is reasonable for most pixels")
        print(f"   • Can use Gaussian parameters for further analysis")
    
    if np.mean(all_cvs) > 1.0:
        print(f"   • High variability suggests unstable measurements")
        print(f"   • Consider improving measurement conditions")
        print(f"   • May need more frames for stable statistics")

if __name__ == "__main__":
    summarize_analysis() 