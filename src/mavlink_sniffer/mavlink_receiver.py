import numpy as np
import time
from pyhackrf import HackRF

class MavlinkReceiver:
    def __init__(
            self, 
            min_freq=920000, 
            max_freq=928000, 
            net_id=25, 
            num_channels=20, 
            sample_rate=2000000
        ):
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.net_id = net_id
        self.num_channels = num_channels
        self.sample_rate = sample_rate
        
        # 跳頻表計算 (保留您原本的邏輯)
        self.hopping_sequence = self.__calculate_hopping_sequence(net_id, num_channels)
        self.freq_list = self.__calculate_freq_list()
        
        self.sdr = None

    def __calculate_hopping_sequence(self, net_id, num_channels):
        r_next = net_id
        def r_rand():
            nonlocal r_next
            r_next = (r_next * 1103515245 + 12345) & 0xFFFFFFFF
            return int((r_next // 65536) % 32768)

        channel_map = list(range(num_channels))
        for i in range(num_channels - 1):
            j = r_rand() % num_channels
            channel_map[i], channel_map[j] = channel_map[j], channel_map[i]
        return channel_map

    def __calculate_freq_list(self):
        freq_step = (self.max_freq - self.min_freq) // self.num_channels
        freqs = []
        for ch_idx in self.hopping_sequence:
            # HackRF 接收 Hz
            freq_hz = (self.min_freq + (ch_idx * freq_step)) * 1000
            freqs.append(freq_hz)
        return freqs

    def setup_sdr(self):
        """
        使用 hackrf_native 初始化
        """
        print("正在初始化 HackRF...")
        self.sdr = HackRF()
        
        # 1. 開啟裝置
        self.sdr.open()
        
        # 2. 設定參數
        self.sdr.set_sample_rate(self.sample_rate)
        
        # 設定中心頻率 (先鎖定第一個頻率測試)
        target_freq = self.freq_list[0]
        self.sdr.set_freq(target_freq)
        print(f"SDR 設定頻率: {target_freq/1e6} MHz")
        
        # 3. 設定增益 (Amp, LNA, VGA)
        # 這些數值可以根據收訊狀況調整
        self.sdr.set_gains(lna=32, vga=20, amp=True)

    def demodulate_gfsk(self, iq_samples):
        # 簡單的相位差分解調
        phase_diff = np.angle(iq_samples[1:] * np.conj(iq_samples[:-1]))
        bits = (phase_diff > 0).astype(int)
        return bits

    def search_for_packet(self, bits):
        # 轉成字串搜尋 (僅看前 5000 點以節省效能)
        bit_str = "".join(map(str, bits[:5000])) 
        
        # 搜尋前導碼 (Preamble)
        if "0101010101010101" in bit_str:
            return True, "Found Preamble (0101...)"
            
        # 搜尋同步字 (Sync Word) - 假設值，實際需看 SiK 設定
        if "0010110111010100" in bit_str:
            return True, "Found SYNC WORD!"
            
        return False, ""

    def rx_callback(self, samples):
        """
        這是 hackrf_native 的 Callback。
        輸入 samples 已經是 numpy int8 array，不需要再 frombuffer。
        """
        
        # 1. 將整數轉成複數 (Complex64)
        # 我們的 hackrf_native 已經直接傳回 numpy array
        # 偶數位是 I，奇數位是 Q
        # 正規化到 -1.0 ~ 1.0
        iq_data = (samples[0::2] + 1j * samples[1::2]) / 128.0
        
        # 2. 丟進去解調
        bits = self.demodulate_gfsk(iq_data)
        found, msg = self.search_for_packet(bits)
        
        if found:
            print(f"[{time.time():.2f}] Callback 偵測: {msg}")

    def start_listening(self):
        print("開始接收數據 (使用 Callback 模式)... 按 Ctrl+C 停止")
        try:
            # 啟動接收，綁定 callback
            self.sdr.start_rx(self.rx_callback)
            
            # 主程式保持運行
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n停止接收。")
        except Exception as e:
            print(f"發生錯誤: {e}")
        finally:
            if self.sdr:
                self.sdr.close()
                print("SDR 已安全關閉。")

if __name__ == "__main__":
    receiver = MavlinkReceiver(
        min_freq=920000, 
        max_freq=928000, 
        net_id=25, 
        num_channels=20
    )
    
    receiver.setup_sdr()
    receiver.start_listening()