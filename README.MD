# Sample ETL project

This project demonstrates a simple Extract, Transform, Load (ETL) pipeline
using AWS. Inputs are uploaded to an S3 bucket which automatically triggers a
Lambda function that processes the input file and writes the results to
another S3 bucket. Terraform is used to manage the cloud infrastructure. The
data comes from [Kaggle's Spaceship Titanic](https://www.kaggle.com/competitions/spaceship-titanic/)
competition.

## Setup project

1. Install conda
1. Install dependencies: `conda env create -f env.yml`

## Create infrastructure

1. `cd infra`
1. `terraform init` (only required the first time)
1. `terraform apply`
1. Confirm changes by entering "yes"

## Update infrastructure

1. Change local state
	- change function code and/or
	- change variables
1. `terraform -chdir=infra/ apply`
1. Confirm changes by entering "yes"

## Test infrastructure

### If the inputs bucket is new and/or empty

Upload a CSV file:
```
aws s3 cp tests/fixture/test.csv s3://etl-sample-input
```
which will trigger the Lambda processing. After a few moments, you should be able to see the result in the outputs bucket:
```
$ aws s3 ls etl-sample-output
2023-04-25 17:17:11     462360 test.csv
```
Download the file:
```
aws s3 cp s3://etl-sample-output/test.csv result.tsv
```
And compare it with the expected result:
```
diff -q result.tsv tests/fixture/expected.csv
```

### If the file already exists in the inputs bucket

Trigger the function as S3 would do:

1. `FUNCTION_ARN=$(terraform -chdir=infra/ output -raw arn)`
1. `aws lambda invoke --function-name $FUNCTION_ARN --payload file://tests/fixture/s3-put-event.json lambda.out`

You should see a successful status output:
```
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```
as well as the return value "true" inside `lambda.out`.

## Remove all infrastructure

1. `terraform -chdir=infra/ destroy`
1. Confirm changes by entering "yes"

## Run local tests

These do no require a network connection as API calls are mocked out.
```
python -m unittest discover tests/
```
