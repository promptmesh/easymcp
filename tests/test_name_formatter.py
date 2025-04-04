import pytest
from easymcp.client.utils import format_server_name

@pytest.mark.parametrize("input_str,expected", [
    ("", ""),
    ("test", "test"),
    ("test-test", "test-test"),
    ("test_test", "test-test"),
    ("test.test", "test-test"),
    ("test.test.test", "test-test-test"),
    ("test_test_test", "test-test-test"),
])
def test_format_server_name(input_str, expected):
    assert format_server_name(input_str) == expected
