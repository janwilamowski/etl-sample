# output of lambda arn
output "arn" {
  value = aws_lambda_function.etl_sample.arn
}
