# 音声入力→SOAP変換API 利用手順書

## 🎯 概要

歯科医師の診察記録音声をAmazon TranscribeとBedrock (Claude)を使用して歯科特化SOAP形式に変換するREST APIです。

## 🔧 検証環境

- **ベースURL**: https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/
- **リージョン**: ap-northeast-1
- **認証**: 現在認証なし（検証環境）

## 📋 API仕様

### 1. アップロード用URL取得

音声ファイルをS3にアップロードするためのpresigned URLを取得します。

```http
GET /storages/voice-upload-url?filename=your-audio-file.wav
```

**クエリパラメータ:**
- `filename` (必須): アップロードする音声ファイル名（拡張子を含む）

**対応ファイル形式:**
- `.mp3`, `.mp4`, `.m4a`, `.wav`, `.flac`, `.amr`, `.ogg`, `.webm`

**レスポンス例:**
```json
{
  "upload_id": "upload-20250829-123456",
  "presigned_url": "https://s3.amazonaws.com/bucket/uploads/voice-20250829-123456.wav",
  "expires_in": 3600,
  "s3_key": "transcription/source/upload-20250829-123456.wav",
  "content_type": "audio/wav",
  "original_filename": "your-audio-file.wav"
}
```

### 2. 音声→SOAP変換ジョブ作成

文字起こしとSOAP形式変換のジョブを作成します。

```http
POST /jobs/voice2soap
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "upload_id": "upload-20250829-123456"
}
```

または直接S3キーを指定:
```json
{
  "source_s3_key": "transcription/source/voice-file.wav"
}
```

**レスポンス例:**
```json
{
  "job_id": "voice2soap-20250829-123456"
}
```

### 3. 処理結果取得

音声の文字起こし結果とSOAP形式データを取得します。

```http
GET /jobs/voice2soap/{job_id}
```

**レスポンス例:**
```json
{
  "job_id": "voice2soap-20250829-123456",
  "status": "completed",
  "transcription_text": "患者さんの主訴は右上の奥歯が痛いということでした...",
  "soap_data": {
    "subjective": "患者の主訴：右上奥歯の疼痛、3日前から症状出現",
    "objective": "口腔内所見：右上第一大臼歯に深いう蝕を確認、歯肉の発赤・腫脹あり",
    "assessment": "右上第一大臼歯の急性歯髄炎の疑い",
    "plan": "根管治療の実施、抗生剤と鎮痛剤の処方、1週間後の再診予約"
  }
}
```

**ステータス一覧:**
- `pending`: 処理待機中
- `in_progress`: 処理中
- `completed`: 完了
- `failed`: 失敗

## 🚀 利用手順（ステップバイステップ）

### Step 1: アップロード用URL取得

```bash
curl -X GET "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/storages/voice-upload-url?filename=your-audio-file.wav"
```

### Step 2: 音声ファイルのアップロード

Step 1で取得した`presigned_url`を使用してファイルをアップロード：

```bash
curl -X PUT \
  "取得したpresigned_url" \
  --data-binary @"音声ファイル.wav" \
  -H "Content-Type: audio/wav"
```

### Step 3: SOAP変換ジョブの作成

```bash
curl -X POST \
  "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "Step1で取得したupload_id"
  }'
```

### Step 4: 結果の確認

```bash
curl -X GET \
  "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap/Step3で取得したjob_id"
```

処理中の場合は数分待ってから再度確認してください。

## 📝 cURLを使った完全な実行例

```bash
#!/bin/bash

# Step 1: アップロード用URL取得
echo "Step 1: Getting upload URL..."
UPLOAD_RESPONSE=$(curl -s -X GET "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/storages/voice-upload-url?filename=test.m4a")
echo "Upload response: $UPLOAD_RESPONSE"

# レスポンスからupload_idとpresigned_urlを抽出
UPLOAD_ID=$(echo $UPLOAD_RESPONSE | jq -r '.upload_id')
PRESIGNED_URL=$(echo $UPLOAD_RESPONSE | jq -r '.presigned_url')

echo "Upload ID: $UPLOAD_ID"

# Step 2: ファイルアップロード
echo "Step 2: Uploading file..."
curl -X PUT "$PRESIGNED_URL" \
  --data-binary @"test.m4a" \
  -H "Content-Type: audio/mp4"

# Step 3: ジョブ作成
echo "Step 3: Creating voice2soap job..."
JOB_RESPONSE=$(curl -s -X POST \
  "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap" \
  -H "Content-Type: application/json" \
  -d "{\"upload_id\": \"$UPLOAD_ID\"}")

echo "Job response: $JOB_RESPONSE"

# レスポンスからjob_idを抽出
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Step 4: 結果確認（ポーリング）
echo "Step 4: Checking results..."
while true; do
  RESULT=$(curl -s -X GET \
    "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap/$JOB_ID")
  
  STATUS=$(echo $RESULT | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo "Processing completed!"
    echo "Result: $RESULT"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Processing failed!"
    echo "Result: $RESULT"
    break
  fi
  
  echo "Processing... waiting 10 seconds"
  sleep 10
done
```

## 🎵 対応音声形式

- **対応拡張子**: `.mp3`, `.mp4`, `.m4a`, `.wav`, `.flac`, `.amr`, `.ogg`, `.webm`
- **推奨形式**: WAV（非圧縮）またはM4A（高品質圧縮）
- **サンプリングレート**: 8kHz〜48kHz
- **言語**: 日本語
- **最大ファイルサイズ**: 2GB（Amazon Transcribeの制限）
- **最大処理時間**: 約4時間（Amazon Transcribeの制限）

## ⚠️ 注意事項

1. **処理時間**: 音声の長さによって処理時間が変動します（目安：1分の音声で1〜2分程度）
2. **ステータス確認**: ジョブ作成後は定期的にステータスを確認してください
3. **エラーハンドリング**: ステータスが`failed`の場合、エラー詳細を確認してください
4. **音声品質**: クリアな音声ほど精度が向上します
5. **医療用語**: 歯科医療特化のプロンプトを使用していますが、専門用語の認識精度は音声品質に依存します

## 📊 SOAP形式について

生成されるSOAPデータは以下の4つの要素で構成されます：

- **Subjective（主観的情報）**: 患者の主訴、症状の経過、既往歴など
- **Objective（客観的情報）**: 口腔内所見、検査結果、バイタルサインなど  
- **Assessment（評価）**: 診断、重症度評価、リスク要因など
- **Plan（計画）**: 治療方針、処方、次回予約など

## 🔍 トラブルシューティング

### よくあるエラー

1. **"Job not found"**: 無効なjob_idが指定されています
2. **"No files found"**: upload_idに対応するファイルがS3に存在しません
3. **"Empty transcription text"**: 音声の文字起こしが空です（無音または認識不能）
4. **"Invalid JSON generated"**: Bedrockの応答が不正です

### 対処方法

- 音声ファイルがクリアで聞き取りやすいか確認
- ネットワーク接続を確認
- APIレスポンスのエラーメッセージを確認
- 処理中の場合は時間を置いて再実行

## 📞 サポート

検証環境での問題や質問については、開発チームまでお問い合わせください。
