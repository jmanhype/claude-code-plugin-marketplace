──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 4
Num Total  Tests : 5
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, _, removed spotify.ArtistFollowing records using
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
assert model changes match spotify.ArtistFollowing.
```python
with test(
    """
    assert model changes match spotify.ArtistFollowing.
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
assert all artists from added artist follows are of public_data.genre genre.
```python
with test(
    """
    assert all artists from added artist follows are of public_data.genre genre.
    """
):
    added_artist_genres = list_of(added_artist_followings, "artist.genre")
    test.case(added_artist_genres, "all ==", public_data.genre)
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.
>> Failed Requirement
assert all artists from added artist follows have >= public_data.min_followers
followers.
```python
with test(
    """
    assert all artists from added artist follows have >=
public_data.min_followers followers.
    """
):
    added_artist_follower_count = list_of(added_artist_followings,
"artist.follower_count")
```
----------
AssertionError: The left modifier is 'all' with allow_left_empty=False, but left
operand is empty.