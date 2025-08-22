#!/bin/bash

# 環境変数の取得
ENV=$1

# 引数チェック
if [ -z "$ENV" ]; then
    echo "Error: Environment parameter is required."
    echo "Usage: $0 <environment>"
    exit 1
fi

# Chaliceをデプロイ
echo "Deploying to $ENV environment..."
docker compose exec app chalice deploy --stage=$ENV

# デプロイ結果のチェック
DEPLOY_STATUS=$?
if [ $DEPLOY_STATUS -ne 0 ]; then
    echo "Deployment failed with status: $DEPLOY_STATUS"
    exit $DEPLOY_STATUS
fi

echo "Deployment process completed successfully."
