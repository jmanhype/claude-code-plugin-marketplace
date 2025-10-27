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
AssertionError:  [] == [23, 105, 139, 143, 214, 259, 310]

In right but not left:
[23, 105, 139, 143, 214, 259, 310]

Original values:
[] == [259, 105, 139, 143, 214, 23, 310]
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
AssertionError:  [] == [4, 7, 8, 16]

In right but not left:
[4, 7, 8, 16]

Original values:
[] == [8, 16, 4, 7]