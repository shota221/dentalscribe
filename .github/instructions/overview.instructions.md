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
複数音声ファイルのTranscribe→SOAP変換ジョブ起動
```json
Request: {
  "upload_ids": [
    "upload-20250815-123456",
    "upload-20250815-123457",
    "upload-20250815-123458"
  ]
}

Response: {
  "job_id": "voice2soap-20250815-123456",
  "status": "QUEUED",
  "service": "voice2soap",
  "message": "Voice to SOAP conversion job started",
  "child_jobs": [
    {
      "job_id": "transcribe-20250815-123456-1",
      "upload_id": "upload-20250815-123456",
      "status": "QUEUED",
      "service": "transcribe"
    },
    {
      "job_id": "transcribe-20250815-123456-2", 
      "upload_id": "upload-20250815-123457",
      "status": "COMPLETED",
      "service": "transcribe"
    },
    {
      "job_id": "transcribe-20250815-123456-3",
      "upload_id": "upload-20250815-123458", 
      "status": "QUEUED",
      "service": "transcribe"
    }
  ]
}
```

**処理フロー**:
1. 各upload_idに対してTranscript生成済みかチェック
2. 未生成の場合はTranscribeジョブを開始
3. 既に生成済みの場合はスキップ
4. 全てのTranscribeジョブ完了後、結果を結合
5. 結合されたテキストをBedrockに送信してSOAP形式に変換

### GET /api/v1/jobs/voice2soap/{job_id}
複数Transcribe結果結合 → Bedrock SOAP変換 → 結果取得
```json
Response: {
  "job_id": "voice2soap-20250815-123456",
  "status": "completed",
  "soap_data": {
    "subjective": "患者の主訴（複数音声ファイルから統合）",
    "objective": "客観的所見（複数音声ファイルから統合）", 
    "assessment": "診断（複数音声ファイルから統合）",
    "plan": "治療計画（複数音声ファイルから統合）"
  },
  "transcription_text": "結合された文字起こし結果",
  "child_jobs": [
    {
      "job_id": "transcribe-20250815-123456-1",
      "upload_id": "upload-20250815-123456",
      "status": "COMPLETED",
      "transcription_text": "1つ目の音声の文字起こし結果"
    },
    {
      "job_id": "transcribe-20250815-123456-2",
      "upload_id": "upload-20250815-123457", 
      "status": "COMPLETED",
      "transcription_text": "2つ目の音声の文字起こし結果"
    },
    {
      "job_id": "transcribe-20250815-123456-3",
      "upload_id": "upload-20250815-123458",
      "status": "COMPLETED", 
      "transcription_text": "3つ目の音声の文字起こし結果"
    }
  ]
}
```

## 🎯 成功基準

- [ ] 複数音声アップロード → 個別Transcribeジョブ起動
- [ ] Transcribe完了状態チェック機能
- [ ] 複数Transcribe結果の結合処理  
- [ ] 結合結果 → Bedrock SOAP変換
- [ ] 歯科特化SOAP形式での統合出力
- [ ] cURL/Postmanでテスト可能

## 🚨 開発ガイドライン

### PoCレベル割り切り
✅ **実装**: 複数音声処理、Transcribe状態管理、結果結合、SOAP変換、エラーハンドリング  
❌ **省略**: 詳細セキュリティ、高度な例外処理、UI、永続化DB

### AWS設定
```bash
AWS_REGION=ap-northeast-1
# 必要権限: transcribe:*, bedrock:InvokeModel, s3:*
```

### 開発フロー
1. 既存のdentalscribeディレクトリ活用
2. Upload API実装（複数ファイル対応）
3. 複数Transcribe管理機能実装
4. Transcribe結果結合機能実装
5. Result API実装（Bedrock連携・統合SOAP生成）
6. 統合テスト