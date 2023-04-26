#Create Variables
variable "function_name" {
  default = ""
}
variable "handler_name" {
  default = ""
}
variable "runtime" {
  default = ""
}
variable "timeout" {
  default = ""
}
variable "memory" {
  default = ""
}

variable "lambda_role_name" {
  default = ""
}

variable "lambda_iam_policy_name" {
  default = ""
}

variable "inputs_bucket_name" {
  default = ""
}

variable "outputs_bucket_name" {
  default = ""
}

variable "environment" {
  default = "dev"
}