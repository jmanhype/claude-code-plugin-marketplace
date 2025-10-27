──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 5
Num Total  Tests : 6
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
assert no new venmo.Transaction was added using models.changed_records.
──────────────────────────────────── Fails ─────────────────────────────────────
>> Failed Requirement
assert answers match.
```python
with test(
    """
    assert answers match.
    """
):
    test.answer(predicted_answer, ground_truth_answer)
```
----------
AssertionError:  '<<not_given>>' == 'null'
>> Failed Requirement
assert model changes match venmo.Transaction, venmo.TransactionLike
```python
with test(
    """
    assert model changes match venmo.Transaction, venmo.TransactionLike
    """
):
    changed_model_names = models.changed_model_names()
    test.case(
        changed_model_names,
```
----------
AssertionError:  set() == {'venmo.TransactionLike', 'venmo.Transaction'}

In right but not left:
['venmo.TransactionLike', 'venmo.Transaction']
>> Failed Requirement
assert set of all new transaction likes (obtained via models.changed_records)
is identical to set of private_data.recent_relative_transaction_ids.
```python
with test(
    """
    assert set of all new transaction likes (obtained via
models.changed_records)
    is identical to set of private_data.recent_relative_transaction_ids.
    """
):
    added_transaction_likes, _, _ =
models.changed_records("venmo.TransactionLike")
    liked_transaction_ids = set_of(added_transaction_likes, "transaction_id")
```
----------
AssertionError:  set() == {3299, 5224, 4243, 8223, 8218, 8220, 6909, 5215}

In right but not left:
[3299, 5224, 4243, 8223, 8218, 8220, 6909, 5215]
>> Failed Requirement
assert all newly liked transaction_ids are in
private_data.recent_transaction_ids.
```python
with test(
    """
    assert all newly liked transaction_ids are in
private_data.recent_transaction_ids.
    """
):
    test.case(
        liked_transaction_ids,
        "all in",
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert all newly liked transaction_ids are in
private_data.relative_transaction_ids.
```python
with test(
    """
    assert all newly liked transaction_ids are in
private_data.relative_transaction_ids.
    """
):
    test.case(
        liked_transaction_ids,
        "all in",
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.