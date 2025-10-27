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
AssertionError:  [] == [1, 25, 52]

In right but not left:
[1, 25, 52]

Original values:
[] == [1, 52, 25]
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
AssertionError:  [] == [5, 6, 7, 16, 17, 18, 23, 26, 27, 49, 53, 63, 66, 76, 80,
81, 82]

In right but not left:
[5, 6, 7, 16, 17, 18, 23, 26, 27, 49, 53, 63, 66, 76, 80, 81, 82]

Original values:
[] == [66, 5, 6, 7, 76, 16, 17, 18, 80, 81, 82, 23, 26, 27, 49, 53, 63]
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