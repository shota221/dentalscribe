# 音声入力→SOAP変換API 利用手順書

## 🎯 概要

歯科医師の診察記録音声をAmazon TranscribeとBedrock (Claude)を使用して歯科特化SOAP形式に変換するREST APIです。**複数の音声ファイルを統合してSOAP記録を生成**することができます。

## 🔧 検証環境

- **ベースURL**: 
 【dev】https://3pq5yf6sz7.execute-api.ap-northeast-1.amazonaws.com/dev/
 【stg】https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/
- **リージョン**: ap-northeast-1
- **認証**: 【stgのみ】ヘッダーに "x-api-key":"O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1" 

## 📋 API仕様

### 1. アップロード用URL取得

音声ファイルをS3にアップロードするためのpresigned URLを取得します。**複数ファイルの場合は、ファイル数分実行してください。**

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

**複数の音声ファイル**の文字起こしとSOAP形式変換のジョブを作成します。

```http
POST /jobs/voice2soap
Content-Type: application/json
```

**リクエストボディ（複数upload_id）:**

```json
{
  "upload_ids": [
    "upload-20250829-123456",
    "upload-20250829-123457",
    "upload-20250829-123458"
  ]
}
```

**レスポンス例:**

```json
{
  "job_id": "voice2soap-20250829-123456",
  "status": "QUEUED",
  "service": "voice2soap",
  "message": "Voice to SOAP conversion job started",
  "child_jobs": [
    {
      "job_id": "transcribe-20250829-123456-1",
      "upload_id": "upload-20250829-123456",
      "status": "QUEUED",
      "service": "transcribe"
    },
    {
      "job_id": "transcribe-20250829-123456-2",
      "upload_id": "upload-20250829-123457",
      "status": "COMPLETED",
      "service": "transcribe"
    },
    {
      "job_id": "transcribe-20250829-123456-3",
      "upload_id": "upload-20250829-123458",
      "status": "QUEUED",
      "service": "transcribe"
    }
  ]
}
```

**処理フロー:**
1. 各upload_idに対してTranscribe完了状態をチェック
2. **未完了**のもののみTranscribeジョブを作成・開始
3. **既に完了済み**のものはスキップ（効率化）
4. 全てのTranscribeジョブが完了（成功・失敗問わず）したら次の段階へ
5. **成功したTranscribeジョブが1つ以上**あれば結果を結合
6. 結合されたテキストをBedrockに送信してSOAP形式に変換

### 3. 処理結果取得

**複数の音声ファイルを統合した**文字起こし結果とSOAP形式データを取得します。

```http
GET /jobs/voice2soap/{job_id}
```

**レスポンス例（進行中）:**

```json
{
  "job_id": "voice2soap-20250829-123456",
  "status": "in_progress",
  "transcription_text": "",
  "soap_data": null,
  "child_jobs": [
    {
      "job_id": "transcribe-20250829-123456-1",
      "upload_id": "upload-20250829-123456",
      "status": "COMPLETED",
      "transcription_text": "患者は右上の奥歯に痛みを訴えています..."
    },
    {
      "job_id": "transcribe-20250829-123456-2",
      "upload_id": "upload-20250829-123457",
      "status": "COMPLETED",
      "transcription_text": "口腔内検査では歯肉の腫脹が確認されました..."
    },
    {
      "job_id": "transcribe-20250829-123456-3",
      "upload_id": "upload-20250829-123458",
      "status": "IN_PROGRESS",
      "transcription_text": ""
    }
  ]
}
```

**レスポンス例（完了時）:**

```json
{
  "job_id": "voice2soap-20250829-123456",
  "status": "completed",
  "transcription_text": "患者は右上の奥歯に痛みを訴えています...\n\n口腔内検査では歯肉の腫脹が確認されました...\n\n治療計画として抗生剤の投与を検討します...",
  "soap_data": {
    "subjective": "患者の主訴：右上奥歯の疼痛、3日前から症状出現（複数音声ファイルから統合）",
    "objective": "口腔内所見：右上第一大臼歯に深いう蝕を確認、歯肉の発赤・腫脹あり（複数音声ファイルから統合）",
    "assessment": "右上第一大臼歯の急性歯髄炎の疑い（複数音声ファイルから統合）",
    "plan": "根管治療の実施、抗生剤と鎮痛剤の処方、1週間後の再診予約（複数音声ファイルから統合）"
  },
  "child_jobs": [
    {
      "job_id": "transcribe-20250829-123456-1",
      "upload_id": "upload-20250829-123456",
      "status": "COMPLETED",
      "transcription_text": "1つ目の音声の文字起こし結果"
    },
    {
      "job_id": "transcribe-20250829-123456-2",
      "upload_id": "upload-20250829-123457",
      "status": "COMPLETED",
      "transcription_text": "2つ目の音声の文字起こし結果"
    },
    {
      "job_id": "transcribe-20250829-123456-3",
      "upload_id": "upload-20250829-123458",
      "status": "FAILED",
      "transcription_text": ""
    }
  ]
}
```

**ステータス一覧:**
- `queued`: 処理待機中
- `in_progress`: 処理中
- `completed`: 完了
- `failed`: 失敗

## 🚀 利用手順（複数ファイル対応）

### Step 1: 複数ファイルのアップロード用URL取得

**ファイル1**
```bash
curl -X GET "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/storages/voice-upload-url?filename=file1.wav" \
  -H "x-api-key: O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1"
```

**ファイル2**
```bash
curl -X GET "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/storages/voice-upload-url?filename=file2.wav" \
  -H "x-api-key: O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1"
```

**ファイル3**
```bash
curl -X GET "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/storages/voice-upload-url?filename=file3.wav" \
  -H "x-api-key: O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1"
```

### Step 2: 各音声ファイルのアップロード

各ファイルを対応するpresigned_urlでアップロード：

```bash
# ファイル1
curl -X PUT "Step1で取得したpresigned_url_1" \
  --data-binary @"file1.wav" \
  -H "Content-Type: audio/wav"

# ファイル2  
curl -X PUT "Step1で取得したpresigned_url_2" \
  --data-binary @"file2.wav" \
  -H "Content-Type: audio/wav"

# ファイル3
curl -X PUT "Step1で取得したpresigned_url_3" \
  --data-binary @"file3.wav" \
  -H "Content-Type: audio/wav"
```

### Step 3: 複数ファイル統合SOAP変換ジョブの作成

```bash
curl -X POST \
  "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap" \
  -H "Content-Type: application/json" \
  -H "x-api-key: O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1" \
  -d '{
    "upload_ids": [
      "Step1で取得したupload_id_1",
      "Step1で取得したupload_id_2", 
      "Step1で取得したupload_id_3"
    ]
  }'
```

### Step 4: 統合結果の確認

```bash
curl -X GET \
  "https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg/jobs/voice2soap/Step3で取得したjob_id" \
  -H "x-api-key: O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1"
```

処理中の場合は数分待ってから再度確認してください。**複数ファイルの場合、処理時間が長くなる可能性があります。**

## 📝 cURLを使った完全な実行例（複数ファイル）

```bash
#!/bin/bash

API_KEY="O1Lc7G72jE1X3fUcaFPgA8lbPR3X6wF7aOUbAkq1"
BASE_URL="https://uopem2ywhe.execute-api.ap-northeast-1.amazonaws.com/stg"

# 音声ファイル配列
FILES=("file1.m4a" "file2.m4a" "file3.m4a")
UPLOAD_IDS=()

# Step 1 & 2: 各ファイルのアップロード
for FILE in "${FILES[@]}"; do
  echo "Processing $FILE..."
  
  # アップロード用URL取得
  UPLOAD_RESPONSE=$(curl -s -X GET "$BASE_URL/storages/voice-upload-url?filename=$FILE" \
    -H "x-api-key: $API_KEY")
  
  UPLOAD_ID=$(echo $UPLOAD_RESPONSE | jq -r '.upload_id')
  PRESIGNED_URL=$(echo $UPLOAD_RESPONSE | jq -r '.presigned_url')
  
  echo "Upload ID for $FILE: $UPLOAD_ID"
  UPLOAD_IDS+=("$UPLOAD_ID")
  
  # ファイルアップロード
  curl -X PUT "$PRESIGNED_URL" \
    --data-binary @"$FILE" \
    -H "Content-Type: audio/mp4"
  
  echo "Uploaded: $FILE"
done

# Step 3: 複数ファイル統合ジョブ作成
echo "Creating voice2soap job for multiple files..."

# upload_idsを配列からJSON形式に変換
UPLOAD_IDS_JSON=$(printf '%s\n' "${UPLOAD_IDS[@]}" | jq -R . | jq -s .)

JOB_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs/voice2soap" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d "{\"upload_ids\": $UPLOAD_IDS_JSON}")

echo "Job response: $JOB_RESPONSE"

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Step 4: 結果確認（ポーリング）
echo "Checking results..."
while true; do
  RESULT=$(curl -s -X GET "$BASE_URL/jobs/voice2soap/$JOB_ID" \
    -H "x-api-key: $API_KEY")
  
  STATUS=$(echo $RESULT | jq -r '.status')
  echo "Status: $STATUS"
  
  # 子ジョブの進行状況も表示
  echo "Child jobs status:"
  echo $RESULT | jq '.child_jobs[] | {upload_id: .upload_id, status: .status}'
  
  if [ "$STATUS" = "completed" ]; then
    echo "Processing completed!"
    echo "Integrated transcription result:"
    echo $RESULT | jq '.transcription_text'
    echo "Integrated SOAP data:"
    echo $RESULT | jq '.soap_data'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Processing failed!"
    echo "Result: $RESULT"
    break
  fi
  
  echo "Processing... waiting 15 seconds"
  sleep 15
done
```

## 🎵 対応音声形式

- **対応拡張子**: `.mp3`, `.mp4`, `.m4a`, `.wav`, `.flac`, `.amr`, `.ogg`, `.webm`
- **推奨形式**: WAV（非圧縮）またはM4A（高品質圧縮）
- **サンプリングレート**: 8kHz〜48kHz
- **言語**: 日本語
- **最大ファイルサイズ**: 2GB（Amazon Transcribeの制限）
- **最大処理時間**: 約4時間（Amazon Transcribeの制限）
- **複数ファイル**: 制限なし（ただし、ファイル数が多いほど処理時間が長くなります）

## ⚠️ 注意事項

1. **処理時間**: 複数音声ファイルの場合、処理時間が大幅に増加します（目安：3ファイル×1分の音声で5〜10分程度）
2. **ステータス確認**: 複数ファイル処理中はchild_jobs配列で個別進行状況を確認できます
3. **部分失敗**: 一部のファイルの文字起こしが失敗しても、成功したファイルでSOAP記録を生成します
4. **全失敗**: 全てのファイルが失敗した場合のみ、ジョブ全体が失敗となります
5. **既存ファイル**: 同じupload_idで既にTranscribe済みの場合は、再処理せずに既存結果を使用します（効率化）
6. **音声品質**: 複数ファイルの音声品質にばらつきがある場合、全体の精度に影響する可能性があります

## 📊 SOAP形式について（複数ファイル統合）

複数の音声ファイルから生成されるSOAPデータは、全ての音声内容を統合して以下の4つの要素で構成されます：

- **Subjective（主観的情報）**: 複数音声から抽出された患者の主訴、症状の経過、既往歴など
- **Objective（客観的情報）**: 複数音声から抽出された口腔内所見、検査結果、バイタルサインなど  
- **Assessment（評価）**: 複数音声から総合的に導出された診断、重症度評価、リスク要因など
- **Plan（計画）**: 複数音声から統合された治療方針、処方、次回予約など

**統合処理**: 複数の文字起こし結果を時系列に結合し、Bedrockが全体を理解してSOAP形式に構造化します。

## 🔍 トラブルシューティング

### よくあるエラー

1. **"Job not found"**: 無効なjob_idが指定されています
2. **"upload_ids cannot be empty"**: 空の配列が指定されています
3. **"No files found with upload_id prefix"**: upload_idに対応するファイルがS3に存在しません
4. **"All transcribe jobs failed"**: 全てのTranscribeジョブが失敗しました

### 対処方法

- 各音声ファイルがクリアで聞き取りやすいか確認
- 複数ファイルの音声品質を統一
- 子ジョブのステータスを個別に確認
- 一部失敗の場合は成功したファイルの内容を確認
- ネットワーク接続を確認
- APIレスポンスのエラーメッセージを確認

## 📞 サポート

検証環境での問題や質問については、開発チームまでお問い合わせください。

**新機能**: 複数音声ファイルの統合処理により、診察の異なる場面（問診、検査、治療計画など）を分けて録音し、統合されたSOAP記録を生成できます。