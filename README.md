## プロジェクト作成

```
cp ./templates/env.template .env
```
.env をすべて埋める。
このとき AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY は IAM ロール編集権限のあるAWSユーザーのものにすること。

必要があれば、Lambdaを実行するpythonのランタイムに合わせて infra/Dockerfile の FROM 句を変更する。
以下コマンドの初回実行で src 下に .envファイルに記述した APP_NAME のプロジェクトが作成される。

```
docker compose up -d --build
```

## 開発

### 参照

* https://aws.amazon.com/jp/builders-flash/202003/chalice-api/
* https://aws.github.io/chalice/quickstart.html

### 外部ライブラリのインポート

外部ライブラリを import する場合は {APP_NAME} 配下のrequirements.txt にライブラリ名を記載し、以下を実行

```
docker compose up -d --force-recreate
```


## ローカル環境での動作確認/テスト

### API 動作確認

```
docker compose up -d --force-recreate
curl localhost:{.envで設定したポート}
```

### テスト

{APP_NAME}/tests に テストファイルを作成 [[参考](https://aws.github.io/chalice/topics/testing.html)] し、以下を実行。

```
docker compose exec app pytest -s tests
```

## デプロイ

**デプロイ前に、/src/dentalscribe/.chalice/config.json記載の環境変数をステージ環境に合わせること**

```
docker compose up -d --force-recreate
./deploy.sh {dev|stg|prod}
```

