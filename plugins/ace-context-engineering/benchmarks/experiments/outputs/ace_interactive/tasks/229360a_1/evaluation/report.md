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
AssertionError:  [] == [52, 69, 75, 77, 111, 113, 166, 184, 206, 228, 250, 252]

In right but not left:
[52, 69, 75, 77, 111, 113, 166, 184, 206, 228, 250, 252]

Original values:
[] == [228, 69, 166, 75, 77, 206, 111, 113, 52, 184, 250, 252]
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
AssertionError:  [] == [4, 10, 15, 18]

In right but not left:
[4, 10, 15, 18]

Original values:
[] == [10, 18, 4, 15]