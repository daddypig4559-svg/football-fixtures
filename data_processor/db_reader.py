#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據讀取器 - 從fixtures.db讀取足球賽事數據
支持59聯賽篩選和繁體中文翻譯
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 添加api_football_sync目錄到路徑，以便導入league_manager
sys.path.insert(0, str(Path(__file__).parent.parent / 'api_football_sync'))

# 嘗試導入league_manager中的聯賽映射
try:
    from league_manager import LEAGUE_ID_TO_TRADITIONAL_CHINESE
    TARGET_LEAGUE_IDS = set(LEAGUE_ID_TO_TRADITIONAL_CHINESE.keys())
    print(f"[INFO] 已加載 {len(TARGET_LEAGUE_IDS)} 個目標聯賽ID")
except ImportError as e:
    print(f"[WARN] 無法導入league_manager: {e}")
    # 如果導入失敗，使用默認的59聯賽ID列表（從之前的工作中提取）
    TARGET_LEAGUE_IDS = {
        39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
        59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78,
        79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
        99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114,
        115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130,
        131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146,
        147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162,
        163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178,
        179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194,
        195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
        211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226,
        227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242,
        243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258,
        259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274,
        275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290,
        291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306,
        307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322,
        323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338,
        339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354,
        355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370,
        371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386,
        387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402,
        403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418,
        419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434,
        435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450,
        451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466,
        467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482,
        483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498,
        499, 500
    }
    print(f"[INFO] 使用默認的 {len(TARGET_LEAGUE_IDS)} 個聯賽ID")

def get_db_path():
    """獲取fixtures.db文件路徑"""
    # 嘗試多個可能的位置
    possible_paths = [
        Path(__file__).parent.parent / 'api_football_sync' / 'fixtures.db',
        Path(__file__).parent.parent / 'fixtures.db',
        Path('/root/.openclaw/workspace/api_football_sync/fixtures.db'),
        Path('/root/.openclaw/workspace/fixtures.db'),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"[INFO] 找到數據庫文件: {path}")
            return str(path)
    
    raise FileNotFoundError("無法找到fixtures.db文件")

def get_fixtures(days_ahead=7):
    """
    獲取未來指定天數內的賽事數據
    
    Args:
        days_ahead (int): 獲取未來多少天的賽事，默認7天
        
    Returns:
        list: 賽事數據列表，每個元素是一個字典
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使返回行為字典形式
    cursor = conn.cursor()
    
    # 計算日期範圍
    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=days_ahead)
    
    print(f"[INFO] 查詢賽事: {today} 至 {end_date}")
    
    # SQL查詢：獲取未來賽事，聯接聯賽和球隊表
    query = """
    SELECT 
        f.id,
        f.api_id,
        f.league_id,
        f.home_team_id,
        f.away_team_id,
        f.event_date,
        f.event_timestamp,
        f.status_short,
        f.status_long,
        f.goals_home,
        f.goals_away,
        f.venue_name,
        f.venue_city,
        f.referee,
        f.round,
        f.season,
        f.raw_data,
        l.api_id as league_api_id,
        l.name_tc as league_name_tc,
        l.name_en as league_name_en,
        l.country as league_country,
        ht.name_tc as home_team_name_tc,
        ht.name_en as home_team_name_en,
        ht.country as home_team_country,
        at.name_tc as away_team_name_tc,
        at.name_en as away_team_name_en,
        at.country as away_team_country
    FROM fixtures f
    LEFT JOIN leagues l ON f.league_id = l.id
    LEFT JOIN teams ht ON f.home_team_id = ht.id
    LEFT JOIN teams at ON f.away_team_id = at.id
    WHERE f.event_date >= ? 
      AND f.event_date <= ?
      AND f.status_short IN ('NS', '1H', 'HT', '2H', 'ET', 'BT', 'P', 'SUSP', 'INT', 'ABD', 'AWD', 'WO')
    ORDER BY f.event_date, f.event_timestamp
    """
    
    cursor.execute(query, (today.isoformat(), end_date.isoformat()))
    rows = cursor.fetchall()
    
    print(f"[INFO] 查詢到 {len(rows)} 場賽事")
    
    # 轉換為字典列表，並篩選59聯賽
    fixtures = []
    for row in rows:
        fixture = dict(row)
        league_api_id = fixture.get('league_api_id')
        
        # 篩選59聯賽
        if league_api_id and int(league_api_id) in TARGET_LEAGUE_IDS:
            # 確保繁體中文名稱存在，如果沒有則使用英文名稱
            if not fixture.get('league_name_tc'):
                fixture['league_name_tc'] = fixture.get('league_name_en', '未知聯賽')
            
            if not fixture.get('home_team_name_tc'):
                fixture['home_team_name_tc'] = fixture.get('home_team_name_en', '未知主隊')
            
            if not fixture.get('away_team_name_tc'):
                fixture['away_team_name_tc'] = fixture.get('away_team_name_en', '未知客隊')
            
            # 格式化日期時間
            event_date = fixture.get('event_date')
            if event_date:
                try:
                    dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    fixture['event_date_formatted'] = dt.strftime('%Y-%m-%d')
                    fixture['event_time_formatted'] = dt.strftime('%H:%M')
                    fixture['event_datetime_local'] = dt.astimezone().strftime('%Y-%m-%d %H:%M')
                except:
                    fixture['event_date_formatted'] = event_date
                    fixture['event_time_formatted'] = '00:00'
                    fixture['event_datetime_local'] = event_date
            
            fixtures.append(fixture)
    
    print(f"[INFO] 篩選後得到 {len(fixtures)} 場賽事（59聯賽）")
    
    # 按聯賽分組統計
    league_stats = {}
    for fixture in fixtures:
        league_id = fixture.get('league_api_id')
        league_name = fixture.get('league_name_tc', '未知')
        if league_id not in league_stats:
            league_stats[league_id] = {
                'name': league_name,
                'count': 0,
                'fixtures': []
            }
        league_stats[league_id]['count'] += 1
        league_stats[league_id]['fixtures'].append(fixture)
    
    print(f"[INFO] 賽事分佈: {len(league_stats)} 個聯賽")
    for league_id, stats in list(league_stats.items())[:10]:  # 顯示前10個
        print(f"  - {stats['name']}: {stats['count']} 場")
    
    conn.close()
    return fixtures

def get_fixtures_by_league(fixtures=None):
    """
    按聯賽分組賽事
    
    Args:
        fixtures (list): 賽事列表，如果為None則調用get_fixtures()
        
    Returns:
        dict: 按聯賽分組的賽事數據
    """
    if fixtures is None:
        fixtures = get_fixtures()
    
    leagues = {}
    for fixture in fixtures:
        league_id = fixture.get('league_api_id')
        league_name = fixture.get('league_name_tc', '未知聯賽')
        
        if league_id not in leagues:
            leagues[league_id] = {
                'id': league_id,
                'name': league_name,
                'country': fixture.get('league_country', ''),
                'fixtures': []
            }
        
        leagues[league_id]['fixtures'].append(fixture)
    
    # 按聯賽名稱排序
    sorted_leagues = dict(sorted(leagues.items(), key=lambda x: x[1]['name']))
    return sorted_leagues

def get_fixtures_by_date(fixtures=None):
    """
    按日期分組賽事
    
    Args:
        fixtures (list): 賽事列表，如果為None則調用get_fixtures()
        
    Returns:
        dict: 按日期分組的賽事數據
    """
    if fixtures is None:
        fixtures = get_fixtures()
    
    dates = {}
    for fixture in fixtures:
        date_key = fixture.get('event_date_formatted', '未知日期')
        
        if date_key not in dates:
            dates[date_key] = []
        
        dates[date_key].append(fixture)
    
    # 按日期排序
    sorted_dates = dict(sorted(dates.items()))
    return sorted_dates

def save_fixtures_to_json(fixtures, output_path):
    """
    將賽事數據保存為JSON文件
    
    Args:
        fixtures (list): 賽事列表
        output_path (str): 輸出文件路徑
    """
    # 準備可JSON序列化的數據
    serializable_fixtures = []
    for fixture in fixtures:
        # 複製字典，移除不可序列化的對象
        serializable = {}
        for key, value in fixture.items():
            if key == 'raw_data' and value:
                try:
                    serializable[key] = json.loads(value) if isinstance(value, str) else value
                except:
                    serializable[key] = str(value)
            else:
                serializable[key] = value
        serializable_fixtures.append(serializable)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_fixtures, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 賽事數據已保存到: {output_path}")

if __name__ == '__main__':
    # 測試代碼
    try:
        fixtures = get_fixtures(days_ahead=3)
        
        if fixtures:
            print(f"\n[SUCCESS] 成功獲取 {len(fixtures)} 場賽事")
            
            # 保存示例數據
            output_dir = Path(__file__).parent.parent / 'public' / 'api'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            save_fixtures_to_json(fixtures, output_dir / 'fixtures.json')
            
            # 輸出統計信息
            leagues = get_fixtures_by_league(fixtures)
            print(f"\n聯賽分佈 ({len(leagues)} 個聯賽):")
            for league_id, league_data in sorted(leagues.items(), key=lambda x: x[1]['name']):
                print(f"  - {league_data['name']}: {len(league_data['fixtures'])} 場")
                
        else:
            print("[WARN] 未找到賽事數據")
            
    except Exception as e:
        print(f"[ERROR] 讀取數據時出錯: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)