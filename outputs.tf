output "stream_name" { value = aws_kinesis_stream.aulas.name }
output "tabla"       { value = aws_dynamodb_table.lecturas.name }
output "sqs_url"     { value = aws_sqs_queue.rechazados.url }
output "lab_role"    { value = data.aws_iam_role.lab_role.arn }
output "dashboard_url" {value = "http://${aws_instance.web.public_ip}"}
