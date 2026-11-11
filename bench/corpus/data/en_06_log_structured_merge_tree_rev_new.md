In computer science, the log-structured merge-tree (also known as LSM tree, or LSMT) is a data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume, such as transactional log data. LSM trees, like other search trees, maintain key-value pairs. LSM trees maintain data in two or more separate structures, each of which is optimized for its respective underlying storage medium; data is synchronized between the two structures efficiently, in batches.

One simple version of the LSM tree is a two-level LSM tree. As described by Patrick O'Neil, a two-level LSM tree comprises two tree-like structures, called C<sub>0</sub> and C<sub>1</sub>. C<sub>0</sub> is smaller and entirely resident in memory, whereas C<sub>1</sub> is resident on disk. New records are inserted into the memory-resident C<sub>0</sub> component. If the insertion causes the C<sub>0</sub> component to exceed a certain size threshold, a contiguous segment of entries is removed from C<sub>0</sub> and merged into C<sub>1</sub> on disk. The performance characteristics of LSM trees stem from the fact that each component is tuned to the characteristics of its underlying storage medium, and that data is efficiently migrated across media in rolling batches, using an algorithm reminiscent of merge sort. Such tuning involves writing data in a sequential manner as opposed to as a series of separate random access requests. This optimization reduces total seek time in hard-disk drives (HDDs) and latency in solid-state drives (SSDs).
alt=Diagram illustrating compaction of data in a log-structured merge tree|thumb|Diagram illustrating compaction of data in a log-structured merge tree

Most LSM trees used in practice employ multiple levels. Level 0 is kept in main memory, and might be represented using a tree. The on-disk data is organized into sorted runs of data. Each run contains data sorted by the index key. A run can be represented on disk as a single file, or alternatively as a collection of files with non-overlapping key ranges. To perform a query on a particular key to get its associated value, one must search in the Level 0 tree and also each run.
The Stepped-Merge version of the LSM tree is a variant of the LSM tree that supports multiple levels with multiple tree structures at each level.

A particular key may appear in several runs, and what that means for a query depends on the application.  Some applications simply want the newest key-value pair with a given key. Some applications must combine the values in some way to get the proper aggregate value to return. For example, in Apache Cassandra, each value represents a row in a database, and different versions of the row may have different sets of columns.

In order to keep down the cost of queries, the system must avoid a situation where there are too many runs.

Extensions to the 'leveled' method to incorporate B+ tree structures have been suggested, for example bLSM and Diff-Index. LSM-tree was originally designed for write-intensive workloads. As increasingly more read and write workloads co-exist under an LSM-tree storage structure, read data accesses can experience high latency and low throughput due to frequent invalidations of cached data in buffer caches by LSM-tree compaction operations. To re-enable effective buffer caching for fast data accesses, a Log-Structured buffered-Merged tree (LSbM-tree) is proposed and implemented.

## Operations

### Write
In LSM-trees, write operations are designed to optimize performance by reducing random I/O and leveraging sequential disk writes. When a write operation is initiated, the data is first buffered in an in-memory component, often implemented using a sorted data structure such as a Skip list or B+ tree.

Once the in-memory buffer becomes full, it is flushed to the disk as an immutable sorted component at the first level (C1). This flush is performed sequentially, ensuring high I/O efficiency by avoiding the costly random writes typical of traditional indexing methods. To maintain durability, the system may use a write-ahead log (WAL) that records all incoming writes before they are added to the memory buffer. This ensures that no data is lost in the event of a crash during a write.

As data accumulates across levels on the disk, LSM trees employ a merge process similar to merge sort to consolidate entries and maintain a consistent sorted order across levels. This process also handles updates and deletes, removing redundant or obsolete entries. Updates are treated as new writes, while deletes are marked with a tombstone entry, which is a placeholder indicating that the key has been deleted. These tombstones are later removed during the merging process.

Two common merging policies govern how data flows through the levels: levelling and tiering. In levelling, only one component exists per level, and merging happens more frequently, reducing the total number of components but increasing write amplification. In tiering, multiple components can coexist within a level, and merging occurs less frequently, reducing write amplification but increasing read costs because more components need to be searched.

This design leads to amortized write costs of <math>O \left ({T \cdot L \over B} \right ) </math> for leveling merge policies, where <math>T</math> is the size ratio between levels, <math>L</math> is the number of levels, and <math>B</math> is the number of entries per page.

### Point lookup
A point lookup operation retrieves the value associated with a specific key. In LSM trees, because of the multi-level structure and the immutability of disk components, point lookups involve checking several levels to ensure the most up-to-date value for the key is returned.

The process begins with a search in the in-memory component (C0), which holds the latest data. Since this component is organized as a sorted structure, the search is efficient. If the key is found here, its value is returned right away.

If the key isn't found in memory, the search moves to the disk components, starting with the first level (C1) and continuing through deeper levels (C2, C3, etc.). Each disk level is also sorted, allowing for efficient searches using methods like binary search or tree search. Newer levels are checked first because they contain the most recent updates and deletions for the key.

To make the search faster, LSM trees often use a bloom filter for each on-disk component. These filters are probabilistic structures that help quickly determine whether a key is definitely absent from a component. Before accessing any disk component, the system checks the Bloom filter. If the filter indicates the key is not present, the component is skipped, saving time. If the filter suggests the key might be there, the system proceeds to search for the component.

The lookup operation stops as soon as the key is found, ensuring the most recent version is returned. If the search reaches the final level without finding the key, the system concludes that the key doesn't exist.

Point lookup complexity is <math>O(L)</math> without Bloom filters, as each level must be searched. With Bloom filters, the cost for zero-result lookups is significantly reduced to <math>O\left(L \cdot e^{-\frac{M}{N}}\right)</math>, where M is the total Bloom filter size and N is the number of keys. For existing key lookups, the cost is <math>O(1)</math> due to the presence of Bloom filters.

### Range query
A range query retrieves all key-value pairs within a specified range. The operation involves scanning multiple components across the LSM tree's hierarchical structure and consolidating entries to ensure accurate and complete results.

A range query begins by searching the in-memory component (C0). Since this component is typically a sorted data structure, range queries can be done efficiently. Once the in-memory component is finished, the query proceeds to the disk components, starting from the first level (C1) and continuing to deeper levels.

Each disk component is also stored as a sorted structure allowing efficient range scans within individual components. To perform the range query, the system locates the starting point in each relevant component and scans sequentially until the end of the range is reached. The results from each component are then merged into a priority queue to reconcile duplicates, updates, and deletes, ensuring the final result only includes the latest version of each key.

For efficiency, LSM trees often divide disk components into smaller, disjoint key ranges. In this way, when processing a range query, the system can search only the partitions that have overlap ranges to reduce the number of components accessed. Similar to point lookup, Bloom filters are sometimes used to quickly decide whether a disk component contains any keys within the queried range, allowing the system to skip components that are guaranteed to be irrelevant.

The performance of a range query in LSM-trees depends on the query's selectivity. For short-range queries, which access fewer keys than twice the number of levels, the query must examine components across all levels, leading to a cost proportional to the number of levels. For long-range queries, which access many keys, the price is dominated by scanning the largest level, as it contains most of the data. For this reason, the runtime for short-range queries is <math>O(L)</math> and <math>O\left(\frac{s}{B}\right)</math> for long-range queries, where <math>s</math> is the number of keys in the range.

## References

;General
*
*

## External links
* [http://www.benstopford.com/2015/02/14/log-structured-merge-trees An Overview of Log Structured Merge Trees]

Category:Trees (data structures)
Category:Database index techniques

