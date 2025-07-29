"""
传感器一致性分析增强模块
包含多种一致性评估方法和校正算法
"""

import numpy as np
import scipy.ndimage as ndimage
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import cv2

class ConsistencyAnalyzer:
    """传感器一致性分析器"""
    
    def __init__(self):
        self.baseline_map = None
        self.sensitivity_map = None
        self.dead_zones = None
        self.reference_pressure = None
        
    def analyze_consistency(self, max_value_data, reference_pressure=None):
        """
        全面的一致性分析
        
        Args:
            max_value_data: dict {(x, y): max_value} 最大值数据
            reference_pressure: float 参考压力值
            
        Returns:
            dict: 包含多种一致性指标的分析结果
        """
        if not max_value_data:
            return None
            
        # 转换为矩阵形状
        matrix = self._dict_to_matrix(max_value_data)
        
        analysis_results = {
            'basic_stats': self._basic_statistics(matrix),
            'spatial_consistency': self._spatial_consistency_analysis(matrix),
            'uniformity_metrics': self._uniformity_metrics(matrix),
            'dead_zone_analysis': self._dead_zone_analysis(matrix),
            'sensitivity_mapping': self._sensitivity_mapping(matrix, reference_pressure),
            'cluster_analysis': self._cluster_analysis(matrix),
            'gradient_analysis': self._gradient_analysis(matrix)
        }
        
        return analysis_results
    
    def _dict_to_matrix(self, data_dict):
        """将字典数据转换为矩阵"""
        if not data_dict:
            return np.array([])
            
        max_x = max(pos[0] for pos in data_dict.keys()) + 1
        max_y = max(pos[1] for pos in data_dict.keys()) + 1
        
        matrix = np.zeros((max_x, max_y))
        for (x, y), value in data_dict.items():
            matrix[x, y] = value
            
        return matrix
    
    def _basic_statistics(self, matrix):
        """基础统计分析"""
        valid_data = matrix[matrix > 0]  # 排除零值
        
        if len(valid_data) == 0:
            return None
            
        return {
            'mean': np.mean(valid_data),
            'std': np.std(valid_data),
            'cv': np.std(valid_data) / np.mean(valid_data) if np.mean(valid_data) > 0 else 0,
            'min': np.min(valid_data),
            'max': np.max(valid_data),
            'median': np.median(valid_data),
            'q25': np.percentile(valid_data, 25),
            'q75': np.percentile(valid_data, 75),
            'active_sensors': len(valid_data),
            'total_sensors': matrix.size
        }
    
    def _spatial_consistency_analysis(self, matrix):
        """空间一致性分析"""
        # 计算每个传感器与其邻居的差异
        neighbor_diff = []
        smoothness_map = np.zeros_like(matrix)
        
        for i in range(1, matrix.shape[0]-1):
            for j in range(1, matrix.shape[1]-1):
                if matrix[i, j] > 0:
                    # 8邻域
                    neighbors = matrix[i-1:i+2, j-1:j+2]
                    valid_neighbors = neighbors[neighbors > 0]
                    
                    if len(valid_neighbors) > 1:
                        center_value = matrix[i, j]
                        neighbor_values = valid_neighbors[valid_neighbors != center_value]
                        
                        if len(neighbor_values) > 0:
                            avg_neighbor = np.mean(neighbor_values)
                            diff = abs(center_value - avg_neighbor) / max(center_value, avg_neighbor)
                            neighbor_diff.append(diff)
                            smoothness_map[i, j] = diff
        
        return {
            'neighbor_consistency': np.mean(neighbor_diff) if neighbor_diff else 0,
            'smoothness_std': np.std(neighbor_diff) if neighbor_diff else 0,
            'smoothness_map': smoothness_map,
            'high_variation_points': len([d for d in neighbor_diff if d > 0.3]) if neighbor_diff else 0
        }
    
    def _uniformity_metrics(self, matrix):
        """均匀性指标"""
        valid_data = matrix[matrix > 0]
        
        if len(valid_data) == 0:
            return None
            
        # 计算均匀性指数
        mean_val = np.mean(valid_data)
        uniformity_index = 1 - (np.std(valid_data) / mean_val) if mean_val > 0 else 0
        
        # 计算响应范围
        response_range = np.max(valid_data) - np.min(valid_data)
        relative_range = response_range / mean_val if mean_val > 0 else 0
        
        # 计算离群值比例
        z_scores = np.abs(zscore(valid_data))
        outlier_ratio = len(z_scores[z_scores > 2.5]) / len(z_scores)
        
        return {
            'uniformity_index': uniformity_index,
            'response_range': response_range,
            'relative_range': relative_range,
            'outlier_ratio': outlier_ratio,
            'response_ratio': np.max(valid_data) / np.min(valid_data) if np.min(valid_data) > 0 else float('inf')
        }
    
    def _dead_zone_analysis(self, matrix):
        """死区分析"""
        # 识别死区（无响应或响应极低的区域）
        threshold = np.mean(matrix[matrix > 0]) * 0.1 if np.any(matrix > 0) else 0
        dead_zones = matrix < threshold
        
        # 连通域分析
        labeled_zones, num_zones = ndimage.label(dead_zones)
        zone_sizes = []
        
        for i in range(1, num_zones + 1):
            zone_size = np.sum(labeled_zones == i)
            zone_sizes.append(zone_size)
        
        return {
            'dead_zone_ratio': np.sum(dead_zones) / matrix.size,
            'num_dead_zones': num_zones,
            'avg_dead_zone_size': np.mean(zone_sizes) if zone_sizes else 0,
            'largest_dead_zone': max(zone_sizes) if zone_sizes else 0,
            'dead_zone_map': dead_zones
        }
    
    def _sensitivity_mapping(self, matrix, reference_pressure=None):
        """敏感度映射"""
        if reference_pressure is None:
            # 使用中位数作为参考
            reference_pressure = np.median(matrix[matrix > 0]) if np.any(matrix > 0) else 1.0
        
        # 计算相对敏感度
        sensitivity_map = np.zeros_like(matrix)
        valid_mask = matrix > 0
        
        if np.any(valid_mask):
            sensitivity_map[valid_mask] = matrix[valid_mask] / reference_pressure
        
        # 敏感度统计
        valid_sensitivity = sensitivity_map[valid_mask]
        
        return {
            'reference_pressure': reference_pressure,
            'sensitivity_map': sensitivity_map,
            'avg_sensitivity': np.mean(valid_sensitivity) if len(valid_sensitivity) > 0 else 0,
            'sensitivity_std': np.std(valid_sensitivity) if len(valid_sensitivity) > 0 else 0,
            'low_sensitivity_ratio': len(valid_sensitivity[valid_sensitivity < 0.5]) / len(valid_sensitivity) if len(valid_sensitivity) > 0 else 0,
            'high_sensitivity_ratio': len(valid_sensitivity[valid_sensitivity > 1.5]) / len(valid_sensitivity) if len(valid_sensitivity) > 0 else 0
        }
    
    def _cluster_analysis(self, matrix):
        """聚类分析，识别性能相似的传感器区域"""
        valid_data = matrix[matrix > 0]
        
        if len(valid_data) < 10:  # 数据太少无法聚类
            return None
        
        # 准备聚类数据
        coordinates = []
        values = []
        
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if matrix[i, j] > 0:
                    coordinates.append([i, j])
                    values.append(matrix[i, j])
        
        # 特征组合：位置 + 响应值
        features = np.column_stack([coordinates, values])
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # K-means聚类
        n_clusters = min(5, len(features) // 10)  # 动态确定聚类数
        if n_clusters < 2:
            return None
            
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # 分析聚类结果
        cluster_stats = {}
        for i in range(n_clusters):
            cluster_mask = cluster_labels == i
            cluster_values = np.array(values)[cluster_mask]
            
            cluster_stats[f'cluster_{i}'] = {
                'size': np.sum(cluster_mask),
                'mean_response': np.mean(cluster_values),
                'std_response': np.std(cluster_values),
                'coordinates': np.array(coordinates)[cluster_mask]
            }
        
        return {
            'n_clusters': n_clusters,
            'cluster_labels': cluster_labels,
            'cluster_stats': cluster_stats,
            'silhouette_score': self._calculate_silhouette_score(features_scaled, cluster_labels)
        }
    
    def _gradient_analysis(self, matrix):
        """梯度分析，检测响应的空间变化"""
        if matrix.size == 0:
            return None
            
        # 计算梯度
        grad_x, grad_y = np.gradient(matrix)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 只考虑有效数据区域
        valid_mask = matrix > 0
        if not np.any(valid_mask):
            return None
            
        valid_gradient = gradient_magnitude[valid_mask]
        
        return {
            'avg_gradient': np.mean(valid_gradient),
            'max_gradient': np.max(valid_gradient),
            'gradient_std': np.std(valid_gradient),
            'gradient_map': gradient_magnitude,
            'high_gradient_ratio': len(valid_gradient[valid_gradient > np.mean(valid_gradient) + 2*np.std(valid_gradient)]) / len(valid_gradient)
        }
    
    def _calculate_silhouette_score(self, features, labels):
        """计算轮廓系数"""
        try:
            from sklearn.metrics import silhouette_score
            if len(np.unique(labels)) > 1:
                return silhouette_score(features, labels)
        except:
            pass
        return 0.0
    
    def generate_calibration_map(self, matrix, target_response=None):
        """
        生成校正映射
        
        Args:
            matrix: 传感器响应矩阵
            target_response: 目标响应值，默认使用中位数
            
        Returns:
            校正系数矩阵
        """
        if target_response is None:
            valid_data = matrix[matrix > 0]
            target_response = np.median(valid_data) if len(valid_data) > 0 else 1.0
        
        calibration_map = np.ones_like(matrix)
        valid_mask = matrix > 0
        
        # 计算校正系数
        calibration_map[valid_mask] = target_response / matrix[valid_mask]
        
        # 限制校正系数范围，避免过度校正
        calibration_map = np.clip(calibration_map, 0.1, 10.0)
        
        return {
            'calibration_map': calibration_map,
            'target_response': target_response,
            'correction_range': (np.min(calibration_map[valid_mask]), np.max(calibration_map[valid_mask])) if np.any(valid_mask) else (1.0, 1.0)
        }


class CalibrationSystem:
    """校正系统"""
    
    def __init__(self):
        self.calibration_coefficients = None
        self.calibration_method = 'linear'
        
    def linear_calibration(self, raw_data, calibration_map):
        """线性校正"""
        return raw_data * calibration_map
    
    def polynomial_calibration(self, raw_data, coefficients):
        """多项式校正"""
        # 实现2次多项式校正
        corrected = np.zeros_like(raw_data)
        for i in range(raw_data.shape[0]):
            for j in range(raw_data.shape[1]):
                if len(coefficients) >= 3:
                    x = raw_data[i, j]
                    corrected[i, j] = coefficients[0] + coefficients[1] * x + coefficients[2] * x**2
                else:
                    corrected[i, j] = raw_data[i, j]
        return corrected
    
    def adaptive_calibration(self, raw_data, sensitivity_map, dead_zone_map):
        """自适应校正"""
        corrected = raw_data.copy()
        
        # 对低敏感度区域进行增强
        low_sensitivity_mask = (sensitivity_map < 0.7) & (sensitivity_map > 0)
        corrected[low_sensitivity_mask] *= 1.5
        
        # 对高敏感度区域进行衰减
        high_sensitivity_mask = sensitivity_map > 1.3
        corrected[high_sensitivity_mask] *= 0.8
        
        # 死区插值修复
        if np.any(dead_zone_map):
            corrected = self._interpolate_dead_zones(corrected, dead_zone_map)
        
        return corrected
    
    def _interpolate_dead_zones(self, data, dead_zone_map):
        """插值修复死区"""
        # 使用OpenCV的inpaint功能修复死区
        if not np.any(dead_zone_map):
            return data
            
        # 转换为uint8格式
        data_normalized = ((data - data.min()) / (data.max() - data.min()) * 255).astype(np.uint8)
        mask = dead_zone_map.astype(np.uint8) * 255
        
        # 修复
        inpainted = cv2.inpaint(data_normalized, mask, 3, cv2.INPAINT_TELEA)
        
        # 转换回原始范围
        result = inpainted.astype(np.float64) / 255.0 * (data.max() - data.min()) + data.min()
        
        return result


def run_comprehensive_analysis(consistency_data):
    """运行全面的一致性分析"""
    analyzer = ConsistencyAnalyzer()
    
    # 执行分析
    results = analyzer.analyze_consistency(consistency_data)
    
    if results:
        print("=== 传感器一致性分析报告 ===")
        
        # 基础统计
        basic = results['basic_stats']
        if basic:
            print(f"\n基础统计:")
            print(f"  有效传感器: {basic['active_sensors']}/{basic['total_sensors']} ({basic['active_sensors']/basic['total_sensors']*100:.1f}%)")
            print(f"  响应范围: {basic['min']:.4f} - {basic['max']:.4f}")
            print(f"  平均响应: {basic['mean']:.4f} ± {basic['std']:.4f}")
            print(f"  变异系数: {basic['cv']:.3f} ({basic['cv']*100:.1f}%)")
        
        # 均匀性指标
        uniformity = results['uniformity_metrics']
        if uniformity:
            print(f"\n均匀性评估:")
            print(f"  均匀性指数: {uniformity['uniformity_index']:.3f}")
            print(f"  响应比率: {uniformity['response_ratio']:.2f}")
            print(f"  离群值比例: {uniformity['outlier_ratio']:.1%}")
        
        # 空间一致性
        spatial = results['spatial_consistency']
        if spatial:
            print(f"\n空间一致性:")
            print(f"  邻域一致性: {spatial['neighbor_consistency']:.3f}")
            print(f"  高变异点数: {spatial['high_variation_points']}")
        
        # 死区分析
        dead_zone = results['dead_zone_analysis']
        if dead_zone:
            print(f"\n死区分析:")
            print(f"  死区比例: {dead_zone['dead_zone_ratio']:.1%}")
            print(f"  死区数量: {dead_zone['num_dead_zones']}")
            print(f"  最大死区: {dead_zone['largest_dead_zone']} 像素")
        
        # 敏感度映射
        sensitivity = results['sensitivity_mapping']
        if sensitivity:
            print(f"\n敏感度分析:")
            print(f"  平均敏感度: {sensitivity['avg_sensitivity']:.3f}")
            print(f"  低敏感度比例: {sensitivity['low_sensitivity_ratio']:.1%}")
            print(f"  高敏感度比例: {sensitivity['high_sensitivity_ratio']:.1%}")
    
    return results


# 使用示例
if __name__ == "__main__":
    # 模拟一致性数据
    test_data = {}
    for i in range(32):
        for j in range(32):
            # 模拟不均匀的传感器响应
            base_response = 0.5 + 0.3 * np.sin(i/10) * np.cos(j/10)
            noise = np.random.normal(0, 0.1)
            test_data[(i, j)] = max(0, base_response + noise)
    
    # 运行分析
    results = run_comprehensive_analysis(test_data)