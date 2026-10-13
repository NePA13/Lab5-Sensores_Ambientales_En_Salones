#!/bin/bash
# version imagenes: ${version}
dnf install -y docker
systemctl enable --now docker

aws ecr get-login-password --region ${region} \
  | docker login --username AWS --password-stdin ${registry}

docker run -d --name web --restart always -p 80:8080 \
  -e AWS_REGION=${region} \
  -e TABLA=${tabla} \
  -e SQS_URL=${sqs_url} \
  ${web_image}

docker run -d --name simulador --restart always \
  -e AWS_REGION=${region} \
  -e STREAM_NAME=${stream} \
  ${sim_image}
