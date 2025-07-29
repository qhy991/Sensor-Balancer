"""
颜色条功能测试脚本
用于验证颜色条是否能正确显示渐变色
"""

import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class ColorbarTestWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("颜色条测试")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QtWidgets.QHBoxLayout()
        
        # 左侧：热力图
        heatmap_widget = pg.GraphicsLayoutWidget()
        heatmap_plot = heatmap_widget.addPlot()
        heatmap_plot.setAspectLocked(False)
        
        # 创建测试数据
        test_data = np.random.rand(64, 64) * 0.5 + 0.1
        heatmap_image = pg.ImageItem()
        heatmap_plot.addItem(heatmap_image)
        heatmap_image.setImage(test_data)
        
        # 设置颜色映射
        colormap = pg.colormap.get('viridis')
        heatmap_image.setColorMap(colormap)
        
        # 设置坐标轴
        heatmap_plot.setLabel('left', 'Y轴')
        heatmap_plot.setLabel('bottom', 'X轴')
        heatmap_plot.setTitle('测试热力图')
        
        # 右侧：颜色条
        colorbar_layout = QtWidgets.QVBoxLayout()
        
        # 颜色条标题
        colorbar_title = QtWidgets.QLabel("数值范围")
        colorbar_title.setAlignment(QtCore.Qt.AlignCenter)
        colorbar_title.setStyleSheet("font-weight: bold; font-size: 12px; margin: 5px; color: #333;")
        colorbar_layout.addWidget(colorbar_title)
        
        # 创建颜色条容器
        colorbar_container = QtWidgets.QWidget()
        colorbar_container.setFixedWidth(120)
        colorbar_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        colorbar_container_layout = QtWidgets.QVBoxLayout(colorbar_container)
        colorbar_container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 创建颜色条
        colorbar_widget = pg.GraphicsLayoutWidget()
        colorbar_widget.setFixedHeight(300)
        colorbar_plot = colorbar_widget.addPlot()
        colorbar_plot.setAspectLocked(False)
        
        # 创建颜色条图像
        colorbar_image = pg.ImageItem()
        colorbar_plot.addItem(colorbar_image)
        
        # 设置颜色条坐标轴样式
        colorbar_plot.setLabel('left', '数值', color='#333', size='10pt')
        colorbar_plot.hideAxis('bottom')
        colorbar_plot.hideAxis('top')
        colorbar_plot.hideAxis('right')
        
        # 设置坐标轴样式
        colorbar_plot.getAxis('left').setPen(pg.mkPen(color='#333', width=1))
        colorbar_plot.getAxis('left').setTextPen(pg.mkPen(color='#333'))
        
        # 添加颜色条到容器
        colorbar_container_layout.addWidget(colorbar_widget)
        
        # 添加数值标签
        min_label = QtWidgets.QLabel("最小值: 0.1000")
        min_label.setAlignment(QtCore.Qt.AlignCenter)
        min_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        max_label = QtWidgets.QLabel("最大值: 0.6000")
        max_label.setAlignment(QtCore.Qt.AlignCenter)
        max_label.setStyleSheet("font-size: 10px; color: #666; margin: 2px;")
        
        colorbar_container_layout.addWidget(max_label)
        colorbar_container_layout.addStretch()
        colorbar_container_layout.addWidget(min_label)
        
        colorbar_layout.addWidget(colorbar_container)
        colorbar_layout.addStretch()
        
        # 创建颜色条数据
        min_val, max_val = test_data.min(), test_data.max()
        colorbar_data = np.linspace(max_val, min_val, 100).reshape(100, 1)
        colorbar_image.setImage(colorbar_data)
        colorbar_image.setLevels((min_val, max_val))
        colorbar_image.setColorMap(colormap)
        
        # 设置颜色条标签范围
        colorbar_plot.setYRange(min_val, max_val)
        colorbar_plot.setXRange(0, 1)
        
        # 组装布局
        layout.addWidget(heatmap_widget, 4)
        layout.addLayout(colorbar_layout, 1)
        
        self.setLayout(layout)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ColorbarTestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 