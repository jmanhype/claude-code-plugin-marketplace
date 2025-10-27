──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 3
Num Failed Tests : 6
Num Total  Tests : 9
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, updated, removed venmo.Transaction records using
models.changed_records,
and assert 0 transactions were added or removed.
>> Passed Requirement
obtain added, removed venmo.TransactionLike records using
models.changed_records,
and assert 0 transaction likes were removed.
>> Passed Requirement
obtain added, updated, removed venmo.TransactionComment records using
models.changed_records,
and assert 0 transaction comments were updated or removed.
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
assert model changes match venmo.Transaction, venmo.TransactionLike,
venmo.TransactionComment
```python
with test(
    """
    assert model changes match venmo.Transaction, venmo.TransactionLike,
venmo.TransactionComment
    """
):
    changed_model_names = models.changed_model_names()
    test.case(
        changed_model_names,
```
----------
AssertionError:
set()
==
{'venmo.TransactionLike', 'venmo.TransactionComment', 'venmo.Transaction'}

In right but not left:
['venmo.TransactionLike', 'venmo.TransactionComment', 'venmo.Transaction']
>> Failed Requirement
assert updated transactions have only changed in like_count field using
models.changed_field_names.
```python
with test(
    """
    assert updated transactions have only changed in like_count field using
models.changed_field_names.
    """
):
    list_of_updated_transaction_fields = [
        models.changed_field_names("venmo.Transaction", updated_transaction.id)
        for updated_transaction in updated_transactions
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert transaction_ids of added transaction likes match exactly to
private_data.after_threshold_contact_transaction_ids (ignore order).
```python
with test(
    """
    assert transaction_ids of added transaction likes match exactly to
    private_data.after_threshold_contact_transaction_ids (ignore order).
    """
):
    added_transaction_like_ids = list_of(added_transaction_likes,
"transaction_id")
    test.case(
```
----------
AssertionError:
[]
==
[8280, 8281, 8282, 8283, 8284, 8285, 8286, 8287, 8288, 8295, 8297, 8298]

In right but not left:
[8280, 8281, 8282, 8283, 8284, 8285, 8286, 8287, 8288, 8295, 8297, 8298]
>> Failed Requirement
assert set of transaction_ids of added transaction comments match exactly
to private_data.after_threshold_contact_transaction_ids (ignore order).
```python
with test(
    """
    assert set of transaction_ids of added transaction comments match exactly
    to private_data.after_threshold_contact_transaction_ids (ignore order).
    """
):
    added_transaction_comment_ids = list_of(added_transaction_comments,
"transaction_id")
    test.case(
```
----------
AssertionError:
[]
==
[8280, 8281, 8282, 8283, 8284, 8285, 8286, 8287, 8288, 8295, 8297, 8298]

In right but not left:
[8280, 8281, 8282, 8283, 8284, 8285, 8286, 8287, 8288, 8295, 8297, 8298]
>> Failed Requirement
assert all added transaction comments have comment public_data.comment
(normalize_text=True)
```python
with test(
    """
    assert all added transaction comments have comment public_data.comment
(normalize_text=True)
    """
):
    test.case(
        list_of(added_transaction_comments, "comment"),
        "all ==",
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.