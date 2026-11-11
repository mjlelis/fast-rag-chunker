In computer science, locality-sensitive hashing (LSH) is a fuzzy hashing technique that hashes similar input items into the same "buckets" with high probability. The number of buckets is much smaller than the universe of possible input items.

Locality-preserving hashing was initially devised as a way to facilitate data pipelining in implementations of massively parallel algorithms that use randomized routing and universal hashing to reduce memory contention and network congestion.

## Definitions
A finite family <math> \mathcal F</math> of functions <math>h\colon M \to S</math> is defined to be an LSH family
for
* a metric space <math>\mathcal M =(M, d)</math>,
* a threshold <math>r>0</math>,
* an approximation factor <math>c>1</math>,
* and probabilities <math>p_1 > p_2</math>

if it satisfies the following condition. For any two points <math>a, b \in M</math> and a hash function <math>h</math> chosen uniformly at random from <math>\mathcal F</math>:
* If <math>d(a,b) \le r</math>, then <math>h(a)=h(b)</math> (i.e.,  and  collide) with probability at least <math>p_1</math>,
* If <math>d(a,b) \ge cr</math>, then <math>h(a)=h(b)</math> with probability at most <math>p_2</math>.

Such a family <math>\mathcal F</math> is called <math>(r,cr,p_1,p_2)</math>-sensitive.

### LSH with respect to a similarity measure
Alternatively it is possible to define an LSH family on a universe of items  endowed with a similarity function <math>\phi\colon U \times U \to [0,1]</math>. In this setting, a LSH scheme is a family of hash functions  coupled with a probability distribution  over  such that a function <math>h \in H</math> chosen according to  satisfies <math>Pr [h(a) = h(b)] = \phi(a,b)</math> for each <math>a,b \in U</math>.

### Amplification

Given a <math>(d_1, d_2, p_1, p_2)</math>-sensitive family <math>\mathcal F</math>, we can construct new families <math>\mathcal G</math> by either the AND-construction or OR-construction of <math>\mathcal F</math>.
*Hierarchical clustering
*Genome-wide association study
*Image similarity identification
**VisualRank
*Gene expression similarity identification
*Audio similarity identification
*Nearest neighbor search
*Audio fingerprint
*Digital video fingerprinting
*Shared memory organization in parallel computing
*Training fully connected neural networks
*Computer security
*Machine learning

## Methods

### Bit sampling for Hamming distance

One of the easiest ways to construct an LSH family is by bit sampling. and that this bound is tight.

Because min-wise independent families are too big for practical applications, two variant notions of min-wise independence are introduced: restricted min-wise independent permutations families, and approximate min-wise independent families.
Restricted min-wise independence is the min-wise independence property restricted to certain sets of cardinality at most .
Approximate min-wise independence differs from the property by at most a fixed .

### Open source methods

#### Nilsimsa Hash

Nilsimsa is a locality-sensitive hashing algorithm used in anti-spam efforts. The goal of Nilsimsa is to generate a hash digest of an email message such that the digests of two similar messages are similar to each other.  The paper suggests that the Nilsimsa satisfies three requirements:

# The digest identifying each message should not vary significantly for changes that can be produced automatically.
# The encoding must be robust against intentional attacks.
# The encoding should support an extremely low risk of false positives.

Testing performed in the paper on a range of file types identified the Nilsimsa hash as having a significantly higher false positive rate when compared to other similarity digest schemes such as TLSH, Ssdeep and Sdhash.

#### TLSH

TLSH is locality-sensitive hashing algorithm designed for a range of security and digital forensic applications.

### Random projection

thumb | <math>\frac{\theta(u,v)}{\pi}</math> is approximately proportional to <math>1-\cos(\theta(u,v))</math> on the interval [0, <math>\pi</math>

The random projection method of LSH due to Moses Charikar) uses an approximation of the cosine distance between vectors.  The technique was used to approximate the NP-complete max-cut problem. the probability of two vectors being on different sides of the random hyperplane is approximately proportional to the cosine distance between them.

### Stable distributions

The hash function
<math>h_{\mathbf{a},b} (\boldsymbol{\upsilon}) :
\mathcal{R}^d
\to \mathcal{N} </math> maps a -dimensional vector
<math>\boldsymbol{\upsilon}</math> onto the set of integers. Each hash function
in the family is indexed by a choice of random <math>\mathbf{a}</math> and
<math>b</math> where <math>\mathbf{a}</math> is a -dimensional
vector with
entries chosen independently from a stable distribution and
<math>b</math> is
a real number chosen uniformly from the range [0,r]. For a fixed
<math>\mathbf{a},b</math> the hash function <math>h_{\mathbf{a},b}</math> is
given by <math>h_{\mathbf{a},b} (\boldsymbol{\upsilon}) = \left \lfloor
\frac{\mathbf{a}\cdot \boldsymbol{\upsilon}+b}{r} \right \rfloor </math>.

Other construction methods for hash functions have been proposed to better fit the data.

In particular k-means hash functions are better in practice than projection-based hash functions, but without any theoretical guarantee.

### Semantic hashing
Semantic hashing is a technique that attempts to map input items to addresses such that closer inputs have higher semantic similarity. The hashcodes are found via training of an artificial neural network or graphical model.

## Algorithm for nearest neighbor search

One of the main applications of LSH is to provide a method for efficient approximate nearest neighbor search algorithms.  Consider an LSH family <math>\mathcal F</math>.  The algorithm has two main parameters: the width parameter  and the number of hash tables .

In the first step, we define a new family <math>\mathcal G</math> of hash functions , where each function  is obtained by concatenating  functions <math>h_1, \ldots, h_k</math> from <math>\mathcal F</math>, i.e., <math>g(p) = [h_1(p), \ldots, h_k(p)]</math>.  In other words, a random hash function  is obtained by concatenating  randomly chosen hash functions from <math>\mathcal F</math>.  The algorithm then constructs  hash tables, each corresponding to a different randomly chosen hash function .

In the preprocessing step we hash all  -dimensional points from the data set  into each of the  hash tables.  Given that the resulting hash tables have only  non-zero entries, one can reduce the amount of memory used per each hash table to <math>O(n)</math> using standard hash functions.

Given a query point , the algorithm iterates over the  hash functions .  For each  considered, it retrieves the data points that are hashed into the same bucket as .  The process is stopped as soon as a point within distance  from  is found.

Given the parameters  and , the algorithm has the following performance guarantees:
* preprocessing time: <math>O(nLkt)</math>, where  is the time to evaluate a function <math>h \in \mathcal F</math> on an input point ;
* space: <math>O(nL)</math>, plus the space for storing data points;
* query time: <math>O(L(kt+dnP_2^k))</math>;
* the algorithm succeeds in finding a point within distance  from  (if there exists a point within distance ) with probability at least <math>1 - ( 1 - P_1^k ) ^ L</math>;

For a fixed approximation ratio <math>c=1+\epsilon</math> and probabilities <math>P_1</math> and <math>P_2</math>, one can set <math>k = \left\lceil\tfrac{\log n}{\log 1/P_2}\right\rceil</math> and <math>L = \lceil P_1^{-k}\rceil = O(n^{\rho}P_1^{-1})</math>, where <math>\rho={\tfrac{\log P_1}{\log P_2}}</math>. Then one obtains the following performance guarantees:
* preprocessing time: <math>O(n^{1+\rho}P_1^{-1}kt)</math>;
* space: <math>O(n^{1+\rho}P_1^{-1})</math>, plus the space for storing data points;
* query time: <math>O(n^{\rho}P_1^{-1}(kt+d))</math>;

### Finding nearest neighbor without fixed dimensionality

To generalize the above algorithm without radius  being fixed, we can take the algorithm and do a sort of binary search over . It has been shown that there is a data structure for the approximate nearest neighbor with the following performance guarantees:
* space: <math>O(n^{1+\rho}P_1^{-1}d\log^2 n)</math>;
* query time: <math>O(n^{\rho}P_1^{-1}(kt+d)\log n)</math>;
* the algorithm succeeds in finding the nearest neighbor with probability at least <math>1 - (( 1 - P_1^k ) ^ L\log n)</math>;

### Improvements

When  is large, it is possible to reduce the hashing time from <math>O(n^{\rho})</math>.
This was shown by and which gave
* query time: <math>O(t\log^2(1/P_2)/P_1 + n^{\rho}(d + 1/P_1))</math>;
* space: <math>O(n^{1+\rho}/P_1 + \log^2(1/P_2)/P_1)</math>;

It is also sometimes the case that the factor <math>1/P_1</math> can be very large.
This happens for example with Jaccard similarity data, where even the most similar neighbor often has a quite low Jaccard similarity with the query.
In it was shown how to reduce the query time to <math>O(n^\rho/P_1^{1-\rho})</math> (not including hashing costs) and similarly the space usage.

## See also

*
*
*
*
*
*
*
*Random indexing
*
*
*
*
*

## References

## Further reading

*Samet, H. (2006) Foundations of Multidimensional and Metric Data Structures. Morgan Kaufmann.
*
*

## External links
* [https://web.mit.edu/andoni/www/LSH/index.html Alex Andoni's LSH homepage]
* [https://lshkit.sourceforge.net/ LSHKIT: A C++ Locality Sensitive Hashing Library]
* [https://github.com/simonemainardi/LSHash A Python Locality Sensitive Hashing library that optionally supports persistence via redis]
* [https://web.archive.org/web/20101203074412/http://www.vision.caltech.edu/malaa/software/research/image-search/ Caltech Large Scale Image Search Toolbox]: a Matlab toolbox implementing several LSH hash functions, in addition to Kd-Trees, Hierarchical K-Means, and Inverted File search algorithms.
* [https://github.com/salviati/slash Slash: A C++ LSH library, implementing Spherical LSH by Terasawa, K., Tanaka, Y]
* [https://github.com/RSIA-LIESMARS-WHU/LSHBOX LSHBOX: An Open Source C++ Toolbox of Locality-Sensitive Hashing for Large Scale Image Retrieval, Also Support Python and MATLAB.]
* [https://github.com/DBWangGroupUNSW/SRS SRS: A C++ Implementation of An In-memory, Space-efficient Approximate Nearest Neighbor Query Processing Algorithm based on p-stable Random Projection]
* [https://github.com/trendmicro/tlsh TLSH open source on Github]
* [https://github.com/idealista/tlsh-js JavaScript port of TLSH (Trend Micro Locality Sensitive Hashing) bundled as node.js module]
*  [https://github.com/idealista/tlsh Java port of TLSH (Trend Micro Locality Sensitive Hashing) bundled as maven package]

Category:Search algorithms
Category:Classification algorithms
Category:Dimension reduction
Category:Hashing
Category:Probabilistic data structures

