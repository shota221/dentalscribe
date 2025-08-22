# 音声入力→SOAP変換PoC - プロジェクト概要

## 🎯 プロジェクト概要

**目的**: 音声入力→Amazon Transcribe→Bedrock (Claude)→歯科特化SOAP形式変換のPoC  
**期間**: 2025/8/15～8/29（2週間）  
**成果物**: REST API（UI不要）

## 🛠️ 技術スタック

- **Backend**: AWS Lambda + Chalice (Python 3.9+)
- **音声処理**: Amazon Transcribe（日本語）
- **SOAP変換**: Amazon Bedrock (Claude)
- **Storage**: Amazon S3
- **リージョン**: ap-northeast-1（必須）

## 📁 ディレクトリ構成

```
/home/ubuntu/aidd/dentalscribe/
├── .env
├── .github/
│   └── instructions/
├── README.md
├── deploy.sh
├── docker-compose.yaml
├── infra/
│   ├── Dockerfile
│   └── start_local_server.sh
├── src/
│   └── dentalscribe/
│       ├── .chalice/
│       │   └── config.json
│       ├── .gitignore
│       ├── app.py
│       ├── chalicelib/
│       │   ├── clients/
│       │   ├── config/
│       │   ├── enums/
│       │   ├── exceptions/
│       │   ├── models/
│       │   ├── prompts/
│       │   ├── repositories/
│       │   ├── requests/
│       │   ├── responses/
│       │   ├── services/
│       │   └── utils/
│       ├── requirements.txt
│       └── tests/
│           └── __init__.py
└── templates/
    ├── .env.template
    └── config.json.template
```

## 🔌 API設計

### GET /api/v1/storages/voice-upload-url
アップロード用presigned URL取得
```json
Response: {
  "upload_id": "upload-20250815-123456",
  "presigned_url": "https://s3.amazonaws.com/...",
  "expires_in": 3600,
  "s3_key": "uploads/voice-20250815-123456.wav",
  "content_type": "audio/wav",
  "original_filename": "voice-20250815-123456.wav"
}
```

### POST /api/v1/jobs/voice2soap
Transcribe job起動
```json
Request: {
  "upload_id": "upload-20250815-123456"
}

Response: {
  "job_id": "transcribe-20250815-123456",
  "status": "QUEUED",
  "service": "transcribe",
  "message": "Transcription job started"
}
```

### GET /api/v1/jobs/voice2soap/{job_id}
Transcribe結果 → Bedrock SOAP変換 → 結果取得
```json
Response: {
  "job_id": "transcribe-20250815-123456",
  "status": "completed",
  "soap_data": {
    "subjective": "患者の主訴",
    "objective": "客観的所見", 
    "assessment": "診断",
    "plan": "治療計画"
  },
  "transcription_text": "文字起こし結果"
}
```

## 🎯 成功基準

- [ ] 音声アップロード → Transcribe job起動
- [ ] Transcribe結果 → Bedrock SOAP変換
- [ ] 歯科特化SOAP形式での出力
- [ ] cURL/Postmanでテスト可能

## 🚨 開発ガイドライン

### PoCレベル割り切り
✅ **実装**: 基本的な音声処理、SOAP変換、エラーハンドリング  
❌ **省略**: 詳細セキュリティ、高度な例外処理、UI、永続化DB

### AWS設定
```bash
AWS_REGION=ap-northeast-1
# 必要権限: transcribe:*, bedrock:InvokeModel, s3:*
```

### 開発フロー
1. 既存のdentalscribeディレクトリ活用
2. Upload API実装（Transcribe連携）
3. Result API実装（Bedrock連携）
4. 統合テスト