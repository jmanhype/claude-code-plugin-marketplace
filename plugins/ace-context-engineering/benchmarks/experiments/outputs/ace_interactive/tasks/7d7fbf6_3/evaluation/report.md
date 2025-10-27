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
['/home/adrian/pictures/vacations/bali.zip',
'/home/adrian/pictures/vacations/maui.zip',
'/home/adrian/pictures/vacations/santorini.zip',
'/home/adrian/pictures/vacations/seoul.zip']

In right but not left:
['/home/adrian/pictures/vacations/bali.zip',
'/home/adrian/pictures/vacations/maui.zip',
'/home/adrian/pictures/vacations/santorini.zip',
'/home/adrian/pictures/vacations/seoul.zip']
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
['/home/adrian/pictures/vacations/bali/IMG_0119053.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_1dde920.jpg',
'/home/adrian/pictures/vacations/bali/IMG_2f048c8.png',
'/home/adrian/pictures/vacations/bali/IMG_339d934.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_9b67bd2.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_af5d7ee.jpg',
'/home/adrian/pictures/vacations/bali/IMG_b2800a4.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_c91b566.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_d24f03e.png',
'/home/adrian/pictures/vacations/bali/IMG_ee3882f.png',
'/home/adrian/pictures/vacations/maui/IMG_3fe4803.png',
'/home/adrian/pictures/vacations/maui/IMG_48913de.png',
'/home/adrian/pictures/vacations/maui/IMG_98ad601.jpg',
'/home/adrian/pictures/vacations/maui/IMG_99ffb0c.png',
'/home/adrian/pictures/vacations/maui/IMG_d67f65c.jpeg',
'/home/adrian/pictures/vacations/maui/IMG_f035dbe.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_244b1ea.png',
'/home/adrian/pictures/vacations/santorini/IMG_3994cc8.png',
'/home/adrian/pictures/vacations/santorini/IMG_4e67b34.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_956ee2c.png',
'/home/adrian/pictures/vacations/santorini/IMG_a314a5a.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_b616169.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_c26eda4.png',
'/home/adrian/pictures/vacations/santorini/IMG_c8e3e7e.jpg',
'/home/adrian/pictures/vacations/santorini/IMG_cb8d5e2.jpeg',
'/home/adrian/pictures/vacations/seoul/IMG_10e9b0e.png',
'/home/adrian/pictures/vacations/seoul/IMG_2fc9ca9.png',
'/home/adrian/pictures/vacations/seoul/IMG_3b0c306.jpeg',
'/home/adrian/pictures/vacations/seoul/IMG_431de59.jpg',
'/home/adrian/pictures/vacations/seoul/IMG_8445393.png',
'/home/adrian/pictures/vacations/seoul/IMG_885f88e.jpg',
'/home/adrian/pictures/vacations/seoul/IMG_f2e5d16.png',
'/home/adrian/pictures/vacations/seoul/IMG_f6fb2fc.jpeg']

In right but not left:
['/home/adrian/pictures/vacations/bali/IMG_0119053.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_1dde920.jpg',
'/home/adrian/pictures/vacations/bali/IMG_2f048c8.png',
'/home/adrian/pictures/vacations/bali/IMG_339d934.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_9b67bd2.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_af5d7ee.jpg',
'/home/adrian/pictures/vacations/bali/IMG_b2800a4.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_c91b566.jpeg',
'/home/adrian/pictures/vacations/bali/IMG_d24f03e.png',
'/home/adrian/pictures/vacations/bali/IMG_ee3882f.png',
'/home/adrian/pictures/vacations/maui/IMG_3fe4803.png',
'/home/adrian/pictures/vacations/maui/IMG_48913de.png',
'/home/adrian/pictures/vacations/maui/IMG_98ad601.jpg',
'/home/adrian/pictures/vacations/maui/IMG_99ffb0c.png',
'/home/adrian/pictures/vacations/maui/IMG_d67f65c.jpeg',
'/home/adrian/pictures/vacations/maui/IMG_f035dbe.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_244b1ea.png',
'/home/adrian/pictures/vacations/santorini/IMG_3994cc8.png',
'/home/adrian/pictures/vacations/santorini/IMG_4e67b34.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_956ee2c.png',
'/home/adrian/pictures/vacations/santorini/IMG_a314a5a.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_b616169.jpeg',
'/home/adrian/pictures/vacations/santorini/IMG_c26eda4.png',
'/home/adrian/pictures/vacations/santorini/IMG_c8e3e7e.jpg',
'/home/adrian/pictures/vacations/santorini/IMG_cb8d5e2.jpeg',
'/home/adrian/pictures/vacations/seoul/IMG_10e9b0e.png',
'/home/adrian/pictures/vacations/seoul/IMG_2fc9ca9.png',
'/home/adrian/pictures/vacations/seoul/IMG_3b0c306.jpeg',
'/home/adrian/pictures/vacations/seoul/IMG_431de59.jpg',
'/home/adrian/pictures/vacations/seoul/IMG_8445393.png',
'/home/adrian/pictures/vacations/seoul/IMG_885f88e.jpg',
'/home/adrian/pictures/vacations/seoul/IMG_f2e5d16.png',
'/home/adrian/pictures/vacations/seoul/IMG_f6fb2fc.jpeg']
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
Munch({'/home/adrian/pictures/vacations/bali/IMG_0119053.jpeg':
'binary:df4ec66f74...', '/home/adrian/pictures/vacations/bali/IMG_1dde920.jpg':
'binary:a663deb66e...', '/home/adrian/pictures/vacations/bali/IMG_2f048c8.png':
'binary:a4ada86c15...', '/home/adrian/pictures/vacations/bali/IMG_339d934.jpeg':
'binary:89e4836d75...', '/home/adrian/pictures/vacations/bali/IMG_9b67bd2.jpeg':
'binary:51b1ddc966...', '/home/adrian/pictures/vacations/bali/IMG_af5d7ee.jpg':
'binary:81314bde34...', '/home/adrian/pictures/vacations/bali/IMG_b2800a4.jpeg':
'binary:3e22cf6767...', '/home/adrian/pictures/vacations/bali/IMG_c91b566.jpeg':
'binary:a487c2c1fc...', '/home/adrian/pictures/vacations/bali/IMG_d24f03e.png':
'binary:20ae4cd188...', '/home/adrian/pictures/vacations/bali/IMG_ee3882f.png':
'binary:a3bbd9978e...', '/home/adrian/pictures/vacations/maui/IMG_3fe4803.png':
'binary:512aa2b6eb...', '/home/adrian/pictures/vacations/maui/IMG_48913de.png':
'binary:bb1e76913b...', '/home/adrian/pictures/vacations/maui/IMG_98ad601.jpg':
'binary:0f8047e444...', '/home/adrian/pictures/vacations/maui/IMG_99ffb0c.png':
'binary:1338369410...', '/home/adrian/pictures/vacations/maui/IMG_d67f65c.jpeg':
'binary:e3c42c807a...', '/home/adrian/pictures/vacations/maui/IMG_f035dbe.jpeg':
'binary:e686e2aae1...',
'/home/adrian/pictures/vacations/santorini/IMG_244b1ea.png':
'binary:67a1584532...',
'/home/adrian/pictures/vacations/santorini/IMG_3994cc8.png':
'binary:b41ac61033...',
'/home/adrian/pictures/vacations/santorini/IMG_4e67b34.jpeg':
'binary:d38d02a5c0...',
'/home/adrian/pictures/vacations/santorini/IMG_956ee2c.png':
'binary:108c812053...',
'/home/adrian/pictures/vacations/santorini/IMG_a314a5a.jpeg':
'binary:56a5b60bcb...',
'/home/adrian/pictures/vacations/santorini/IMG_b616169.jpeg':
'binary:6e76ec1154...',
'/home/adrian/pictures/vacations/santorini/IMG_c26eda4.png':
'binary:49e188d8a5...',
'/home/adrian/pictures/vacations/santorini/IMG_c8e3e7e.jpg':
'binary:2eaeb747c6...',
'/home/adrian/pictures/vacations/santorini/IMG_cb8d5e2.jpeg':
'binary:77bc5a41b2...', '/home/adrian/pictures/vacations/seoul/IMG_10e9b0e.png':
'binary:e13df67563...', '/home/adrian/pictures/vacations/seoul/IMG_2fc9ca9.png':
'binary:ecd2b06e70...',
'/home/adrian/pictures/vacations/seoul/IMG_3b0c306.jpeg':
'binary:29a80473fd...', '/home/adrian/pictures/vacations/seoul/IMG_431de59.jpg':
'binary:1fadd38717...', '/home/adrian/pictures/vacations/seoul/IMG_8445393.png':
'binary:5038f1e9e4...', '/home/adrian/pictures/vacations/seoul/IMG_885f88e.jpg':
'binary:f370ae1abc...', '/home/adrian/pictures/vacations/seoul/IMG_f2e5d16.png':
'binary:e29be0494e...',
'/home/adrian/pictures/vacations/seoul/IMG_f6fb2fc.jpeg':
'binary:6963932de3...'})
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
['~/pictures/vacations/bali/', '~/pictures/vacations/maui/',
'~/pictures/vacations/santorini/', '~/pictures/vacations/seoul/']

In right but not left:
['~/pictures/vacations/bali/', '~/pictures/vacations/maui/',
'~/pictures/vacations/santorini/', '~/pictures/vacations/seoul/']