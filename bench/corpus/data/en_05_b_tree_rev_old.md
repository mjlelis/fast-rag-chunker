In computer science, a B-tree is a self-balancing tree data structure that maintains sorted data and allows searches, sequential access, insertions, and deletions in logarithmic time. The B-tree generalizes the binary search tree, allowing nodes to have more than two children.

By allowing more children under one node than a regular self-balancing binary search tree, the B-tree reduces the height of the tree and puts the data in fewer separate blocks. This is especially important for trees stored in secondary storage (e.g., disk drives), as these systems have relatively high latency and work with relatively large blocks of data, hence the B-tree's use in databases and file systems. This remains a major advantage when the tree is stored in memory, as modern computer systems rely heavily on CPU caches. Compared to reading from the cache, reading from memory after a cache miss costs significant time.

## History
Vishal velusamy While working at Boeing Research Labs, Rudolf Bayer and Edward M. McCreight invented B-trees to efficiently manage index pages for large random-access files. Their basic assumption was that indices would be so voluminous that only small chunks of the tree could fit in the main memory. Bayer and McCreight's paper Organization and maintenance of large ordered indices When asked, "I want to know what B in B-Tree stands for," McCreight answered:<blockquote>Everybody does!

So you just have no idea what a lunchtime conversation can turn into. So there we were, Rudy and I, at lunch. We had to give the thing a name.... We were working for Boeing at the time, but we couldn't use the name without talking to the lawyers. So there's a B.

It has to do with Balance. There's another B.

Rudy was the senior author. Rudy (Bayer) was several years older than I am, and had... many more publications than I did. So there's another B.

And so at the lunch table, we never did resolve whether there was one of those that made more sense than the rest.

What Rudy likes to say is, the more you think about what the B in B-Tree means, the better you understand B-Trees!</blockquote>

## Definition
According to Knuth's definition, a B-tree of order m is a tree that satisfies the following properties:

# Every node has at most m children.
# Every node, except for the root and the leaves, has at least ⌈m/2⌉ children.
# The root node has at least two children unless it is a leaf.
# All leaves appear on the same level.
# A non-leaf node with k children contains k&minus;1 keys.

The keys of each non-leaf node act as separation values that divide its subtrees. For example, if an internal node has 3 child nodes (or subtrees), then it must have 2 keys: a<sub>1</sub> and a<sub>2</sub>. All values in the leftmost subtree will be less than a<sub>1</sub>, all values in the middle subtree will be between a<sub>1</sub> and a<sub>2</sub>, and all values in the rightmost subtree will be greater than a<sub>2</sub>.

;Internal nodes
: Internal nodes (also known as inner nodes) are all nodes except for leaf nodes and the root node. They are usually represented as an ordered set of elements and child pointers. Every internal node contains a maximum of U children and a minimum of L children. Thus, the number of elements is always 1 less than the number of child pointers (the number of elements is between L−1 and U−1). U must be either 2L or 2L−1; therefore, each internal node is at least half full. The relationship between U and L implies that two half-full nodes can be joined to make a legal node, and one full node can be split into two legal nodes (if there's room to push one element up into the parent). These properties make it possible to delete and insert new values into a B-tree while also adjusting the tree to preserve its properties.
;The root node
: The root node's number of children has the same upper limit as internal nodes but has no lower limit. For example, when there are fewer than L−1 elements in the entire tree, the root will be the only node in the tree with no children at all.

;Leaf nodes
: In Knuth's terminology, the "leaf" nodes are the actual data objects/chunks. The internal nodes that are one level above these leaves are what would be called the "leaves" by other authors: these nodes only store keys (at most m-1, and at least m/2-1 if they are not the root) and pointers (one for each key) to nodes carrying the data objects/chunks.

A B-tree of depth n+1 can hold about U times as many items as a B-tree of depth n, but the cost of search, insert, and delete operations grows with the depth of the tree. As with any balanced tree, the cost grows much more slowly than the number of elements.

Some balanced trees store values only at leaf nodes and use different kinds of nodes for leaf nodes and internal nodes. B-trees keep values in every node in the tree except leaf nodes.

### Differences in terminology
The literature on B-trees is not uniform in its terminology.

Bayer and McCreight (1972), Comer (1979), and others define the order of a B-tree as the minimum number of keys in a non-root node. Folk and Zoellick point out that terminology is ambiguous because the maximum number of keys is unclear. An order 3 B-tree might hold a maximum of 6 keys or a maximum of 7 keys. Knuth (1998) avoids the problem by defining the order to be the maximum number of children (which is one more than the maximum number of keys).

The term leaf is also inconsistent. Bayer and McCreight (1972) considered the leaf level to be the lowest level of keys, but Knuth considered the leaf level to be one level below the lowest keys. There are many possible implementation choices. In some designs, the leaves may hold the entire data record; in other designs, the leaves may only hold pointers to the data record. Those choices are not fundamental to the idea of a B-tree.

For simplicity, most authors assume there is a fixed number of keys that fit in a node. The basic assumption is that the key size and node size are both fixed. In practice, variable-length keys may be employed.

## Informal description
thumb|400px|right|A B-tree  of order 5

### Node structure
As with other trees, B-trees can be represented as a collection of three types of nodes: root, internal (a.k.a. interior), and leaf.

Note the following variable definitions:

*  - Maximum number of potential search keys for each node in a B-tree. (This value is constant over the entire tree.)
*  - The pointer to a child node that starts a sub-tree.
*  - The pointer to a record that stores the data.
*  - The search key at the zero-based node index .

In B-trees, the following properties are maintained for these nodes:

* If  exists in any node in a B-tree, then  exists in that node where <math>i \ge 1</math>.
* All leaf nodes have the same number of ancestors (i.e., they are all at the same depth).

Each internal node in a B-tree has the following format:

!pt<sub>0</sub>
!k<sub>0</sub>
!pr<sub>0</sub>
!pt<sub>1</sub>
!k<sub>1</sub>
!pr<sub>1</sub>
!pt<sub>2</sub>
!...
!k<sub>K-1</sub>
!pt<sub>K</sub>
!pr<sub>K-1</sub>

!
! colspan="3" |
! colspan="2" |

! style="text-align:right;" scope=row | when
!  exists
!  and <br/>exist
!  exists,<br/>and  does not exist
!  and <br/>do not exist
!  exists
!  does not exist

! style="text-align:right;" scope=row | Points to subtree<br/>in which all search keys,  :

Each leaf node in a B-tree has the following format:

!pr<sub>0</sub>
!k<sub>0</sub>
!pr<sub>1</sub>
!k<sub>1</sub>
!...
!pr<sub>K-1</sub>
!k<sub>K-1</sub>

! when  exists
! when  does not exist

The node bounds are summarized in the table below:

! rowspan="2" | Node type
! colspan="2" | number<br/> of keys
! colspan="2" | number<br/> of child nodes

! Min !! Max
! Min !! Max

### Insertion and deletion
To maintain the predefined range of child nodes, internal nodes may be joined or split.

Usually, the number of keys is chosen to vary between  and <math>2d</math>, where  is the minimum number of keys, and <math>d+1</math> is the minimum degree or branching factor of the tree. The factor of 2 will guarantee that nodes can be split or combined.

If an internal node has <math>2d</math> keys, then adding a key to that node can be accomplished by splitting the hypothetical <math>2d+1</math> key node into two  key nodes and moving the key that would have been in the middle to the parent node. Each split node has the required minimum number of keys. Similarly, if an internal node and its neighbor each have  keys, then a key may be deleted from the internal node by combining it with its neighbor. Deleting the key would make the internal node have <math>d-1</math> keys; joining the neighbor would add  keys plus one more key brought down from the neighbor's parent. The result is an entirely full node of <math>2d</math> keys.

A B-tree is kept balanced after insertion by splitting a would-be overfilled node, of <math>2d+1</math> keys, into two -key siblings and inserting the mid-value key into the parent. Depth only increases when the root is split, maintaining balance. Similarly, a B-tree is kept balanced after deletion by merging or redistributing keys among siblings to maintain the -key minimum for non-root nodes. A merger reduces the number of keys in the parent, potentially forcing it to merge or redistribute keys with its siblings, and so on. The only change in depth occurs when the root has two children, of  and (transitionally) <math>d-1</math> keys, in which case the two siblings and parent are merged, reducing the depth by one.

This depth will increase slowly as elements are added to the tree, but an increase in the overall depth is infrequent, and results in all leaf nodes being one more node farther away from the root.

### Comparison to other trees
Because a range of child nodes is permitted, B-trees do not need re-balancing as frequently as other self-balancing search trees, but may waste some space since nodes are not entirely full.

B-trees have substantial advantages over alternative implementations when the time to access the data of a node greatly exceeds the time spent processing that data, because the cost of accessing the node may then be amortized over multiple operations within the node. This usually occurs when the node data are stored in secondary storage, such as disk drives. By maximizing the number of keys within each internal node, the height of the tree decreases, and the number of expensive node accesses is reduced. In addition, rebalancing of the tree occurs less frequently. The maximum number of child nodes depends on the information that must be stored for each child node and the size of a full disk block or an analogous size in secondary storage. While 2–3 B-trees are easier to explain, practical B-trees using secondary storage need a large number of child nodes to improve performance.

### Variants
The term B-tree may refer to a specific design or a general class of designs. In the narrow sense, a B-tree stores keys in its internal nodes but need not store those keys in the records at the leaves. The general class includes variations such as the B+ tree, the B<sup>*</sup> tree and the B<sup>*+</sup> tree.
* In the B+ tree, the internal nodes do not store any pointers to records; thus all pointers to records are stored in the leaf nodes. In addition, a leaf node may include a pointer to the next leaf node to speed up sequential access. Because B+ tree internal nodes have fewer pointers, each node can hold more keys, causing the tree to be shallower and thus faster to search.
* The B<sup>*</sup> tree balances more neighboring internal nodes to keep the internal nodes more densely packed. This variant ensures non-root nodes are at least 2/3 full instead of 1/2. As the most costly part of the operation of inserting the node in a B-tree is splitting the node, B<sup>*</sup>-trees are created to postpone the splitting operation as long as they can. To maintain this, instead of immediately splitting up a node when it gets full, its keys are shared with a node next to it. This spill operation is less costly to do than split because it requires only shifting the keys between existing nodes, not allocating memory for a new one. For inserting, first, it is checked whether the node has some free space in it, and if so, the new key is just inserted in the node. However, if the node is full (it has  keys, where  is the order of the tree as the maximum number of pointers to subtrees from one node), it needs to be checked whether the right sibling exists and has some free space. If the right sibling has  keys, then keys are redistributed between the two sibling nodes as evenly as possible. For this purpose,  keys from the current node, the new key inserted, one key from the parent node and  keys from the sibling node are seen as an ordered array of  keys. The array becomes split by half so that  lowest keys stay in the current node, the next (middle) key is inserted in the parent, and the rest go to the right sibling. (The newly inserted key might end up in any of the three places.) The situation when the right sibling is full and the left isn't is analogous. When both the sibling nodes are full, then the two nodes (current node and a sibling) are split into three, and one more key is shifted up the tree to the parent node. If the parent is full, then the spill/split operation propagates towards the root node. Deleting nodes is somewhat more complex than inserting, however.
* The B<sup>*+</sup> tree combines the main B+ tree and B<sup>*</sup> tree features together.
* B-trees can be turned into order statistic trees to allow rapid searches for the Nth record in key order, or counting the number of records between any two records, and various other related operations.

## B-tree usage in databases

### Sorted file search time
Sorting and searching algorithms can be characterized by the number of comparison operations that must be performed using order notation. A binary search of a sorted table with  records, for example, can be done in roughly  comparisons. If the table had 1,000,000 records, then a specific record could be located with at most 20 comparisons: .

Large databases have historically been kept on disk drives. The time required to read a record on a disk drive far exceeds the time needed to compare keys once the record is available due to seek time and rotational delay. The seek time may be 0 to 20 or more milliseconds, and the rotational delay averages about half the rotation period. For a 7200 RPM drive, the rotation period is 8.33 milliseconds. For a drive such as the Seagate ST3500320NS, the track-to-track seek time is 0.8 milliseconds and the average reading seek time is 8.5 milliseconds. For simplicity, assume reading from disk takes about 10 milliseconds.

The time required to locate one record out of a million in the example above would be 20 disk reads, each taking 10 milliseconds, which equals 0.2 seconds.

The search time is reduced because individual records are grouped together in a disk block. A disk block might be 16 kilobytes in size. If each record is 160 bytes, then 100 records could be stored in each block. The disk read time above was actually for an entire block. Once the disk head is in position, one or more disk blocks can be read with little delay. With 100 records per block, the last 6 or so comparisons don't need to do any disk reads—the comparisons are all within the last disk block read.

To speed up the search further, the time to do the first 13 to 14 comparisons (which each required disk access) must be reduced.

### Index performance
A B-tree index can be used to improve performance. A B-tree index creates a multi-level tree structure that breaks a database down into fixed-size blocks or pages. Each level of this tree can be used to link those pages via an address location, allowing one page (known as a node, or internal page) to refer to another with leaf pages at the lowest level. One page is typically the starting point of the tree, or the "root". This is where the search for a particular key would begin, traversing a path that terminates in a leaf. Most pages in this structure will be leaf pages which refer to specific table rows.

Because each node (or internal page) can have more than two children, a B-tree index will usually have a shorter height (the distance from the root to the farthest leaf) than a Binary Search Tree. In the example above, initial disk reads narrowed the search range by a factor of two. That can be improved by creating an auxiliary index that contains the first record in each disk block (sometimes called a sparse index). This auxiliary index would be 1% of the size of the original database, but it can be searched quickly. Finding an entry in the auxiliary index would tell us which block to search in the main database; after searching the auxiliary index, we would have to search only that one block of the main database—at a cost of one more disk read.

In the above example, the index would hold 10,000 entries and would take at most 14 comparisons to return a result. Like the main database, the last six or so comparisons in the auxiliary index would be on the same disk block. The index could be searched in about eight disk reads, and the desired record could be accessed in 9 disk reads.

Creating an auxiliary index can be repeated to make an auxiliary index to the auxiliary index. That would create an aux-aux index that would need only 100 entries and would fit in one disk block.

Instead of reading 14 disk blocks to find the desired record, we only need to read 3 blocks. This blocking is the core idea behind the creation of the B-tree, where disk blocks form a hierarchy of levels to make up the index. Reading and searching the first (and only) block of the aux-aux index, which is the root of the tree, identifies the relevant block in aux-index in the level below. Reading and searching that aux-index block identifies the relevant block to read until the fin
