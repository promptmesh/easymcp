import pytest
from easymcp.client.utils import format_server_name

@pytest.mark.parametrize("input_str,expected", [
    # Basic
    ("", ""),
    ("test", "test"),
    ("test-test", "test-test"),
    ("test_test", "test-test"),
    ("test.test", "test-test"),
    ("test.test.test", "test-test-test"),
    ("test_test_test", "test-test-test"),

    # Mixed separators
    ("test_test.test", "test-test-test"),
    ("test.test_test", "test-test-test"),
    ("test-test_test", "test-test-test"),

    # Leading/trailing separators
    ("_test", "-test"),
    (".test", "-test"),
    ("test_", "test-"),
    ("test.", "test-"),
    ("_test_", "-test-"),
    (".test.", "-test-"),

    # Numbers
    ("test123", "test123"),
    ("123_test", "123-test"),
    ("test_123.test", "test-123-test"),

    # Whitespace
    (" test ", "test"),
    ("test  test", "testtest"),

    # Uppercase preserved
    ("Test_Test", "Test-Test"),

    # Special characters removed
    ("test@name", "testname"),
    ("test!name", "testname"),
    ("test$name", "testname"),
    ("test#name", "testname"),

    # Emoji/unicode removed
    ("test_🚀", "test-"),
    ("测试_测试", "-"),

    # Long string
    ("a" * 100 + "_test", "a" * 100 + "-test"),
])
def test_format_server_name(input_str, expected):
    assert format_server_name(input_str) == expected
