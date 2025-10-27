──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 3
Num Failed Tests : 5
Num Total  Tests : 8
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
assert answers match.
>> Passed Requirement
obtain added, updated, removed file_system.File records using
models.changed_records,
and assert 0 were updated.
>> Passed Requirement
obtain added, removed file_system.Directory records using
models.changed_records.
and assert 0 were added.
──────────────────────────────────── Fails ─────────────────────────────────────
>> Failed Requirement
assert model changes match file_system.Directory, file_system.File.
```python
with test(
    """
    assert model changes match file_system.Directory, file_system.File.
    """
):
    test.case(models.changed_model_names(), "==", {"file_system.Directory",
"file_system.File"})
```
----------
AssertionError:  set() == {'file_system.File', 'file_system.Directory'}

In right but not left:
['file_system.File', 'file_system.Directory']
>> Failed Requirement
assert all added files have paths that match private_data.compressed_file_paths
(ignoring order).
```python
with test(
    """
    assert all added files have paths that match
private_data.compressed_file_paths (ignoring order).
    """
):
    added_file_paths = list_of(added_files, "path")
    test.case(
        added_file_paths,
```
----------
AssertionError:
[]
==
['/home/nicholas/photographs/vacations/athens.zip',
'/home/nicholas/photographs/vacations/maui.zip',
'/home/nicholas/photographs/vacations/stockholm.zip',
'/home/nicholas/photographs/vacations/tokyo.zip']

In right but not left:
['/home/nicholas/photographs/vacations/athens.zip',
'/home/nicholas/photographs/vacations/maui.zip',
'/home/nicholas/photographs/vacations/stockholm.zip',
'/home/nicholas/photographs/vacations/tokyo.zip']
>> Failed Requirement
assert all removed files have paths that match keys of
private_data.decompressed_file_path_to_content (ignoring order).
```python
with test(
    """
    assert all removed files have paths that match keys of
    private_data.decompressed_file_path_to_content (ignoring order).
    """
):
    removed_file_paths = list_of(removed_files, "path")
    test.case(
```
----------
AssertionError:
[]
==
['/home/nicholas/photographs/vacations/athens/IMG_18b492a.png',
'/home/nicholas/photographs/vacations/athens/IMG_5006de6.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_7636b3c.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_922a618.jpg',
'/home/nicholas/photographs/vacations/athens/IMG_963ca81.png',
'/home/nicholas/photographs/vacations/athens/IMG_a936c2f.jpg',
'/home/nicholas/photographs/vacations/athens/IMG_aba3ce8.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_fda8834.jpg',
'/home/nicholas/photographs/vacations/maui/IMG_9f7c27c.png',
'/home/nicholas/photographs/vacations/maui/IMG_b0f0ed4.jpeg',
'/home/nicholas/photographs/vacations/maui/IMG_b172472.png',
'/home/nicholas/photographs/vacations/maui/IMG_cb542ad.jpeg',
'/home/nicholas/photographs/vacations/maui/IMG_edd789d.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_0008fa9.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_2a48c09.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_46206a7.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_4cdf20e.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_7fee728.png',
'/home/nicholas/photographs/vacations/stockholm/IMG_9b03d76.png',
'/home/nicholas/photographs/vacations/stockholm/IMG_b111891.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_b609fff.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_ce9d7d5.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_ec08657.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_22aca45.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_2673592.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_4f579de.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_68ecb7e.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_7c18318.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_978d639.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_aef0467.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_e4d2f65.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_ef3d27d.jpeg',
'/home/nicholas/photographs/vacations/tokyo/IMG_f09272f.png']

In right but not left:
['/home/nicholas/photographs/vacations/athens/IMG_18b492a.png',
'/home/nicholas/photographs/vacations/athens/IMG_5006de6.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_7636b3c.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_922a618.jpg',
'/home/nicholas/photographs/vacations/athens/IMG_963ca81.png',
'/home/nicholas/photographs/vacations/athens/IMG_a936c2f.jpg',
'/home/nicholas/photographs/vacations/athens/IMG_aba3ce8.jpeg',
'/home/nicholas/photographs/vacations/athens/IMG_fda8834.jpg',
'/home/nicholas/photographs/vacations/maui/IMG_9f7c27c.png',
'/home/nicholas/photographs/vacations/maui/IMG_b0f0ed4.jpeg',
'/home/nicholas/photographs/vacations/maui/IMG_b172472.png',
'/home/nicholas/photographs/vacations/maui/IMG_cb542ad.jpeg',
'/home/nicholas/photographs/vacations/maui/IMG_edd789d.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_0008fa9.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_2a48c09.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_46206a7.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_4cdf20e.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_7fee728.png',
'/home/nicholas/photographs/vacations/stockholm/IMG_9b03d76.png',
'/home/nicholas/photographs/vacations/stockholm/IMG_b111891.jpeg',
'/home/nicholas/photographs/vacations/stockholm/IMG_b609fff.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_ce9d7d5.jpg',
'/home/nicholas/photographs/vacations/stockholm/IMG_ec08657.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_22aca45.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_2673592.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_4f579de.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_68ecb7e.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_7c18318.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_978d639.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_aef0467.png',
'/home/nicholas/photographs/vacations/tokyo/IMG_e4d2f65.jpg',
'/home/nicholas/photographs/vacations/tokyo/IMG_ef3d27d.jpeg',
'/home/nicholas/photographs/vacations/tokyo/IMG_f09272f.png']
>> Failed Requirement
assert path to content mapping of removed files match
private_data.decompressed_file_path_to_content.
```python
with test(
    """
    assert path to content mapping of removed files match
private_data.decompressed_file_path_to_content.
    """
):
    removed_path_to_content = dict_of(removed_files, "path", "content")
    test.case(removed_path_to_content, "==",
private_data.decompressed_file_path_to_content)
```
----------
AssertionError:
{}
==
Munch({'/home/nicholas/photographs/vacations/athens/IMG_18b492a.png':
'binary:9de57233c1...',
'/home/nicholas/photographs/vacations/athens/IMG_5006de6.jpeg':
'binary:e4cd4581b5...',
'/home/nicholas/photographs/vacations/athens/IMG_7636b3c.jpeg':
'binary:6e5478f444...',
'/home/nicholas/photographs/vacations/athens/IMG_922a618.jpg':
'binary:7cd5ea1c16...',
'/home/nicholas/photographs/vacations/athens/IMG_963ca81.png':
'binary:6fbaf10dbc...',
'/home/nicholas/photographs/vacations/athens/IMG_a936c2f.jpg':
'binary:1eef6d730f...',
'/home/nicholas/photographs/vacations/athens/IMG_aba3ce8.jpeg':
'binary:56e70284bf...',
'/home/nicholas/photographs/vacations/athens/IMG_fda8834.jpg':
'binary:39f82f3b86...',
'/home/nicholas/photographs/vacations/maui/IMG_9f7c27c.png':
'binary:6d95f29617...',
'/home/nicholas/photographs/vacations/maui/IMG_b0f0ed4.jpeg':
'binary:1fa1662a14...',
'/home/nicholas/photographs/vacations/maui/IMG_b172472.png':
'binary:2b493af416...',
'/home/nicholas/photographs/vacations/maui/IMG_cb542ad.jpeg':
'binary:ec1c0ffe80...',
'/home/nicholas/photographs/vacations/maui/IMG_edd789d.jpg':
'binary:fc74ab2185...',
'/home/nicholas/photographs/vacations/stockholm/IMG_0008fa9.jpeg':
'binary:c763bea6d6...',
'/home/nicholas/photographs/vacations/stockholm/IMG_2a48c09.jpeg':
'binary:9519690459...',
'/home/nicholas/photographs/vacations/stockholm/IMG_46206a7.jpg':
'binary:89be9c5b0c...',
'/home/nicholas/photographs/vacations/stockholm/IMG_4cdf20e.jpeg':
'binary:09f72672ab...',
'/home/nicholas/photographs/vacations/stockholm/IMG_7fee728.png':
'binary:170fc08f89...',
'/home/nicholas/photographs/vacations/stockholm/IMG_9b03d76.png':
'binary:974cac2612...',
'/home/nicholas/photographs/vacations/stockholm/IMG_b111891.jpeg':
'binary:ea1a9c65c8...',
'/home/nicholas/photographs/vacations/stockholm/IMG_b609fff.jpg':
'binary:1923ed31fd...',
'/home/nicholas/photographs/vacations/stockholm/IMG_ce9d7d5.jpg':
'binary:9040620ea8...',
'/home/nicholas/photographs/vacations/stockholm/IMG_ec08657.png':
'binary:c692da968a...',
'/home/nicholas/photographs/vacations/tokyo/IMG_22aca45.jpg':
'binary:47f4afbdb0...',
'/home/nicholas/photographs/vacations/tokyo/IMG_2673592.png':
'binary:5b18dda49e...',
'/home/nicholas/photographs/vacations/tokyo/IMG_4f579de.jpg':
'binary:c0b165b9a7...',
'/home/nicholas/photographs/vacations/tokyo/IMG_68ecb7e.jpg':
'binary:6933c652c9...',
'/home/nicholas/photographs/vacations/tokyo/IMG_7c18318.png':
'binary:13efc5c157...',
'/home/nicholas/photographs/vacations/tokyo/IMG_978d639.png':
'binary:7b230c6f06...',
'/home/nicholas/photographs/vacations/tokyo/IMG_aef0467.png':
'binary:1f07fc0f1d...',
'/home/nicholas/photographs/vacations/tokyo/IMG_e4d2f65.jpg':
'binary:9752e09831...',
'/home/nicholas/photographs/vacations/tokyo/IMG_ef3d27d.jpeg':
'binary:51233af4e1...',
'/home/nicholas/photographs/vacations/tokyo/IMG_f09272f.png':
'binary:5d821fd219...'})
>> Failed Requirement
assert all removed file_system.Directory records have tilde_paths that match
private_data.decompressed_directory_paths (ignoring order).
```python
with test(
    """
    assert all removed file_system.Directory records have tilde_paths that match
    private_data.decompressed_directory_paths (ignoring order).
    """
):
    removed_directory_paths = list_of(removed_directories, "tilde_path")
    test.case(
```
----------
AssertionError:
[]
==
['~/photographs/vacations/athens/', '~/photographs/vacations/maui/',
'~/photographs/vacations/stockholm/', '~/photographs/vacations/tokyo/']

In right but not left:
['~/photographs/vacations/athens/', '~/photographs/vacations/maui/',
'~/photographs/vacations/stockholm/', '~/photographs/vacations/tokyo/']