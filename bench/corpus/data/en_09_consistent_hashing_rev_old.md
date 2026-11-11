In computer science, consistent hashing In contrast, in most traditional hash tables, a change in the number of array slots causes nearly all keys to be remapped because the mapping between the keys and the slots is defined by a modular operation.

Consistent hashing is used by Content Delivery Networks because it is useful for distributing requests for content from a rotating population of web servers. Tim Berners-Lee credits consistent hashing algorithms, and Daniel Lewin as their inventor, with solving the slashdotting problem which plagued the World Wide Web in the 1990s.

## History

The term "consistent hashing" was introduced by David Karger et al. at MIT for use in distributed caching, particularly for the web. This academic paper from 1997 in Symposium on Theory of Computing introduced the term "consistent hashing" as a way of distributing requests among a changing population of web servers. Each slot is then represented by a server in a distributed system or cluster. The addition of a server and the removal of a server (during scalability or outage) requires only <math>num\_keys/num\_slots</math> items to be re-shuffled when the number of slots (i.e. servers) change. The authors mention linear hashing and its ability to handle sequential server addition and removal, while consistent hashing allows servers to be added and removed in an arbitrary order.
The paper was later re-purposed to address technical challenge of keeping track of a file in peer-to-peer networks such as a distributed hash table.

Teradata used this technique in their distributed database, released in 1986, although they did not use this term. Teradata still uses the concept of a hash table to fulfill exactly this purpose. Akamai Technologies was founded in 1998 by the scientists Daniel Lewin and F. Thomson Leighton (co-authors of the article coining "consistent hashing"). In Akamai's content delivery network, consistent hashing is used to balance the load within a cluster of servers, while a stable marriage algorithm is used to balance load across clusters.

Consistent hashing has also been used to reduce the impact of partial system failures in large web applications to provide robust caching without incurring the system-wide fallout of a failure. Consistent hashing is also the cornerstone of distributed hash tables (DHTs), which employ hash values to partition a keyspace across a distributed set of nodes, then construct an overlay network of connected nodes that provide efficient node retrieval by key.

Rendezvous hashing, designed in 1996, is a simpler and more general technique . It achieves the goals of consistent hashing using the very different highest random weight (HRW) algorithm.

## Basic technique
thumb|In this case, using consistent hashing would result in the "BLOB" getting stored server 139. A BLOB is mapped to the next server that appears on the circle in clockwise order until it reaches a server which is <math>\zeta \le \text{server ID}</math>

In the problem of load balancing, for example, when a BLOB has to be assigned to one of <math>n</math> servers on a cluster, a standard hash function could be used in such a way that we calculate the hash value for that BLOB, assuming the resultant value of the hash is <math>\beta</math>, we perform modular operation with the number of servers (<math>n</math> in this case) to determine the server in which we can place the BLOB: <math>\zeta = \beta\ \%\ n</math>; hence the BLOB will be placed in the server whose <math>\text{server ID}</math> is successor of <math>\zeta</math> in this case. However, when a server is added or removed during outage or scaling (when <math>n</math> changes), all the BLOBs in every server should be reassigned and moved due to rehashing, but this operation is expensive.

Consistent hashing was designed to avoid the problem of having to reassign every BLOB when a server is added or removed throughout the cluster. The central idea is to use a hash function that maps both the BLOB and servers to a unit circle, usually <math>2\pi</math> radians. For example, <math>\zeta = \Phi\ \%\ 360</math> (where <math>\Phi</math> is hash of a BLOB or server's identifier, like IP address or UUID). Each BLOB is then assigned to the next server that appears on the circle in clockwise order. Usually, binary search algorithm or linear search is used to find a "spot" or server to place that particular BLOB in <math>O(\log N)</math> or <math>O(N)</math> complexities respectively; and in every iteration, which happens in clockwise manner, an operation <math>\zeta\ \le\ \Psi</math> (where <math>\Psi</math> is the value of the server within the cluster) is performed to find the server to place the BLOB. This provides an even distribution of BLOBs to servers. But, more importantly, if a server fails and is removed from the circle, only the BLOBs that were mapped to the failed server need to be reassigned to the next server in clockwise order. Likewise, if a new server is added, it is added to the unit circle, and only the BLOBs mapped to that server need to be reassigned.

Importantly, when a server is added or removed, the vast majority of the BLOBs maintain their prior server assignments, and the addition of <math>n^{th}</math> server only causes <math>1/n</math> fraction of the BLOBs to relocate. Although the process of moving BLOBs across cache servers in the cluster depends on the context, commonly, the newly added cache server identifies its "predecessor" and moves all the BLOBs, whose mapping belongs to this server (i.e. whose hash value is less than that of the new server), from it. However, in the case of web page caches, in most implementations there is no involvement of moving or copying, assuming the cached BLOB is small enough. When a request hits a newly added cache server, a cache miss happens and a request to the actual web server is made and the BLOB is cached locally for future requests. The redundant BLOBs on the previously used cache servers would be removed as per the cache eviction policies.

### Implementation
Let <math>h_{b}(x)</math> and <math>h_{s}(x)</math> be the hash functions used for the BLOB and server's unique identifier respectively. In practice, a binary search tree (BST) is used to dynamically maintain the <math>\text{server ID}</math> within a cluster or hashring, and to find the successor or minimum within the BST, tree traversal is used.
;Inserting <math>x</math> into the cluster
:Let <math>\beta</math> be the hash value of a BLOB such that, <math>h_{b}(x)=\beta\ \%\ 360</math> where <math>x \in \mathrm{BLOB}</math> and <math>h_{b}(x)=\zeta</math>. To insert <math>x</math>, find the successor of <math>\zeta</math> in the BST of <math>\text{server ID}</math>s. If <math>\zeta</math> is larger than all of the <math>\text{server ID}</math>s, the BLOB is placed in the server with smallest <math>\text{server ID}</math> value.
;Deleting <math>x</math> from the cluster
:Find the successor of <math>\zeta</math> in the BST, remove the BLOB from the returned <math>\text{server ID}</math>. If <math>\zeta</math> has no successor, remove the BLOB from the smallest of the <math>\text{server ID}</math>s.
;Insert a server into cluster
:Let <math>\Phi</math> be the hash value of a server's identifier such that, <math>h_{s}(x)=\Phi\ \%\ 360</math> where <math>x \in \{\text{IP address, UUID}\}</math> and <math>h_{s}(x)=\theta</math>. Move all the BLOBs, whose hash value is smaller than <math>\theta</math>, from the server whose <math>\text{server ID}</math> is successor of <math>\theta</math>. If <math>\theta</math> is largest of all the <math>\text{server ID}</math>s, move the relevant BLOBs from the smallest of the <math>\text{server ID}</math>s into <math>\theta</math>.
;Delete a server from cluster
:Find the successor of <math>\theta</math> in the BST, move the BLOBs from <math>\theta</math> into its successor server. If <math>\theta</math> doesn't have a successor, move the BLOBs into the smallest of the <math>\text{server ID}</math>s.

### Variance reduction

To avoid skewness of multiple nodes within the radian, which happen due to lack of uniform distribution of the servers within the cluster, multiple labels are used. Those duplicate labels are called "virtual nodes" i.e. multiple labels which point to a single "real" label or server within the cluster. The amount of virtual nodes or duplicate labels used for a particular server within a cluster is called the "weight" of that particular server.

## Practical extensions

A number of extensions to the basic technique are needed for effectively using consistent hashing for load balancing in practice. In the basic scheme above, if a server fails, all its BLOBs are reassigned to the next server in clockwise order, potentially doubling the load of that server. This may not be desirable. To ensure a more even redistribution of BLOBs on server failure, each server can be hashed to multiple locations on the unit circle. When a server fails, the BLOBs assigned to each of its replicas on the unit circle will get reassigned to a different server in clockwise order, thus redistributing the BLOBs more evenly. Another extension concerns a situation where a single BLOB gets "hot" and is accessed a large number of times and will have to be hosted in multiple servers. In this situation, the BLOB may be assigned to multiple contiguous servers by traversing the unit circle in clockwise order. A more complex practical consideration arises when two BLOBs are hashed near each other in the unit circle and both get "hot" at the same time. In this case, both BLOBs will use the same set of contiguous servers in the unit circle. This situation can be ameliorated by each BLOB choosing a different hash function for mapping servers to the unit circle.
* OpenStack's Object Storage Service Swift
* Partitioning component of Amazon's storage system Dynamo
* Data partitioning in Apache Cassandra
* Data partitioning in ScyllaDB
* Data partitioning in Voldemort
* Akka's consistent hashing router
* Riak, a distributed key-value database
* Gluster, a network-attached storage file system
* Akamai content delivery network
* Discord chat application
* Load balancing gRPC requests to a distributed cache in SpiceDB
* Chord algorithm
* MinIO object storage system

## References

### Works cited
*
*

## External links
* [https://web.archive.org/web/20110721203235/http://www.tomkleinpeter.com/2008/03/17/programmers-toolbox-part-3-consistent-hashing/ Understanding Consistent hashing]
* [http://michaelnielsen.org/blog/consistent-hashing Consistent hashing by Michael Nielsen on June 3, 2009]
* [https://www.youtube.com/watch?v=apHAqUG3Pi8 Consistent Hashing, Danny Lewin, and the Creation of Akamai]
* Jump Consistent Hashing: A Fast, Minimal Memory, Consistent Hash Algorithm
* [https://medium.com/i0exception/rendezvous-hashing-8c00e2fb58b0 Rendezvous Hashing: an alternative to Consistent Hashing]
* Implementations in various languages:
** [https://github.com/chrismoos/hash-ring C]
** [https://web.archive.org/web/20210414205133/http://www.martinbroadhurst.com/consistent-hash-ring.html C++]
** [http://code.google.com/p/consistent-hash/ C#]
** [https://web.archive.org/web/20110711100426/https://github.com/basho/riak_core/blob/master/src/chash.erl Erlang]
** [https://github.com/stathat/consistent Go]
** [https://web.archive.org/web/20120605030524/http://weblogs.java.net/blog/tomwhite/archive/2007/11/consistent_hash.html Java]
** [https://github.com/pda/flexihash  PHP]
** [https://github.com/afirel/consistent_hashr Ruby]
** [http://techspot.zzzeek.org/2012/07/07/the-absolutely-simplest-consistent-hashing-example/ Python]
** [http://michaelnielsen.org/blog/consistent-hashing/ Python (again)]
** [https://metacpan.org/pod/Set::ConsistentHash Perl]
** [https://github.com/bradclawsie/Hash-Consistent Perl6]

Category:Hashing

