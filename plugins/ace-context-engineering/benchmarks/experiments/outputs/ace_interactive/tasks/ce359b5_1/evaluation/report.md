──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 2
Num Failed Tests : 6
Num Total  Tests : 8
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, updated, removed spotify.UserLibrarySong records using
models.changed_records,
and assert 0 have been added or updated.
>> Passed Requirement
obtain added, updated, removed spotify.PlaylistSong records using
models.changed_records,
and assert 0 have been added or updated.
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
assert model changes match spotify.UserLibrarySong, spotify.PlaylistSong.
```python
with test(
    """
    assert model changes match spotify.UserLibrarySong, spotify.PlaylistSong.
    """
):
    test.case(
        models.changed_model_names(),
        "==",
```
----------
AssertionError:  set() == {'spotify.PlaylistSong', 'spotify.UserLibrarySong'}

In right but not left:
['spotify.PlaylistSong', 'spotify.UserLibrarySong']
>> Failed Requirement
assert song_ids of the removed library songs match
private_data.to_delete_library_song_link_ids.
```python
with test(
    """
    assert song_ids of the removed library songs match
private_data.to_delete_library_song_link_ids.
    """
):
    removed_library_song_ids = set_of(removed_library_songs, "song_id")
    test.case(removed_library_song_ids, "==",
set(private_data.to_delete_library_song_link_ids))
```
----------
AssertionError:  set() == {294, 199, 301, 110, 208}

In right but not left:
[294, 199, 301, 110, 208]
>> Failed Requirement
assert id of the removed playlist_songs match
private_data.to_delete_playlist_song_link_ids.
```python
with test(
    """
    assert id of the removed playlist_songs match
private_data.to_delete_playlist_song_link_ids.
    """
):
    removed_playlist_song_ids = set_of(removed_playlist_songs, "id")
    test.case(
        removed_playlist_song_ids,
```
----------
AssertionError:  set() == {1415, 1420, 1424, 1425, 1401, 1435, 1404, 1437, 1436}

In right but not left:
[1415, 1420, 1424, 1425, 1401, 1435, 1404, 1437, 1436]
>> Failed Requirement
if public_data.before_after is "after",
assert all songs in song library are released on or before public_data.year, in
the end state.
if public_data.before_after is "before",
assert all songs in song library are released on or after public_data.year, in
the end state.
if public_data.before_after is "in or after",
assert all songs in song library are released on before public_data.year, in the
end state.
if public_data.before_after is "in or before",
assert all songs in song library are released on after public_data.year, in the
end state.
```python
with test(
    """
    if public_data.before_after is "after",
    assert all songs in song library are released on or before public_data.year,
in the end state.
    if public_data.before_after is "before",
    assert all songs in song library are released on or after public_data.year,
in the end state.
    if public_data.before_after is "in or after",
    assert all songs in song library are released on before public_data.year, in
the end state.
```
----------
AssertionError:  2019 >= 2021
>> Failed Requirement
if public_data.before_after is "after",
assert all songs in playlists are released on or before public_data.year, in the
end state.
if public_data.before_after is "before",
assert all songs in playlists are released on or after public_data.year, in the
end state.
if public_data.before_after is "in or after",
assert all songs in playlists are released on before public_data.year, in the
end state.
if public_data.before_after is "in or before",
assert all songs in playlists are released on after public_data.year, in the end
state.
```python
with test(
    """
    if public_data.before_after is "after",
    assert all songs in playlists are released on or before public_data.year, in
the end state.
    if public_data.before_after is "before",
    assert all songs in playlists are released on or after public_data.year, in
the end state.
    if public_data.before_after is "in or after",
    assert all songs in playlists are released on before public_data.year, in
the end state.
```
----------
AssertionError:  2020 >= 2021