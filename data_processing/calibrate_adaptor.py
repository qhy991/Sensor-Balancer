# algorithm_class 是 sensor_calibrate.py 中 Algorithm 的子类
eps = 1e-12

import os
import base64
import hashlib


class SimpleEncryption:
    """简化的加密类，使用base64和简单的哈希替代cryptography"""
    
    def __init__(self):
        self.salt = b'SIMPLE_SALT_2024'

    def _get_key(self, passphrase: str) -> bytes:
        """生成简单的密钥"""
        key_material = passphrase.encode('utf-8') + self.salt
        return hashlib.sha256(key_material).digest()

    def encrypt(self, plaintext: str, passphrase: str) -> str:
        """简单的加密（实际是编码）"""
        # 为了简化，这里只是base64编码
        return base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')

    def decrypt(self, encrypted_data: str, passphrase: str) -> str:
        """简单的解密（实际是解码）"""
        # 为了简化，这里只是base64解码
        return base64.b64decode(encrypted_data).decode('utf-8')


class CalibrateAdaptor:

    def __init__(self, sensor_class, algorithm_class, *args, **kwargs):
        sensor_shape = sensor_class.SENSOR_SHAPE
        self.algorithm_class = algorithm_class
        self.algorithm = algorithm_class(sensor_class, None, *args, **kwargs)
        self.__sensor_shape = sensor_shape

    def range(self):
        return self.algorithm.get_range()

    def load(self, path, forced_to_use_clb):
        is_encrypted = None
        if path.endswith('.clb'):
            is_encrypted = True
        elif path.endswith('.csv'):
            is_encrypted = False
        else:
            raise ValueError('Unsupported file format. Only .clb and .csv are supported.')
        
        if is_encrypted or forced_to_use_clb:
            content = ''.join([_.decode() for _ in open(path, 'rb').readlines()])
            se = SimpleEncryption()
            content = se.decrypt(content, '-')
        else:
            content = ''.join(open(path, 'rt').readlines())
        assert self.algorithm.load(content)

    def transform_frame(self, voltage_frame):
        # 将一帧从原始数据变为标定结果
        # 原始数据为量化电压
        force_frame = self.algorithm.transform_streaming(voltage_frame)
        # force_frame = average_2x2_blocks(force_frame)
        return force_frame

    def __bool__(self):
        return self.algorithm_class.IS_NOT_IDLE


if __name__ == '__main__':

    # transform '.csv' to '.clb'
    folder = os.path.join(os.path.dirname(__file__), '../calibrate_files')
    for file in os.listdir(folder):
        if file.endswith('.csv'):
            path = os.path.join(folder, file)
            se = SimpleEncryption()
            with open(path, 'rt') as f:
                content = ''.join(f.readlines())
            encrypted_content = se.encrypt(content, '-')
            with open(path.replace('.csv', '.clb'), 'wb') as f:
                f.write(encrypted_content.encode())


