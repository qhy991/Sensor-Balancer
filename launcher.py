#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
称重测量系统启动器
选择运行应用版本或调试版本
"""

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class LauncherWindow(QWidget):
    """启动器窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("称重测量系统启动器")
        self.setGeometry(300, 300, 500, 400)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("称重测量系统")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #0078d4; margin: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本选择组
        version_group = QGroupBox("选择运行模式")
        version_layout = QVBoxLayout()
        
        # 应用版本
        app_layout = QHBoxLayout()
        
        app_icon = QLabel("📱")
        app_icon.setStyleSheet("font-size: 48px; margin: 10px;")
        
        app_info = QVBoxLayout()
        app_title = QLabel("应用版本")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #28a745;")
        
        app_desc = QLabel("简化界面，专注于核心测量功能\n内置校准参数，开箱即用")
        app_desc.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        
        app_info.addWidget(app_title)
        app_info.addWidget(app_desc)
        
        app_btn = QPushButton("启动应用版本")
        app_btn.clicked.connect(self.launch_app_version)
        app_btn.setStyleSheet("background-color: #28a745; font-size: 12px; padding: 8px 16px;")
        
        app_layout.addWidget(app_icon)
        app_layout.addLayout(app_info)
        app_layout.addStretch()
        app_layout.addWidget(app_btn)
        
        version_layout.addLayout(app_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        version_layout.addWidget(line)
        
        # 调试版本
        debug_layout = QHBoxLayout()
        
        debug_icon = QLabel("🔧")
        debug_icon.setStyleSheet("font-size: 48px; margin: 10px;")
        
        debug_info = QVBoxLayout()
        debug_title = QLabel("调试版本")
        debug_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #dc3545;")
        
        debug_desc = QLabel("完整功能，包含所有调试工具\n热力图、校准分析、实时数据等")
        debug_desc.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        
        debug_info.addWidget(debug_title)
        debug_info.addWidget(debug_desc)
        
        debug_btn = QPushButton("启动调试版本")
        debug_btn.clicked.connect(self.launch_debug_version)
        debug_btn.setStyleSheet("background-color: #dc3545; font-size: 12px; padding: 8px 16px;")
        
        debug_layout.addWidget(debug_icon)
        debug_layout.addLayout(debug_info)
        debug_layout.addStretch()
        debug_layout.addWidget(debug_btn)
        
        version_layout.addLayout(debug_layout)
        
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # 快速启动选项
        quick_group = QGroupBox("快速启动")
        quick_layout = QHBoxLayout()
        
        simple_btn = QPushButton("简化模式")
        simple_btn.clicked.connect(self.launch_simple_mode)
        simple_btn.setStyleSheet("background-color: #6c757d; font-size: 11px; padding: 6px 12px;")
        
        quick_layout.addWidget(simple_btn)
        quick_layout.addStretch()
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        # 底部信息
        info_layout = QHBoxLayout()
        info_layout.addStretch()
        
        version_info = QLabel("版本: 1.0.0 | 支持64x64压力传感器")
        version_info.setStyleSheet("font-size: 10px; color: #999;")
        
        info_layout.addWidget(version_info)
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
    
    def launch_app_version(self):
        """启动应用版本"""
        try:
            print("🚀 启动应用版本...")
            self.hide()
            
            # 导入并启动应用版本
            from weight_measurement_app import WeightMeasurementApp
            import sys
            
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            window = WeightMeasurementApp()
            window.show()
            
            # 连接窗口关闭信号
            window.destroyed.connect(self.show)
            
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动应用版本失败: {e}")
            print(f"❌ 启动应用版本失败: {e}")
            self.show()
    
    def launch_debug_version(self):
        """启动调试版本"""
        try:
            print("🔧 启动调试版本...")
            self.hide()
            
            # 导入并启动调试版本
            from weight_measurement_tool import WeightMeasurementInterface
            import sys
            
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            window = WeightMeasurementInterface()
            window.show()
            
            # 连接窗口关闭信号
            window.destroyed.connect(self.show)
            
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动调试版本失败: {e}")
            print(f"❌ 启动调试版本失败: {e}")
            self.show()
    
    def launch_simple_mode(self):
        """启动简化模式（调试版本的简化模式）"""
        try:
            print("📱 启动简化模式...")
            self.hide()
            
            # 导入并启动调试版本
            from weight_measurement_tool import WeightMeasurementInterface
            import sys
            
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            window = WeightMeasurementInterface()
            window.show()
            
            # 自动切换到简化模式
            window.toggle_simple_mode()
            
            # 连接窗口关闭信号
            window.destroyed.connect(self.show)
            
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动简化模式失败: {e}")
            print(f"❌ 启动简化模式失败: {e}")
            self.show()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 创建启动器窗口
    launcher = LauncherWindow()
    launcher.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 