#!/usr/bin/env python3
"""
简单的全屏测试
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt

class SimpleFullscreenTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全屏测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 添加说明标签
        info_label = QLabel("这是一个全屏测试窗口\n点击下面的按钮测试全屏功能")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; margin: 20px;")
        layout.addWidget(info_label)
        
        # 添加全屏按钮
        self.fullscreen_btn = QPushButton("进入全屏")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.fullscreen_btn)
        
        # 添加退出按钮
        exit_btn = QPushButton("退出应用")
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #dc3545; color: white;")
        layout.addWidget(exit_btn)
        
        print("✅ 测试窗口已创建")
        print("✅ 窗口可以调整大小:", not self.isFixedSize())
        print("✅ 窗口最小大小:", self.minimumSize())
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("进入全屏")
            print("✅ 退出全屏模式")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")
            print("✅ 进入全屏模式")

def main():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = SimpleFullscreenTest()
    window.show()
    
    print("✅ 测试窗口已显示")
    print("如果窗口可以全屏显示，说明全屏功能正常！")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 