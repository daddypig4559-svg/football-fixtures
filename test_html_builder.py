#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試HTML生成器
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from static_generator.html_builder import HTMLBuilder
from data_processor.db_reader import get_fixtures, get_fixtures_by_league

print("🔧 測試HTML生成器...")

try:
    # 創建生成器實例
    builder = HTMLBuilder(template_dir='templates', output_dir='public/test')
    
    # 獲取賽事數據
    print("📊 獲取賽事數據...")
    fixtures = get_fixtures(days_ahead=2)  # 只獲取未來2天，減少數據量
    
    if not fixtures:
        print("⚠️ 未找到賽事數據")
        sys.exit(1)
    
    print(f"✅ 獲取到 {len(fixtures)} 場賽事")
    
    # 測試生成首頁
    print("\n🏠 測試生成首頁...")
    leagues = get_fixtures_by_league(fixtures)
    
    # 準備模板數據
    template_data = {
        'title': '足球賽事中心 - 測試版',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_fixtures': len(fixtures),
        'leagues_count': len(leagues),
        'leagues': leagues,
        'fixtures': fixtures,
        'has_fixtures': len(fixtures) > 0
    }
    
    # 渲染首頁
    try:
        index_html = builder.render_template('index.html.j2', template_data)
        
        # 保存文件
        output_path = Path('public/test') / 'index.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"✅ 首頁生成成功: {output_path}")
        print(f"   文件大小: {len(index_html)} 字節")
        
        # 檢查生成的文件
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 讀取前500字符
                print(f"\n📄 文件預覽 (前500字符):")
                print("-" * 50)
                print(content[:500])
                print("-" * 50)
        else:
            print("❌ 文件未生成")
            
    except Exception as e:
        print(f"❌ 首頁生成失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 測試生成JSON API
    print("\n📡 測試生成JSON API...")
    try:
        api_data = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'total_fixtures': len(fixtures),
                'leagues_count': len(leagues),
                'days_ahead': 2
            },
            'fixtures': fixtures[:50]  # 限制數量
        }
        
        api_dir = Path('public/test') / 'api'
        api_dir.mkdir(parents=True, exist_ok=True)
        
        api_path = api_dir / 'fixtures.json'
        with open(api_path, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON API生成成功: {api_path}")
        print(f"   包含 {len(api_data['fixtures'])} 場賽事")
        
    except Exception as e:
        print(f"❌ JSON API生成失敗: {e}")
    
    # 測試生成聯賽頁面
    print("\n🏆 測試生成聯賽頁面...")
    try:
        # 選擇前3個聯賽進行測試
        test_leagues = list(leagues.items())[:3]
        
        for league_id, league_data in test_leagues:
            league_name = league_data['name']
            league_fixtures = league_data['fixtures']
            
            league_data = {
                'title': f'{league_name} - 賽事日程',
                'league_name': league_name,
                'league_id': league_id,
                'fixtures': league_fixtures,
                'total_fixtures': len(league_fixtures),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染聯賽頁面
            league_html = builder.render_template('league.html.j2', league_data)
            
            # 保存文件
            league_dir = Path('public/test') / 'leagues'
            league_dir.mkdir(parents=True, exist_ok=True)
            
            # 創建安全的文件名
            safe_name = ''.join(c for c in league_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '-').lower()
            
            league_path = league_dir / f'{safe_name}.html'
            
            with open(league_path, 'w', encoding='utf-8') as f:
                f.write(league_html)
            
            print(f"  ✅ {league_name}: {league_path} ({len(league_fixtures)} 場)")
            
    except Exception as e:
        print(f"❌ 聯賽頁面生成失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 測試完成!")
    print(f"   生成目錄: {Path('public/test').absolute()}")
    print(f"   總賽事數: {len(fixtures)}")
    print(f"   聯賽數量: {len(leagues)}")
    
except Exception as e:
    print(f"❌ HTML生成器測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 需要導入的模塊
from datetime import datetime
import json