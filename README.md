# cloud-run-daily-tracker

日次アイテム管理アプリ。Google Sheetsと連携してチームで共有できる。

**本番URL**: https://daily-tracker-959189601741.asia-northeast1.run.app

---

## 構成

```
cloud-run-daily-tracker/
├── main.py           # FastAPI (API + HTML配信)
├── templates/
│   └── index.html    # フロントエンド
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## セットアップ

### 1. スプレッドシートを準備

1. Google スプレッドシートを新規作成
2. シート名を **「データ」** に変更
3. 1行目にヘッダー: `日付 | アイテム名 | 入力時刻 | チェック | チェック時刻`
4. スプレッドシートIDをメモ（URLの `/d/` と `/edit` の間）
5. `bigquery@logistics-449115.iam.gserviceaccount.com` に編集権限を付与

### 2. デプロイ

```bash
gcloud config set project logistics-449115

gcloud run deploy daily-tracker \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "SPREADSHEET_ID=ここにスプレッドシートID"
```

---

## 環境変数

| 変数 | 必須 | デフォルト | 説明 |
|------|------|-----------|------|
| `SPREADSHEET_ID` | ✅ | - | スプレッドシートID |
| `SHEET_NAME` | - | データ | シート名 |
| `CUTOFF_HOUR` | - | 18 | 翌日切り替え時刻 |

---

## 設計思想

Cloud Run上の中継エンジンとして機能。
フロントエンドはHTMLを配信するが、データ層はすべてGoogle Sheetsに委譲。
URLを共有するだけでチーム全員が同じデータにアクセスできる。

---

## 注意

- サービスアカウントキーがコンテナに内蔵されている
- 公開リポジトリ（Docker Hub等）へのpushは不可
- Artifact Registry（GCP内）へのpushは問題なし
- 将来的にはSecret Managerへの移行を推奨
