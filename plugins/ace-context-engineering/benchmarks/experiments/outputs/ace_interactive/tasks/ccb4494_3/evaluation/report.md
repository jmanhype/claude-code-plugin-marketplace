──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 4
Num Total  Tests : 5
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, removed spotify.SongLike records using models.changed_records,
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
assert model changes match spotify.SongLike.
```python
with test(
    """
    assert model changes match spotify.SongLike.
    """
):
    test.case(models.changed_model_names(), "==", {"spotify.Song",
"spotify.SongLike"})
```
----------
AssertionError:  set() == {'spotify.Song', 'spotify.SongLike'}

In right but not left:
['spotify.Song', 'spotify.SongLike']
>> Failed Requirement
assert all song_ids from the added song likes are in
private_data.song_ids_in_queue.
```python
with test(
    """
    assert all song_ids from the added song likes are in
private_data.song_ids_in_queue.
    """
):
    added_song_like_ids = list_of(added_song_likes, "song_id")
    test.case(added_song_like_ids, "all in", private_data.song_ids_in_queue)
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert song_ids from the added song likes match the
private_data.song_ids_to_like (ignore order).
```python
with test(
    """
    assert song_ids from the added song likes match the
private_data.song_ids_to_like (ignore order).
    """
):
```
----------
AssertionError:  [] == [14, 22, 149, 209, 225, 226]

In right but not left:
[14, 22, 149, 209, 225, 226]

Original values:
[] == [225, 14, 22, 226, 149, 209]