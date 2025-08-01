#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试弹窗绘图功能
"""

import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def test_dialog_plot():
    """测试弹窗绘图"""
    print("🔍 测试弹窗绘图功能...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QtWidgets.QWidget()
    main_window.setWindowTitle("弹窗绘图测试")
    main_window.setGeometry(100, 100, 400, 300)
    
    # 创建布局
    layout = QVBoxLayout()
    
    # 添加标签
    label = QLabel("点击按钮测试弹窗绘图")
    layout.addWidget(label)
    
    # 添加测试按钮
    test_btn = QPushButton("测试弹窗绘图")
    
    def create_dialog_plot():
        """创建弹窗绘图"""
        try:
            # 创建对话框窗口
            plot_dialog = QDialog()
            plot_dialog.setWindowTitle("测试弹窗绘图")
            plot_dialog.setGeometry(100, 100, 1200, 800)
            plot_dialog.setModal(False)  # 非模态对话框
            plot_dialog.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
            
            # 创建matplotlib图形
            fig = Figure(figsize=(12, 8), dpi=100)
            canvas = FigureCanvas(fig)
            
            # 创建2x2的子图布局
            ax1 = fig.add_subplot(221)
            ax2 = fig.add_subplot(222)
            ax3 = fig.add_subplot(223)
            ax4 = fig.add_subplot(224)
            
            # 生成测试数据
            x = np.linspace(0, 10, 50)
            y1 = np.sin(x)
            y2 = np.cos(x)
            y3 = np.tan(x)
            y4 = np.exp(-x/5)
            
            # 绘制数据
            ax1.plot(x, y1, 'b-', linewidth=2, label='sin(x)')
            ax1.set_title('子图1: sin(x)', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            ax2.plot(x, y2, 'r-', linewidth=2, label='cos(x)')
            ax2.set_title('子图2: cos(x)', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            ax3.plot(x, y3, 'g-', linewidth=2, label='tan(x)')
            ax3.set_title('子图3: tan(x)', fontsize=12, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            ax4.plot(x, y4, 'm-', linewidth=2, label='exp(-x/5)')
            ax4.set_title('子图4: exp(-x/5)', fontsize=12, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # 调整子图间距
            fig.tight_layout(pad=2.0)
            
            # 创建信息标签
            info_text = "测试弹窗绘图功能 - 包含4个子图的完整显示"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("font-size: 12px; font-weight: bold; color: blue; padding: 5px;")
            info_label.setAlignment(QtCore.Qt.AlignCenter)
            
            # 创建按钮
            close_btn = QPushButton("关闭")
            close_btn.setStyleSheet("QPushButton { font-size: 12px; padding: 8px; }")
            close_btn.clicked.connect(plot_dialog.accept)
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            button_layout.addWidget(close_btn)
            button_layout.addStretch()
            
            # 创建主布局
            main_layout = QVBoxLayout()
            main_layout.addWidget(info_label)
            main_layout.addWidget(canvas, 1)  # 图表占据主要空间
            main_layout.addLayout(button_layout)
            
            plot_dialog.setLayout(main_layout)
            
            # 显示对话框
            plot_dialog.show()
            plot_dialog.raise_()
            plot_dialog.activateWindow()
            
            print("✅ 测试弹窗绘图已创建")
            
        except Exception as e:
            print(f"❌ 创建弹窗绘图失败: {e}")
            import traceback
            traceback.print_exc()
    
    test_btn.clicked.connect(create_dialog_plot)
    layout.addWidget(test_btn)
    
    # 设置主窗口布局
    main_window.setLayout(layout)
    
    # 显示主窗口
    main_window.show()
    
    print("✅ 测试应用程序已启动")
    print("请点击'测试弹窗绘图'按钮")
    
    # 运行应用程序
    return app.exec_()

if __name__ == "__main__":
    print("🚀 开始弹窗绘图测试...")
    print("=" * 50)
    
    try:
        result = test_dialog_plot()
        print(f"应用程序退出，返回值: {result}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("测试完成。") 