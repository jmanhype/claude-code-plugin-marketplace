──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 5
Num Total  Tests : 6
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, updated, removed venmo.PaymentRequest records using
models.changed_records,
and assert 0 requests were added or removed.
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
assert model changes match venmo.Notification, venmo.PaymentRequest,
ignoring venmo.User, venmo.Transaction.
```python
with test(
    """
    assert model changes match venmo.Notification, venmo.PaymentRequest,
    ignoring venmo.User, venmo.Transaction.
    """
):
    test.case(
        models.changed_model_names(ignore=["venmo.User", "venmo.Transaction"]),
```
----------
AssertionError:  set() == {'venmo.Notification', 'venmo.PaymentRequest'}

In right but not left:
['venmo.Notification', 'venmo.PaymentRequest']
>> Failed Requirement
assert set of updated payment request ids match exactly
to private_data.to_accept_payment_request_ids (ignore order).
```python
with test(
    """
    assert set of updated payment request ids match exactly
    to private_data.to_accept_payment_request_ids (ignore order).
    """
):
    updated_payment_request_ids = list_of(updated_payment_requests, "id")
    test.case(
```
----------
AssertionError:  [] == [2336, 2339, 3730, 3731, 3732, 4396, 4400, 4401, 5139,
5143]

In right but not left:
[2336, 2339, 3730, 3731, 3732, 4396, 4400, 4401, 5139, 5143]
>> Failed Requirement
if public_data.accept_reject is "accept", assert all these payment request
are approved in the end state, otherwise,
assert all these payment request are rejected in the end state.
```python
with test(
    """
    if public_data.accept_reject is "accept", assert all these payment request
    are approved in the end state, otherwise,
    assert all these payment request are rejected in the end state.
    """
):
    expected_field_name = (
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
if public_data.accept_reject is "accept", assert only field that has changed in
these
payment_requests is approved_at using models.changed_field_names. otherwise,
assert only field that has changed in these payment_requests is denied_at using
models.changed_field_names.
```python
with test(
    """
    if public_data.accept_reject is "accept", assert only field that has changed
in these
    payment_requests is approved_at using models.changed_field_names. otherwise,
    assert only field that has changed in these payment_requests is denied_at
using models.changed_field_names.
    """
):
    all_changed_fields = [
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.