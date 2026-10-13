resource "aws_ecr_repository" "web" {
  name         = "aulas-web"
  force_delete = true
}

resource "aws_ecr_repository" "simulador" {
  name         = "aulas-simulador"
  force_delete = true
}

locals {
  registry = split("/", aws_ecr_repository.web.repository_url)[0]

  # Si cambia cualquier archivo de web/ o producer/, se vuelven a subir las imágenes
  hash_web = sha1(join("", [for f in fileset("${path.module}/web", "**") : filesha1("${path.module}/web/${f}")]))
  hash_sim = sha1(join("", [for f in fileset("${path.module}/producer", "**") : filesha1("${path.module}/producer/${f}")]))
}

resource "terraform_data" "push_imagenes" {
  triggers_replace = [local.hash_web, local.hash_sim]

  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/push_imagenes.sh"
    environment = {
      AWS_PROFILE = "academy"
      REGISTRY    = local.registry
    }
  }

  depends_on = [aws_ecr_repository.web, aws_ecr_repository.simulador]
}
