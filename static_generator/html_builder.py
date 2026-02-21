#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML生成器 - 使用Jinja2模板生成靜態網站
生成HTML頁面和JSON API
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

# 嘗試導入Jinja2，如果未安裝則嘗試安裝
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("[WARN] Jinja2未安裝，嘗試安裝...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jinja2"])
    from jinja2 import Environment, FileSystemLoader, select_autoescape

# 添加父目錄到路徑以便導入db_reader
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processor.db_reader import get_fixtures, get_fixtures_by_league, get_fixtures_by_date

class HTMLBuilder:
    """HTML生成器類"""
    
    def __init__(self, template_dir='../templates', output_dir='../public'):
        """
        初始化生成器
        
        Args:
            template_dir (str): 模板目錄路徑
            output_dir (str): 輸出目錄路徑
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        
        # 創建目錄
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 設置Jinja2環境
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 添加自定義過濾器
        self.env.filters['format_time'] = self.format_time_filter
        self.env.filters['format_date'] = self.format_date_filter
        self.env.filters['league_icon'] = self.league_icon_filter
        
        print(f"[INFO] HTML生成器初始化完成")
        print(f"       模板目錄: {self.template_dir}")
        print(f"       輸出目錄: {self.output_dir}")
    
    def format_time_filter(self, time_str):
        """格式化時間字符串"""
        if not time_str:
            return "待定"
        try:
            # 嘗試解析時間
            if ':' in time_str:
                return time_str
            return time_str
        except:
            return time_str
    
    def format_date_filter(self, date_str):
        """格式化日期字符串"""
        if not date_str:
            return "待定"
        try:
            # 將YYYY-MM-DD轉換為中文格式
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%m月%d日')
        except:
            return date_str
    
    def league_icon_filter(self, league_name):
        """根據聯賽名稱返回對應的圖標類"""
        league_icons = {
            '英超': 'premier-league',
            '西甲': 'la-liga',
            '德甲': 'bundesliga',
            '意甲': 'serie-a',
            '法甲': 'ligue-1',
            '歐冠': 'champions-league',
            '歐霸': 'europa-league',
            '歐協': 'europa-conference',
            '亞冠': 'afc-champions',
            '中超': 'csl',
        }
        
        for key, icon in league_icons.items():
            if key in league_name:
                return icon
        
        return 'default-league'
    
    def generate_index(self, fixtures=None, days_ahead=7):
        """
        生成首頁
        
        Args:
            fixtures (list): 賽事列表，如果為None則自動獲取
            days_ahead (int): 顯示未來多少天的賽事
            
        Returns:
            str: 生成的HTML文件路徑
        """
        print("[INFO] 生成首頁...")
        
        if fixtures is None:
            fixtures = get_fixtures(days_ahead=days_ahead)
        
        # 按日期分組
        fixtures_by_date = get_fixtures_by_date(fixtures)
        
        # 按聯賽分組
        fixtures_by_league = get_fixtures_by_league(fixtures)
        
        # 準備模板數據
        template_data = {
            'title': '足球賽事數據中心',
            'subtitle': '實時更新的足球賽事信息（繁體中文）',
            'fixtures': fixtures,
            'fixtures_by_date': fixtures_by_date,
            'fixtures_by_league': fixtures_by_league,
            'total_fixtures': len(fixtures),
            'total_leagues': len(fixtures_by_league),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'days_ahead': days_ahead,
        }
        
        # 加載模板
        template = self.env.get_template('index.html.j2')
        
        # 渲染HTML
        html_content = template.render(**template_data)
        
        # 保存文件
        output_path = self.output_dir / 'index.html'
        output_path.write_text(html_content, encoding='utf-8')
        
        print(f"[INFO] 首頁已生成: {output_path}")
        return str(output_path)
    
    def generate_league_pages(self, fixtures=None):
        """
        生成聯賽分頁
        
        Args:
            fixtures (list): 賽事列表，如果為None則自動獲取
            
        Returns:
            dict: 生成的HTML文件路徑字典
        """
        print("[INFO] 生成聯賽分頁...")
        
        if fixtures is None:
            fixtures = get_fixtures()
        
        fixtures_by_league = get_fixtures_by_league(fixtures)
        
        league_pages = {}
        
        for league_id, league_data in fixtures_by_league.items():
            league_name = league_data['name']
            
            # 準備模板數據
            template_data = {
                'title': f'{league_name} - 賽事列表',
                'league': league_data,
                'fixtures': league_data['fixtures'],
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # 加載模板
            template = self.env.get_template('league.html.j2')
            
            # 渲染HTML
            html_content = template.render(**template_data)
            
            # 創建聯賽目錄
            league_dir = self.output_dir / 'leagues'
            league_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成安全的文件名
            safe_name = ''.join(c for c in league_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_').replace('-', '_')
            if not safe_name:
                safe_name = f'league_{league_id}'
            
            # 保存文件
            output_path = league_dir / f'{safe_name}.html'
            output_path.write_text(html_content, encoding='utf-8')
            
            league_pages[league_id] = str(output_path)
        
        print(f"[INFO] 已生成 {len(league_pages)} 個聯賽分頁")
        return league_pages
    
    def generate_json_api(self, fixtures=None):
        """
        生成JSON API數據
        
        Args:
            fixtures (list): 賽事列表，如果為None則自動獲取
            
        Returns:
            dict: 生成的JSON文件路徑字典
        """
        print("[INFO] 生成JSON API...")
        
        if fixtures is None:
            fixtures = get_fixtures()
        
        # 創建API目錄
        api_dir = self.output_dir / 'api'
        api_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 完整賽事數據
        full_data = {
            'status': 'success',
            'count': len(fixtures),
            'generated_at': datetime.now().isoformat(),
            'data': fixtures
        }
        
        full_path = api_dir / 'fixtures.json'
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        # 2. 按聯賽分組的數據
        fixtures_by_league = get_fixtures_by_league(fixtures)
        leagues_data = {
            'status': 'success',
            'count': len(fixtures_by_league),
            'generated_at': datetime.now().isoformat(),
            'data': fixtures_by_league
        }
        
        leagues_path = api_dir / 'leagues.json'
        with open(leagues_path, 'w', encoding='utf-8') as f:
            json.dump(leagues_data, f, ensure_ascii=False, indent=2)
        
        # 3. 按日期分組的數據
        fixtures_by_date = get_fixtures_by_date(fixtures)
        dates_data = {
            'status': 'success',
            'count': len(fixtures_by_date),
            'generated_at': datetime.now().isoformat(),
            'data': fixtures_by_date
        }
        
        dates_path = api_dir / 'dates.json'
        with open(dates_path, 'w', encoding='utf-8') as f:
            json.dump(dates_data, f, ensure_ascii=False, indent=2)
        
        # 4. 統計數據
        stats_data = {
            'status': 'success',
            'generated_at': datetime.now().isoformat(),
            'total_fixtures': len(fixtures),
            'total_leagues': len(fixtures_by_league),
            'total_dates': len(fixtures_by_date),
            'leagues': [
                {
                    'id': league_id,
                    'name': data['name'],
                    'count': len(data['fixtures'])
                }
                for league_id, data in fixtures_by_league.items()
            ]
        }
        
        stats_path = api_dir / 'stats.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] JSON API已生成到 {api_dir}")
        
        return {
            'fixtures': str(full_path),
            'leagues': str(leagues_path),
            'dates': str(dates_path),
            'stats': str(stats_path)
        }
    
    def generate_css(self):
        """
        生成CSS樣式文件
        """
        print("[INFO] 生成CSS樣式...")
        
        css_dir = self.output_dir / 'css'
        css_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本CSS樣式
        css_content = """
/* 足球賽事數據中心 - 主要樣式 */
:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --success-color: #27ae60;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    --light-color: #ecf0f1;
    --dark-color: #34495e;
    --border-radius: 8px;
    --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    --transition: all 0.3s ease;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 頭部樣式 */
header {
    background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
    color: white;
    padding: 2rem 0;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: var(--box-shadow);
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
}

header .subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    max-width: 800px;
    margin: 0 auto;
}

/* 統計卡片 */
.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--box-shadow);
    text-align: center;
    transition: var(--transition);
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
}

.stat-card h3 {
    color: var(--secondary-color);
    margin-bottom: 0.5rem;
    font-size: 1.8rem;
}

.stat-card p {
    color: #666;
    font-size: 0.9rem;
}

/* 賽事卡片 */
.fixtures-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.fixture-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--box-shadow);
    transition: var(--transition);
    border-left: 4px solid var(--primary-color);
}

.fixture-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.fixture-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #eee;
}

.league-badge {
    background: var(--primary-color);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.fixture-time {
    color: #666;
    font-size: 0.9rem;
}

.fixture-teams {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.team {
    text-align: center;
    flex: 1;
}

.team-name {
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.3rem;
}

.team-country {
    font-size: 0.8rem;
    color: #666;
}

.vs {
    font-weight: 700;
    color: var(--primary-color);
    margin: 0 1rem;
}

.fixture-details {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #666;
}

.detail-item {
    display: flex;
    align-items: center;
}

.detail-item i {
    margin-right: 0.5rem;
    color: var(--primary-color);
}

/* 聯賽導航 */
.league-nav {
    background: white;
    border-radius: var(--border-radius);
    padding: 1rem;
    margin-bottom: 2rem;
    box-shadow: var(--box-shadow);
}

.league-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    list-style: none;
}

.league-item {
    background: var(--light-color);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    transition: var(--transition);
    cursor: pointer;
}

.league-item:hover {
    background: var(--primary-color);
    color: white;
}

.league-item.active {
    background: var(--primary-color);
    color: white;
}

/* 日期導航 */
.date-nav {
    background: white;
    border-radius: var(--border-radius);
    padding: 1rem;
    margin-bottom: 2rem;
    box-shadow: var(--box-shadow);
}

.date-list {
    display: flex;
    overflow-x: auto;
    gap: 0.5rem;
    padding-bottom: 0.5rem;
}

.date-item {
    background: var(--light-color);
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
    font-size: 0.9rem;
    white-space: nowrap;
    transition: var(--transition);
    cursor: pointer;
}

.date-item:hover {
    background: var(--primary-color);
    color: white;
}

.date-item.active {
    background: var(--primary-color);
    color: white;
}

/* 頁腳 */
footer {
    background: var(--secondary-color);
    color: white;
    padding: 2rem 0;
    margin-top: 3rem;
    text-align: center;
}

footer p {
    margin-bottom: 0.5rem;
    opacity: 0.8;
}

footer a {
    color: var(--primary-color);
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

/* 響應式設計 */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    .fixtures-container {
        grid-template-columns: 1fr;
    }
    
    .stats-container {
        grid-template-columns: 1fr;
    }
    
    .league-list {
        justify-content: center;
    }
    
    .date-list {
        justify-content: flex-start;
    }
}

/* 加載動畫 */
.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s linear infinite;
}

@keyframes spin {
    100% { transform: rotate(360deg); }
}
"""
        
        css_path = css_dir / 'style.css'
        css_path.write_text(css_content, encoding='utf-8')
        
        print(f"[INFO] CSS樣式已生成: {css_path}")
        return str(css_path)
    
    def generate_js(self):
        """
        生成JavaScript文件
        """
        print("[INFO] 生成JavaScript...")
        
        js_dir = self.output_dir / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本JavaScript功能
        js_content = """
// 足球賽事數據中心 - JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化功能
    initFilters();
    initSearch();
    initDateNavigation();
    initLeagueNavigation();
    
    // 更新時間
    updateLiveTime();
    setInterval(updateLiveTime, 60000);
    
    // 加載JSON數據（如果可用）
    loadJSONData();
});

// 初始化篩選器
function initFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            
            // 更新按鈕狀態
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選賽事
            filterFixtures(filterValue);
        });
    });
}

// 篩選賽事
function filterFixtures(filterType) {
    const fixtures = document.querySelectorAll('.fixture-card');
    
    fixtures.forEach(fixture => {
        switch(filterType) {
            case 'all':
                fixture.style.display = 'block';
                break;
            case 'today':
                const fixtureDate = fixture.getAttribute('data-date');
                const today = new Date().toISOString().split('T')[0];
                fixture.style.display = fixtureDate === today ? 'block' : 'none';
                break;
            case 'tomorrow':
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                const tomorrowStr = tomorrow.toISOString().split('T')[0];
                const fixtureDate2 = fixture.getAttribute('data-date');
                fixture.style.display = fixtureDate2 === tomorrowStr ? 'block' : 'none';
                break;
            case 'live':
                const status = fixture.getAttribute('data-status');
                fixture.style.display = status === 'live' ? 'block' : 'none';
                break;
            default:
                fixture.style.display = 'block';
        }
    });
}

// 初始化搜索
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        
        if (searchTerm.length === 0) {
            // 顯示所有賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                card.style.display = 'block';
            });
            return;
        }
        
        // 搜索賽事
        document.querySelectorAll('.fixture-card').forEach(card => {
            const homeTeam = card.getAttribute('data-home-team').toLowerCase();
            const awayTeam = card.getAttribute('data-away-team').toLowerCase();
            const league = card.getAttribute('data-league').toLowerCase();
            
            if (homeTeam.includes(searchTerm) || 
                awayTeam.includes(searchTerm) || 
                league.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// 初始化日期導航
function initDateNavigation() {
    const dateItems = document.querySelectorAll('.date-item');
    
    dateItems.forEach(item => {
        item.addEventListener('click', function() {
            const date = this.getAttribute('data-date');
            
            // 更新按鈕狀態
            dateItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選該日期的賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                const cardDate = card.getAttribute('data-date');
                card.style.display = cardDate === date ? 'block' : 'none';
            });
        });
    });
}

// 初始化聯賽導航
function initLeagueNavigation() {
    const leagueItems = document.querySelectorAll('.league-item');
    
    leagueItems.forEach(item => {
        item.addEventListener('click', function() {
            const leagueId = this.getAttribute('data-league-id');
            
            // 更新按鈕狀態
            leagueItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選該聯賽的賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                const cardLeagueId = card.getAttribute('data-league-id');
                card.style.display = cardLeagueId === leagueId ? 'block' : 'none';
            });
        });
    });
}

// 更新實時時間
function updateLiveTime() {
    const timeElements = document.querySelectorAll('.live-time');
    
    timeElements.forEach(element => {
        const timestamp = parseInt(element.getAttribute('data-timestamp'));
        if (timestamp) {
            const now = Math.floor(Date.now() / 1000);
            const diff = now - timestamp;
            
            if (diff < 0) {
                // 比賽尚未開始
                const hours = Math.floor(-diff / 3600);
                const minutes = Math.floor((-diff % 3600) / 60);
                
                if (hours > 0) {
                    element.textContent = `${hours}小時${minutes}分鐘後開始`;
                } else {
                    element.textContent = `${minutes}分鐘後開始`;
                }
                element.className = 'live-time upcoming';
            } else if (diff < 7200) { // 2小時內，認為是比賽中
                const minutes = Math.floor(diff / 60);
                element.textContent = `${minutes}'`;
                element.className = 'live-time live';
            } else {
                element.textContent = '已結束';
                element.className = 'live-time finished';
            }
        }
    });
}

// 加載JSON數據
function loadJSONData() {
    // 嘗試加載API數據
    fetch('/api/fixtures.json')
        .then(response => response.json())
        .then(data => {
            console.log('成功加載賽事數據:', data);
            // 可以在這裡處理動態加載的數據
        })
        .catch(error => {
            console.log('無法加載API數據:', error);
        });
}

// 分享功能
function shareFixture(fixtureId) {
    const fixture = document.querySelector(`[data-fixture-id="${fixtureId}"]`);
    if (!fixture) return;
    
    const homeTeam = fixture.getAttribute('data-home-team');
    const awayTeam = fixture.getAttribute('data-away-team');
    const league = fixture.getAttribute('data-league');
    const time = fixture.getAttribute('data-time');
    
    const shareText = `📅 ${league}: ${homeTeam} vs ${awayTeam} - ${time}`;
    
    // 嘗試使用Web Share API
    if (navigator.share) {
        navigator.share({
            title: '足球賽事',
            text: shareText,
            url: window.location.href
        });
    } else {
        // 降級方案：複製到剪貼板
        navigator.clipboard.writeText(shareText)
            .then(() => alert('賽事信息已複製到剪貼板！'))
            .catch(err => console.error('複製失敗:', err));
    }
}
"""
        
        js_path = js_dir / 'main.js'
        js_path.write_text(js_content, encoding='utf-8')
        
        print(f"[INFO] JavaScript已生成: {js_path}")
        return str(js_path)
    
    def generate_all(self, days_ahead=7):
        """
        生成所有靜態文件
        
        Args:
            days_ahead (int): 顯示未來多少天的賽事
            
        Returns:
            dict: 所有生成的文件路徑
        """
        print("[INFO] 開始生成所有靜態文件...")
        
        # 獲取賽事數據
        fixtures = get_fixtures(days_ahead=days_ahead)
        
        # 生成各種文件
        result = {
            'index': self.generate_index(fixtures, days_ahead),
            'league_pages': self.generate_league_pages(fixtures),
            'json_api': self.generate_json_api(fixtures),
            'css': self.generate_css(),
            'js': self.generate_js()
        }
        
        print("[SUCCESS] 所有靜態文件生成完成！")
        return result

if __name__ == '__main__':
    # 測試代碼
    builder = HTMLBuilder()
    
    try:
        result = builder.generate_all(days_ahead=3)
        print(f"\n生成結果:")
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} 個文件")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"[ERROR] 生成失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)