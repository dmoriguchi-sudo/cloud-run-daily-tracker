# CLAUDE.md - cloud-run-daily-tracker

## プロジェクト概要
Cloud Run上で動作する日次トラッキング処理。
WebアプリとしてFlask/FastAPIベースのUIを持ち、静的ファイルとテンプレートを含む。

## 技術スタック
- Python 3.11
- Docker / Google Cloud Run
- Flask または FastAPI（templatesディレクトリあり）
- Google Cloud BigQuery

## 主要ファイル
| ファイル | 役割 |
|---|---|
| `main.py` | メインアプリ |
| `Dockerfile` | コンテナ定義 |
| `requirements.txt` | 依存ライブラリ |
| `templates/` | HTMLテンプレート |
| `static/` | 静的ファイル（CSS/JS等） |

## デプロイ方法
```bash
gcloud run deploy cloud-run-daily-tracker \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## ローカル実行方法
```bash
pip install -r requirements.txt
python main.py
```

## 注意事項
- README.md と readmi.md（typoあり）の2つが存在する
