data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_security_group" "web" {
  name        = "aulas-web-sg"
  description = "HTTP para el dashboard y SSH"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  iam_instance_profile   = "LabInstanceProfile"
  key_name               = "vockey"
  vpc_security_group_ids = [aws_security_group.web.id]

  # Para que los contenedores puedan obtener las credenciales del rol
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  user_data = templatefile("${path.module}/scripts/user_data.sh", {
    version   = terraform_data.push_imagenes.id
    region    = "us-east-1"
    registry  = local.registry
    web_image = "${aws_ecr_repository.web.repository_url}:latest"
    sim_image = "${aws_ecr_repository.simulador.repository_url}:latest"
    tabla     = aws_dynamodb_table.lecturas.name
    sqs_url   = aws_sqs_queue.rechazados.url
    stream    = aws_kinesis_stream.aulas.name
  })
  user_data_replace_on_change = true

  tags = { Name = "aulas-dashboard" }
}
