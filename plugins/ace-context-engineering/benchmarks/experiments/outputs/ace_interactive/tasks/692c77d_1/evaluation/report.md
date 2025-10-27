──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 6
Num Total  Tests : 7
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, updated, removed spotify.SongReview records using
models.changed_records,
and assert 0 have been removed.
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
assert model changes match spotify.SongReview.
```python
with test(
    """
    assert model changes match spotify.SongReview.
    """
):
    test.case(models.changed_model_names(), "==", {"spotify.Song",
"spotify.SongReview"})
```
----------
AssertionError:  set() == {'spotify.Song', 'spotify.SongReview'}

In right but not left:
['spotify.Song', 'spotify.SongReview']
>> Failed Requirement
assert song_ids of the updated song reviews match
private_data.to_update_review_song_ids (ignore_order)
```python
with test(
    """
    assert song_ids of the updated song reviews match
private_data.to_update_review_song_ids (ignore_order)
    """
):
    updated_review_song_ids = list_of(updated_song_reviews, "song_id")
    test.case(
        updated_review_song_ids, "==", private_data.to_update_review_song_ids,
ignore_order=True
```
----------
AssertionError:  [] == [159, 211, 254]

In right but not left:
[159, 211, 254]

Original values:
[] == [211, 254, 159]
>> Failed Requirement
assert song_ids of the added song reviews match
private_data.to_add_review_song_ids (ignore_order)
```python
with test(
    """
    assert song_ids of the added song reviews match
private_data.to_add_review_song_ids (ignore_order)
    """
):
    added_review_song_ids = list_of(added_song_reviews, "song_id")
    test.case(
        added_review_song_ids, "==", private_data.to_add_review_song_ids,
ignore_order=True
```
----------
AssertionError:  [] == [28, 40, 95, 122, 175, 231, 239, 249]

In right but not left:
[28, 40, 95, 122, 175, 231, 239, 249]

Original values:
[] == [231, 40, 175, 239, 249, 122, 28, 95]
>> Failed Requirement
assert all added_review_song_ids have rating of public_data.target_rating.
```python
with test(
    """
    assert all added_review_song_ids have rating of public_data.target_rating.
    """
):
    test.case(list_of(added_song_reviews, "rating"), "all ==",
public_data.target_rating)
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert all updated_review_song_ids have rating of public_data.target_rating.
```python
with test(
    """
    assert all updated_review_song_ids have rating of public_data.target_rating.
    """
):
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.