# DentalScribe CloudWatch Alarms - Terraform

このディレクトリには、DentalScribeアプリケーション用のCloudWatchアラートのTerraform設定が含まれています。

## 📋 概要

試作段階です。

以下のAWSリソースの監視アラートを設定します：

### 監視対象サービス
- **Lambda関数**: エラー、スロットリング、実行時間、並行実行数
- **DynamoDB**: 読み込み・書き込みスロットル
- **SQS**: メッセージ滞留時間、キュー長、Dead Letter Queue
- **API Gateway**: 4XX/5XX エラー、レイテンシ

## 🚀 使用方法

### 1. 初期設定

```bash
cd terraform

# terraform.tfvars ファイルを作成
cp terraform.tfvars.example terraform.tfvars

# 環境に応じて terraform.tfvars を編集
vim terraform.tfvars
```

### 2. 必須変数の設定

`terraform.tfvars` で以下の値を設定してください：

```hcl
environment            = "dev"  # dev, stg, prod
lambda_function_name   = "dentalscribe-dev"
dynamodb_table_name    = "dentalscribe-dev-jobs"
sqs_queue_name         = "dentalscribe-dev-job-queue"
sqs_dlq_name           = "dentalscribe-dev-job-queue-dlq"
s3_bucket_name         = "dentalscribe-dev-storage"
alarm_email            = "your-email@example.com"  # ⚠️ 必ず変更してください
```

### 3. Terraform実行

```bash
# 初期化
terraform init

# プランの確認
terraform plan

# 適用
terraform apply
```

### 4. SNS Email確認

Terraform apply後、指定したメールアドレスに確認メールが届きます。
**必ずメール内のリンクをクリックして購読を確認してください。**

## 📊 設定されるアラート一覧

### Lambda関連
| アラート名 | 説明 | 閾値 |
|-----------|------|------|
| lambda-errors | Lambda実行エラー | 5回/5分 |
| lambda-throttles | Lambda スロットリング | 5回/5分 |
| lambda-duration | Lambda実行時間が長い | 30秒平均 |
| lambda-concurrent-executions | 並行実行数が多い | 100 |

### DynamoDB関連
| アラート名 | 説明 | 閾値 |
|-----------|------|------|
| dynamodb-read-throttles | 読み込みスロットル | 5回/5分 |
| dynamodb-write-throttles | 書き込みスロットル | 5回/5分 |

### SQS関連
| アラート名 | 説明 | 閾値 |
|-----------|------|------|
| sqs-oldest-message-age | メッセージ処理遅延 | 10分 |
| sqs-messages-visible | キュー内メッセージ数 | 100件 |
| dlq-messages | DLQにメッセージあり | 1件以上 |

### API Gateway関連
| アラート名 | 説明 | 閾値 |
|-----------|------|------|
| api-5xx-errors | サーバーエラー | 10回/5分 |
| api-4xx-errors | クライアントエラー | 50回/5分 |
| api-latency | APIレイテンシ | 5秒平均 |

## ⚙️ 閾値のカスタマイズ

`terraform.tfvars` で以下の閾値を調整できます：

```hcl
lambda_error_threshold    = 5      # Lambda エラー閾値
lambda_duration_threshold = 30000  # Lambda 実行時間閾値 (ミリ秒)
sqs_age_threshold         = 600    # SQS メッセージ年齢閾値 (秒)
dlq_message_threshold     = 1      # DLQ メッセージ閾値
```

## 🏗️ 環境別デプロイ

### Dev環境
```bash
terraform workspace new dev
terraform workspace select dev
terraform apply -var-file="terraform.tfvars"
```

### Staging環境
```bash
# stg用の tfvars を作成
cp terraform.tfvars terraform.stg.tfvars
# 編集して stg環境の値に変更
vim terraform.stg.tfvars

terraform workspace new stg
terraform workspace select stg
terraform apply -var-file="terraform.stg.tfvars"
```

### Production環境
```bash
# prod用の tfvars を作成
cp terraform.tfvars terraform.prod.tfvars
# 編集して prod環境の値に変更
vim terraform.prod.tfvars

terraform workspace new prod
terraform workspace select prod
terraform apply -var-file="terraform.prod.tfvars"
```

##  アラート確認

### AWS Console
1. CloudWatch → アラーム で設定されたアラートを確認
2. SNS → トピック で通知先を確認

### AWS CLI
```bash
# アラート一覧
aws cloudwatch describe-alarms --alarm-name-prefix "dentalscribe-dev"

# SNSトピック確認
aws sns list-topics --query "Topics[?contains(TopicArn, 'dentalscribe')]"

# 購読状態確認
aws sns list-subscriptions-by-topic --topic-arn <SNS_TOPIC_ARN>
```

## 🧹 リソース削除

```bash
# 削除前に確認
terraform plan -destroy

# 削除実行
terraform destroy
```

## 📝 注意事項

1. **Email購読の確認**: terraform apply後、必ずメールで購読を確認してください
2. **リソース名**: ChaliceでデプロイされたリソースのARNと名前を正確に指定してください
3. **料金**: CloudWatchアラームは月額$0.10/アラーム、SNSは無料枠あり

## 🆘 トラブルシューティング

### アラートが発火しない
- メトリクス名とディメンションが正しいか確認
- CloudWatch Logs Insightsでメトリクスデータを確認
- `treat_missing_data = "notBreaching"` により、データがない場合はアラートが発火しません

### Email通知が届かない
- SNSトピックの購読が確認済みか確認
- スパムフォルダを確認
- AWS SESの送信制限を確認（Sandbox環境の場合）

## 📚 参考資料

- [AWS CloudWatch Alarms](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/AlarmThatSendsEmail.html)
- [Terraform AWS Provider - CloudWatch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)
- [AWS SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)
