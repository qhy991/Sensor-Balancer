#!/usr/bin/env python3
"""
测试图表渲染和保存功能
验证修复后的自动保存对话框是否正常工作
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from datetime import datetime

class TestPlotRenderingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试图表渲染和保存")
        self.setGeometry(100, 100, 500, 300)
        
        layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("这个测试将验证图表渲染和保存功能是否正常工作")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 测试按钮
        test_btn = QPushButton("测试图表渲染和保存")
        test_btn.clicked.connect(self.test_plot_rendering)
        layout.addWidget(test_btn)
        
        # 状态标签
        self.status_label = QLabel("状态: 等待测试")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def test_plot_rendering(self):
        """测试图表渲染和保存"""
        self.status_label.setText("状态: 正在创建图表...")
        QApplication.processEvents()
        
        # 创建测试数据
        x = np.linspace(0, 10, 100)
        y = np.sin(x) * np.cos(x * 0.5)
        
        # 创建PyQtGraph窗口
        plot_window = pg.GraphicsLayoutWidget()
        plot_window.setWindowTitle('测试图表渲染')
        plot_window.resize(800, 600)
        
        # 创建绘图
        plot = plot_window.addPlot(title="测试图表渲染")
        plot.plot(x, y, pen='blue', symbol='o', symbolSize=8)
        plot.setLabel('left', 'Y轴')
        plot.setLabel('bottom', 'X轴')
        plot.showGrid(x=True, y=True, alpha=0.3)
        
        # 添加一些额外的元素来测试复杂渲染
        # 添加文本
        text_item = pg.TextItem(text="测试文本", color='red', anchor=(0, 0))
        text_item.setPos(2, 0.5)
        plot.addItem(text_item)
        
        # 添加矩形
        rect = pg.ROI([1, -0.5], [2, 1], pen=pg.mkPen('green', width=2))
        plot.addItem(rect)
        
        # 显示窗口
        plot_window.show()
        
        # 强制更新和渲染
        plot_window.scene().update()
        QApplication.processEvents()
        
        self.status_label.setText("状态: 图表已显示，等待渲染完成...")
        QApplication.processEvents()
        
        # 使用改进的渲染检查
        QTimer.singleShot(800, lambda: self.auto_save_dialog(plot_window))
    
    def auto_save_dialog(self, plot_window):
        """自动弹出保存对话框"""
        try:
            self.status_label.setText("状态: 正在准备保存...")
            QApplication.processEvents()
            
            # 确保图表窗口仍然有效
            if not hasattr(plot_window, 'scene'):
                print(f"⚠️ 图表窗口无效，无法保存")
                self.status_label.setText("状态: 图表窗口无效")
                return
            
            # 强制更新图表多次，确保完全渲染
            for i in range(5):
                plot_window.scene().update()
                QApplication.processEvents()
                QTimer.singleShot(50, lambda: None)  # 短暂延迟
            
            # 等待更长时间确保渲染完成
            QTimer.singleShot(500, lambda: self._show_save_dialog(plot_window))
            
        except Exception as e:
            print(f"⚠️ 自动保存对话框出错: {e}")
            self.status_label.setText(f"状态: 错误 - {e}")
            import traceback
            traceback.print_exc()
    
    def _show_save_dialog(self, plot_window):
        """显示保存对话框"""
        try:
            self.status_label.setText("状态: 弹出保存对话框...")
            QApplication.processEvents()
            
            # 再次确保图表窗口有效
            if not hasattr(plot_window, 'scene'):
                print(f"⚠️ 图表窗口无效，无法保存")
                self.status_label.setText("状态: 图表窗口无效")
                return
            
            # 最后一次强制更新
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 弹出保存对话框
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存测试图表", 
                f"C:/Users/84672/Documents/Research/test_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
            )
            
            if filename:
                print(f"🔍 用户选择保存到: {filename}")
                self.status_label.setText("状态: 正在保存...")
                QApplication.processEvents()
                
                # 保存前再次确保渲染
                plot_window.scene().update()
                QApplication.processEvents()
                
                # 尝试多种保存方法
                success = False
                
                # 方法1: 使用ImageExporter
                try:
                    if hasattr(pg, 'exporters') and hasattr(pg.exporters, 'ImageExporter'):
                        exporter = pg.exporters.ImageExporter(plot_window.scene())
                        exporter.export(filename)
                        print(f"✅ 使用ImageExporter保存成功")
                        success = True
                except Exception as e:
                    print(f"⚠️ ImageExporter保存失败: {e}")
                
                # 方法2: 使用grab方法
                if not success:
                    try:
                        if hasattr(plot_window, 'grab'):
                            pixmap = plot_window.grab()
                            if pixmap.save(filename):
                                print(f"✅ 使用grab方法保存成功")
                                success = True
                    except Exception as e:
                        print(f"⚠️ grab方法保存失败: {e}")
                
                # 方法3: 使用render方法
                if not success:
                    try:
                        if hasattr(plot_window, 'render'):
                            from PyQt5.QtGui import QPixmap
                            pixmap = QPixmap(plot_window.size())
                            plot_window.render(pixmap)
                            if pixmap.save(filename):
                                print(f"✅ 使用render方法保存成功")
                                success = True
                    except Exception as e:
                        print(f"⚠️ render方法保存失败: {e}")
                
                if success:
                    print(f"✅ 测试图表已保存到: {filename}")
                    self.status_label.setText("状态: 保存成功!")
                    QMessageBox.information(self, "成功", f"测试图表已保存到:\n{filename}")
                else:
                    print(f"❌ 所有保存方法都失败了")
                    self.status_label.setText("状态: 保存失败")
                    QMessageBox.warning(self, "保存失败", "所有保存方法都失败了")
            else:
                print(f"💡 用户取消了保存")
                self.status_label.setText("状态: 用户取消保存")
                
        except Exception as e:
            print(f"⚠️ 显示保存对话框出错: {e}")
            self.status_label.setText(f"状态: 错误 - {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建测试窗口
    window = TestPlotRenderingWidget()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 