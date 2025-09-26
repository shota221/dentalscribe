以下、`GET /storages/voice-download-url` 外部APIエンドポイント追加の機能要件まとめ。

## 目的
- 既にアップロード済み（`upload_id` 付与済）音声ファイルの一時ダウンロード用 Presigned URL をクライアント（CRM / ブラウザ）へ提供。
- アプリ内再生（<audio>）/ 再解析 / 再ダウンロードを可能にする。

## エンドポイント概要
- Method: GET
- Path: /storages/voice-download-url
- Query Param: `upload_id` (必須, 文字列)
- 認証: API Key (ヘッダ `x-api-key`) + 追加で将来 `Authorization: Bearer` など拡張可能
- Idempotent: 同一 `upload_id` での複数リクエストは毎回新しい（または TTL 内再利用可の）Presigned URL を返す

## リクエスト仕様
```
GET /storages/voice-download-url?upload_id={upload_id}
x-api-key: {key}
```

### バリデーション
1. `upload_id` 存在・非空
2. 形式: 英数/ハイフン/アンダースコアのみ（例: ^[A-Za-z0-9_\-]{8,64}$）
3. DB(またはメタストア)でレコード存在確認
4. 状態チェック: 
   - アップロード完了済 (stored / available 状態)
   - 削除・期限切れ状態ならエラー

## 処理フロー（成功ケース）
1. リクエスト受理 → 入力検証
2. upload_idをもとにS3 バケット/キーを特定
3. S3 (またはオブジェクトストレージ) で GET 用 Presigned URL 生成
   - Expiration: デフォルト 5 分
4. レスポンス JSON 返却

## レスポンス (成功 200)
```
{
  "upload_id": "up_abc123",
  "presigned_url": "https://bucket.s3.amazonaws.com/....&X-Amz-Signature=...",
  "content_type": "audio/webm",
  "size": 1234567,
  "expires_in": 300,
  "created_at": "2025-09-23T07:10:12Z",
}
```
