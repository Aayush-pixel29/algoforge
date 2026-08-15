"""Static curriculum definition for DSA learning path."""

from __future__ import annotations

# format: (week_range, leetcode_topic_tag, codeforces_topic_tag, target_rating_band_tuple)
CURRICULUM = [
    ("1-2", "array,string", "implementation,strings", (800, 1100)),
    ("3", "two-pointers,sliding-window", "two pointers", (900, 1200)),
    ("4", "hash-table", "hashing", (900, 1200)),
    ("5", "stack,queue", "data structures", (1000, 1300)),
    ("6", "linked-list", "implementation", (1000, 1300)),
    ("7-8", "tree,binary-tree,binary-search-tree", "trees", (1100, 1400)),
    ("9", "heap-priority-queue", "*special", (1200, 1500)),
    ("10-11", "graph,breadth-first-search,depth-first-search", "graphs, dfs and similar", (1200, 1500)),
    ("12-13", "dynamic-programming", "dp", (1300, 1600)),
    ("14", "greedy,backtracking", "greedy", (1300, 1600)),
]
