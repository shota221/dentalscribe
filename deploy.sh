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

# devまたはstg環境の場合、最新のZIPファイルを削除
if [ "$ENV" == "dev" ] || [ "$ENV" == "stg" ]; then
    echo "Cleaning up deployment artifacts for $ENV environment..."
    
    # 最新のZIPファイルを検索して削除
    LATEST_ZIP=$(docker compose exec app find .chalice/deployments -name "*.zip" -type f -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)
    
    if [ -n "$LATEST_ZIP" ]; then
        echo "Removing latest deployment ZIP: $LATEST_ZIP"
        docker compose exec app rm "$LATEST_ZIP"
        echo "Cleanup completed."
    else
        echo "No deployment ZIP files found."
    fi
else
    echo "Skipping artifact cleanup for $ENV environment."
fi

echo "Deployment process completed successfully."