#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

功能：
    對韌體 binary 進行故障注入 (Fuzzing)，完全不依賴 ELF 檔案。
    
    支援模式 (--mode)：
    1. integrity (預設): 完整性破壞模式。
       - 跳過前 512 bytes (保留中斷向量表，確保能開機進入檢查流程)。
       - 跳過 0xFF (空白填充區)。
       - 隨機修改有效數據。
       - 用途：測試 "韌體防置換/防篡改" 能力 (Secure Boot)。
       
    2. float: 盲測浮點數模式 (Blind Float Hunter)。
       - 掃描全檔尋找疑似 PID、導航參數的 IEEE 754 浮點數。
       - 修改這些數值通常會導致飛行不穩，但不會立即當機。
       - 用途：測試系統強健性 (Robustness)。
"""

import argparse
import random
import struct
import math
from pathlib import Path

def is_plausible_float(bytes_4):
    """
    判斷這 4 個 bytes 是否像是一個 "合理的" 飛控參數 (Float)。
    標準: 
    1. 數值不能是 NaN 或 Inf
    2. 絕對值在 0.0001 ~ 100000.0 之間 (過濾掉極端值)
    3. 或者剛好是 0.0 (常見預設值)
    """
    try:
        val = struct.unpack('<f', bytes_4)[0]
        if math.isnan(val) or math.isinf(val):
            return False
        
        # 很多參數是 0，但也可能是空記憶體，所以我們只給 0.0 低權重
        if val == 0.0:
            return False 

        # 飛控參數通常落在這個範圍 (例如 PID P=0.1, 角度=45.0, 高度=100.0)
        if 1e-5 < abs(val) < 1e6:
            return True
            
        return False
    except:
        return False

def scan_for_floats(data):
    """
    [Mode: Float] 掃描整個 binary，找出所有潛在的 float 位置
    """
    candidates = []
    # 跳過前 4KB (保護 Bootloader/Vector Table/Config)
    PROTECT_OFFSET = 4096 
    
    print("[*] [Blind Mode] 啟動浮點數獵人 (Float Hunter)...")
    
    # 4-byte aligned 掃描 (通常參數會對齊)
    for i in range(PROTECT_OFFSET, len(data) - 4, 4):
        chunk = data[i:i+4]
        if is_plausible_float(chunk):
            candidates.append(i)
            
    return candidates

def get_integrity_candidates(data):
    """
    [Mode: Integrity] 找出所有非填充(0xFF)的區域
    """
    candidates = []
    # 跳過前 512 bytes (Vector Table)
    # 保留 Vector Table 可以確保 Bootloader 至少能跳轉進去執行，
    # 這樣才能證明 "驗證機制失效" (它嘗試執行了壞掉的代碼)。
    PROTECT_OFFSET = 512 
    
    print("[*] [Integrity Mode] 正在分析有效數據區...")
    
    for i in range(PROTECT_OFFSET, len(data)):
        if data[i] != 0xFF: # 只改有東西的地方
            candidates.append(i)
            
    return candidates

def blind_mutate(bin_path, output_path, count=1, mode='integrity'):
    if not Path(bin_path).exists():
        print(f"[Error] 找不到檔案: {bin_path}")
        return

    with open(bin_path, 'rb') as f:
        data = bytearray(f.read())
    
    valid_indices = []
    
    # --- 模式選擇 ---
    print(f"[*] 啟動模式: {mode}")

    if mode == 'float':
        float_offsets = scan_for_floats(data)
        if float_offsets:
            print(f"    -> 找到 {len(float_offsets)} 個疑似浮點數參數位置")
            # 擴展攻擊範圍：攻擊找到的 float 的那 4 個 bytes
            for offset in float_offsets:
                valid_indices.extend([offset, offset+1, offset+2, offset+3])
        else:
            print("[!] 未找到明顯浮點數，切換至 integrity 模式")
            mode = 'integrity'

    if mode == 'integrity':
        # 隨機修改任何代碼/數據，測試防篡改能力
        valid_indices = get_integrity_candidates(data)

    if not valid_indices:
        print("[Error] 沒有可攻擊的目標！(檔案可能是空的或全為 0xFF)")
        return

    print(f"[*] 可攻擊 Byte 總數: {len(valid_indices)}")

    # --- 執行故障注入 ---
    modified_log = []
    for _ in range(count):
        target_idx = random.choice(valid_indices)
        original_byte = data[target_idx]
        
        # 破壞邏輯：使用 XOR 確保數值一定會改變
        xor_mask = random.randint(1, 255)
        new_byte = original_byte ^ xor_mask
        data[target_idx] = new_byte
        
        # 記錄修改資訊
        offset_hex = f"0x{target_idx:X}"
        modified_log.append(f"Offset {offset_hex}: 0x{original_byte:02X} -> 0x{new_byte:02X}")

    # --- 存檔 ---
    with open(output_path, 'wb') as f:
        f.write(data)
    
    print(f"[V] 生成完成: {output_path}")
    for l in modified_log:
        print(f"    {l}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="韌體 Fuzzer (無 ELF 依賴版)")
    parser.add_argument("--bin", required=True, help="輸入 .bin 檔案")
    parser.add_argument("--out", required=True, help="輸出 .bin 檔案")
    parser.add_argument("--count", type=int, default=1, help="修改幾個 Byte (預設 1)")
    parser.add_argument("--mode", choices=['integrity', 'float'], default='integrity', 
                        help="integrity: 隨機破壞(測防置換), float: 參數破壞(測強健性)")
    
    args = parser.parse_args()
    blind_mutate(args.bin, args.out, args.count, args.mode)