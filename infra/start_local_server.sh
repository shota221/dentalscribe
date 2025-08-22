#!/bin/bash

cd /app

if [ -z "$(ls -A $APP_NAME)" ]; then
  rm -rf $APP_NAME
  chalice new-project $APP_NAME
  mkdir $APP_NAME/tests
  touch $APP_NAME/tests/__init__.py
  chmod -R 777 $APP_NAME
fi

cd $APP_NAME
. ./requirements.txt
pip install --no-cache-dir -r requirements.txt --root-user-action=ignore 

# ローカルサーバーを起動
chalice local --host=0.0.0.0 --port=8000 --stage local
