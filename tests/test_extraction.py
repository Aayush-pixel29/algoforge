import pytest
from algoforge.brain.agents import _extract_solutions

def test_standard_gemini_output():
    sample = """
## Solution (Python)
```python
class Solution:
    pass
```
## Solution (Java)
```java
class Solution {}
```
"""
    res = _extract_solutions(sample)
    assert "python" in res
    assert "java" in res
    assert "class Solution:" in res["python"]
    assert "class Solution {}" in res["java"]

def test_crlf_line_endings():
    sample = "## Solution (Python)\r\n```python\r\ndef solve():\r\n    pass\r\n```\r\n## Solution (Java)\r\n```java\r\nclass Solution {}\r\n```"
    res = _extract_solutions(sample)
    assert "python" in res
    assert "java" in res

def test_case_and_tag_variations():
    sample = "## Solution (Python)\n```Python3\ndef solve(): pass\n```\n## Solution (Java)\n```JAVA\nclass Solution {}\n```"
    res = _extract_solutions(sample)
    assert "def solve()" in res["python"]
    assert "class Solution" in res["java"]

def test_trailing_spaces():
    sample = "## Solution (Python)\n```python   \ndef solve(): pass\n```\n## Solution (Java)\n```java   \nclass Solution {}\n```"
    res = _extract_solutions(sample)
    assert "python" in res and "java" in res

def test_multiple_blocks_extracts_from_section():
    sample = """
## Algorithm Walkthrough
```python
# small snippet
```
## Solution (Python)
```python
def full_solution(): pass
```
## Solution (Java)
```java
class Solution {}
```
"""
    res = _extract_solutions(sample)
    assert "def full_solution" in res["python"]

def test_missing_language_raises_error():
    sample_py_only = "## Solution (Python)\n```python\nclass Solution:\n    pass\n```\n"
    with pytest.raises(ValueError, match="expected both python and java"):
        _extract_solutions(sample_py_only)

def test_invalid_markdown_raises_error():
    sample = "Just some text without any code blocks."
    with pytest.raises(ValueError):
        _extract_solutions(sample)
