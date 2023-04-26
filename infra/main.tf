# Create source archive
data "archive_file" "lambda_zip" {
  type             = "zip"
  source_file      = "${path.module}/../src/lambda_function.py"
  output_file_mode = "0666"
  output_path      = "${path.module}/../src.zip"
}

# Creating Lambda IAM resource
resource "aws_iam_role" "lambda_role" {
  name = var.lambda_role_name

  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "loggroup" {
  name = "/aws/lambda/${aws_lambda_function.etl_sample.function_name}"
  retention_in_days = 14
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role = aws_iam_role.lambda_role.id
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment2" {
  role = aws_iam_role.lambda_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Creating Lambda resource
resource "aws_lambda_function" "etl_sample" {
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "${var.handler_name}.lambda_handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory
  filename         = "../src.zip"
  source_code_hash = filebase64sha256("../src.zip")
  layers           = ["arn:aws:lambda:ap-southeast-2:336392948345:layer:AWSSDKPandas-Python39:5"]
  environment {
    variables = {
      env            = var.environment
      DESTINATION_BUCKET   = var.outputs_bucket_name
    }
  }
}

# Creating s3 resources for invoking to lambda function
resource "aws_s3_bucket" "inputs_bucket" {
  bucket = var.inputs_bucket_name
  # acl    = "private"
  force_destroy = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "outputs_bucket" {
  bucket = var.outputs_bucket_name
  # acl    = "private"
  force_destroy = true

  tags = {
    Environment = var.environment
  }
}

# Adding S3 bucket as trigger to my lambda and giving the permissions
resource "aws_s3_bucket_notification" "aws-lambda-trigger" {
  bucket = aws_s3_bucket.inputs_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.etl_sample.arn
    events              = ["s3:ObjectCreated:*"]

  }
}

resource "aws_lambda_permission" "lambda_invoke_permission" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.etl_sample.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${aws_s3_bucket.inputs_bucket.id}"
}
