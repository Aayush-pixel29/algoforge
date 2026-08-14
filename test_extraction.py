"""
Test script to verify extraction of Python and Java solutions from Gemini markdown output.
"""

import re
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.abspath("."))

from algoforge.brain.agents import _extract_solutions

def _extract_solutions_proposed(text: str) -> dict[str, str]:
    """Extract Python and Java code from markdown fences with section-awareness and fallback."""
    text = (text or "").strip()
    solutions = {}
    
    # Targeted extraction under section headers first:
    py_section = re.search(
        r"##\s+Solution[^\n]*?Python[^\n]*\s*```(?:python3?|py)\s*\n([\s\S]*?)```",
        text,
        re.IGNORECASE,
    )
    if py_section:
        solutions["python"] = py_section.group(1).strip()
    else:
        py_match = re.search(r"```(?:python3?|py)\s*\n([\s\S]*?)```", text, re.IGNORECASE)
        if py_match:
            solutions["python"] = py_match.group(1).strip()
            
    java_section = re.search(
        r"##\s+Solution[^\n]*?Java[^\n]*\s*```java\s*\n([\s\S]*?)```",
        text,
        re.IGNORECASE,
    )
    if java_section:
        solutions["java"] = java_section.group(1).strip()
    else:
        java_match = re.search(r"```java\s*\n([\s\S]*?)```", text, re.IGNORECASE)
        if java_match:
            solutions["java"] = java_match.group(1).strip()
            
    if not solutions:
        raise ValueError(
            "Failed to extract code from the agent's markdown response. "
            "The model did not output valid code fences. Pipeline halted."
        )
    return solutions

def run_tests():
    print("=" * 60)
    print("RUNNING GEMINI CODE EXTRACTION TESTS (CURRENT IMPLEMENTATION)")
    print("=" * 60)
    
    test_results = []
    
    # 1. Standard Gemini Output (Ideal case)
    sample_standard = """# Two Sum

## Intuition & Company Pattern
The Two Sum problem asks for indices of two numbers that add up to a target.
Frequently asked at Google, Meta, Amazon.

## Algorithm Walkthrough
We use a hash map to look up complements in O(1) time.

## Complexity
- Time: O(n)
- Space: O(n)

## Solution (Python)
```python
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        lookup = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in lookup:
                return [lookup[diff], i]
            lookup[num] = i
        return []
```

## Solution (Java)
```java
import java.util.HashMap;
import java.util.Map;

class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }
            map.put(nums[i], i);
        }
        return new int[]{};
    }
}
```

## 5 Real-World Project Examples
1. Financial Ledger Reconciliation: Match matching debit and credit entries.
2. Packet Pair De-duplication: Network gateway session matching.
3. Cache Slot Resolution: Finding paired memory chunks.
4. E-commerce Coupon Stacking: Finding pairs of coupons that sum to a basket total.
5. Telemetry Time-window Correlation: Correlating request-response timestamps.

## Key Takeaways
- Hash tables reduce O(n^2) to O(n).
- Complements can be checked on-the-fly.
- One-pass avoids using the same element twice.
"""

    try:
        res1 = _extract_solutions(sample_standard)
        assert "python" in res1, "Missing python key"
        assert "java" in res1, "Missing java key"
        assert "class Solution:" in res1["python"]
        assert "class Solution {" in res1["java"]
        print("[PASS] Test 1: Standard Gemini Output - extracted both Python and Java successfully.")
        test_results.append(("Standard Gemini Output", True, "Successfully extracted both Python and Java"))
    except Exception as e:
        print(f"[FAIL] Test 1: Standard Gemini Output failed: {e}")
        test_results.append(("Standard Gemini Output", False, str(e)))

    # 2. Windows CRLF Line Endings
    sample_crlf = sample_standard.replace("\n", "\r\n")
    try:
        res2 = _extract_solutions(sample_crlf)
        assert "python" in res2, "Missing python key with CRLF"
        assert "java" in res2, "Missing java key with CRLF"
        print("[PASS] Test 2: CRLF Line Endings - extracted both Python and Java successfully.")
        test_results.append(("CRLF Line Endings", True, "Successfully extracted with Windows line endings"))
    except Exception as e:
        print(f"[FAIL] Test 2: CRLF Line Endings failed: {e}")
        test_results.append(("CRLF Line Endings", False, str(e)))

    # 3. Case Variations & Alternative Tags (e.g. ```Python3, ```JAVA, ```py)
    sample_case = """
## Solution (Python)
```Python3
def solve():
    return 42
```

## Solution (Java)
```JAVA
public class Solution {
    public int solve() {
        return 42;
    }
}
```
"""
    try:
        res3 = _extract_solutions(sample_case)
        assert "python" in res3 and "def solve():" in res3["python"]
        assert "java" in res3 and "public class Solution" in res3["java"]
        print("[PASS] Test 3: Tag variations (Python3, JAVA) - extracted successfully.")
        test_results.append(("Tag Variations (Python3, JAVA)", True, "Successfully handled case and tag variations"))
    except Exception as e:
        print(f"[FAIL] Test 3: Tag variations failed: {e}")
        test_results.append(("Tag Variations (Python3, JAVA)", False, str(e)))

    # 4. Trailing spaces after language tag (e.g. ```python   \n)
    sample_spaces = """
## Solution (Python)
```python   
def solve():
    return "ok"
```

## Solution (Java)
```java   
public class Solution {}
```
"""
    try:
        res4 = _extract_solutions(sample_spaces)
        assert "python" in res4 and "java" in res4
        print("[PASS] Test 4: Trailing spaces after language identifier - extracted successfully.")
        test_results.append(("Trailing Spaces after Tag", True, "Successfully handled trailing spaces"))
    except Exception as e:
        print(f"[FAIL] Test 4: Trailing spaces failed: {e}")
        test_results.append(("Trailing Spaces after Tag", False, str(e)))

    # 5. Multiple code blocks: Small snippet in walkthrough BEFORE main solution
    sample_multiple_blocks = """# Problem

## Algorithm Walkthrough
Here is a quick snippet:
```python
# quick pseudo/trace snippet
sample = [1, 2]
```

## Solution (Python)
```python
class Solution:
    def fullSolution(self):
        return True
```

## Solution (Java)
```java
class Solution {
    public boolean fullSolution() {
        return true;
    }
}
```
"""
    try:
        res5 = _extract_solutions(sample_multiple_blocks)
        is_full = "def fullSolution" in res5.get("python", "")
        if is_full:
            print("[PASS] Test 5: Extracted full solution despite earlier snippet.")
            test_results.append(("Multiple Code Blocks in Markdown", True, "Extracted full solution"))
        else:
            print("[WARN/FAIL] Test 5 (Current logic): Extracted the first snippet instead of the main solution block under ## Solution (Python)!")
            test_results.append(("Multiple Code Blocks in Markdown", False, "re.search matched the earlier walkthrough snippet instead of the full solution block under '## Solution (Python)'"))
    except Exception as e:
        print(f"[FAIL] Test 5 failed with exception: {e}")
        test_results.append(("Multiple Code Blocks in Markdown", False, str(e)))

    # Test 5 with proposed fix
    try:
        res5_prop = _extract_solutions_proposed(sample_multiple_blocks)
        is_full_prop = "def fullSolution" in res5_prop.get("python", "")
        assert is_full_prop, "Proposed logic failed to extract full solution"
        print("[PASS] Test 5 (Proposed logic): Correctly extracted full solution under ## Solution (Python).")
    except Exception as e:
        print(f"[FAIL] Test 5 (Proposed logic) failed: {e}")

    # 6. Missing Java (only Python provided)
    sample_py_only = """
## Solution (Python)
```python
class Solution:
    pass
```
"""
    try:
        res6 = _extract_solutions(sample_py_only)
        assert "python" in res6
        assert "java" not in res6
        print("[PASS] Test 6: Python-only markdown gracefully handled (returns dict with python only).")
        test_results.append(("Python Only Output", True, "Returned python only"))
    except Exception as e:
        print(f"[FAIL] Test 6 failed: {e}")
        test_results.append(("Python Only Output", False, str(e)))

    # 7. Empty or Invalid Markdown
    sample_invalid = "Just some text without any code blocks."
    try:
        _extract_solutions(sample_invalid)
        print("[FAIL] Test 7: Expected ValueError on missing code fences, but none was raised.")
        test_results.append(("Invalid/Empty Input", False, "No ValueError raised"))
    except ValueError as e:
        print("[PASS] Test 7: Correctly raised ValueError when no code blocks found.")
        test_results.append(("Invalid/Empty Input", True, "Properly raised ValueError"))
    except Exception as e:
        print(f"[FAIL] Test 7: Unexpected exception: {e}")
        test_results.append(("Invalid/Empty Input", False, str(e)))

    print("\n" + "=" * 60)
    print("SUMMARY OF TEST RESULTS")
    print("=" * 60)
    for name, passed, notes in test_results:
        status = "PASSED" if passed else "FAILED / WARN"
        print(f"[{status:^11}] {name}: {notes}")

if __name__ == "__main__":
    run_tests()
