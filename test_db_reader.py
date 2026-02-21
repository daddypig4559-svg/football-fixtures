#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據庫讀取器
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processor.db_reader import get_fixtures, get_fixtures_by_league

print("🔍 測試數據庫讀取器...")

try:
    # 測試獲取未來3天的賽事
    print("📊 獲取未來3天賽事...")
    fixtures = get_fixtures(days_ahead=3)
    
    if fixtures:
        print(f"✅ 成功獲取 {len(fixtures)} 場賽事")
        
        # 顯示前5場賽事
        print("\n📋 前5場賽事:")
        for i, f in enumerate(fixtures[:5]):
            home = f.get('home_team_name_tc', f.get('home_team_name_en', '未知'))
            away = f.get('away_team_name_tc', f.get('away_team_name_en', '未知'))
            league = f.get('league_name_tc', f.get('league_name_en', '未知'))
            date = f.get('event_date_formatted', '未知日期')
            time = f.get('event_time_formatted', '未知時間')
            print(f"  {i+1}. {home} vs {away} ({league}) - {date} {time}")
        
        # 測試按聯賽分組
        print("\n🏆 聯賽分組統計:")
        leagues = get_fixtures_by_league(fixtures)
        for league_id, league_data in sorted(leagues.items(), key=lambda x: x[1]['name'])[:10]:
            print(f"  - {league_data['name']}: {len(league_data['fixtures'])} 場")
        
        # 保存測試JSON
        import json
        from pathlib import Path
        
        output_dir = Path(__file__).parent / 'public' / 'api'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_data = {
            'total_fixtures': len(fixtures),
            'leagues_count': len(leagues),
            'fixtures': fixtures[:10]  # 只保存前10場
        }
        
        output_path = output_dir / 'test_fixtures.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 測試數據已保存到: {output_path}")
        
    else:
        print("⚠️ 未找到賽事數據")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()