──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 3
Num Failed Tests : 3
Num Total  Tests : 6
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
assert answers match.
>> Passed Requirement
obtain added, removed phone.UserTextMessage records using models.changed_records
and assert 0 were added.
>> Passed Requirement
obtain added, removed phone.UserVoiceMessage records using
models.changed_records,
and assert 0 were added.
──────────────────────────────────── Fails ─────────────────────────────────────
>> Failed Requirement
assert model changes match phone.UserTextMessage, phone.UserVoiceMessage.
```python
with test(
    """
    assert model changes match phone.UserTextMessage, phone.UserVoiceMessage.
    """
):
    changed_model_names = models.changed_model_names()
    test.case(
        changed_model_names,
```
----------
AssertionError:  set() == {'phone.UserTextMessage', 'phone.UserVoiceMessage'}

In right but not left:
['phone.UserTextMessage', 'phone.UserVoiceMessage']
>> Failed Requirement
assert their ids match private_data.to_delete_text_message_ids (ignore order).
```python
with test(
    """
    assert their ids match private_data.to_delete_text_message_ids (ignore
order).
    """
):
    removed_text_message_ids = list_of(removed_user_text_messages, "id")
    test.case(
        removed_text_message_ids,
```
----------
AssertionError:
[]
==
[16794, 16796, 16798, 16800, 16802, 16804, 16806, 16808, 16810, 16812, 16814]

In right but not left:
[16794, 16796, 16798, 16800, 16802, 16804, 16806, 16808, 16810, 16812, 16814]
>> Failed Requirement
assert their ids match private_data.to_delete_voice_message_ids (ignore order).
```python
with test(
    """
    assert their ids match private_data.to_delete_voice_message_ids (ignore
order).
    """
):
    added_user_voice_meails, _, removed_user_voice_messages =
models.changed_records(
        "phone.UserVoiceMessage"
    )
```
----------
AssertionError:  [] == [17022, 17024, 17026, 17028, 17030, 17032, 17034, 17036]

In right but not left:
[17022, 17024, 17026, 17028, 17030, 17032, 17034, 17036]