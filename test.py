import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QFileDialog, QMessageBox
)

# --- 核心依赖 ---
import pyqtgraph as pg
import pyqtgraph.exporters

# ----------------------------------------------------------------------
# 方案一：使用 pyqtgraph.exporters 的可靠保存函数 (推荐)
# ----------------------------------------------------------------------
def save_pyqtgraph_plot_robust(plot_item, filename):
    """
    使用 pyqtgraph.exporters 来可靠地保存图表。
    这个函数确保在导出前所有内容都已渲染。

    参数:
        plot_item: 需要保存的图表对象 (例如 PlotWidget.getPlotItem())。
        filename (str): 保存的文件路径。
    """
    try:
        print(f"🚀 [Robust Save] 准备使用 ImageExporter 保存到: {filename}")
        
        # 1. 创建一个与图表项关联的导出器
        exporter = pg.exporters.ImageExporter(plot_item)

        # 2. (可选) 设置导出参数，例如宽度可以提高分辨率
        # exporter.parameters()['width'] = 1920
        
        # 3. 执行导出
        exporter.export(filename)
        
        print(f"✅ [Robust Save] 图表已成功保存。")
        return True
    except Exception as e:
        print(f"❌ [Robust Save] 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# ----------------------------------------------------------------------
# 主测试窗口
# ----------------------------------------------------------------------
class TestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQtGraph 保存功能测试")
        self.setGeometry(100, 100, 800, 600)

        # --- 设置中心窗口和布局 ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # --- 创建一个 PlotWidget ---
        # PlotWidget 是一个方便的封装，它内部包含了一个 PlotItem
        self.plot_widget = pg.PlotWidget()
        
        # --- 绘制一些示例数据 ---
        x = np.linspace(0, 10, 1000)
        y = np.sin(x) * np.exp(-x / 5)
        self.plot_widget.plot(x, y, pen=pg.mkPen('b', width=2), name="示例曲线")
        self.plot_widget.setTitle("一个简单的示例图表")
        self.plot_widget.setLabel('left', '振幅')
        self.plot_widget.setLabel('bottom', '时间 (s)')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()

        # --- 创建保存按钮 ---
        self.save_button = QPushButton("保存图表到文件...")
        self.save_button.setFixedHeight(40)
        self.save_button.setStyleSheet("font-size: 14px; background-color: #4CAF50; color: white; border-radius: 5px;")
        
        # --- 将组件添加到布局 ---
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.save_button)

        # --- 连接信号和槽 ---
        self.save_button.clicked.connect(self.save_plot)

    def save_plot(self):
        """
        槽函数：当点击保存按钮时触发。
        """
        print("💡 '保存图表' 按钮被点击，准备弹出文件对话框。")
        
        # 弹出文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存图表",
            "my_beautiful_plot.png", # 默认文件名
            "PNG 图片 (*.png);;JPG 图片 (*.jpg)"
        )

        # 如果用户选择了文件名，则继续保存
        if filename:
            # 调用我们可靠的保存函数
            # 注意：我们将 self.plot_widget.getPlotItem() 传递给它
            # getPlotItem() 获取 PlotWidget 内部实际管理绘图的对象
            success = save_pyqtgraph_plot_robust(self.plot_widget.getPlotItem(), filename)
            
            # 向用户报告结果
            if success:
                QMessageBox.information(self, "成功", f"图表已成功保存到:\n{filename}")
            else:
                QMessageBox.warning(self, "失败", "保存图表时发生错误，请查看控制台输出获取详细信息。")
        else:
            print("用户取消了保存操作。")


# --- 程序入口 ---
if __name__ == '__main__':
    # 确保 pyqtgraph 在高清屏幕上显示正常
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    main_window = TestApp()
    main_window.show()
    sys.exit(app.exec_())