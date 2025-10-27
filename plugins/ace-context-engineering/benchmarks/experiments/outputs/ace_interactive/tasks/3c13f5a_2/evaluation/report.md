──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 5
Num Total  Tests : 6
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, updated, removed venmo.PaymentRequest records using
models.changed_records,
and assert 0 were updated or removed.
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
assert model changes match venmo.Notification, venmo.PaymentRequest.
```python
with test(
    """
    assert model changes match venmo.Notification, venmo.PaymentRequest.
    """
):
    changed_model_names = models.changed_model_names()
    test.case(changed_model_names, "==", {"venmo.Notification",
"venmo.PaymentRequest"})
```
----------
AssertionError:  set() == {'venmo.Notification', 'venmo.PaymentRequest'}

In right but not left:
['venmo.Notification', 'venmo.PaymentRequest']
>> Failed Requirement
assert all added payment requests's receivers match
private_data.roommate_venmo_user_ids.
```python
with test(
    """
    assert all added payment requests's receivers match
private_data.roommate_venmo_user_ids.
    """
):
    added_receiver_ids = set_of(added_payment_requests, "receiver_id")
    test.case(added_receiver_ids, "==",
set(private_data.roommate_venmo_user_ids))
```
----------
AssertionError:  set() == {25, 3, 14}

In right but not left:
[25, 3, 14]
>> Failed Requirement
assert all added payment requests's amounts
match private_data.this_month_bill_share (tolerance=0.51)
```python
with test(
    """
    assert all added payment requests's amounts
    match private_data.this_month_bill_share (tolerance=0.51)
    """
):
    added_amounts = list_of(added_payment_requests, "amount")
    test.case(added_amounts, "all ==", private_data.this_month_bill_share,
tolerance=0.51)
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert all added payment requests's notes match public_data.note
(normalize_text=True).
```python
with test(
    """
    assert all added payment requests's notes match public_data.note
(normalize_text=True).
    """
):
    added_notes = list_of(added_payment_requests, "description")
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.