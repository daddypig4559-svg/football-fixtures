#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試完整靜態生成
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from static_generator.html_builder import HTMLBuilder

print("🚀 測試完整靜態生成...")

try:
    # 創建生成器實例
    print("🔧 初始化HTML生成器...")
    builder = HTMLBuilder(template_dir='templates', output_dir='public')
    
    # 測試生成所有文件
    print("📊 開始生成靜態文件...")
    result = builder.generate_all(days_ahead=2)
    
    print(f"✅ 生成完成!")
    
    # 檢查生成的文件
    public_dir = Path('public')
    if public_dir.exists():
        print(f"\n📁 生成的文件列表:")
        
        # 列出所有文件
        for file_path in sorted(public_dir.rglob('*')):
            if file_path.is_file():
                relative_path = file_path.relative_to(public_dir)
                size = file_path.stat().st_size
                print(f"  - {relative_path} ({size:,} 字節)")
    
    # 檢查首頁
    index_path = public_dir / 'index.html'
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)
            print(f"\n🏠 首頁預覽 (前1000字符):")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
    
    # 檢查JSON API
    api_path = public_dir / 'api' / 'fixtures.json'
    if api_path.exists():
        with open(api_path, 'r', encoding='utf-8') as f:
            import json
            data = json.load(f)
            print(f"\n📡 JSON API統計:")
            print(f"  總賽事數: {data.get('total_fixtures', '未知')}")
            print(f"  聯賽數量: {data.get('total_leagues', '未知')}")
            print(f"  生成時間: {data.get('generated_at', '未知')}")
    
    # 檢查CSS和JS文件
    css_path = public_dir / 'css' / 'style.css'
    js_path = public_dir / 'js' / 'app.js'
    
    if css_path.exists():
        css_size = css_path.stat().st_size
        print(f"\n🎨 CSS文件: {css_path} ({css_size:,} 字節)")
    
    if js_path.exists():
        js_size = js_path.stat().st_size
        print(f"📜 JS文件: {js_path} ({js_size:,} 字節)")
    
    print(f"\n🎯 測試總結:")
    print(f"   輸出目錄: {public_dir.absolute()}")
    total_files = sum(1 for _ in public_dir.rglob('*') if _.is_file())
    print(f"   總文件數: {total_files}")
    
    # 檢查文件大小總和
    total_size = sum(f.stat().st_size for f in public_dir.rglob('*') if f.is_file())
    print(f"   總文件大小: {total_size:,} 字節")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)