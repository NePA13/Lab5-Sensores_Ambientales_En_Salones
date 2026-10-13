terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  profile = "academy"
}

# En Learner Lab no se pueden crear roles, se usa el que ya existe
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

resource "aws_kinesis_stream" "aulas" {
  name             = "aulas-sensores-stream"
  shard_count      = 1

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

resource "aws_dynamodb_table" "lecturas" {
  name         = "lecturas-aulas"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "aula"
  range_key    = "timestamp"

  attribute {
    name = "aula"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }
}

resource "aws_sqs_queue" "rechazados" {
  name                      = "lecturas-rechazadas"
  message_retention_seconds = 86400
}
