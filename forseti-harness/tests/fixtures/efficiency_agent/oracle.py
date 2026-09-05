"""Independent acceptance check for the isolated agent task (not pytest-collected)."""
from task import unique_in_order

assert unique_in_order([3, 1, 3, 2, 1]) == [3, 1, 2]
assert unique_in_order([[2], [1], [2]]) == [[2], [1]]
assert unique_in_order([]) == []
values = [3, 1, 3]
assert unique_in_order(iter(values)) == [3, 1]
assert values == [3, 1, 3]
print("agent_fixture_oracle: passed (order, unhashable values, empty, iterator, no mutation)")
