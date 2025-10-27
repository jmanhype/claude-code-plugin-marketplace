──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 3
Num Total  Tests : 4
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, removed spotify.UserArtistFollowing records using
models.changed_records, then,
if public_data.action is "Follow", assert 0 have been removed,
if public_data.action is "Unfollow", assert 0 have been added.
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
    test.case(models.changed_model_names(), "==",
{"spotify.UserArtistFollowing"})
```
----------
AssertionError:  set() == {'spotify.UserArtistFollowing'}

In right but not left:
['spotify.UserArtistFollowing']
>> Failed Requirement
if public_data.action is "Follow",
assert IDs of added artist followings match
private_data.to_be_acted_upon_artist_ids (ignore_order),
if public_data.action is "Unfollow",
assert IDs of removed artist followings match
private_data.to_be_acted_upon_artist_ids (ignore_order).
```python
with test(
    """
    if public_data.action is "Follow",
    assert IDs of added artist followings match
private_data.to_be_acted_upon_artist_ids (ignore_order),
    if public_data.action is "Unfollow",
    assert IDs of removed artist followings match
private_data.to_be_acted_upon_artist_ids (ignore_order).
    """
):
```
----------
AssertionError:  [] == [19, 20, 30, 34, 35]

In right but not left:
[19, 20, 30, 34, 35]