#!/usr/bin/env python3
"""
测试图表保存功能
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg

def test_plot_save():
    """测试图表保存功能"""
    app = QApplication(sys.argv)
    
    # 创建测试数据
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    # 创建PyQtGraph窗口
    plot_window = pg.GraphicsLayoutWidget()
    plot_window.setWindowTitle('测试图表')
    plot_window.resize(800, 600)
    
    # 创建绘图
    plot = plot_window.addPlot(title="测试图表")
    plot.plot(x, y, pen='blue', symbol='o')
    plot.setLabel('left', 'Y轴')
    plot.setLabel('bottom', 'X轴')
    plot.showGrid(x=True, y=True, alpha=0.3)
    
    # 显示窗口
    plot_window.show()
    
    # 强制更新
    plot_window.scene().update()
    app.processEvents()
    
    # 测试保存
    try:
        # 方法1: 使用grab方法
        pixmap = plot_window.grab()
        if pixmap.save("test_plot_grab.png"):
            print("✅ grab方法保存成功")
        else:
            print("❌ grab方法保存失败")
        
        # 方法2: 使用render方法
        pixmap2 = pg.QtGui.QPixmap(plot_window.size())
        plot_window.render(pixmap2)
        if pixmap2.save("test_plot_render.png"):
            print("✅ render方法保存成功")
        else:
            print("❌ render方法保存失败")
        
        # 方法3: 使用ImageExporter
        try:
            exporter = pg.exporters.ImageExporter(plot_window.scene())
            exporter.export("test_plot_exporter.png")
            print("✅ ImageExporter保存成功")
        except Exception as e:
            print(f"❌ ImageExporter保存失败: {e}")
        
    except Exception as e:
        print(f"❌ 保存测试失败: {e}")
    
    print("测试完成，请检查生成的图片文件")
    
    # 保持窗口打开一段时间
    import time
    time.sleep(2)
    
    app.quit()

if __name__ == "__main__":
    test_plot_save() 