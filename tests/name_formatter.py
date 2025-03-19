from easymcp.client.utils import format_server_name

assert format_server_name("test") == "test"
assert format_server_name("test-test") == "test-test"
assert format_server_name("test_test") == "test-test"
assert format_server_name("test.test") == "test-test"
assert format_server_name("test.test.test") == "test-test-test"
assert format_server_name("test_test_test") == "test-test-test"