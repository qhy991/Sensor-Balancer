#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏化测试系统配置文件
Gaming Test System Configuration

配置所有系统参数，包括测试设置、检测参数、UI设置等
Configure all system parameters including test settings, detection parameters, UI settings, etc.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class TestConfiguration:
    """测试配置类 / Test Configuration Class"""
    
    # 基础测试参数 / Basic Test Parameters
    test_directions: List[int] = None  # 测试方向 (度) / Test directions (degrees)
    test_duration: float = 3.0  # 每个方向测试时长 (秒) / Test duration per direction (seconds)
    contact_timeout: float = 10.0  # 接触检测超时 (秒) / Contact detection timeout (seconds)
    stabilization_time: float = 1.0  # 稳定时间 (秒) / Stabilization time (seconds)
    
    # 高级测试设置 / Advanced Test Settings
    enable_warmup: bool = True  # 启用预热阶段 / Enable warmup phase
    warmup_duration: float = 2.0  # 预热时间 (秒) / Warmup duration (seconds)
    enable_rest_between_tests: bool = True  # 测试间隔休息 / Rest between tests
    rest_duration: float = 1.0  # 休息时间 (秒) / Rest duration (seconds)
    
    # 重复测试设置 / Repeat Test Settings
    enable_repeat_test: bool = False  # 启用重复测试 / Enable repeat testing
    repeat_count: int = 3  # 重复次数 / Repeat count
    min_success_rate: float = 0.8  # 最小成功率 / Minimum success rate
    
    def __post_init__(self):
        if self.test_directions is None:
            self.test_directions = [0, 45, 90, 135, 180, 225, 270, 315]  # 默认8方向


@dataclass
class DetectionParameters:
    """检测参数类 / Detection Parameters Class"""
    
    # 压力检测参数 / Pressure Detection Parameters
    pressure_threshold: float = 0.01  # 压力检测阈值 / Pressure detection threshold
    contact_stability_threshold: float = 0.005  # 接触稳定性阈值 / Contact stability threshold
    max_pressure_threshold: float = 0.8  # 最大压力阈值 / Maximum pressure threshold
    
    # 角度检测参数 / Angle Detection Parameters  
    angle_confidence_threshold: float = 0.3  # 角度置信度阈值 / Angle confidence threshold
    angle_tolerance: float = 30.0  # 角度误差容差 (度) / Angle error tolerance (degrees)
    angle_strict_tolerance: float = 15.0  # 严格角度容差 (度) / Strict angle tolerance (degrees)
    
    # 信号滤波参数 / Signal Filtering Parameters
    gaussian_sigma: float = 1.0  # 高斯滤波参数 / Gaussian filter sigma
    median_filter_size: int = 3  # 中值滤波大小 / Median filter size
    enable_temporal_filter: bool = True  # 启用时域滤波 / Enable temporal filtering
    temporal_filter_window: int = 5  # 时域滤波窗口 / Temporal filter window
    
    # 形态学参数 / Morphological Parameters
    morphology_kernel_size: int = 3  # 形态学核大小 / Morphology kernel size
    min_contact_area: int = 10  # 最小接触面积 (像素) / Minimum contact area (pixels)
    max_contact_area: int = 1000  # 最大接触面积 (像素) / Maximum contact area (pixels)


@dataclass
class VisualizationSettings:
    """可视化设置类 / Visualization Settings Class"""
    
    # 界面主题 / UI Theme
    theme: str = "dark"  # 主题: "dark", "light", "auto"
    primary_color: str = "#5E81AC"  # 主色调 / Primary color
    secondary_color: str = "#88C0D0"  # 辅助色 / Secondary color
    accent_color: str = "#D08770"  # 强调色 / Accent color
    
    # 字体设置 / Font Settings
    font_family: str = "Microsoft YaHei"  # 字体族 / Font family
    font_size: int = 10  # 字体大小 / Font size
    title_font_size: int = 14  # 标题字体大小 / Title font size
    
    # 图形设置 / Graphics Settings
    figure_dpi: int = 100  # 图形DPI / Figure DPI
    figure_size: tuple = (10, 8)  # 图形尺寸 / Figure size
    animation_interval: int = 50  # 动画间隔 (毫秒) / Animation interval (ms)
    
    # 箱子3D显示设置 / 3D Box Display Settings
    box_size: float = 1.0  # 箱子尺寸 / Box size
    box_color: str = "#4C566A"  # 箱子颜色 / Box color
    arrow_length: float = 0.5  # 箭头长度 / Arrow length
    arrow_color: str = "#BF616A"  # 箭头颜色 / Arrow color
    
    # 实时数据显示 / Real-time Data Display
    enable_real_time_plot: bool = True  # 启用实时绘图 / Enable real-time plotting
    plot_update_interval: int = 100  # 绘图更新间隔 (毫秒) / Plot update interval (ms)
    max_plot_points: int = 1000  # 最大绘图点数 / Maximum plot points


@dataclass
class SystemSettings:
    """系统设置配置"""
    # 数据处理设置
    sensor_data_shape: tuple = (64, 64)
    data_update_frequency: float = 20.0  # Hz
    max_history_length: int = 1000
    cleanup_interval: float = 30.0  # 秒
    
    # 文件路径设置
    data_export_dir: str = "./data/exports"
    log_dir: str = "./logs"
    config_dir: str = "./config"
    
    # 导出设置
    export_formats: list = field(default_factory=lambda: ["csv", "json", "mat"])
    auto_export: bool = False
    compress_exports: bool = False
    
    # 性能设置
    enable_multiprocessing: bool = False
    max_workers: int = 2
    enable_gpu_acceleration: bool = False
    
    # 传感器连接设置
    default_port: str = "0"  # 默认端口号
    port_type: str = "numeric"  # 端口类型：numeric（数字） 或 com（COM端口）
    connection_timeout: float = 5.0  # 连接超时时间（秒）
    retry_attempts: int = 3  # 重试次数
    auto_detect_port: bool = True  # 是否自动检测端口
    
    # 连接说明
    connection_notes: str = "直接输入数字0即可连接，不需要COM前缀"


@dataclass
class CalibrationSettings:
    """校准设置类 / Calibration Settings Class"""
    
    # 校准参数 / Calibration Parameters
    calibration_duration: float = 10.0  # 校准时长 (秒) / Calibration duration (seconds)
    calibration_samples: int = 100  # 校准样本数 / Calibration samples
    noise_level_threshold: float = 0.001  # 噪声水平阈值 / Noise level threshold
    
    # 自动校准 / Auto Calibration
    enable_auto_calibration: bool = True  # 启用自动校准 / Enable auto calibration
    auto_calibration_interval: int = 3600  # 自动校准间隔 (秒) / Auto calibration interval (seconds)
    
    # 校准验证 / Calibration Validation
    enable_calibration_validation: bool = True  # 启用校准验证 / Enable calibration validation
    validation_tolerance: float = 0.05  # 验证容差 / Validation tolerance


class GameTestConfiguration:
    """游戏测试系统完整配置类"""
    
    def __init__(self):
        self.test_config = TestConfiguration()
        self.detection_params = DetectionParameters() 
        self.visualization = VisualizationSettings()
        self.system = SystemSettings()
        self.calibration = CalibrationSettings()
    
    def get_connection_guide(self) -> dict:
        """获取连接指南"""
        return {
            "简化连接步骤": [
                "1. 将传感器通过USB连接到计算机",
                "2. 在端口输入框中输入数字: 0", 
                "3. 点击开始按钮即可连接",
                "注意：不要输入COM0，直接输入数字0"
            ],
            "连接状态指示": {
                "red": "传感器未连接",
                "yellow": "正在连接中",
                "green": "连接成功，数据正常"
            },
            "故障排除": [
                "如果端口0无法连接，可尝试1、2、3等数字",
                "确保USB连接稳定",
                "检查传感器供电状态",
                "重启程序重新连接"
            ],
            "端口配置": {
                "正确示例": "0",
                "错误示例": "COM0",
                "备选端口": ["1", "2", "3"],
                "端口类型": "数字端口，无需COM前缀"
            }
        }
    
    def save_to_file(self, filepath: str):
        """保存配置到文件"""
        import json
        
        config_dict = {
            "test_configuration": self.test_config.__dict__,
            "detection_parameters": self.detection_params.__dict__,
            "visualization_settings": self.visualization.__dict__,
            "system_settings": self.system.__dict__,
            "calibration_settings": self.calibration.__dict__,
            "connection_guide": self.get_connection_guide()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载配置"""
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 更新配置对象
        if 'test_configuration' in config_dict:
            for key, value in config_dict['test_configuration'].items():
                if hasattr(self.test_config, key):
                    setattr(self.test_config, key, value)
        
        if 'detection_parameters' in config_dict:
            for key, value in config_dict['detection_parameters'].items():
                if hasattr(self.detection_params, key):
                    setattr(self.detection_params, key, value)
        
        if 'visualization_settings' in config_dict:
            for key, value in config_dict['visualization_settings'].items():
                if hasattr(self.visualization, key):
                    setattr(self.visualization, key, value)
        
        if 'system_settings' in config_dict:
            for key, value in config_dict['system_settings'].items():
                if hasattr(self.system, key):
                    setattr(self.system, key, value)
        
        if 'calibration_settings' in config_dict:
            for key, value in config_dict['calibration_settings'].items():
                if hasattr(self.calibration, key):
                    setattr(self.calibration, key, value)


# 创建全局配置实例 / Create global configuration instance
config = GameTestConfiguration()

# 常用配置快捷方式 / Common configuration shortcuts
TEST_CONFIG = config.test_config
DETECTION_PARAMS = config.detection_params
VISUALIZATION = config.visualization
SYSTEM = config.system
CALIBRATION = config.calibration

# 导出配置类 / Export configuration classes
__all__ = [
    'GameTestConfiguration',
    'TestConfiguration', 
    'DetectionParameters',
    'VisualizationSettings',
    'SystemSettings',
    'CalibrationSettings',
    'config',
    'TEST_CONFIG',
    'DETECTION_PARAMS', 
    'VISUALIZATION',
    'SYSTEM',
    'CALIBRATION'
] 