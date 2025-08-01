#!/usr/bin/env python3
"""
测试PositionConsistencyWidget的图表保存功能
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
import pyqtgraph as pg
import pyqtgraph.exporters

def save_pyqtgraph_plot_robust(plot_item, filename):
    """使用 pyqtgraph.exporters 来可靠地保存图表"""
    try:
        print(f"🚀 [Robust Save] 准备使用 ImageExporter 保存到: {filename}")
        exporter = pg.exporters.ImageExporter(plot_item)
        exporter.export(filename)
        print(f"✅ [Robust Save] 图表已成功保存。")
        return True
    except Exception as e:
        print(f"❌ [Robust Save] 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_pyqtgraph_plot(plot_widget, filename):
    """通用的PyQtGraph图表保存函数 - 改进版本"""
    try:
        print(f"🔍 开始保存图表到: {filename}")
        
        # 方法1: 尝试使用ImageExporter (最可靠的方法)
        try:
            if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                # 确定正确的plot_item
                if hasattr(plot_widget, 'scene'):
                    # 如果是GraphicsLayoutWidget，使用scene
                    exporter = pg.exporters.ImageExporter(plot_widget.scene())
                elif hasattr(plot_widget, 'plotItem'):
                    # 如果是PlotWidget，使用plotItem
                    exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
                elif hasattr(plot_widget, 'getPlotItem'):
                    # 如果是PlotWidget，使用getPlotItem()
                    exporter = pg.exporters.ImageExporter(plot_widget.getPlotItem())
                else:
                    # 直接使用plot_widget
                    exporter = pg.exporters.ImageExporter(plot_widget)
                
                # 强制更新场景
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                
                # 执行导出
                exporter.export(filename)
                print(f"✅ 使用ImageExporter保存图表成功: {filename}")
                return True
        except Exception as e:
            print(f"⚠️ ImageExporter保存失败: {e}")
        
        # 方法2: 尝试使用grab方法截图
        try:
            if hasattr(plot_widget, 'grab'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                pixmap = plot_widget.grab()
                if pixmap.save(filename):
                    print(f"✅ 使用grab方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ grab方法保存失败: {e}")
        
        # 方法3: 尝试使用QWidget的render方法
        try:
            if hasattr(plot_widget, 'render'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                from PyQt5.QtGui import QPixmap
                pixmap = QPixmap(plot_widget.size())
                plot_widget.render(pixmap)
                if pixmap.save(filename):
                    print(f"✅ 使用render方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ render方法保存失败: {e}")
        
        # 方法4: 尝试使用QScreen截图
        try:
            screen = QApplication.primaryScreen()
            if screen and hasattr(plot_widget, 'winId'):
                # 强制更新
                if hasattr(plot_widget, 'scene'):
                    plot_widget.scene().update()
                QApplication.processEvents()
                
                pixmap = screen.grabWindow(plot_widget.winId())
                if pixmap.save(filename):
                    print(f"✅ 使用屏幕截图方法保存图表成功: {filename}")
                    return True
        except Exception as e:
            print(f"⚠️ 屏幕截图方法保存失败: {e}")
        
        print(f"❌ 所有保存方法都失败了")
        return False
        
    except Exception as e:
        print(f"❌ 保存图表时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

class TestPositionConsistencyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PositionConsistencyWidget 保存功能测试")
        self.setGeometry(100, 100, 1000, 700)

        # --- 设置中心窗口和布局 ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # --- 创建一个 GraphicsLayoutWidget (模拟一致性分析图表) ---
        self.plot_widget = pg.GraphicsLayoutWidget()
        
        # 创建2x2的子图布局
        # 1. 位置敏感性对比 (左上)
        p1 = self.plot_widget.addPlot(row=0, col=0, title="各位置平均敏感性对比")
        p1.setLabel('left', '平均敏感性')
        p1.setLabel('bottom', '位置')
        p1.showGrid(x=True, y=True, alpha=0.3)
        
        # 模拟数据
        positions = ['中心', '左上', '右上', '左下', '右下']
        sensitivities = [0.0012, 0.0011, 0.0013, 0.0010, 0.0014]
        
        # 创建柱状图
        x_pos = np.arange(len(positions))
        bars1 = pg.BarGraphItem(x=x_pos, height=sensitivities, width=0.6, 
                              brush='skyblue', pen='black')
        p1.addItem(bars1)
        
        # 设置X轴标签
        ax1 = p1.getAxis('bottom')
        ax1.setTicks([[(i, name) for i, name in enumerate(positions)]])
        
        # 2. 位置变异系数对比 (右上)
        p2 = self.plot_widget.addPlot(row=0, col=1, title="各位置平均变异系数对比")
        p2.setLabel('left', '平均变异系数')
        p2.setLabel('bottom', '位置')
        p2.showGrid(x=True, y=True, alpha=0.3)
        
        cvs = [0.02, 0.03, 0.025, 0.035, 0.015]
        bars2 = pg.BarGraphItem(x=x_pos, height=cvs, width=0.6, 
                              brush='lightcoral', pen='black')
        p2.addItem(bars2)
        
        # 设置X轴标签
        ax2 = p2.getAxis('bottom')
        ax2.setTicks([[(i, name) for i, name in enumerate(positions)]])
        
        # 3. 敏感性分布直方图 (左下)
        p3 = self.plot_widget.addPlot(row=1, col=0, title="所有位置敏感性分布")
        p3.setLabel('left', '频次')
        p3.setLabel('bottom', '敏感性')
        p3.showGrid(x=True, y=True, alpha=0.3)
        
        # 模拟直方图数据
        all_sensitivities = np.random.normal(0.0012, 0.0002, 100)
        hist, bins = np.histogram(all_sensitivities, bins=20)
        x_hist = (bins[:-1] + bins[1:]) / 2
        bars3 = pg.BarGraphItem(x=x_hist, height=hist, width=(bins[1]-bins[0])*0.8,
                              brush='lightgreen', pen='black')
        p3.addItem(bars3)
        
        # 4. 位置一致性热力图 (右下)
        p4 = self.plot_widget.addPlot(row=1, col=1, title="位置-砝码敏感性热力图")
        p4.setLabel('left', '位置')
        p4.setLabel('bottom', '砝码')
        
        # 模拟热力图数据
        consistency_matrix = np.random.rand(5, 3) * 0.002 + 0.001
        img_item = pg.ImageItem(consistency_matrix)
        p4.addItem(img_item)
        
        # 设置颜色映射
        try:
            colormap = pg.colormap.get('viridis')
            img_item.setColorMap(colormap)
        except:
            pass
        
        # 设置坐标轴
        p4.setAspectLocked(False)
        p4.invertY(True)  # Y轴向下
        
        # 设置X轴标签
        ax4_x = p4.getAxis('bottom')
        ax4_x.setTicks([[(i, f'W{i+1}') for i in range(3)]])
        
        # 设置Y轴标签
        ax4_y = p4.getAxis('left')
        y_labels = positions
        ax4_y.setTicks([[(i, label) for i, label in enumerate(y_labels)]])
        
        # 添加数值标签
        for i in range(5):
            for j in range(3):
                text = pg.TextItem(text=f'{consistency_matrix[i, j]:.4f}', 
                                 color='white', anchor=(0.5, 0.5))
                text.setPos(j, i)
                p4.addItem(text)

        # --- 创建保存按钮 ---
        self.save_button = QPushButton("保存一致性分析图表")
        self.save_button.setFixedHeight(40)
        self.save_button.setStyleSheet("font-size: 14px; background-color: #4CAF50; color: white; border-radius: 5px;")
        
        # --- 将组件添加到布局 ---
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.save_button)

        # --- 连接信号和槽 ---
        self.save_button.clicked.connect(self.save_plot)

    def save_plot(self):
        """槽函数：当点击保存按钮时触发"""
        print("💡 '保存一致性分析图表' 按钮被点击，准备弹出文件对话框。")
        
        # 弹出文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存一致性分析图表",
            "consistency_analysis_test.png", # 默认文件名
            "PNG 图片 (*.png);;JPG 图片 (*.jpg)"
        )

        # 如果用户选择了文件名，则继续保存
        if filename:
            # 保存前确保渲染 - 多次强制更新
            for i in range(3):
                self.plot_widget.scene().update()
                QApplication.processEvents()
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, lambda: None)  # 短暂延迟
            
            # 方法1: 尝试使用改进的保存函数
            success = save_pyqtgraph_plot(self.plot_widget, filename)
            
            if not success:
                # 方法2: 如果失败，尝试使用robust保存函数
                print("⚠️ 改进的保存函数失败，尝试使用robust保存函数...")
                success = save_pyqtgraph_plot_robust(self.plot_widget.scene(), filename)
            
            # 向用户报告结果
            if success:
                QMessageBox.information(self, "成功", f"一致性分析图表已成功保存到:\n{filename}")
            else:
                QMessageBox.warning(self, "失败", "保存图表时发生错误，请查看控制台输出获取详细信息。")
        else:
            print("用户取消了保存操作。")


# --- 程序入口 ---
if __name__ == '__main__':
    # 确保 pyqtgraph 在高清屏幕上显示正常
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    main_window = TestPositionConsistencyApp()
    main_window.show()
    sys.exit(app.exec_()) 