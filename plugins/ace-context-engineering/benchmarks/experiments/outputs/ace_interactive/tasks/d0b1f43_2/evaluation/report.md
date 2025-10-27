──────────────────────────────── Overall Stats ─────────────────────────────────
Num Passed Tests : 1
Num Failed Tests : 1
Num Total  Tests : 2
──────────────────────────────────── Passes ────────────────────────────────────
>> Passed Requirement
assert no model changes.
──────────────────────────────────── Fails ─────────────────────────────────────
>> Failed Requirement
assert answers match.
```python
with test(
    """
    assert answers match.
    """
):
    test.case(ground_truth_answer, "==", predicted_answer, normalize=float,
tolerance=0.51)
```
----------