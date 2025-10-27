──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 2
Num Failed Tests : 4
Num Total  Tests : 6
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
obtain added, removed spotify.UserLibrarySong records using
models.changed_records,
and assert 0 have been added.
>> Passed Requirement
obtain added, removed spotify.UserLibraryAlbum records using
models.changed_records,
and assert 0 have been added.
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
assert model changes match spotify.UserLibrarySong, spotify.UserLibraryAlbum.
```python
with test(
    """
    assert model changes match spotify.UserLibrarySong,
spotify.UserLibraryAlbum.
    """
):
    test.case(
        models.changed_model_names(),
        "==",
```
----------
AssertionError:  set() == {'spotify.UserLibrarySong',
'spotify.UserLibraryAlbum'}

In right but not left:
['spotify.UserLibrarySong', 'spotify.UserLibraryAlbum']
>> Failed Requirement
assert all removed song_ids match private_data.to_remove_library_song_ids
(ignore_order)
```python
with test(
    """
    assert all removed song_ids match private_data.to_remove_library_song_ids
(ignore_order)
    """
):
    removed_library_song_ids = list_of(removed_library_songs, "song_id")
    test.case(
        removed_library_song_ids,
```
----------
AssertionError:  [] == [16, 21, 42, 63, 65, 73, 135, 147, 150, 165, 225, 257,
302]

In right but not left:
[16, 21, 42, 63, 65, 73, 135, 147, 150, 165, 225, 257, 302]

Original values:
[] == [65, 257, 135, 73, 16, 147, 21, 150, 225, 165, 42, 302, 63]
>> Failed Requirement
assert all removed album_ids match private_data.to_remove_library_album_ids
(ignore_order)
```python
with test(
    """
    assert all removed album_ids match private_data.to_remove_library_album_ids
(ignore_order)
    """
):
    removed_library_album_ids = list_of(removed_library_albums, "album_id")
    test.case(
        removed_library_album_ids,
```
----------
AssertionError:  [] == [2, 3, 6, 7, 12, 14]

In right but not left:
[2, 3, 6, 7, 12, 14]