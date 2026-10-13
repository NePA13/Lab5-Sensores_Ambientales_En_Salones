data "archive_file" "validador" {
  type        = "zip"
  source_file = "${path.module}/lambda/validador.py"
  output_path = "${path.module}/validador.zip"
}

resource "aws_lambda_function" "validador" {
  function_name    = "validador-aulas"
  role             = data.aws_iam_role.lab_role.arn
  handler          = "validador.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.validador.output_path
  source_code_hash = data.archive_file.validador.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      TABLA   = aws_dynamodb_table.lecturas.name
      SQS_URL = aws_sqs_queue.rechazados.url
    }
  }
}

resource "aws_lambda_event_source_mapping" "kinesis_a_lambda" {
  event_source_arn  = aws_kinesis_stream.aulas.arn
  function_name     = aws_lambda_function.validador.arn
  starting_position = "LATEST"
  batch_size        = 100
}

