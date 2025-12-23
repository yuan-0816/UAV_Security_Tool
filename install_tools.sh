#!/bin/bash

# ==============================================================================
# 腳本名稱: install_tools.sh
# 功能: 資安軟體自動安裝
# 目前進度: Nmap (Apt), Zenmap (自動抓最新版 RPM -> Alien -> DEB)
# ==============================================================================

LOG_FILE="install_log.txt"
NMAP_DIST_URL="https://nmap.org/dist/"

# 檢查 Root 權限
if [ "$EUID" -ne 0 ]; then
  echo "錯誤: 請使用 root 權限執行此腳本 (sudo ./install_tools.sh)"
  exit 1
fi

echo "=== 開始執行安裝 $(date) ===" | tee -a "$LOG_FILE"

# 1. 更新系統與安裝必要工具
echo "[*] 更新系統與安裝基礎工具 (curl, alien, wget)..." | tee -a "$LOG_FILE"
export DEBIAN_FRONTEND=noninteractive
apt-get update >> "$LOG_FILE" 2>&1
# 新增 curl 用於分析網頁
apt-get install -y wget alien curl >> "$LOG_FILE" 2>&1

# 2. 安裝 Nmap (核心)
# 重要：因為 RPM 轉檔無法自動解決依賴，我們必須手動先裝好 Nmap 核心
echo "[*] 安裝 Nmap (核心引擎)..." | tee -a "$LOG_FILE"
if apt-get install -y nmap >> "$LOG_FILE" 2>&1; then
    echo " -> Nmap 安裝成功" | tee -a "$LOG_FILE"
else
    echo " -> Nmap 安裝失敗" | tee -a "$LOG_FILE"
fi

# 3. 安裝 Zenmap (自動偵測最新版)
echo "--------------------------------------------------" | tee -a "$LOG_FILE"
echo "[*] 正在連線至 Nmap 官網偵測最新 Zenmap 版本..." | tee -a "$LOG_FILE"

# 邏輯說明: 
# 1. curl 下載網頁原始碼
# 2. grep 抓出所有 zenmap-x.xx-x.noarch.rpm 的檔名
# 3. sort -V (版本排序) 確保抓到數字最大的一版
# 4. tail -n 1 取最後一行(最新版)
LATEST_RPM=$(curl -sL "$NMAP_DIST_URL" | grep -o 'zenmap-[0-9]\+\.[0-9]\+-[0-9]\+\.noarch\.rpm' | sort -V | tail -n 1)

if [ -z "$LATEST_RPM" ]; then
    echo " -> 錯誤: 無法偵測到版本 (可能官網改版或網路問題)" | tee -a "$LOG_FILE"
    echo " -> 嘗試使用備用版本: zenmap-7.95-1.noarch.rpm" | tee -a "$LOG_FILE"
    LATEST_RPM="zenmap-7.95-1.noarch.rpm"
else
    echo " -> 偵測到最新版本檔案: $LATEST_RPM" | tee -a "$LOG_FILE"
fi

DOWNLOAD_URL="${NMAP_DIST_URL}${LATEST_RPM}"

# 下載 RPM
echo "[*] 下載 $LATEST_RPM..." | tee -a "$LOG_FILE"
wget -c "$DOWNLOAD_URL" -O zenmap.rpm >> "$LOG_FILE" 2>&1

if [ -f "zenmap.rpm" ]; then
    echo "[*] 轉換 RPM 為 DEB (Alien)..." | tee -a "$LOG_FILE"
    # --scripts 保留安裝腳本
    alien --scripts --to-deb zenmap.rpm >> "$LOG_FILE" 2>&1
    
    # 找出剛產生的 deb 檔 (排除舊的)
    GENERATED_DEB=$(ls -t zenmap*.deb | head -n 1)
    
    if [ -n "$GENERATED_DEB" ]; then
        echo "[*] 安裝 DEB: $GENERATED_DEB" | tee -a "$LOG_FILE"
        dpkg -i "$GENERATED_DEB" >> "$LOG_FILE" 2>&1
        
        # 驗證
        if dpkg -l | grep -q zenmap; then
            echo " -> Zenmap 安裝成功 (版本: $LATEST_RPM)" | tee -a "$LOG_FILE"
        else
            echo " -> Zenmap 安裝失敗 (dpkg 報錯)" | tee -a "$LOG_FILE"
        fi
    else
        echo " -> Alien 轉換失敗，未產生 .deb 檔" | tee -a "$LOG_FILE"
    fi
    
    # 清理
    rm -f zenmap.rpm zenmap*.deb
else
    echo " -> 下載失敗: 無法取得檔案" | tee -a "$LOG_FILE"
fi

echo "=== 安裝流程結束 ==="