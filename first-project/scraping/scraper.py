from bs4 import BeautifulSoup
import requests
from typing import Dict, List
import os
from urllib.parse import urljoin, urlparse
import hashlib
from pathlib import Path
import re

def is_relevant_image(img_tag) -> bool:
    """画像が記事本文に関連するものかどうかを判定"""
    # 関連記事や広告などの画像を除外
    excluded_classes = [
        'related', 'recommend', 'advertisement', 'banner',
        'sidebar', 'footer', 'header', 'nav', 'menu',
        'thumbnail', 'icon', 'logo', 'social'
    ]
    
    # 除外すべきクラス名やIDを含む画像をスキップ
    if img_tag.get('class'):
        for cls in img_tag['class']:
            if any(excluded in cls.lower() for excluded in excluded_classes):
                return False
    
    if img_tag.get('id'):
        if any(excluded in img_tag['id'].lower() for excluded in excluded_classes):
            return False
    
    # 画像サイズが小さすぎるもの（アイコンなど）を除外
    if img_tag.get('width') and int(img_tag['width']) < 200:
        return False
    if img_tag.get('height') and int(img_tag['height']) < 200:
        return False
    
    # alt属性が空または一般的すぎるものを除外
    alt_text = img_tag.get('alt', '').lower()
    if not alt_text or any(generic in alt_text for generic in ['icon', 'logo', 'banner', 'ad']):
        return False
    
    return True

def get_highest_quality_image_url(url: str) -> str:
    """可能な限り高品質な画像URLを取得"""
    # 一般的な画像サイズパラメータを削除
    url = re.sub(r'[?&](?:w|width|h|height|size|quality|q)=\d+', '', url)
    
    # 画像URLのパターンに基づいて高品質版のURLを生成
    if 'wp-content/uploads' in url:
        # WordPressの場合、サイズ指定を削除
        url = re.sub(r'-\d+x\d+\.', '.', url)
    elif 'pixiv' in url:
        # Pixivの場合、master版を取得
        url = url.replace('_master1200', '_master')
    elif 'twitter' in url:
        # Twitterの場合、オリジナルサイズを取得
        url = url.replace('&name=small', '&name=large')
        url = url.replace('&name=medium', '&name=large')
    
    return url

def download_image(url: str, save_dir: str = "static/images") -> str:
    """画像をダウンロードして保存し、保存先のパスを返す"""
    try:
        # 保存先ディレクトリの作成
        os.makedirs(save_dir, exist_ok=True)
        
        # 高品質な画像URLを取得
        url = get_highest_quality_image_url(url)
        
        # URLからファイル名を生成
        parsed_url = urlparse(url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        if not file_extension:
            file_extension = '.jpg'
        
        # URLのハッシュをファイル名として使用
        file_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{file_hash}{file_extension}"
        save_path = os.path.join(save_dir, filename)
        
        # 画像が既に存在する場合はスキップ
        if os.path.exists(save_path):
            return f"/static/images/{filename}"
        
        # 画像をダウンロード
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        # 画像を保存
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return f"/static/images/{filename}"
    except Exception as e:
        print(f"画像のダウンロードに失敗しました: {url} - {str(e)}")
        return url

def get_absolute_url(base_url: str, relative_url: str) -> str:
    """相対URLを絶対URLに変換"""
    return urljoin(base_url, relative_url)

def scrape_content(url: str) -> Dict[str, str]:
    """BeautifulSoupを使用してURLからコンテンツをスクレイピング"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # メインコンテンツを特定
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I))
        
        if main_content:
            # メインコンテンツ内のテキストを取得
            text = ' '.join(main_content.stripped_strings)
            
            # メインコンテンツ内の画像のみを収集
            images = []
            for img in main_content.find_all('img'):
                if img.get('src') and is_relevant_image(img):
                    absolute_url = get_absolute_url(url, img['src'])
                    saved_path = download_image(absolute_url)
                    images.append(saved_path)
        else:
            # メインコンテンツが見つからない場合は全体から取得
            text = ' '.join(soup.stripped_strings)
            images = []
            for img in soup.find_all('img'):
                if img.get('src') and is_relevant_image(img):
                    absolute_url = get_absolute_url(url, img['src'])
                    saved_path = download_image(absolute_url)
                    images.append(saved_path)
        
        return {
            'text': text,
            'images': images
        }
    except Exception as e:
        raise Exception(f"スクレイピングに失敗しました: {str(e)}")
