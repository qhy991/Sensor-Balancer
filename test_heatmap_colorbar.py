#!/usr/bin/env python3
"""
测试热力图颜色条显示
"""

import sys
import os
import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_heatmap_colorbar():
    """测试热力图颜色条显示"""
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建测试窗口
    window = QtWidgets.QWidget()
    window.setWindowTitle("热力图颜色条测试")
    window.setGeometry(100, 100, 800, 600)
    
    # 创建布局
    layout = QtWidgets.QVBoxLayout()
    
    # 创建热力图
    heatmap_widget = pg.GraphicsLayoutWidget()
    heatmap_plot = heatmap_widget.addPlot()
    heatmap_plot.setAspectLocked(False)
    
    # 创建图像项
    heatmap_image = pg.ImageItem()
    heatmap_plot.addItem(heatmap_image)
    
    # 添加颜色条 - 测试版本
    colorbar = pg.ColorBarItem(values=(0, 1), colorMap='viridis')
    colorbar.setImageItem(heatmap_image)
    # 注意：ColorBarItem没有setLabel方法，标签通过其他方式设置
    
    # 设置坐标轴
    heatmap_plot.setLabel('left', 'Y轴')
    heatmap_plot.setLabel('bottom', 'X轴')
    heatmap_plot.setTitle('测试热力图')
    
    # 生成测试数据
    test_data = np.random.rand(64, 64) * 0.5 + 0.3
    
    # 模拟传感器敏感度不均匀
    sensitivity_gradient = np.linspace(0.7, 1.3, 64)
    for i in range(64):
        test_data[i, :] *= sensitivity_gradient[i]
    
    # 显示数据
    heatmap_image.setImage(test_data.T)
    
    # 设置颜色范围
    min_val, max_val = test_data.min(), test_data.max()
    heatmap_image.setLevels((min_val, max_val))
    colorbar.setLevels((min_val, max_val))
    
    # 添加信息标签
    info_label = QtWidgets.QLabel(f"数据范围: {min_val:.4f} - {max_val:.4f}")
    info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    
    # 组装布局
    layout.addWidget(heatmap_widget)
    layout.addWidget(info_label)
    
    window.setLayout(layout)
    window.show()
    
    print("✅ 热力图颜色条测试窗口已打开")
    print("请检查:")
    print("1. 热力图右侧是否显示颜色条")
    print("2. 颜色条是否显示数值范围")
    print("3. 颜色条是否有'数值范围'标签")
    print("4. 颜色条的颜色是否与热力图对应")
    
    return app.exec_()

if __name__ == "__main__":
    test_heatmap_colorbar() 