#!/usr/bin/env python3
"""
全面测试停止灵敏度测试功能
验证所有停止场景的正确处理
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QTextEdit, QLabel
from PyQt5.QtCore import QTimer

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from LocalSensitivityWidget import LocalSensitivityWidget
    print("✅ LocalSensitivityWidget模块导入成功")
except ImportError as e:
    print(f"❌ 导入LocalSensitivityWidget失败: {e}")
    sys.exit(1)

class ComprehensiveStopTestWindow(QMainWindow):
    """全面测试停止测量功能的窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全面测试停止灵敏度测试功能")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout()
        
        # 左侧：局部灵敏度组件
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("局部灵敏度测试组件:"))
        self.local_sensitivity_widget = LocalSensitivityWidget()
        left_layout.addWidget(self.local_sensitivity_widget)
        
        # 右侧：测试控制面板
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("测试控制面板:"))
        
        # 测试场景按钮
        test_scenarios_layout = QVBoxLayout()
        
        # 场景1：手动停止测试
        self.scenario1_btn = QPushButton("场景1: 手动停止测试")
        self.scenario1_btn.clicked.connect(self.test_manual_stop)
        self.scenario1_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        
        # 场景2：引导窗口关闭
        self.scenario2_btn = QPushButton("场景2: 引导窗口关闭")
        self.scenario2_btn.clicked.connect(self.test_guide_window_close)
        self.scenario2_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        
        # 场景3：测试完成自动停止
        self.scenario3_btn = QPushButton("场景3: 测试完成自动停止")
        self.scenario3_btn.clicked.connect(self.test_auto_completion)
        self.scenario3_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        
        # 场景4：异常情况处理
        self.scenario4_btn = QPushButton("场景4: 异常情况处理")
        self.scenario4_btn.clicked.connect(self.test_exception_handling)
        self.scenario4_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        
        # 场景5：状态验证
        self.scenario5_btn = QPushButton("场景5: 状态验证")
        self.scenario5_btn.clicked.connect(self.test_state_verification)
        self.scenario5_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        
        # 清理环境按钮
        self.cleanup_btn = QPushButton("清理测试环境")
        self.cleanup_btn.clicked.connect(self.cleanup_environment)
        self.cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #757575; }
        """)
        
        test_scenarios_layout.addWidget(self.scenario1_btn)
        test_scenarios_layout.addWidget(self.scenario2_btn)
        test_scenarios_layout.addWidget(self.scenario3_btn)
        test_scenarios_layout.addWidget(self.scenario4_btn)
        test_scenarios_layout.addWidget(self.scenario5_btn)
        test_scenarios_layout.addWidget(self.cleanup_btn)
        
        # 日志显示区域
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("测试日志:"))
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 状态显示
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("当前状态:"))
        self.status_label = QLabel("等待测试...")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        right_layout.addLayout(test_scenarios_layout)
        right_layout.addLayout(log_layout)
        right_layout.addLayout(status_layout)
        
        # 组装主布局
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        central_widget.setLayout(main_layout)
        
        self.log("🎉 全面测试停止灵敏度测试功能已启动！")
        self.log("📋 测试场景:")
        self.log("1. 手动停止测试 - 测试用户主动停止")
        self.log("2. 引导窗口关闭 - 测试窗口关闭处理")
        self.log("3. 测试完成自动停止 - 测试自动完成")
        self.log("4. 异常情况处理 - 测试异常场景")
        self.log("5. 状态验证 - 验证UI状态正确性")
    
    def log(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        print(f"[{timestamp}] {message}")
    
    def update_status(self, status, color="#4CAF50"):
        """更新状态显示"""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                padding: 10px;
                background-color: {color}20;
                border: 1px solid {color};
                border-radius: 4px;
                font-weight: bold;
                color: {color};
            }}
        """)
    
    def test_manual_stop(self):
        """场景1: 手动停止测试"""
        self.log("\n🔧 开始场景1: 手动停止测试")
        self.update_status("正在执行场景1...", "#2196F3")
        
        try:
            # 准备测试环境
            self.prepare_test_environment()
            
            # 开始引导式测试
            self.local_sensitivity_widget.start_guided_measurement()
            self.log("✅ 引导式测试已开始")
            
            # 等待3秒后手动停止
            QTimer.singleShot(3000, self.perform_manual_stop)
            
        except Exception as e:
            self.log(f"❌ 场景1失败: {e}")
            self.update_status("场景1失败", "#F44336")
    
    def perform_manual_stop(self):
        """执行手动停止"""
        self.log("🛑 执行手动停止...")
        self.local_sensitivity_widget.stop_sensitivity_measurement()
        self.log("✅ 手动停止完成")
        self.update_status("场景1完成: 手动停止成功", "#4CAF50")
        
        # 验证状态
        self.verify_stop_state("手动停止")
    
    def test_guide_window_close(self):
        """场景2: 引导窗口关闭"""
        self.log("\n🔧 开始场景2: 引导窗口关闭")
        self.update_status("正在执行场景2...", "#FF9800")
        
        try:
            # 准备测试环境
            self.prepare_test_environment()
            
            # 开始引导式测试
            self.local_sensitivity_widget.start_guided_measurement()
            self.log("✅ 引导式测试已开始")
            
            # 等待2秒后模拟关闭引导窗口
            QTimer.singleShot(2000, self.simulate_window_close)
            
        except Exception as e:
            self.log(f"❌ 场景2失败: {e}")
            self.update_status("场景2失败", "#F44336")
    
    def simulate_window_close(self):
        """模拟窗口关闭"""
        self.log("🛑 模拟关闭引导窗口...")
        
        if hasattr(self.local_sensitivity_widget, 'guide_window') and self.local_sensitivity_widget.guide_window:
            # 模拟用户关闭窗口
            self.local_sensitivity_widget.guide_window.close()
            self.log("✅ 引导窗口已关闭")
            self.update_status("场景2完成: 窗口关闭处理成功", "#4CAF50")
        else:
            self.log("⚠️ 引导窗口不存在")
            self.update_status("场景2失败: 引导窗口不存在", "#F44336")
    
    def test_auto_completion(self):
        """场景3: 测试完成自动停止"""
        self.log("\n🔧 开始场景3: 测试完成自动停止")
        self.update_status("正在执行场景3...", "#4CAF50")
        
        try:
            # 准备少量测试位置
            self.local_sensitivity_widget.selected_region = "center"
            self.local_sensitivity_widget.micro_positions_count_input.setValue(2)  # 2个位置
            self.local_sensitivity_widget.frames_per_position_input.setValue(3)   # 每位置3帧
            self.local_sensitivity_widget.generate_micro_positions()
            self.log("✅ 已生成2个测试位置")
            
            # 开始引导式测试
            self.local_sensitivity_widget.weight_id_input.setText("1")
            self.local_sensitivity_widget.start_guided_measurement()
            self.log("✅ 引导式测试已开始")
            
            # 自动记录数据直到完成
            self.auto_record_until_completion()
            
        except Exception as e:
            self.log(f"❌ 场景3失败: {e}")
            self.update_status("场景3失败", "#F44336")
    
    def auto_record_until_completion(self):
        """自动记录数据直到完成"""
        if (self.local_sensitivity_widget.sensitivity_measurement_active and 
            self.local_sensitivity_widget.current_position_index < len(self.local_sensitivity_widget.micro_positions)):
            
            # 记录当前位置的数据
            self.local_sensitivity_widget.record_position_data()
            self.log(f"📊 记录位置 {self.local_sensitivity_widget.current_position_index + 1} 数据")
            
            # 如果还没完成，继续记录
            if self.local_sensitivity_widget.sensitivity_measurement_active:
                QTimer.singleShot(300, self.auto_record_until_completion)  # 300ms后继续
            else:
                self.log("✅ 自动记录完成，测试已自动停止")
                self.update_status("场景3完成: 自动完成成功", "#4CAF50")
                self.verify_stop_state("自动完成")
        else:
            self.log("✅ 自动记录完成")
    
    def test_exception_handling(self):
        """场景4: 异常情况处理"""
        self.log("\n🔧 开始场景4: 异常情况处理")
        self.update_status("正在执行场景4...", "#F44336")
        
        try:
            # 测试在没有位置的情况下开始测试
            self.local_sensitivity_widget.micro_positions = []
            self.local_sensitivity_widget.start_guided_measurement()
            
        except Exception as e:
            self.log(f"✅ 异常处理正常: {e}")
            self.update_status("场景4完成: 异常处理正常", "#4CAF50")
            
            # 恢复环境
            self.cleanup_environment()
    
    def test_state_verification(self):
        """场景5: 状态验证"""
        self.log("\n🔧 开始场景5: 状态验证")
        self.update_status("正在执行场景5...", "#9C27B0")
        
        try:
            # 验证初始状态
            self.verify_initial_state()
            
            # 准备测试环境
            self.prepare_test_environment()
            
            # 验证准备后状态
            self.verify_prepared_state()
            
            # 开始测试
            self.local_sensitivity_widget.start_guided_measurement()
            
            # 验证测试中状态
            self.verify_running_state()
            
            # 停止测试
            self.local_sensitivity_widget.stop_sensitivity_measurement()
            
            # 验证停止后状态
            self.verify_stop_state("状态验证")
            
            self.update_status("场景5完成: 状态验证成功", "#4CAF50")
            
        except Exception as e:
            self.log(f"❌ 场景5失败: {e}")
            self.update_status("场景5失败", "#F44336")
    
    def prepare_test_environment(self):
        """准备测试环境"""
        self.log("🔧 准备测试环境...")
        
        # 生成测试位置
        if not self.local_sensitivity_widget.micro_positions:
            self.local_sensitivity_widget.selected_region = "center"
            self.local_sensitivity_widget.generate_micro_positions()
            self.log("✅ 已生成测试位置")
        
        # 设置砝码ID
        self.local_sensitivity_widget.weight_id_input.setText("1")
        
        self.log("✅ 测试环境准备完成")
    
    def verify_initial_state(self):
        """验证初始状态"""
        self.log("🔍 验证初始状态...")
        
        # 检查测试状态
        assert not self.local_sensitivity_widget.sensitivity_measurement_active, "初始状态应该是非活动"
        assert len(self.local_sensitivity_widget.sensitivity_data) == 0, "初始数据应该为空"
        
        # 检查UI状态
        assert self.local_sensitivity_widget.start_sensitivity_measurement_btn.isEnabled(), "开始按钮应该可用"
        assert not self.local_sensitivity_widget.stop_sensitivity_measurement_btn.isEnabled(), "停止按钮应该禁用"
        
        self.log("✅ 初始状态验证通过")
    
    def verify_prepared_state(self):
        """验证准备后状态"""
        self.log("🔍 验证准备后状态...")
        
        # 检查位置数据
        assert len(self.local_sensitivity_widget.micro_positions) > 0, "应该有测试位置"
        assert self.local_sensitivity_widget.selected_region is not None, "应该有选中的区域"
        
        self.log("✅ 准备后状态验证通过")
    
    def verify_running_state(self):
        """验证运行中状态"""
        self.log("🔍 验证运行中状态...")
        
        # 检查测试状态
        assert self.local_sensitivity_widget.sensitivity_measurement_active, "测试应该处于活动状态"
        assert not self.local_sensitivity_widget.start_sensitivity_measurement_btn.isEnabled(), "开始按钮应该禁用"
        assert self.local_sensitivity_widget.stop_sensitivity_measurement_btn.isEnabled(), "停止按钮应该可用"
        
        # 检查引导窗口
        assert hasattr(self.local_sensitivity_widget, 'guide_window'), "应该有引导窗口"
        
        self.log("✅ 运行中状态验证通过")
    
    def verify_stop_state(self, scenario_name):
        """验证停止后状态"""
        self.log(f"🔍 验证{scenario_name}后状态...")
        
        # 检查测试状态
        assert not self.local_sensitivity_widget.sensitivity_measurement_active, "测试应该已停止"
        assert self.local_sensitivity_widget.start_sensitivity_measurement_btn.isEnabled(), "开始按钮应该可用"
        assert not self.local_sensitivity_widget.stop_sensitivity_measurement_btn.isEnabled(), "停止按钮应该禁用"
        
        # 检查手动控制按钮
        assert not self.local_sensitivity_widget.next_position_btn.isEnabled(), "下一个位置按钮应该禁用"
        assert not self.local_sensitivity_widget.previous_position_btn.isEnabled(), "上一个位置按钮应该禁用"
        assert not self.local_sensitivity_widget.record_data_btn.isEnabled(), "记录数据按钮应该禁用"
        
        # 检查引导窗口
        assert self.local_sensitivity_widget.guide_window is None, "引导窗口应该已关闭"
        
        self.log(f"✅ {scenario_name}后状态验证通过")
    
    def cleanup_environment(self):
        """清理测试环境"""
        self.log("\n🧹 开始清理测试环境...")
        
        try:
            # 停止任何正在进行的测试
            if self.local_sensitivity_widget.sensitivity_measurement_active:
                self.local_sensitivity_widget.stop_sensitivity_measurement()
                self.log("✅ 已停止正在进行的测试")
            
            # 清空测试数据
            self.local_sensitivity_widget.sensitivity_data = {}
            self.local_sensitivity_widget.micro_positions = []
            
            # 重置UI状态
            self.local_sensitivity_widget.positions_table.setRowCount(0)
            self.local_sensitivity_widget.sensitivity_results_table.setRowCount(0)
            
            # 重置进度条
            self.local_sensitivity_widget.sensitivity_progress_bar.setVisible(False)
            
            # 更新状态
            self.local_sensitivity_widget.sensitivity_status_label.setText("灵敏度测试状态: 已重置")
            self.local_sensitivity_widget.sensitivity_status_label.setStyleSheet("color: gray; font-weight: bold;")
            
            self.log("✅ 测试环境已清理")
            self.update_status("环境已清理", "#9E9E9E")
            
        except Exception as e:
            self.log(f"❌ 清理测试环境失败: {e}")
            self.update_status("清理失败", "#F44336")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    test_window = ComprehensiveStopTestWindow()
    test_window.show()
    
    print("🎯 全面测试说明:")
    print("1. 左侧显示局部灵敏度测试组件")
    print("2. 右侧提供各种测试场景按钮")
    print("3. 日志区域显示详细的测试过程")
    print("4. 状态区域显示当前测试状态")
    print("5. 每个场景都会验证相应的功能")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 