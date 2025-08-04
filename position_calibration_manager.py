#!/usr/bin/env python3
"""
位置校准管理器
用于根据按压重心距离选择最合适的校准关系
"""

import json
import numpy as np
from datetime import datetime
from scipy import stats
import os

class PositionCalibrationManager:
    """位置校准管理器"""
    
    def __init__(self, calibration_file_path=None):
        """
        初始化位置校准管理器
        
        Args:
            calibration_file_path: 校准数据文件路径
        """
        self.calibration_file_path = calibration_file_path
        self.position_data = {}
        self.settings = {}
        self.metadata = {}
        
        if calibration_file_path and os.path.exists(calibration_file_path):
            self.load_calibration_data(calibration_file_path)
    
    def load_calibration_data(self, file_path):
        """加载校准数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.position_data = data.get('positions', {})
            self.settings = data.get('settings', {})
            self.metadata = data.get('metadata', {})
            
            print(f"✅ 成功加载位置校准数据: {file_path}")
            print(f"   包含 {len(self.position_data)} 个校准位置")
            
            return True
        except Exception as e:
            print(f"❌ 加载校准数据失败: {e}")
            return False
    
    def save_calibration_data(self, file_path=None):
        """保存校准数据"""
        if file_path is None:
            file_path = self.calibration_file_path
        
        if file_path is None:
            print("❌ 未指定保存路径")
            return False
        
        try:
            data = {
                'metadata': self.metadata,
                'positions': self.position_data,
                'settings': self.settings
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 校准数据已保存到: {file_path}")
            return True
        except Exception as e:
            print(f"❌ 保存校准数据失败: {e}")
            return False
    
    def calculate_pressure_center(self, pressure_data):
        """
        计算压力数据的重心
        
        Args:
            pressure_data: 64x64的压力数据矩阵
            
        Returns:
            tuple: (center_x, center_y) 重心坐标
        """
        if pressure_data is None or pressure_data.size == 0:
            return None
        
        # 确保数据是64x64
        if pressure_data.shape != (64, 64):
            print(f"⚠️ 压力数据形状不正确: {pressure_data.shape}, 期望 (64, 64)")
            return None
        
        # 计算重心
        total_pressure = np.sum(pressure_data)
        if total_pressure <= 0:
            return None
        
        # 计算加权重心
        y_coords, x_coords = np.mgrid[0:64, 0:64]
        center_x = np.sum(x_coords * pressure_data) / total_pressure
        center_y = np.sum(y_coords * pressure_data) / total_pressure
        
        return (center_x, center_y)
    
    def calculate_distance(self, point1, point2, method='euclidean'):
        """
        计算两点之间的距离
        
        Args:
            point1: (x1, y1)
            point2: (x2, y2)
            method: 距离计算方法 ('euclidean', 'manhattan', 'chebyshev')
            
        Returns:
            float: 距离
        """
        x1, y1 = point1
        x2, y2 = point2
        
        if method == 'euclidean':
            return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        elif method == 'manhattan':
            return abs(x1 - x2) + abs(y1 - y2)
        elif method == 'chebyshev':
            return max(abs(x1 - x2), abs(y1 - y2))
        else:
            print(f"⚠️ 未知的距离计算方法: {method}, 使用欧几里得距离")
            return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def find_nearest_position(self, pressure_center):
        """
        找到距离压力重心最近的校准位置
        
        Args:
            pressure_center: (x, y) 压力重心坐标
            
        Returns:
            tuple: (position_id, position_info, distance)
        """
        if not self.position_data:
            print("⚠️ 没有可用的校准位置数据")
            return None, None, float('inf')
        
        min_distance = float('inf')
        nearest_position_id = None
        nearest_position_info = None
        
        distance_method = self.settings.get('distance_calculation_method', 'euclidean')
        
        for position_id, position_info in self.position_data.items():
            position_coords = (position_info['x'], position_info['y'])
            distance = self.calculate_distance(pressure_center, position_coords, distance_method)
            
            if distance < min_distance:
                min_distance = distance
                nearest_position_id = position_id
                nearest_position_info = position_info
        
        return nearest_position_id, nearest_position_info, min_distance
    
    def get_calibration_parameters(self, pressure_data):
        """
        根据压力数据获取校准参数
        
        Args:
            pressure_data: 64x64的压力数据矩阵
            
        Returns:
            dict: 校准参数 {'slope': float, 'intercept': float, 'position_id': str, 'distance': float}
        """
        # 计算压力重心
        pressure_center = self.calculate_pressure_center(pressure_data)
        if pressure_center is None:
            print("⚠️ 无法计算压力重心")
            return self._get_fallback_parameters()
        
        # 找到最近的校准位置
        position_id, position_info, distance = self.find_nearest_position(pressure_center)
        
        if position_id is None:
            print("⚠️ 未找到合适的校准位置")
            return self._get_fallback_parameters()
        
        # 检查距离阈值
        max_distance = self.settings.get('max_distance_threshold', 50.0)
        if distance > max_distance:
            print(f"⚠️ 距离最近的校准位置过远: {distance:.2f} > {max_distance}")
            return self._get_fallback_parameters()
        
        # 获取校准参数
        calibration = position_info.get('calibration', {})
        slope = calibration.get('slope', 1730.6905)
        intercept = calibration.get('intercept', 126.1741)
        r_squared = calibration.get('r_squared', 0.0)
        
        # 检查R²阈值
        min_r_squared = self.settings.get('min_r_squared_threshold', 0.95)
        if r_squared < min_r_squared:
            print(f"⚠️ 校准位置R²值过低: {r_squared:.4f} < {min_r_squared}")
            return self._get_fallback_parameters()
        
        return {
            'slope': slope,
            'intercept': intercept,
            'position_id': position_id,
            'position_name': position_info.get('name', position_id),
            'distance': distance,
            'r_squared': r_squared,
            'pressure_center': pressure_center
        }
    
    def _get_fallback_parameters(self):
        """获取备用校准参数"""
        fallback_position = self.settings.get('fallback_position', 'center')
        
        if fallback_position in self.position_data:
            calibration = self.position_data[fallback_position].get('calibration', {})
            return {
                'slope': calibration.get('slope', 1730.6905),
                'intercept': calibration.get('intercept', 126.1741),
                'position_id': fallback_position,
                'position_name': self.position_data[fallback_position].get('name', fallback_position),
                'distance': float('inf'),
                'r_squared': calibration.get('r_squared', 0.0),
                'pressure_center': None,
                'is_fallback': True
            }
        else:
            # 默认参数
            return {
                'slope': 1730.6905,
                'intercept': 126.1741,
                'position_id': 'default',
                'position_name': '默认位置',
                'distance': float('inf'),
                'r_squared': 0.0,
                'pressure_center': None,
                'is_fallback': True
            }
    
    def calculate_weight(self, pressure_data, zero_pressure=0.0):
        """
        计算重量
        
        Args:
            pressure_data: 64x64的压力数据矩阵
            zero_pressure: 归零压力
            
        Returns:
            dict: 计算结果
        """
        # 计算总压力
        total_pressure = np.sum(pressure_data)
        
        # 获取校准参数
        cal_params = self.get_calibration_parameters(pressure_data)
        
        # 计算净压力
        net_pressure = total_pressure - zero_pressure
        
        # 计算重量 - 归零后只使用斜率，不使用偏置
        if zero_pressure > 0:
            # 已归零：重量 = 斜率 × 净压力
            weight = cal_params['slope'] * net_pressure
        else:
            # 未归零：重量 = 斜率 × 净压力 + 偏置
            weight = cal_params['slope'] * net_pressure + cal_params['intercept']
        
        weight = max(0.0, weight)  # 确保重量不为负
        
        return {
            'weight': weight,
            'total_pressure': total_pressure,
            'net_pressure': net_pressure,
            'calibration_params': cal_params,
            'is_zeroed': zero_pressure > 0
        }
    
    def update_position_calibration(self, position_id, slope, intercept, r_squared, measurement_count=1):
        """
        更新位置的校准参数
        
        Args:
            position_id: 位置ID
            slope: 斜率
            intercept: 截距
            r_squared: R²值
            measurement_count: 测量次数
        """
        if position_id not in self.position_data:
            print(f"⚠️ 位置 {position_id} 不存在")
            return False
        
        # 更新校准参数
        self.position_data[position_id]['calibration'] = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'measurement_count': measurement_count,
            'last_updated': datetime.now().isoformat()
        }
        
        print(f"✅ 已更新位置 {position_id} 的校准参数")
        return True
    
    def get_position_info(self, position_id):
        """获取位置信息"""
        return self.position_data.get(position_id, {})
    
    def get_all_positions(self):
        """获取所有位置信息"""
        return self.position_data
    
    def get_calibration_summary(self):
        """获取校准数据摘要"""
        summary = {
            'total_positions': len(self.position_data),
            'positions': {}
        }
        
        for position_id, position_info in self.position_data.items():
            calibration = position_info.get('calibration', {})
            summary['positions'][position_id] = {
                'name': position_info.get('name', position_id),
                'coordinates': (position_info['x'], position_info['y']),
                'slope': calibration.get('slope', 0.0),
                'intercept': calibration.get('intercept', 0.0),
                'r_squared': calibration.get('r_squared', 0.0),
                'measurement_count': calibration.get('measurement_count', 0),
                'last_updated': calibration.get('last_updated', '')
            }
        
        return summary 