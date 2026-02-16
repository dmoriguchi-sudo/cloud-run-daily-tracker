# 日めくりアイテム管理 - Cloud Run デプロイ手順

## 構成

```
cloud-run-daily-tracker/
├── main.py                  ← FastAPI (API + HTML配信)
├── templates/
│   └── index.html           ← フロントエンド
├── service-account-key.json ← サービスアカウント鍵（内蔵）
├── Dockerfile
├── requirements.txt
└── README.md
```

## 手順1: スプレッドシートを準備

1. Google スプレッドシートを新規作成
2. シート名を **「データ」** に変更
3. 1行目にヘッダー: `日付 | アイテム名 | 入力時刻 | チェック | チェック時刻`
4. **スプレッドシートIDをメモ** （URLの `/d/` と `/edit` の間）
5. **共有設定**: `bigquery@logistics-449115.iam.gserviceaccount.com` に **編集権限** を付与

## 手順2: デプロイ

```bash
cd cloud-run-daily-tracker

# GCPプロジェクト設定
gcloud config set project logistics-449115

# デプロイ（スプレッドシートIDだけ書き換え）
gcloud run deploy daily-tracker \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "SPREADSHEET_ID=ここにスプレッドシートID"
```

これだけ！

## 手順3: 確認

デプロイ後に表示されるURL（`https://daily-tracker-xxxxx-an.a.run.app`）にアクセス。
アプリが表示されれば完了。チームにこのURLを共有するだけ。

## 環境変数

| 変数 | 必須 | デフォルト | 説明 |
|------|------|-----------|------|
| `SPREADSHEET_ID` | ✅ | - | スプレッドシートID |
| `SHEET_NAME` | - | データ | シート名 |
| `CUTOFF_HOUR` | - | 18 | 翌日切り替え時刻 |

## ⚠️ セキュリティ注意

- `service-account-key.json` がコンテナに内蔵されています
- **このイメージを公開リポジトリ（Docker Hub等）にpushしないでください**
- Artifact Registry（GCP内）へのpushは問題ありません
- 将来的にはSecret Managerへの移行を推奨します
# cloud-run-daily-tracker
