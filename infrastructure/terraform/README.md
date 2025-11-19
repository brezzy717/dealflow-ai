# Terraform Stacks

`environments/dev` and `environments/prod` hold environment-specific state files. Root templates define shared infrastructure modules (VPC, Neon/Postgres, Redis, job queues).
