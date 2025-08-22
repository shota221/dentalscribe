FROM python:3.12

# AWS CLI v2をインストール
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./infra/start_local_server.sh /start_local_server.sh
RUN pip install -U pip --root-user-action=ignore && pip install --no-cache-dir chalice pytest pytest-env --root-user-action=ignore 
ARG APP_NAME
WORKDIR /app/${APP_NAME}
CMD ["/bin/sh", "/start_local_server.sh"]