import json
import unittest
from unittest.mock import call, MagicMock, patch

import pandas as pd

from src.lambda_function import lambda_handler, load_s3, transform


# We want to ensure that S3 calls are being made without relying too much on
# the implementation details, i.e. whether resources or clients are used in
# boto3. For that reason, we expect the Bucket resource being used but
# abstract away the remaining calls by substituting a generic mock object.
s3_mock = MagicMock()
bucket_mock = MagicMock()
s3_mock.Bucket = MagicMock(return_value=bucket_mock)


class TestEtlSample(unittest.TestCase):

    def setUp(self):
        self.input_data = pd.read_csv('tests/fixture/test.csv', index_col='PassengerId')


    def test_transform(self):
        # avoid CabinNum being automatically cast to float
        expected = pd.read_csv('tests/fixture/expected.csv', index_col='PassengerId', dtype={'CabinNum': str})
        actual = transform(self.input_data)
        self.assertTrue(actual.equals(expected))


    @patch.object(load_s3, '__defaults__', ('etl-sample-output',))
    @patch('src.lambda_function.s3', s3_mock)
    @patch('src.lambda_function.extract')
    def test_pipeline(self, mocked_extract):
        with open('tests/fixture/event.json') as test_event:
            event = json.load(test_event)
        lambda_handler(event, None)

        mocked_extract.assert_called_once()
        expected_bucket_calls = [call('etl-sample-input'), call('etl-sample-output')]
        s3_mock.Bucket.assert_has_calls(expected_bucket_calls)
