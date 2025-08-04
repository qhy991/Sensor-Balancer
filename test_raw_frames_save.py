#!/usr/bin/env python3
"""
测试保存原始帧数据功能的脚本
"""

import numpy as np
import json
import os
from datetime import datetime

def create_test_frames():
    """创建测试用的帧数据"""
    print("🔧 创建测试帧数据...")
    
    # 创建200帧64x64的测试数据
    frames = []
    base_data = np.random.rand(64, 64) * 0.0001  # 基础数据
    
    for i in range(200):
        # 每帧添加一些随机变化
        frame_data = base_data + np.random.rand(64, 64) * 0.00001
        frames.append(frame_data)
    
    print(f"✅ 创建了 {len(frames)} 帧测试数据")
    print(f"   数据形状: {frames[0].shape}")
    print(f"   数值范围: {np.min(frames):.8f} - {np.max(frames):.8f}")
    
    return frames

def test_save_npz_format(frames, filename="test_raw_frames.npz"):
    """测试保存为NPZ格式"""
    print(f"\n📁 测试保存为NPZ格式: {filename}")
    
    try:
        # 计算参考数据
        reference_data = np.mean(frames, axis=0)
        
        # 保存数据
        frames_array = np.array(frames)
        np.savez_compressed(
            filename,
            frames=frames_array,
            reference_data=reference_data,
            timestamp=datetime.now().isoformat(),
            frame_count=len(frames),
            frame_shape=frames_array.shape[1:]
        )
        
        # 检查文件
        file_size = os.path.getsize(filename)
        print(f"✅ 保存成功")
        print(f"   文件大小: {file_size/1024:.1f} KB")
        print(f"   帧数: {len(frames)}")
        print(f"   数据形状: {frames_array.shape}")
        
        # 测试加载
        loaded_data = np.load(filename)
        loaded_frames = [frame for frame in loaded_data['frames']]
        loaded_reference = loaded_data['reference_data']
        
        print(f"✅ 加载测试成功")
        print(f"   加载帧数: {len(loaded_frames)}")
        print(f"   参考数据形状: {loaded_reference.shape}")
        
        # 验证数据一致性
        frames_match = all(np.allclose(f1, f2) for f1, f2 in zip(frames, loaded_frames))
        reference_match = np.allclose(reference_data, loaded_reference)
        
        print(f"   帧数据一致性: {'✅' if frames_match else '❌'}")
        print(f"   参考数据一致性: {'✅' if reference_match else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def test_save_json_format(frames, filename="test_raw_frames.json"):
    """测试保存为JSON格式"""
    print(f"\n📁 测试保存为JSON格式: {filename}")
    
    try:
        # 计算参考数据
        reference_data = np.mean(frames, axis=0)
        
        # 保存数据
        data_dict = {
            'frames': [frame.tolist() for frame in frames],
            'reference_data': reference_data.tolist(),
            'timestamp': datetime.now().isoformat(),
            'frame_count': len(frames),
            'frame_shape': list(frames[0].shape)
        }
        
        with open(filename, 'w') as f:
            json.dump(data_dict, f, indent=2)
        
        # 检查文件
        file_size = os.path.getsize(filename)
        print(f"✅ 保存成功")
        print(f"   文件大小: {file_size/1024:.1f} KB")
        print(f"   帧数: {len(frames)}")
        
        # 测试加载
        with open(filename, 'r') as f:
            loaded_dict = json.load(f)
        
        loaded_frames = [np.array(frame) for frame in loaded_dict['frames']]
        loaded_reference = np.array(loaded_dict['reference_data'])
        
        print(f"✅ 加载测试成功")
        print(f"   加载帧数: {len(loaded_frames)}")
        print(f"   参考数据形状: {loaded_reference.shape}")
        
        # 验证数据一致性
        frames_match = all(np.allclose(f1, f2) for f1, f2 in zip(frames, loaded_frames))
        reference_match = np.allclose(reference_data, loaded_reference)
        
        print(f"   帧数据一致性: {'✅' if frames_match else '❌'}")
        print(f"   参考数据一致性: {'✅' if reference_match else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def compare_formats():
    """比较不同格式的文件大小"""
    print(f"\n📊 格式比较:")
    
    frames = create_test_frames()
    
    # 测试NPZ格式
    npz_success = test_save_npz_format(frames, "test_raw_frames.npz")
    
    # 测试JSON格式
    json_success = test_save_json_format(frames, "test_raw_frames.json")
    
    if npz_success and json_success:
        npz_size = os.path.getsize("test_raw_frames.npz")
        json_size = os.path.getsize("test_raw_frames.json")
        
        print(f"\n📈 文件大小比较:")
        print(f"   NPZ格式: {npz_size/1024:.1f} KB")
        print(f"   JSON格式: {json_size/1024:.1f} KB")
        print(f"   压缩比: {json_size/npz_size:.1f}x")
        
        # 清理测试文件
        os.remove("test_raw_frames.npz")
        os.remove("test_raw_frames.json")
        
        print(f"\n🧹 测试文件已清理")

def main():
    """主函数"""
    print("🧪 测试保存原始帧数据功能")
    print("=" * 50)
    
    compare_formats()
    
    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    main() 