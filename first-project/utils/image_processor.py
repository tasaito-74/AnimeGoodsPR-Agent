from PIL import Image
import os
from io import BytesIO
import requests

def resize_image(image_path: str, max_size_kb: int = 400) -> str:
    """
    画像を指定サイズ以下にリサイズする
    """
    try:
        # 画像を開く
        if image_path.startswith('http'):
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(image_path)

        # 元の画像サイズを取得
        original_size = os.path.getsize(image_path) if not image_path.startswith('http') else len(response.content)
        
        # 既に指定サイズ以下の場合はそのまま返す
        if original_size <= max_size_kb * 1024:
            return image_path

        # リサイズ比率を計算
        ratio = (max_size_kb * 1024) / original_size
        new_width = int(img.width * ratio ** 0.5)
        new_height = int(img.height * ratio ** 0.5)

        # 画像をリサイズ
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 保存先のパスを生成
        save_dir = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        save_path = os.path.join(save_dir, f"resized_{filename}")

        # 画像を保存
        img.save(save_path, quality=85, optimize=True)

        return save_path
    except Exception as e:
        print(f"画像のリサイズに失敗しました: {str(e)}")
        return image_path 