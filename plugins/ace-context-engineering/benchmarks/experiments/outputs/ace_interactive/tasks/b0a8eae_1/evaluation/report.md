──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 0
Num Failed Tests : 5
Num Total  Tests : 5
──────────────────────────────────── Passes ────────────────────────────────────
None
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
assert model changes match spotify.MusicPlayer.
```python
with test(
    """
    assert model changes match spotify.MusicPlayer.
    """
):
    test.case(models.changed_model_names(), "==", {"spotify.MusicPlayer"})
```
----------
AssertionError:  set() == {'spotify.MusicPlayer'}

In right but not left:
['spotify.MusicPlayer']
>> Failed Requirement
assert music_player in the end state is in the playing state.
```python
with test(
    """
    assert music_player in the end state is in the playing state.
    """
):
    spotify_user = models.end.spotify.User.find_from(main_user)
    music_player =
models.end.spotify.MusicPlayer.find_one(user_id=spotify_user.id)
    test.case(music_player.is_playing, "is_truthy")
```
----------
AssertionError:  False is_truthy True

Original values:
False is_truthy '<SPECIAL_NOT_PASSED>'
>> Failed Requirement
assert the music_player's queue_songs' total duration in the end state
is >= data.private.workout_duration_mins.
```python
with test(
    """
    assert the music_player's queue_songs' total duration in the end state
    is >= data.private.workout_duration_mins.
    """
):
    queue_songs = music_player.queue_songs
    total_duration = sum_of(queue_songs, "duration")
```
----------
AssertionError:  0 >= 85
>> Failed Requirement
assert the set music_player's queue_songs' song_ids in the end state
match set of private_data.long_enough_playlist_song_ids.
```python
with test(
    """
    assert the set music_player's queue_songs' song_ids in the end state
    match set of private_data.long_enough_playlist_song_ids.
    """
):
    queue_song_ids = set_of(queue_songs, "id")
```
----------
AssertionError:
set()
==
{129, 2, 261, 8, 138, 150, 158, 164, 59, 191, 68, 76, 82, 86, 219, 221, 223,
234, 107, 237, 121, 251}

In right but not left:
[129, 2, 261, 8, 138, 150, 158, 164, 59, 191, 68, 76, 82, 86, 219, 221, 223,
234, 107, 237, 121, 251]