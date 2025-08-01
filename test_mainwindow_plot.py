#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QMainWindow绘图功能
"""

import sys
import os
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def test_mainwindow_plot():
    """测试QMainWindow绘图"""
    print("🔍 测试QMainWindow绘图功能...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("传感器质量-压力关系分析")
    main_window.setGeometry(100, 100, 1200, 800)
    
    # 创建中央部件
    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    
    # 创建matplotlib图形
    fig = Figure(figsize=(12, 8), dpi=100)
    canvas = FigureCanvas(fig)
    
    # 创建2x2的子图布局
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)
    
    # 生成测试数据（模拟砝码数据）
    masses = [50, 100, 150, 500, 550, 600, 650]
    pressures = [0.002, 0.004, 0.006, 0.020, 0.022, 0.024, 0.026]
    sensitivities = [0.00004, 0.00004, 0.00004, 0.00004, 0.00004, 0.00004, 0.00004]
    cvs = [0.008, 0.012, 0.015, 0.025, 0.030, 0.035, 0.040]
    
    # 1. 质量-总压力关系图
    ax1.scatter(masses, pressures, s=120, alpha=0.8, c='blue', edgecolors='black', linewidth=1.5)
    ax1.plot(masses, pressures, 'r--', alpha=0.8, linewidth=2.5, label='趋势线')
    ax1.set_xlabel('质量 (g)', fontsize=12)
    ax1.set_ylabel('平均总压力', fontsize=12)
    ax1.set_title('质量-总压力关系', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # 添加数据点标签
    for i, (mass, pressure) in enumerate(zip(masses, pressures)):
        ax1.annotate(f'{mass}g', (mass, pressure), 
                   xytext=(8, 8), textcoords='offset points', 
                   fontsize=10, alpha=0.9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # 2. 质量-敏感性关系图
    ax2.scatter(masses, sensitivities, s=120, alpha=0.8, c='green', edgecolors='black', linewidth=1.5)
    ax2.plot(masses, sensitivities, 'r--', alpha=0.8, linewidth=2.5, label='趋势线')
    ax2.set_xlabel('质量 (g)', fontsize=12)
    ax2.set_ylabel('敏感性(总)', fontsize=12)
    ax2.set_title('质量-敏感性关系', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    # 添加数据点标签
    for i, (mass, sensitivity) in enumerate(zip(masses, sensitivities)):
        ax2.annotate(f'{mass}g', (mass, sensitivity), 
                   xytext=(8, 8), textcoords='offset points', 
                   fontsize=10, alpha=0.9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
    
    # 3. 压力-敏感性关系图
    ax3.scatter(pressures, sensitivities, s=120, alpha=0.8, c='orange', edgecolors='black', linewidth=1.5)
    ax3.set_xlabel('平均总压力', fontsize=12)
    ax3.set_ylabel('敏感性(总)', fontsize=12)
    ax3.set_title('压力-敏感性关系', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # 添加数据点标签
    for i, (pressure, sensitivity) in enumerate(zip(pressures, sensitivities)):
        ax3.annotate(f'{masses[i]}g', (pressure, sensitivity), 
                   xytext=(8, 8), textcoords='offset points', 
                   fontsize=10, alpha=0.9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
    
    # 4. 变异系数分析图
    colors = ['green' if cv < 0.01 else 'orange' if cv < 0.05 else 'red' for cv in cvs]
    bars = ax4.bar(range(len(masses)), cvs, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_xlabel('砝码质量', fontsize=12)
    ax4.set_ylabel('变异系数', fontsize=12)
    ax4.set_title('测量稳定性分析', fontsize=14, fontweight='bold')
    ax4.set_xticks(range(len(masses)))
    ax4.set_xticklabels([f'{mass}g' for mass in masses], fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # 添加阈值线
    ax4.axhline(y=0.01, color='green', linestyle='--', alpha=0.8, linewidth=2, label='优秀 (<1%)')
    ax4.axhline(y=0.05, color='orange', linestyle='--', alpha=0.8, linewidth=2, label='良好 (<5%)')
    ax4.legend(fontsize=10)
    
    # 添加数值标签
    for i, (bar, cv) in enumerate(zip(bars, cvs)):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                f'{cv:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    # 调整子图间距
    fig.tight_layout(pad=2.0)
    
    # 创建信息标签
    info_text = f"分析结果: {len(masses)}个砝码，总测量次数: 140"
    info_label = QLabel(info_text)
    info_label.setStyleSheet("font-size: 12px; font-weight: bold; color: blue; padding: 5px;")
    info_label.setAlignment(QtCore.Qt.AlignCenter)
    
    # 创建按钮
    close_btn = QPushButton("关闭")
    close_btn.setStyleSheet("QPushButton { font-size: 12px; padding: 8px; }")
    close_btn.clicked.connect(main_window.close)
    
    # 创建按钮布局
    button_layout = QHBoxLayout()
    button_layout.addWidget(close_btn)
    button_layout.addStretch()
    
    # 创建主布局
    main_layout = QVBoxLayout()
    main_layout.addWidget(info_label)
    main_layout.addWidget(canvas, 1)  # 图表占据主要空间
    main_layout.addLayout(button_layout)
    
    central_widget.setLayout(main_layout)
    
    # 显示窗口
    main_window.show()
    main_window.raise_()
    main_window.activateWindow()
    
    print("✅ QMainWindow绘图测试已创建")
    print("请查看窗口中的4个子图")
    
    # 运行应用程序
    return app.exec_()

if __name__ == "__main__":
    print("🚀 开始QMainWindow绘图测试...")
    print("=" * 50)
    
    try:
        result = test_mainwindow_plot()
        print(f"应用程序退出，返回值: {result}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("测试完成。") 