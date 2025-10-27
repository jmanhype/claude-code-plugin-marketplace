──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 3
Num Total  Tests : 4
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, removed spotify.UserArtistFollowing records using
models.changed_records
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
assert model changes match spotify.UserArtistFollowing.
```python
with test(
    """
    assert model changes match spotify.UserArtistFollowing.
    """
):
    test.case(
        models.changed_model_names(),
        "==",
```
----------
AssertionError:  set() == {'spotify.UserArtistFollowing'}

In right but not left:
['spotify.UserArtistFollowing']
>> Failed Requirement
assert artist_ids of the added artist followings match
private_data.to_be_followed_artist_ids.
```python
with test(
    """
    assert artist_ids of the added artist followings match
private_data.to_be_followed_artist_ids.
    """
):
    added_artist_follow_ids = set_of(added_artist_followings, "artist_id")
```
----------
AssertionError:  set() == {33, 10, 12, 21, 28}

In right but not left:
[33, 10, 12, 21, 28]