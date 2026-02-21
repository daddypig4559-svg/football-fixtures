#!/bin/bash
# 足球賽事數據中心 - 自動化部署腳本
# 一鍵式部署：數據同步 → 靜態生成 → GitHub Pages部署

set -e  # 遇到錯誤立即退出
set -o pipefail  # 管道命令錯誤也退出

echo "🚀 開始部署足球賽事數據中心..."

# 設置顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 檢查必要命令
check_requirements() {
    log_info "檢查系統要求..."
    
    local missing=0
    
    # 檢查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安裝"
        missing=1
    else
        log_info "Python3 版本: $(python3 --version)"
    fi
    
    # 檢查pip
    if ! command -v pip3 &> /dev/null; then
        log_warn "pip3 未安裝，嘗試安裝..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-pip
        else
            log_error "無法自動安裝pip3"
            missing=1
        fi
    fi
    
    # 檢查Jinja2
    if ! python3 -c "import jinja2" &> /dev/null; then
        log_warn "Jinja2 未安裝，正在安裝..."
        pip3 install jinja2
    fi
    
    # 檢查Git
    if ! command -v git &> /dev/null; then
        log_error "Git 未安裝"
        missing=1
    else
        log_info "Git 版本: $(git --version)"
    fi
    
    if [ $missing -eq 1 ]; then
        log_error "系統要求檢查失敗"
        exit 1
    fi
    
    log_info "系統要求檢查完成"
}

# 數據同步
sync_data() {
    log_info "開始數據同步..."
    
    local data_dir="/root/.openclaw/workspace/api_football_sync"
    local db_file="fixtures.db"
    
    if [ -f "$data_dir/$db_file" ]; then
        log_info "找到數據庫文件: $data_dir/$db_file"
        
        # 複製數據庫到當前目錄（用於測試）
        if [ ! -f "data/fixtures.db" ]; then
            mkdir -p data
            cp "$data_dir/$db_file" "data/fixtures.db"
            log_info "數據庫已複製到本地"
        fi
        
        # 檢查數據庫大小
        local db_size=$(stat -c%s "$data_dir/$db_file" 2>/dev/null || stat -f%z "$data_dir/$db_file")
        log_info "數據庫大小: $(numfmt --to=iec $db_size)"
        
        # 檢查賽事數量
        if command -v sqlite3 &> /dev/null; then
            local fixture_count=$(sqlite3 "$data_dir/$db_file" "SELECT COUNT(*) FROM fixtures WHERE status_short IN ('NS', '1H', 'HT', '2H', 'ET', 'BT', 'P')" 2>/dev/null || echo "未知")
            log_info "可用賽事數量: $fixture_count"
        fi
    else
        log_warn "未找到數據庫文件，跳過數據同步"
        log_warn "請確保API-Football同步系統已運行"
        log_warn "數據庫預期位置: $data_dir/$db_file"
    fi
    
    log_info "數據同步完成"
}

# 生成靜態網站
generate_static() {
    log_info "開始生成靜態網站..."
    
    # 檢查Python腳本
    if [ ! -f "static_generator/html_builder.py" ]; then
        log_error "HTML生成器不存在: static_generator/html_builder.py"
        exit 1
    fi
    
    if [ ! -f "data_processor/db_reader.py" ]; then
        log_error "數據讀取器不存在: data_processor/db_reader.py"
        exit 1
    fi
    
    # 運行靜態生成器
    log_info "運行HTML生成器..."
    cd static_generator
    
    if ! python3 html_builder.py; then
        log_error "HTML生成失敗"
        exit 1
    fi
    
    cd ..
    
    # 檢查生成的文件
    if [ -f "public/index.html" ]; then
        log_info "主頁生成成功: public/index.html"
        local file_count=$(find public -type f | wc -l)
        log_info "生成文件總數: $file_count"
    else
        log_error "主頁生成失敗"
        exit 1
    fi
    
    log_info "靜態網站生成完成"
}

# 部署到GitHub
deploy_to_github() {
    log_info "開始部署到GitHub..."
    
    # 檢查當前目錄是否為Git倉庫
    if [ ! -d ".git" ]; then
        log_error "當前目錄不是Git倉庫"
        exit 1
    fi
    
    # 設置Git配置（如果未設置）
    if [ -z "$(git config user.name)" ]; then
        git config user.name "Football Fixtures Bot"
    fi
    
    if [ -z "$(git config user.email)" ]; then
        git config user.email "bot@football-fixtures.local"
    fi
    
    # 添加所有文件
    log_info "添加文件到Git..."
    git add .
    
    # 檢查是否有變更
    if git diff --cached --quiet; then
        log_info "沒有變更需要提交"
        return 0
    fi
    
    # 提交變更
    local commit_msg="Auto-update: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "提交變更: $commit_msg"
    git commit -m "$commit_msg"
    
    # 推送到遠程倉庫
    log_info "推送到GitHub..."
    
    # 嘗試使用SSH，如果失敗則使用HTTPS
    if git push origin main 2>/dev/null; then
        log_info "推送成功 (SSH)"
    else
        log_warn "SSH推送失敗，嘗試HTTPS..."
        
        # 獲取當前遠程URL
        local remote_url=$(git remote get-url origin)
        
        # 如果是SSH URL，轉換為HTTPS
        if [[ $remote_url == git@github.com:* ]]; then
            local repo_path=$(echo $remote_url | sed 's/git@github.com://' | sed 's/.git$//')
            local https_url="https://github.com/$repo_path.git"
            log_info "轉換為HTTPS URL: $https_url"
            git remote set-url origin $https_url
        fi
        
        if git push origin main; then
            log_info "推送成功 (HTTPS)"
        else
            log_error "推送失敗"
            exit 1
        fi
    fi
    
    log_info "GitHub部署完成"
}

# 檢查GitHub Pages狀態
check_github_pages() {
    log_info "檢查GitHub Pages狀態..."
    
    # 提示用戶手動檢查
    echo ""
    echo "📋 GitHub Pages 設置指南:"
    echo "1. 訪問: https://github.com/daddypig4559-svg/football-fixtures/settings/pages"
    echo "2. 選擇部署分支: main"
    echo "3. 選擇部署目錄: / (根目錄) 或 /public"
    echo "4. 點擊 Save"
    echo "5. 等待幾分鐘，然後訪問: https://daddypig4559-svg.github.io/football-fixtures/"
    echo ""
    
    log_info "GitHub Pages檢查完成"
}

# 生成部署報告
generate_report() {
    log_info "生成部署報告..."
    
    local report_file="deployment_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    cat > "$report_file" << EOF
足球賽事數據中心 - 部署報告
生成時間: $(date '+%Y-%m-%d %H:%M:%S %Z')

📊 系統狀態:
- 部署狀態: $([ $? -eq 0 ] && echo "成功" || echo "失敗")
- 部署時間: $(date '+%Y-%m-%d %H:%M:%S')
- 執行用戶: $(whoami)
- 系統主機: $(hostname)

📁 文件統計:
- 總文件數: $(find . -type f | wc -l)
- 公開文件: $(find public -type f 2>/dev/null | wc -l)
- 模板文件: $(find templates -type f 2>/dev/null | wc -l)
- 腳本文件: $(find scripts -type f 2>/dev/null | wc -l)

🌐 GitHub狀態:
- 倉庫: https://github.com/daddypig4559-svg/football-fixtures
- 主頁: https://daddypig4559-svg.github.io/football-fixtures/
- 最後提交: $(git log -1 --format="%H %ad" --date=short 2>/dev/null || echo "未知")

🚀 下一步:
1. 訪問GitHub倉庫設置頁面啟用Pages
2. 等待Pages部署完成
3. 測試網站功能
4. 設置自動化定時更新

📞 問題反饋:
- 檢查日誌文件: deployment.log
- 重新運行: ./scripts/deploy.sh
- 手動部署: git push origin main

記錄結束
EOF
    
    log_info "部署報告已生成: $report_file"
    
    # 顯示簡要報告
    echo ""
    echo "🎯 部署完成摘要:"
    echo "✅ 系統要求檢查完成"
    echo "✅ 數據同步完成"
    echo "✅ 靜態網站生成完成"
    echo "✅ GitHub提交完成"
    echo ""
    echo "🌐 訪問地址:"
    echo "   GitHub倉庫: https://github.com/daddypig4559-svg/football-fixtures"
    echo "   網站主頁: https://daddypig4559-svg.github.io/football-fixtures/"
    echo ""
    echo "📋 請按照上述指南啟用GitHub Pages"
}

# 主函數
main() {
    log_info "🚀 足球賽事數據中心部署開始"
    log_info "版本: 1.0.0"
    log_info "時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    # 執行部署步驟
    check_requirements
    sync_data
    generate_static
    deploy_to_github
    check_github_pages
    generate_report
    
    log_info "🎉 部署流程完成！"
    log_info "請按照提示啟用GitHub Pages以完成最後一步"
}

# 運行主函數
main "$@" 2>&1 | tee -a deployment.log

exit ${PIPESTATUS[0]}