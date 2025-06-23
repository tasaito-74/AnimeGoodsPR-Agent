#!/usr/bin/env python3
"""
アニメ記事生成支援サービスの起動スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """依存関係のチェック"""
    print("依存関係をチェックしています...")
    
    try:
        import fastapi
        import uvicorn
        import openai
        import google
        import bs4
        import playwright
        print("✓ 必要なパッケージがインストールされています")
        return True
    except ImportError as e:
        print(f"✗ 不足しているパッケージ: {e}")
        return False

def install_dependencies():
    """依存関係のインストール"""
    print("依存関係をインストールしています...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依存関係のインストールが完了しました")
        return True
    except subprocess.CalledProcessError:
        print("✗ 依存関係のインストールに失敗しました")
        return False

def setup_playwright():
    """Playwrightのセットアップ"""
    print("Playwrightをセットアップしています...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✓ Playwrightのセットアップが完了しました")
        return True
    except subprocess.CalledProcessError:
        print("✗ Playwrightのセットアップに失敗しました")
        return False

def check_env_file():
    """環境変数ファイルのチェック"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️ .envファイルが見つかりません")
            print("以下のコマンドで.envファイルを作成してください:")
            print("cp .env.example .env")
            print("その後、.envファイルを編集してAPIキーを設定してください")
            return False
        else:
            print("✗ .env.exampleファイルが見つかりません")
            return False
    
    print("✓ .envファイルが見つかりました")
    return True

def start_server():
    """サーバーの起動"""
    print("サーバーを起動しています...")
    print("ブラウザで http://localhost:8000 にアクセスしてください")
    print("停止するには Ctrl+C を押してください")
    print("-" * 50)
    
    try:
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
    except Exception as e:
        print(f"サーバー起動エラー: {e}")

def main():
    """メイン関数"""
    print("=" * 50)
    print("アニメ記事生成支援サービス")
    print("=" * 50)
    
    # 依存関係のチェック
    if not check_dependencies():
        print("\n依存関係をインストールしますか？ (y/n): ", end="")
        if input().lower() == 'y':
            if not install_dependencies():
                return
            if not setup_playwright():
                return
        else:
            return
    
    # Playwrightのセットアップ
    try:
        import playwright
        setup_playwright()
    except ImportError:
        pass
    
    # 環境変数ファイルのチェック
    if not check_env_file():
        print("\n.envファイルを設定してから再度実行してください")
        return
    
    print("\n" + "=" * 50)
    start_server()

if __name__ == "__main__":
    main() 