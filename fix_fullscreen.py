#!/usr/bin/env python3
"""
修复全屏问题的脚本
"""

import os

def fix_fullscreen_issue():
    """修复全屏问题"""
    file_path = "weight_measurement_tool.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找并删除apply_simple_mode调用
    modified = False
    new_lines = []
    
    for i, line in enumerate(lines):
        # 跳过apply_simple_mode调用和其注释
        if line.strip() == "# 应用简化模式" or line.strip() == "self.apply_simple_mode()":
            print(f"🗑️ 删除第{i+1}行: {line.strip()}")
            modified = True
            continue
        new_lines.append(line)
    
    if modified:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("✅ 全屏问题修复完成！")
        return True
    else:
        print("ℹ️ 未找到需要修复的代码")
        return False

if __name__ == "__main__":
    fix_fullscreen_issue() 