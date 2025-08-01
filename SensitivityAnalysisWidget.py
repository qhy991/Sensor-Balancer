import json
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, 
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, 
    QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog, QDialog, 
    QApplication, QSizePolicy
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import pyqtgraph as pg
from PyQt5.QtGui import QPixmap

# 检查PyQtGraph可用性
try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("⚠️ PyQtGraph不可用，图表功能将被禁用")

# 导入保存图表的通用函数
try:
    from sensor_sensitivity_calibration import save_pyqtgraph_plot
except ImportError:
    def save_pyqtgraph_plot(plot_window, filename):
        """保存PyQtGraph图表的通用函数"""
        try:
            if hasattr(plot_window, 'scene'):
                # 尝试使用PyQtGraph的导出功能
                if hasattr(plot_window, 'grab'):
                    pixmap = plot_window.grab()
                    return pixmap.save(filename)
                else:
                    print("⚠️ PyQtGraph图表保存功能不可用")
                    return False
            else:
                print("⚠️ 无效的图表窗口")
                return False
        except Exception as e:
            print(f"⚠️ 保存图表失败: {e}")
            return False

class SensitivityAnalysisWidget(QWidget):
    """敏感性分析组件 - 新增"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 分析控制组
        control_group = QGroupBox("敏感性分析")
        control_layout = QHBoxLayout()
        
        self.load_analysis_data_btn = QPushButton("加载分析数据")
        self.load_analysis_data_btn.clicked.connect(self.load_analysis_data)
        
        self.generate_report_btn = QPushButton("生成分析报告")
        self.generate_report_btn.clicked.connect(self.generate_analysis_report)
        self.generate_report_btn.setEnabled(False)
        
        self.plot_sensitivity_btn = QPushButton("绘制敏感性曲线")
        self.plot_sensitivity_btn.clicked.connect(self.plot_sensitivity_curves)
        self.plot_sensitivity_btn.setEnabled(False)
        
        control_layout.addWidget(self.load_analysis_data_btn)
        control_layout.addWidget(self.generate_report_btn)
        control_layout.addWidget(self.plot_sensitivity_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        
        # 分析结果显示
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        
        results_layout.addWidget(self.analysis_text)
        results_group.setLayout(results_layout)
        
        # 组装布局
        layout.addWidget(control_group)
        layout.addWidget(results_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def load_analysis_data(self):
        """加载分析数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择分析数据文件", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.analysis_data = json.load(f)
                
                self.generate_report_btn.setEnabled(True)
                self.plot_sensitivity_btn.setEnabled(True)
                
                # 显示基本信息
                self.display_basic_info()
                
                QMessageBox.information(self, "成功", "分析数据加载成功")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载分析数据失败: {e}")
    
    def display_basic_info(self):
        """显示基本信息"""
        if not self.analysis_data:
            return
        
        info_text = f"""
敏感性标定数据分析
生成时间: {self.analysis_data.get('timestamp', '未知')}
校准文件: {self.analysis_data.get('calibration_file', '未知')}

砝码数量: {len(self.analysis_data.get('weights', {}))}
测量数据: {len(self.analysis_data.get('measurements', {}))}
标定结果: {len(self.analysis_data.get('results', {}))}

===== 砝码信息 =====
"""
        
        for weight_id, weight_info in self.analysis_data.get('weights', {}).items():
            info_text += f"{weight_id}: {weight_info['mass']}{weight_info['unit']} (力: {weight_info['force']:.4f}N)\n"
        
        self.analysis_text.setText(info_text)
    
    def generate_analysis_report(self):
        """生成分析报告"""
        if not self.analysis_data:
            QMessageBox.warning(self, "警告", "请先加载分析数据")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存分析报告", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", "文本文件 (*.txt);;HTML文件 (*.html)"
        )
        
        if filename:
            try:
                if filename.endswith('.html'):
                    self.generate_html_report(filename)
                else:
                    self.generate_text_report(filename)
                
                QMessageBox.information(self, "成功", f"分析报告已保存到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成报告失败: {e}")
    
    def generate_text_report(self, filename):
        """生成文本报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器敏感性标定分析报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始数据文件: {self.analysis_data.get('calibration_file', '未知')}\n")
            f.write(f"数据生成时间: {self.analysis_data.get('timestamp', '未知')}\n\n")
            
            # 整体敏感性分析
            overall = self.analysis_data.get('overall_sensitivity', {})
            if overall:
                f.write("===== 整体敏感性分析 =====\n")
                f.write(f"平均敏感性(总压力): {overall.get('avg_sensitivity_total', 0):.6f} ± {overall.get('std_sensitivity_total', 0):.6f}\n")
                f.write(f"平均敏感性(平均压力): {overall.get('avg_sensitivity_mean', 0):.6f} ± {overall.get('std_sensitivity_mean', 0):.6f}\n")
                f.write(f"平均敏感性(最大压力): {overall.get('avg_sensitivity_max', 0):.6f} ± {overall.get('std_sensitivity_max', 0):.6f}\n\n")
            
            # 详细结果分析
            f.write("===== 详细标定结果 =====\n")
            for weight_id, result in self.analysis_data.get('results', {}).items():
                f.write(f"\n砝码 {weight_id}:\n")
                f.write(f"  质量: {result['weight_info']['mass']}{result['weight_info']['unit']}\n")
                f.write(f"  测量次数: {result['measurement_count']}\n")
                f.write(f"  平均总压力: {result['avg_total_pressure']:.6f}\n")
                f.write(f"  标准差: {result['std_total_pressure']:.6f}\n")
                f.write(f"  敏感性(总): {result['sensitivity_total']:.6f}\n")
                f.write(f"  敏感性(平均): {result['sensitivity_mean']:.6f}\n")
                f.write(f"  变异系数: {result['cv']:.3f}\n")
            
            # 质量评估
            f.write("\n===== 质量评估 =====\n")
            if overall:
                cv_values = [r['cv'] for r in self.analysis_data.get('results', {}).values()]
                avg_cv = np.mean(cv_values)
                f.write(f"平均变异系数: {avg_cv:.3f}\n")
                
                if avg_cv < 0.1:
                    f.write("评估结果: 优秀 - 传感器一致性很好\n")
                elif avg_cv < 0.2:
                    f.write("评估结果: 良好 - 传感器一致性较好\n")
                elif avg_cv < 0.3:
                    f.write("评估结果: 一般 - 传感器一致性中等\n")
                else:
                    f.write("评估结果: 较差 - 传感器一致性需要改进\n")
    
    def generate_html_report(self, filename):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>传感器敏感性标定分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .poor {{ color: red; }}
    </style>
</head>
<body>
    <h1>传感器敏感性标定分析报告</h1>
    <p><strong>报告生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>原始数据文件:</strong> {self.analysis_data.get('calibration_file', '未知')}</p>
    <p><strong>数据生成时间:</strong> {self.analysis_data.get('timestamp', '未知')}</p>
    
    <h2>整体敏感性分析</h2>
"""
        
        overall = self.analysis_data.get('overall_sensitivity', {})
        if overall:
            html_content += f"""
    <table>
        <tr><th>指标</th><th>数值</th></tr>
        <tr><td>平均敏感性(总压力)</td><td>{overall.get('avg_sensitivity_total', 0):.6f} ± {overall.get('std_sensitivity_total', 0):.6f}</td></tr>
        <tr><td>平均敏感性(平均压力)</td><td>{overall.get('avg_sensitivity_mean', 0):.6f} ± {overall.get('std_sensitivity_mean', 0):.6f}</td></tr>
        <tr><td>平均敏感性(最大压力)</td><td>{overall.get('avg_sensitivity_max', 0):.6f} ± {overall.get('std_sensitivity_max', 0):.6f}</td></tr>
    </table>
"""
        
        html_content += """
    <h2>详细标定结果</h2>
    <table>
        <tr>
            <th>砝码ID</th>
            <th>质量</th>
            <th>测量次数</th>
            <th>平均总压力</th>
            <th>标准差</th>
            <th>敏感性(总)</th>
            <th>变异系数</th>
        </tr>
"""
        
        for weight_id, result in self.analysis_data.get('results', {}).items():
            cv_class = "good" if result['cv'] < 0.1 else "warning" if result['cv'] < 0.2 else "poor"
            html_content += f"""
        <tr>
            <td>{weight_id}</td>
            <td>{result['weight_info']['mass']}{result['weight_info']['unit']}</td>
            <td>{result['measurement_count']}</td>
            <td>{result['avg_total_pressure']:.6f}</td>
            <td>{result['std_total_pressure']:.6f}</td>
            <td>{result['sensitivity_total']:.6f}</td>
            <td class="{cv_class}">{result['cv']:.3f}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def plot_sensitivity_curves(self):
        """绘制敏感性曲线"""
        if not self.analysis_data:
            QMessageBox.warning(self, "警告", "请先加载分析数据")
            return
        
        try:
            # 创建PyQtGraph绘图窗口
            plot_window = pg.GraphicsLayoutWidget()
            plot_window.setWindowTitle('敏感性分析曲线')
            plot_window.resize(1200, 800)
            
            results = self.analysis_data.get('results', {})
            if not results:
                QMessageBox.warning(self, "警告", "没有标定结果数据")
                return
            
            # 准备数据
            weights = []
            masses = []
            sensitivities_total = []
            sensitivities_mean = []
            cvs = []
            
            for weight_id, result in results.items():
                weights.append(weight_id)
                masses.append(result['weight_info']['mass'])
                sensitivities_total.append(result['sensitivity_total'])
                sensitivities_mean.append(result['sensitivity_mean'])
                cvs.append(result['cv'])
            
            # 1. 敏感性 vs 质量
            p1 = plot_window.addPlot(row=0, col=0, title="敏感性 vs 质量")
            p1.setLabel('left', '敏感性')
            p1.setLabel('bottom', '质量 (g)')
            p1.showGrid(x=True, y=True, alpha=0.3)
            
            # 绘制总压力敏感性
            line1 = pg.PlotDataItem(masses, sensitivities_total, pen=pg.mkPen('blue', width=3), 
                                  symbol='o', symbolSize=10, symbolBrush='blue')
            p1.addItem(line1)
            
            # 绘制平均压力敏感性
            line2 = pg.PlotDataItem(masses, sensitivities_mean, pen=pg.mkPen('red', width=3), 
                                  symbol='s', symbolSize=10, symbolBrush='red')
            p1.addItem(line2)
            
            # 添加图例
            legend1 = pg.LegendItem(offset=(30, 30))
            legend1.addItem(line1, '总压力敏感性')
            legend1.addItem(line2, '平均压力敏感性')
            
            # 2. 变异系数 vs 质量
            p2 = plot_window.addPlot(row=0, col=1, title="变异系数 vs 质量")
            p2.setLabel('left', '变异系数')
            p2.setLabel('bottom', '质量 (g)')
            p2.showGrid(x=True, y=True, alpha=0.3)
            
            line3 = pg.PlotDataItem(masses, cvs, pen=pg.mkPen('green', width=3), 
                                  symbol='o', symbolSize=10, symbolBrush='green')
            p2.addItem(line3)
            
            # 3. 压力 vs 质量
            p3 = plot_window.addPlot(row=1, col=0, title="压力 vs 质量")
            p3.setLabel('left', '平均总压力')
            p3.setLabel('bottom', '质量 (g)')
            p3.showGrid(x=True, y=True, alpha=0.3)
            
            pressures = [result['avg_total_pressure'] for result in results.values()]
            line4 = pg.PlotDataItem(masses, pressures, pen=pg.mkPen('magenta', width=3), 
                                  symbol='o', symbolSize=10, symbolBrush='magenta')
            p3.addItem(line4)
            
            # 4. 敏感性分布直方图
            p4 = plot_window.addPlot(row=1, col=1, title="敏感性分布")
            p4.setLabel('left', '频次')
            p4.setLabel('bottom', '敏感性')
            p4.showGrid(x=True, y=True, alpha=0.3)
            
            # 创建直方图
            y, x = np.histogram(sensitivities_total, bins=len(sensitivities_total))
            x = x[:-1]  # 移除最后一个边界值
            bar_graph = pg.BarGraphItem(x=x, height=y, width=(max(x)-min(x))/len(x)*0.8, 
                                      brush=pg.mkBrush('skyblue'), 
                                      pen=pg.mkPen('black', width=1))
            p4.addItem(bar_graph)
            
            # 显示窗口
            # plot_window.show()  # 注释掉这行，让add_save_button_to_plot来处理窗口显示
            
            # 强制更新和渲染
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 在图表窗口添加保存按钮
            self.add_save_button_to_plot(plot_window)
            
            print(f"✅ 敏感性曲线图表绘制完成")
            print(f"💡 提示：图表窗口中有保存按钮")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制敏感性曲线失败: {e}")
            print(f"❌ 绘制敏感性曲线失败: {e}")
            import traceback
            traceback.print_exc()
    
    def auto_save_dialog(self, plot_window):
        """自动弹出保存对话框"""
        try:
            # 确保图表窗口仍然有效
            if not hasattr(plot_window, 'scene'):
                print(f"⚠️ 图表窗口无效，无法保存")
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
            import traceback
            traceback.print_exc()
    
    def _show_save_dialog(self, plot_window):
        """显示保存对话框"""
        try:
            # 再次确保图表窗口有效
            if not hasattr(plot_window, 'scene'):
                print(f"⚠️ 图表窗口无效，无法保存")
                return
            
            # 最后一次强制更新
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 弹出保存对话框
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存敏感性分析图表", 
                f"C:/Users/84672/Documents/Research/sensitivity_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
            )
            
            if filename:
                print(f"🔍 用户选择保存到: {filename}")
                
                # 保存前再次确保渲染
                plot_window.scene().update()
                QApplication.processEvents()
                
                # 使用通用保存函数
                if save_pyqtgraph_plot(plot_window, filename):
                    print(f"✅ 敏感性分析图表已保存到: {filename}")
                    QMessageBox.information(self, "成功", f"敏感性分析图表已保存到:\n{filename}")
                else:
                    # 如果通用保存函数失败，尝试直接保存
                    print(f"⚠️ 通用保存函数失败，尝试直接保存...")
                    if self.save_plot_directly(plot_window, filename):
                        print(f"✅ 直接保存成功: {filename}")
                        QMessageBox.information(self, "成功", f"敏感性分析图表已保存到:\n{filename}")
                    else:
                        QMessageBox.warning(self, "保存失败", "所有保存方法都失败了")
            else:
                print(f"💡 用户取消了保存")
                
        except Exception as e:
            print(f"⚠️ 显示保存对话框出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
            import traceback
            traceback.print_exc()
    
    def plot_consistency_analysis(self):
        """绘制一致性分析图表"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有一致性结果数据")
            return
        
        try:
            # 验证数据完整性
            if not PYQTGRAPH_AVAILABLE:
                QMessageBox.critical(self, "错误", "PyQtGraph模块不可用，无法绘制图表")
                return
            
            # 检查数据是否为空
            if len(self.consistency_results) == 0:
                QMessageBox.warning(self, "警告", "一致性结果数据为空")
                return
            
            print(f"🔍 开始绘制一致性分析图表，数据包含 {len(self.consistency_results)} 个位置")
            
            # 创建PyQtGraph绘图窗口
            plot_window = pg.GraphicsLayoutWidget()
            plot_window.setWindowTitle('位置一致性分析')
            plot_window.resize(1400, 1000)
            
            # 准备数据
            positions = []
            position_names = []
            avg_sensitivities = []
            avg_cvs = []
            all_sensitivities = []
            
            for position_id, position_results in self.consistency_results.items():
                if not position_results:  # 跳过空的位置结果
                    continue
                    
                positions.append(position_id)
                position_name = self.guide_positions.get(position_id, {}).get('name', position_id)
                position_names.append(position_name)
                
                # 收集该位置的所有敏感性数据
                position_sensitivities = []
                position_cvs = []
                
                for result in position_results.values():
                    if 'sensitivity_total' in result and result['sensitivity_total'] > 0:
                        position_sensitivities.append(result['sensitivity_total'])
                    if 'cv' in result and result['cv'] >= 0:
                        position_cvs.append(result['cv'])
                
                # 计算平均值
                if position_sensitivities:
                    avg_sensitivity = np.mean(position_sensitivities)
                    avg_sensitivities.append(avg_sensitivity)
                    all_sensitivities.extend(position_sensitivities)
                else:
                    avg_sensitivities.append(0)
                
                if position_cvs:
                    avg_cv = np.mean(position_cvs)
                    avg_cvs.append(avg_cv)
                else:
                    avg_cvs.append(0)
            
            # 检查是否有有效数据
            if not positions or not avg_sensitivities or not avg_cvs:
                QMessageBox.warning(self, "警告", "没有有效的图表数据")
                return
            
            print(f"📊 准备绘制 {len(positions)} 个位置的数据")
            
            # 创建2x2子图布局
            # 1. 位置敏感性对比 (左上)
            p1 = plot_window.addPlot(row=0, col=0, title="各位置平均敏感性对比")
            p1.setLabel('left', '平均敏感性')
            p1.setLabel('bottom', '位置')
            p1.showGrid(x=True, y=True, alpha=0.3)
            
            # 创建柱状图
            x_pos = np.arange(len(positions))
            bars1 = pg.BarGraphItem(x=x_pos, height=avg_sensitivities, width=0.6, 
                                  brush='skyblue', pen='black')
            p1.addItem(bars1)
            
            # 设置X轴标签
            ax1 = p1.getAxis('bottom')
            ax1.setTicks([[(i, name) for i, name in enumerate(position_names)]])
            
            # 添加数值标签
            for i, value in enumerate(avg_sensitivities):
                if value > 0:  # 只显示非零值
                    text = pg.TextItem(text=f'{value:.4f}', color='black')
                    text.setPos(i, value + max(avg_sensitivities) * 0.02)
                    p1.addItem(text)
            
            # 2. 位置变异系数对比 (右上)
            p2 = plot_window.addPlot(row=0, col=1, title="各位置平均变异系数对比")
            p2.setLabel('left', '平均变异系数')
            p2.setLabel('bottom', '位置')
            p2.showGrid(x=True, y=True, alpha=0.3)
            
            bars2 = pg.BarGraphItem(x=x_pos, height=avg_cvs, width=0.6, 
                                  brush='lightcoral', pen='black')
            p2.addItem(bars2)
            
            # 设置X轴标签
            ax2 = p2.getAxis('bottom')
            ax2.setTicks([[(i, name) for i, name in enumerate(position_names)]])
            
            # 添加数值标签
            for i, value in enumerate(avg_cvs):
                if value > 0:  # 只显示非零值
                    text = pg.TextItem(text=f'{value:.3f}', color='black')
                    text.setPos(i, value + max(avg_cvs) * 0.02)
                    p2.addItem(text)
            
            # 3. 敏感性分布直方图 (左下)
            p3 = plot_window.addPlot(row=1, col=0, title="所有位置敏感性分布")
            p3.setLabel('left', '频次')
            p3.setLabel('bottom', '敏感性')
            p3.showGrid(x=True, y=True, alpha=0.3)
            
            # 计算直方图
            if all_sensitivities:
                hist, bins = np.histogram(all_sensitivities, bins=min(20, len(all_sensitivities)))
                x_hist = (bins[:-1] + bins[1:]) / 2
                bars3 = pg.BarGraphItem(x=x_hist, height=hist, width=(bins[1]-bins[0])*0.8,
                                      brush='lightgreen', pen='black')
                p3.addItem(bars3)
            
            # 4. 位置一致性热力图 (右下)
            p4 = plot_window.addPlot(row=1, col=1, title="位置-砝码敏感性热力图")
            p4.setLabel('left', '位置')
            p4.setLabel('bottom', '砝码')
            
            # 创建位置-砝码矩阵
            position_ids = list(self.consistency_results.keys())
            weight_ids = set()
            for position_results in self.consistency_results.values():
                weight_ids.update(position_results.keys())
            weight_ids = sorted(list(weight_ids))
            
            if position_ids and weight_ids:
                consistency_matrix = np.zeros((len(position_ids), len(weight_ids)))
                for i, position_id in enumerate(position_ids):
                    for j, weight_id in enumerate(weight_ids):
                        if (position_id in self.consistency_results and 
                            weight_id in self.consistency_results[position_id] and
                            'sensitivity_total' in self.consistency_results[position_id][weight_id]):
                            consistency_matrix[i, j] = self.consistency_results[position_id][weight_id]['sensitivity_total']
                
                # 创建热力图
                img_item = pg.ImageItem(consistency_matrix)
                p4.addItem(img_item)
                
                # 设置颜色映射
                try:
                    colormap = pg.colormap.get('viridis')
                    img_item.setColorMap(colormap)
                except:
                    # 如果viridis不可用，使用默认颜色映射
                    pass
                
                # 设置坐标轴
                p4.setAspectLocked(False)
                p4.invertY(True)  # Y轴向下
                
                # 设置X轴标签
                ax4_x = p4.getAxis('bottom')
                ax4_x.setTicks([[(i, str(wid)) for i, wid in enumerate(weight_ids)]])
                
                # 设置Y轴标签
                ax4_y = p4.getAxis('left')
                y_labels = [self.guide_positions.get(pid, {}).get('name', pid) for pid in position_ids]
                ax4_y.setTicks([[(i, label) for i, label in enumerate(y_labels)]])
                
                # 添加数值标签
                for i in range(len(position_ids)):
                    for j in range(len(weight_ids)):
                        if consistency_matrix[i, j] > 0:
                            text = pg.TextItem(text=f'{consistency_matrix[i, j]:.4f}', 
                                             color='white', anchor=(0.5, 0.5))
                            text.setPos(j, i)
                            p4.addItem(text)
                
                # 添加颜色条
                try:
                    colorbar = pg.ColorBarItem(values=(consistency_matrix.min(), consistency_matrix.max()), 
                                             colorMap=colormap, label='敏感性')
                    colorbar.setImageItem(img_item)
                except:
                    pass  # 如果颜色条创建失败，跳过
            
            # 显示窗口
            plot_window.show()
            print(f"✅ 一致性分析图表绘制完成")
            
            # 保存图表引用以便后续保存
            self.current_plot_window = plot_window
            
            # 启用保存图表按钮
            self.save_consistency_plot_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制一致性分析图失败: {e}")
            print(f"❌ 绘制一致性分析图失败: {e}")
            import traceback
            traceback.print_exc()
    
    
    
    def save_consistency_results(self):
        """保存一致性结果"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存位置一致性结果", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
            "JSON文件 (*.json);;CSV文件 (*.csv);;文本文件 (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_consistency_results_json(filename)
                elif filename.endswith('.csv'):
                    self.save_consistency_results_csv(filename)
                else:
                    self.save_consistency_results_txt(filename)
                
                QMessageBox.information(self, "成功", f"结果已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_consistency_results_json(self, filename):
        """保存为JSON格式"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'guide_positions': self.guide_positions,
            'consistency_results': self.consistency_results,
            'analysis_summary': self.get_consistency_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_consistency_results_csv(self, filename):
        """保存为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['位置ID', '位置名称', '砝码ID', '测量次数', '平均总压力', '标准差', '变异系数'])
            
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                for weight_id, result in position_results.items():
                    writer.writerow([
                        position_id,
                        position_name,
                        weight_id,
                        result['measurement_count'],
                        f"{result['avg_total_pressure']:.6f}",
                        f"{result['std_total_pressure']:.6f}",
                        f"{result['cv']:.3f}"
                    ])
    
    def save_consistency_results_txt(self, filename):
        """保存为文本格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器位置一致性分析结果\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("===== 引导位置信息 =====\n")
            for position_id, position_info in self.guide_positions.items():
                f.write(f"{position_id}: {position_info['name']} ({position_info['x']}, {position_info['y']}) - {position_info['description']}\n")
            
            f.write("\n===== 一致性分析结果 =====\n")
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                f.write(f"\n位置 {position_id} ({position_name}):\n")
                
                for weight_id, result in position_results.items():
                    f.write(f"  砝码 {weight_id}:\n")
                    f.write(f"    测量次数: {result['measurement_count']}\n")
                    f.write(f"    平均总压力: {result['avg_total_pressure']:.6f}\n")
                    f.write(f"    标准差: {result['std_total_pressure']:.6f}\n")
                    f.write(f"    敏感性(总): {result['sensitivity_total']:.6f}\n")
                    f.write(f"    变异系数: {result['cv']:.3f}\n")
            
            # 添加分析摘要
            summary = self.get_consistency_summary()
            f.write(f"\n===== 分析摘要 =====\n")
            f.write(f"平均变异系数: {summary['avg_cv']:.3f} ± {summary['std_cv']:.3f}\n")
            f.write(f"平均敏感性: {summary['avg_sensitivity']:.6f} ± {summary['std_sensitivity']:.6f}\n")
            f.write(f"位置间一致性CV: {summary['position_consistency_cv']:.3f}\n")
    
    def get_consistency_summary(self):
        """获取一致性分析摘要"""
        if not self.consistency_results:
            return {}
        
        all_cvs = []
        all_sensitivities = []
        
        for position_results in self.consistency_results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in self.consistency_results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        return {
            'avg_cv': avg_cv,
            'std_cv': std_cv,
            'avg_sensitivity': avg_sensitivity,
            'std_sensitivity': std_sensitivity,
            'position_consistency_cv': position_consistency_cv
        }
    
    
    
    def save_consistency_plot(self, plot_window=None):
        """保存一致性分析图"""
        try:
            # 如果没有传入plot_window，尝试使用当前保存的图表窗口
            if plot_window is None:
                if hasattr(self, 'current_plot_window') and self.current_plot_window is not None:
                    plot_window = self.current_plot_window
                else:
                    QMessageBox.warning(self, "警告", "没有可保存的图表窗口，请先绘制图表")
                    return
            
            # 检查plot_window是否有效
            if not plot_window or not hasattr(plot_window, 'scene'):
                QMessageBox.warning(self, "警告", "图表窗口无效")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存一致性分析图", 
                f"consistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"
            )
            
            if filename:
                print(f"🔍 尝试保存图表到: {filename}")
                
                # 确保图表窗口已经渲染
                if hasattr(plot_window, 'scene'):
                    # 强制更新图表
                    plot_window.scene().update()
                    QApplication.processEvents()
                
                # 使用通用保存函数
                if save_pyqtgraph_plot(plot_window, filename):
                    print(f"✅ 一致性分析图已保存到: {filename}")
                    QMessageBox.information(self, "成功", f"一致性分析图已保存到:\n{filename}")
                else:
                    # 如果通用保存函数失败，尝试直接保存
                    print(f"⚠️ 通用保存函数失败，尝试直接保存...")
                    if self.save_plot_directly(plot_window, filename):
                        print(f"✅ 直接保存成功: {filename}")
                        QMessageBox.information(self, "成功", f"一致性分析图已保存到:\n{filename}")
                    else:
                        raise Exception("所有保存方法都失败了")
                
        except Exception as e:
            print(f"⚠️ 保存一致性分析图时出错: {e}")
            QMessageBox.warning(self, "保存失败", f"保存图片时出错:\n{e}")
            import traceback
            traceback.print_exc()
    
    def save_plot_directly(self, plot_window, filename):
        """直接保存图表的方法"""
        try:
            # 方法1: 使用grab方法
            if hasattr(plot_window, 'grab'):
                pixmap = plot_window.grab()
                if pixmap.save(filename):
                    print(f"✅ 使用grab方法保存成功")
                    return True
            
            # 方法2: 使用render方法
            if hasattr(plot_window, 'render'):
                pixmap = QPixmap(plot_window.size())
                plot_window.render(pixmap)
                if pixmap.save(filename):
                    print(f"✅ 使用render方法保存成功")
                    return True
            
            # 方法3: 使用屏幕截图
            try:
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                if screen and hasattr(plot_window, 'winId'):
                    pixmap = screen.grabWindow(plot_window.winId())
                    if pixmap.save(filename):
                        print(f"✅ 使用屏幕截图方法保存成功")
                        return True
            except Exception as e:
                print(f"⚠️ 屏幕截图方法失败: {e}")
            
            return False
            
        except Exception as e:
            print(f"⚠️ 直接保存方法失败: {e}")
            return False
    
    def update_consistency_results_table(self, results):
        """更新一致性结果表格"""
        # 计算总行数
        total_rows = 0
        for position_results in results.values():
            total_rows += len(position_results)
        
        self.consistency_results_table.setRowCount(total_rows)
        
        row = 0
        for position_id, position_results in results.items():
            position_name = self.guide_positions[position_id]['name']
            
            for weight_id, result in position_results.items():
                # 设置表格数据
                self.consistency_results_table.setItem(row, 0, QTableWidgetItem(str(position_id)))
                self.consistency_results_table.setItem(row, 1, QTableWidgetItem(position_name))
                self.consistency_results_table.setItem(row, 2, QTableWidgetItem(str(weight_id)))
                self.consistency_results_table.setItem(row, 3, QTableWidgetItem(str(result['measurement_count'])))
                self.consistency_results_table.setItem(row, 4, QTableWidgetItem(f"{result['avg_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 5, QTableWidgetItem(f"{result['std_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 6, QTableWidgetItem(f"{result['cv']:.3f}"))
                
                row += 1
        
        # 调整表格列宽
        self.consistency_results_table.resizeColumnsToContents()
    
    def show_consistency_analysis(self, results):
        """显示一致性分析结果"""
        if not results:
            return
        
        # 计算整体一致性指标
        all_cvs = []
        all_sensitivities = []
        
        for position_results in results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        analysis_text = f"""位置一致性分析结果:

整体统计:
• 平均变异系数: {avg_cv:.3f} ± {std_cv:.3f}
• 平均敏感性: {avg_sensitivity:.6f} ± {std_sensitivity:.6f}
• 位置间一致性CV: {position_consistency_cv:.3f}

位置数量: {len(results)}
总测量点: {sum(len(pos_results) for pos_results in results.values())}

一致性评估:
"""
        
        if position_consistency_cv < 0.05:
            analysis_text += "• 位置一致性: 优秀 (<5%)\n"
        elif position_consistency_cv < 0.1:
            analysis_text += "• 位置一致性: 良好 (5-10%)\n"
        elif position_consistency_cv < 0.2:
            analysis_text += "• 位置一致性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 位置一致性: 较差 (>20%)\n"
        
        if avg_cv < 0.05:
            analysis_text += "• 测量稳定性: 优秀 (<5%)\n"
        elif avg_cv < 0.1:
            analysis_text += "• 测量稳定性: 良好 (5-10%)\n"
        elif avg_cv < 0.2:
            analysis_text += "• 测量稳定性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 测量稳定性: 较差 (>20%)\n"
        
        QMessageBox.information(self, "位置一致性分析完成", analysis_text)
    
    def update_position_table(self):
        """更新位置表格"""
        self.position_table.setRowCount(len(self.guide_positions))
        
        for row, (position_id, position_info) in enumerate(self.guide_positions.items()):
            self.position_table.setItem(row, 0, QTableWidgetItem(position_id))
            self.position_table.setItem(row, 1, QTableWidgetItem(position_info['name']))
            self.position_table.setItem(row, 2, QTableWidgetItem(str(position_info['x'])))
            self.position_table.setItem(row, 3, QTableWidgetItem(str(position_info['y'])))
            self.position_table.setItem(row, 4, QTableWidgetItem(position_info['description']))
    
    def update_position_selection(self):
        """更新位置选择下拉框"""
        self.position_combo.clear()
        self.position_combo.addItem("选择位置")
        
        for position_id in self.guide_positions.keys():
            self.position_combo.addItem(position_id)
    
    def update_weight_selection_for_consistency(self, weights):
        """更新一致性测试的砝码选择下拉框"""
        self.consistency_weight_combo.clear()
        self.consistency_weight_combo.addItem("选择砝码")
        
        for weight_id in weights.keys():
            self.consistency_weight_combo.addItem(weight_id)
    
    def start_position_measurement(self):
        """开始位置测量"""
        if self.position_combo.currentText() == "选择位置":
            QMessageBox.warning(self, "警告", "请选择测试位置")
            return
        
        if self.consistency_weight_combo.currentText() == "选择砝码":
            QMessageBox.warning(self, "警告", "请选择测试砝码")
            return
        
        # 检查校准数据
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if main_interface and hasattr(main_interface, 'calibration_map'):
            if main_interface.calibration_map is None:
                QMessageBox.warning(self, "警告", "请先加载校准数据")
                return
        
        # 检查传感器连接状态
        if main_interface and hasattr(main_interface, 'is_running'):
            if not main_interface.is_running:
                QMessageBox.warning(self, "警告", "请先启动传感器")
                return
        
        self.current_position_id = self.position_combo.currentText()
        self.current_weight_id = self.consistency_weight_combo.currentText()
        self.measurement_count = self.position_measurement_count_input.value()
        self.position_measurement_active = True
        
        print(f"🚀 开始位置测量: 位置={self.current_position_id}, 砝码={self.current_weight_id}, 次数={self.measurement_count}")
        
        self.start_position_measurement_btn.setEnabled(False)
        self.stop_position_measurement_btn.setEnabled(True)
        self.position_progress_bar.setVisible(True)
        self.position_progress_bar.setMaximum(self.measurement_count)
        self.position_progress_bar.setValue(0)
        
        # 通知主界面开始位置测量
        if main_interface and hasattr(main_interface, 'start_position_consistency_measurement'):
            main_interface.start_position_consistency_measurement(
                self.current_position_id, 
                self.current_weight_id, 
                self.measurement_count
            )
            print(f"✅ 已通知主界面开始位置测量")
    
    def stop_position_measurement(self):
        """停止位置测量"""
        self.position_measurement_active = False
        self.start_position_measurement_btn.setEnabled(True)
        self.stop_position_measurement_btn.setEnabled(False)
        self.position_progress_bar.setVisible(False)
        
        # 通知主界面停止位置测量
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if main_interface and hasattr(main_interface, 'stop_position_consistency_measurement'):
            main_interface.stop_position_consistency_measurement()
    
    def record_position_measurement_data(self, pressure_data):
        """记录位置测量数据（支持位置区分）"""
        if not self.position_measurement_active or self.current_position_id is None or self.current_weight_id is None:
            return
        
        try:
            # 计算压力数据
            total_pressure = np.sum(pressure_data)
            mean_pressure = np.mean(pressure_data)
            max_pressure = np.max(pressure_data)
            
            # 基线校正（从主界面获取基线数据）
            corrected_total = total_pressure
            corrected_mean = mean_pressure
            corrected_max = max_pressure
            
            parent = self.parent()
            main_interface = None
            
            if parent and hasattr(parent, 'parent'):
                tab_widget = parent.parent()
                if tab_widget and hasattr(tab_widget, 'parent'):
                    main_interface = tab_widget.parent()
            
            if main_interface and hasattr(main_interface, 'sensitivity_widget'):
                weight_calibration = main_interface.sensitivity_widget.weight_calibration
                
                if weight_calibration.baseline_data:
                    baseline_stats = weight_calibration.get_baseline_stats()
                    corrected_total = total_pressure - baseline_stats['avg_total_pressure']
                    corrected_mean = mean_pressure - baseline_stats['avg_mean_pressure']
                    corrected_max = max_pressure - baseline_stats['avg_max_pressure']
            
            # 创建测量记录
            measurement = {
                'timestamp': datetime.now(),
                'position_id': self.current_position_id,
                'weight_id': self.current_weight_id,
                'total_pressure': total_pressure,
                'mean_pressure': mean_pressure,
                'max_pressure': max_pressure,
                'corrected_total_pressure': corrected_total,
                'corrected_mean_pressure': corrected_mean,
                'corrected_max_pressure': corrected_max,
                'raw_data': pressure_data.copy()
            }
            
            # 初始化位置数据存储
            if self.current_position_id not in self.position_data:
                self.position_data[self.current_position_id] = {}
            
            if self.current_weight_id not in self.position_data[self.current_position_id]:
                self.position_data[self.current_position_id][self.current_weight_id] = []
            
            # 存储测量数据
            self.position_data[self.current_position_id][self.current_weight_id].append(measurement)
            
            # 获取当前测量次数
            current_count = len(self.position_data[self.current_position_id][self.current_weight_id])
            print(f"✅ 位置测量记录成功: 位置={self.current_position_id}, 砝码={self.current_weight_id}, 次数={current_count}/{self.measurement_count}")
            
            # 更新进度条并添加调试信息
            self.position_progress_bar.setValue(current_count)
            print(f"🔍 进度条已更新: 当前值={self.position_progress_bar.value()}, 最大值={self.position_progress_bar.maximum()}, 可见性={self.position_progress_bar.isVisible()}")
            
            # 更新主界面状态栏
            if main_interface and hasattr(main_interface, 'measurement_status_label'):
                progress = (current_count / self.measurement_count) * 100
                main_interface.measurement_status_label.setText(
                    f"位置测量: {self.current_position_id}-{self.current_weight_id} ({current_count}/{self.measurement_count}) [{progress:.1f}%]"
                )
            
            # 强制更新UI
            QApplication.processEvents()
            
            if current_count >= self.measurement_count:
                print(f"✅ 位置测量完成，停止测量")
                self.stop_position_measurement()
                QMessageBox.information(self, "完成", f"位置 {self.current_position_id} 砝码 {self.current_weight_id} 测量完成")
                
        except Exception as e:
            print(f"❌ 记录位置测量数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_position_consistency(self):
        """计算位置一致性（使用位置专用数据）"""
        if not self.position_data:
            QMessageBox.warning(self, "警告", "请先进行位置测量")
            return
        
        # 获取砝码信息
        parent = self.parent()
        main_interface = None
        
        if parent and hasattr(parent, 'parent'):
            tab_widget = parent.parent()
            if tab_widget and hasattr(tab_widget, 'parent'):
                main_interface = tab_widget.parent()
        
        if not main_interface or not hasattr(main_interface, 'sensitivity_widget'):
            QMessageBox.warning(self, "警告", "无法获取砝码信息")
            return
        
        weight_calibration = main_interface.sensitivity_widget.weight_calibration
        
        # 计算每个位置的一致性
        results = {}
        
        for position_id, position_weights in self.position_data.items():
            position_results = {}
            
            for weight_id, measurements in position_weights.items():
                if not measurements:
                    continue
                
                weight_info = weight_calibration.weights[weight_id]
                force = weight_info['force']
                
                # 使用校正后的数据计算一致性
                total_pressures = [m['corrected_total_pressure'] for m in measurements]
                mean_pressures = [m['corrected_mean_pressure'] for m in measurements]
                max_pressures = [m['corrected_max_pressure'] for m in measurements]
                
                # 计算统计信息
                avg_total_pressure = np.mean(total_pressures)
                std_total_pressure = np.std(total_pressures)
                avg_mean_pressure = np.mean(mean_pressures)
                std_mean_pressure = np.std(mean_pressures)
                avg_max_pressure = np.mean(max_pressures)
                std_max_pressure = np.std(max_pressures)
                
                # 计算变异系数
                cv_total = std_total_pressure / avg_total_pressure if avg_total_pressure > 0 else 0
                cv_mean = std_mean_pressure / avg_mean_pressure if avg_mean_pressure > 0 else 0
                cv_max = std_max_pressure / avg_max_pressure if avg_max_pressure > 0 else 0
                
                position_results[weight_id] = {
                    'weight_info': weight_info,
                    'measurement_count': len(measurements),
                    'avg_total_pressure': avg_total_pressure,
                    'std_total_pressure': std_total_pressure,
                    'avg_mean_pressure': avg_mean_pressure,
                    'std_mean_pressure': std_mean_pressure,
                    'avg_max_pressure': avg_max_pressure,
                    'std_max_pressure': std_max_pressure,
                    'cv': cv_total,  # 使用总压力的变异系数作为主要CV
                    'cv_total': cv_total,
                    'cv_mean': cv_mean,
                    'cv_max': cv_max,
                    'sensitivity_total': avg_total_pressure / force if force > 0 else 0
                }
            
            results[position_id] = position_results
        
        # 更新结果显示
        self.update_consistency_results_table(results)
        
        # 存储结果到组件属性中
        self.consistency_results = results
        
        # 显示分析结果
        self.show_consistency_analysis(results)
        
        print(f"✅ 位置一致性分析完成，共分析 {len(results)} 个位置")
        print(f"📊 结果已存储到 consistency_results 中")
    
    def update_consistency_results_table(self, results):
        """更新一致性结果表格"""
        # 计算总行数
        total_rows = 0
        for position_results in results.values():
            total_rows += len(position_results)
        
        self.consistency_results_table.setRowCount(total_rows)
        
        row = 0
        for position_id, position_results in results.items():
            position_name = self.guide_positions[position_id]['name']
            
            for weight_id, result in position_results.items():
                # 设置表格数据
                self.consistency_results_table.setItem(row, 0, QTableWidgetItem(str(position_id)))
                self.consistency_results_table.setItem(row, 1, QTableWidgetItem(position_name))
                self.consistency_results_table.setItem(row, 2, QTableWidgetItem(str(weight_id)))
                self.consistency_results_table.setItem(row, 3, QTableWidgetItem(str(result['measurement_count'])))
                self.consistency_results_table.setItem(row, 4, QTableWidgetItem(f"{result['avg_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 5, QTableWidgetItem(f"{result['std_total_pressure']:.6f}"))
                self.consistency_results_table.setItem(row, 6, QTableWidgetItem(f"{result['cv']:.3f}"))
                
                row += 1
        
        # 调整表格列宽
        self.consistency_results_table.resizeColumnsToContents()
    
    def show_consistency_analysis(self, results):
        """显示一致性分析结果"""
        if not results:
            return
        
        # 计算整体一致性指标
        all_cvs = []
        all_sensitivities = []
        
        for position_results in results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        analysis_text = f"""位置一致性分析结果:

整体统计:
• 平均变异系数: {avg_cv:.3f} ± {std_cv:.3f}
• 平均敏感性: {avg_sensitivity:.6f} ± {std_sensitivity:.6f}
• 位置间一致性CV: {position_consistency_cv:.3f}

位置数量: {len(results)}
总测量点: {sum(len(pos_results) for pos_results in results.values())}

一致性评估:
"""
        
        if position_consistency_cv < 0.05:
            analysis_text += "• 位置一致性: 优秀 (<5%)\n"
        elif position_consistency_cv < 0.1:
            analysis_text += "• 位置一致性: 良好 (5-10%)\n"
        elif position_consistency_cv < 0.2:
            analysis_text += "• 位置一致性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 位置一致性: 较差 (>20%)\n"
        
        if avg_cv < 0.05:
            analysis_text += "• 测量稳定性: 优秀 (<5%)\n"
        elif avg_cv < 0.1:
            analysis_text += "• 测量稳定性: 良好 (5-10%)\n"
        elif avg_cv < 0.2:
            analysis_text += "• 测量稳定性: 一般 (10-20%)\n"
        else:
            analysis_text += "• 测量稳定性: 较差 (>20%)\n"
        
        QMessageBox.information(self, "位置一致性分析完成", analysis_text)
    
    def save_consistency_results(self):
        """保存一致性结果"""
        if not self.consistency_results:
            QMessageBox.warning(self, "警告", "没有结果可保存")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存位置一致性结果", "C:\\Users\\84672\\Documents\\Research\\balance-sensor\\consistency-test", 
            "JSON文件 (*.json);;CSV文件 (*.csv);;文本文件 (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.save_consistency_results_json(filename)
                elif filename.endswith('.csv'):
                    self.save_consistency_results_csv(filename)
                else:
                    self.save_consistency_results_txt(filename)
                
                QMessageBox.information(self, "成功", f"结果已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_consistency_results_json(self, filename):
        """保存为JSON格式"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'guide_positions': self.guide_positions,
            'consistency_results': self.consistency_results,
            'analysis_summary': self.get_consistency_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_consistency_results_csv(self, filename):
        """保存为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['位置ID', '位置名称', '砝码ID', '测量次数', '平均总压力', '标准差', '变异系数'])
            
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                for weight_id, result in position_results.items():
                    writer.writerow([
                        position_id,
                        position_name,
                        weight_id,
                        result['measurement_count'],
                        f"{result['avg_total_pressure']:.6f}",
                        f"{result['std_total_pressure']:.6f}",
                        f"{result['cv']:.3f}"
                    ])
    
    def save_consistency_results_txt(self, filename):
        """保存为文本格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("传感器位置一致性分析结果\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("===== 引导位置信息 =====\n")
            for position_id, position_info in self.guide_positions.items():
                f.write(f"{position_id}: {position_info['name']} ({position_info['x']}, {position_info['y']}) - {position_info['description']}\n")
            
            f.write("\n===== 一致性分析结果 =====\n")
            for position_id, position_results in self.consistency_results.items():
                position_name = self.guide_positions[position_id]['name']
                f.write(f"\n位置 {position_id} ({position_name}):\n")
                
                for weight_id, result in position_results.items():
                    f.write(f"  砝码 {weight_id}:\n")
                    f.write(f"    测量次数: {result['measurement_count']}\n")
                    f.write(f"    平均总压力: {result['avg_total_pressure']:.6f}\n")
                    f.write(f"    标准差: {result['std_total_pressure']:.6f}\n")
                    f.write(f"    敏感性(总): {result['sensitivity_total']:.6f}\n")
                    f.write(f"    变异系数: {result['cv']:.3f}\n")
            
            # 添加分析摘要
            summary = self.get_consistency_summary()
            f.write(f"\n===== 分析摘要 =====\n")
            f.write(f"平均变异系数: {summary['avg_cv']:.3f} ± {summary['std_cv']:.3f}\n")
            f.write(f"平均敏感性: {summary['avg_sensitivity']:.6f} ± {summary['std_sensitivity']:.6f}\n")
            f.write(f"位置间一致性CV: {summary['position_consistency_cv']:.3f}\n")
    
    def get_consistency_summary(self):
        """获取一致性分析摘要"""
        if not self.consistency_results:
            return {}
        
        all_cvs = []
        all_sensitivities = []
        
        for position_results in self.consistency_results.values():
            for result in position_results.values():
                all_cvs.append(result['cv'])
                all_sensitivities.append(result['sensitivity_total'])
        
        avg_cv = np.mean(all_cvs)
        std_cv = np.std(all_cvs)
        avg_sensitivity = np.mean(all_sensitivities)
        std_sensitivity = np.std(all_sensitivities)
        
        # 计算位置间一致性
        position_sensitivities = {}
        for position_id, position_results in self.consistency_results.items():
            position_sensitivities[position_id] = []
            for result in position_results.values():
                position_sensitivities[position_id].append(result['sensitivity_total'])
        
        position_avg_sensitivities = {pos_id: np.mean(sens) for pos_id, sens in position_sensitivities.items()}
        position_consistency_cv = np.std(list(position_avg_sensitivities.values())) / np.mean(list(position_avg_sensitivities.values())) if np.mean(list(position_avg_sensitivities.values())) > 0 else 0
        
        return {
            'avg_cv': avg_cv,
            'std_cv': std_cv,
            'avg_sensitivity': avg_sensitivity,
            'std_sensitivity': std_sensitivity,
            'position_consistency_cv': position_consistency_cv
        }
    
    
    
    def add_save_button_to_plot(self, plot_window):
        """在图表窗口中添加一个保存按钮"""
        try:
            # 创建一个包含图表和按钮的主窗口
            main_window = QWidget()
            main_window.setWindowTitle("敏感性分析图表")
            main_window.resize(plot_window.width(), plot_window.height() + 60)  # 为按钮留出空间
            
            # 创建垂直布局
            layout = QVBoxLayout()
            
            # 添加图表窗口
            layout.addWidget(plot_window)
            
            # 创建保存按钮
            save_button = QPushButton("保存图表")
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50; /* 绿色背景 */
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: none;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049; /* 深绿色背景 */
                }
                QPushButton:pressed {
                    background-color: #388e3c; /* 更深的绿色背景 */
                }
            """)
            
            # 连接按钮点击信号到保存函数
            save_button.clicked.connect(lambda: self.save_consistency_plot(plot_window))
            
            # 设置按钮大小
            save_button.setFixedHeight(40)
            
            # 添加按钮到布局
            layout.addWidget(save_button)
            
            # 设置主窗口布局
            main_window.setLayout(layout)
            
            # 显示主窗口
            main_window.show()
            
            # 强制更新图表窗口
            plot_window.scene().update()
            QApplication.processEvents()
            
            # 保存主窗口引用
            self.current_plot_window = main_window
            
            print(f"✅ 保存按钮已添加到图表窗口底部")
            
        except Exception as e:
            print(f"⚠️ 添加保存按钮失败: {e}")
            import traceback
            traceback.print_exc()
    
    
    
