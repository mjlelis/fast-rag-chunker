In computing, a Bloom filter is a space-efficient probabilistic data structure, conceived by Burton Howard Bloom in 1970, that is used to test whether an element is a member of a set. False positive matches are possible, but false negatives are not – in other words, a query returns either "possibly in set" or "definitely not in set". Elements can be added to the set, but not removed (though this can be addressed with the counting Bloom filter variant); the more items added, the larger the probability of false positives.

Bloom proposed the technique for applications where the amount of source data would require an impractically large amount of memory if "conventional" error-free hashing techniques were applied. He gave the example of a hyphenation algorithm for a dictionary of 500,000 words, out of which 90% follow simple hyphenation rules, but the remaining 10% require expensive disk accesses to retrieve specific hyphenation patterns. With sufficient memory, an error-free hash could be used to eliminate all unnecessary disk accesses; on the other hand, with limited memory, Bloom's technique uses a smaller hash area but still eliminates most unnecessary accesses. For example, a hash area only 18% of the size needed by an ideal error-free hash still eliminates 87% of the disk accesses.

More generally, fewer than 10 bits per element are required for a 1% false positive probability, independent of the size or number of elements in the set.

## Algorithm description
thumb|360px|An example of a Bloom filter, representing the set {{math|{x, y, z} }}. The colored arrows show the positions in the bit array that each set element is mapped to. The element  is not in the set {{math|{x, y, z} }}, because it hashes to one bit-array position containing 0. For this figure,  and .

An empty Bloom filter is a bit array of  bits, all set to 0. It is equipped with  different hash functions, which map set elements to one of the  possible array positions. To be optimal, the hash functions should be uniformly distributed and independent. Typically,  is a small constant which depends on the desired false error rate  , while  is proportional to  and the number of elements to be added.

To add an element, feed it to each of the  hash functions to get  array positions. Set the bits at all these positions to 1.

To test whether an element is in the set, feed it to each of the  hash functions to get  array positions. If any of the bits at these positions is 0, the element is definitely not in the set; if it were, then all the bits would have been set to 1 when it was inserted. If all are 1, then either the element is in the set, or the bits have by chance been set to 1 during the insertion of other elements, resulting in a false positive. In a simple Bloom filter, there is no way to distinguish between the two cases, but more advanced techniques can address this problem.

The requirement of designing  different independent hash functions can be prohibitive for large . For a good hash function with a wide output, there should be little if any correlation between different bit-fields of such a hash, so this type of hash can be used to generate multiple "different" hash functions by slicing its output into multiple bit fields.  Alternatively, one can pass  different initial values (such as 0, 1, ..., &nbsp;&minus;&nbsp;1) to a hash function that takes an initial value; or add (or append) these values to the key. For larger  and/or , independence among the hash functions can be relaxed with negligible increase in false positive rate. (Specifically,  show the effectiveness of deriving the  indices using enhanced double hashing
and triple hashing, variants of double hashing that are effectively simple random number generators seeded with the two or three hash values.)

Removing an element from this simple Bloom filter is impossible because there is no way to tell which of the  bits it maps to should be cleared.  Although setting any one of those  bits to zero suffices to remove the element, it would also remove any other elements that happen to map onto that bit. Since the simple algorithm provides no way to determine whether any other elements have been added that affect the bits for the element to be removed, clearing any of the bits would introduce the possibility of false negatives.

One-time removal of an element from a Bloom filter can be simulated by having a second Bloom filter that contains items that have been removed.  However, false positives in the second filter become false negatives in the composite filter, which may be undesirable.  In this approach re-adding a previously removed item is not possible, as one would have to remove it from the "removed" filter.

It is often the case that all the keys are available but are expensive to enumerate (for example, requiring many disk reads).  When the false positive rate gets too high, the filter can be regenerated; this should be a relatively rare event.

## Space and time advantages
thumb|360px|Bloom filter used to speed up answers in a key-value storage system. Values are stored on a disk which has slow access times. Bloom filter decisions are much faster. However some unnecessary disk accesses are made when the filter reports a positive (in order to weed out the false positives). Overall answer speed is better with the Bloom filter than without the Bloom filter. Use of a Bloom filter for this purpose, however, does increase memory usage.

While risking false positives, Bloom filters have a substantial space advantage over other data structures for representing sets, such as self-balancing binary search trees, tries, hash tables, or simple arrays or linked lists of the entries. Most of these require storing at least the data items themselves, which can require anywhere from a small number of bits, for small integers, to an arbitrary number of bits, such as for strings ( are an exception since they can share storage between elements with equal prefixes).  However, Bloom filters do not store the data items at all, and a separate solution must be provided for the actual storage. Linked structures incur an additional linear space overhead for pointers. A Bloom filter with a 1% error and an optimal value of , in contrast, requires only about 9.6 bits per element, regardless of the size of the elements. This advantage comes partly from its compactness, inherited from arrays, and partly from its probabilistic nature. The 1% false-positive rate can be reduced by a factor of ten by adding only about 4.8 bits per element.

However, if the number of potential values is small and many of them can be in the set, the Bloom filter is easily surpassed by the deterministic bit array, which requires only one bit for each potential element. Hash tables gain a space and time advantage if they begin ignoring collisions and store only whether each bucket contains an entry; in this case, they have effectively become Bloom filters with .

Bloom filters also have the unusual property that the time needed either to add items or to check whether an item is in the set is a fixed constant, , completely independent of the number of items already in the set. No other constant-space set data structure has this property, but the average access time of sparse hash tables can make them faster in practice than some Bloom filters.  In a hardware implementation, however, the Bloom filter shines because its  lookups are independent and can be parallelized.

To understand its space efficiency, it is instructive to compare the general Bloom filter with its special case when .  If , then in order to keep the false positive rate sufficiently low, a small fraction of bits should be set, which means the array must be very large and contain long runs of zeros.  The information content of the array relative to its size is low.  The generalized Bloom filter ( greater than 1) allows many more bits to be set while still maintaining a low false positive rate; if the parameters ( and ) are chosen well, about half of the bits will be set, and these will be apparently random, minimizing redundancy and maximizing information content.

## Probability of false positives
thumb|360px|The false positive probability  as a function of number of elements  in the filter and the filter size . An optimal number of hash functions  has been assumed.

Assume that a hash function selects each array position with equal probability. If m is the number of bits in the array, the probability that a certain bit is not set to 1 by a certain hash function during the insertion of an element is
:<math>1-\frac{1}{m}.</math>

If k is the number of hash functions and each has no significant correlation between each other, then the probability that the bit is not set to 1 by any of the hash functions is
:<math>\left(1-\frac{1}{m}\right)^k.</math>

We can use the well-known identity for e<sup>&minus;1</sup>
:<math>\lim_{m\to\infty} \left(1 - \frac{1}{m}\right)^m = \frac{1}{e}</math>
to conclude that, for large m,
:<math>\left(1-\frac{1}{m}\right)^k = \left(\left(1-\frac{1}{m}\right)^m\right)^{k/m} \approx e^{-k/m}.</math>

If we have inserted n elements, the probability that a certain bit is still 0 is

:<math>\left(1-\frac{1}{m}\right)^{kn} \approx e^{-kn/m};</math>

the probability that it is 1 is therefore

:<math>1-\left(1-\frac{1}{m}\right)^{kn} \approx 1 - e^{-kn/m}.</math>

Now test membership of an element that is not in the set. Each of the k array positions computed by the hash functions is 1 with a probability as above. The probability of all of them being 1, which would cause the algorithm to erroneously claim that the element is in the set, is often given as

:<math>\varepsilon = \left(1-\left[1-\frac{1}{m}\right]^{kn}\right)^k \approx \left( 1-e^{-kn/m} \right)^k.</math>

This is not strictly correct as it assumes independence for the probabilities of each bit being set. However, assuming it is a close approximation we have that the probability of false positives decreases as m (the number of bits in the array) increases, and increases as n (the number of inserted elements) increases.

The true probability of a false positive, without assuming independence, is

: <math>\frac{1}{m^{k(n+1)}}\sum_{i=1}^m i^k i! {m \choose i} \left\{ {kn \atop i}\right\}</math>

where the {braces} denote Stirling numbers of the second kind.

An alternative analysis arriving at the same approximation without the assumption of independence is given by Mitzenmacher and Upfal. After all n items have been added to the Bloom filter, let q be the fraction of the m bits that are set to 0. (That is, the number of bits still set to 0 is qm.) Then, when testing membership of an element not in the set, for the array position given by any of the k hash functions, the probability that the bit is found set to 1 is <math>1-q</math>. So the probability that all k hash functions find their bit set to 1 is   Further, the expected value of q is the probability that a given array position is left untouched by each of the k hash functions for each of the n items, which is (as above)
: <math>E[q] = \left(1 - \frac{1}{m}\right)^{kn}</math>.
It is possible to prove, without the independence assumption, that q is very strongly concentrated around its expected value.  In particular, from the Azuma–Hoeffding inequality, they prove that
: <math> \Pr(\left|q - E[q]\right| \ge \frac{\lambda}{m}) \le 2\exp(-2\lambda^2/kn) </math>
Because of this, we can say that the exact probability of false positives is
: <math> \sum_{t} \Pr(q = t) (1 - t)^k \approx (1 - E[q])^k = \left(1-\left[1-\frac{1}{m}\right]^{kn}\right)^k \approx \left( 1-e^{-kn/m} \right)^k</math>
as before.

### Optimal number of hash functions
The number of hash functions, k, must be a positive integer.  Putting this constraint aside, for a given m and n, the value of k that minimizes the false positive probability is

:<math>k = \frac{m}{n} \ln 2.</math>

The required number of bits, m, given n (the number of inserted elements) and a desired false positive probability ε (and assuming the optimal value of k is used) can be computed by substituting the optimal value of k in the probability expression above:
:<math>\varepsilon = \left( 1-e^{-(\frac m n \ln 2) \frac n m} \right)^{\frac m n\ln 2}=\left(\frac 1 2 \right)^{\frac m n\ln 2}</math>
which can be simplified to:
:<math>\ln (\varepsilon) = -\frac{m}{n}\ln(2)^2.</math>
This results in:
:<math>m=-\frac{n\ln(\varepsilon)}{\ln (2)^2}</math>
So the optimal number of bits per element is
:<math>\frac{m}{n}=-\frac{\ln(\varepsilon)}{\ln (2)^2}\approx-2.08\ln(\varepsilon)</math>
with the corresponding number of hash functions k (ignoring integrality):
:<math>k=-\frac{\ln (\varepsilon)}{\ln(2)}. </math>

This means that for a given false positive probability ε, the length of a Bloom filter m is proportionate to the number of elements being filtered n and the required number of hash functions only depends on the target false positive probability ε.

The formula <math>m=-\frac{n\ln\varepsilon}{(\ln 2)^2}</math> is approximate for three reasons.  First, and of least concern, it approximates
<math>1 - \frac{1}{m}</math> as <math>e^{-\frac{1}{m}}</math>, which is a good asymptotic approximation (i.e., which holds as m →∞).  Second, of more concern, it assumes that during the membership test the event that one tested bit is set to 1 is independent of the event that any other tested bit is set to 1.  Third, of most concern, it assumes that <math>k = \frac{m}{n} \ln 2</math> is fortuitously integral.

Goel and Gupta, however, give a rigorous upper bound that makes no approximations and requires no assumptions.  They show that the false positive probability for a finite Bloom filter with m bits (<math> m > 1</math>), n elements, and k hash functions is at most

:<math>\varepsilon \leq \left( 1-e^{-\frac{k(n+0.5)}{m-1}} \right)^k.</math>

This bound can be interpreted as saying that the approximate formula <math>\left( 1-e^{-\frac{kn}m} \right)^k</math> can be applied at a penalty of at most half an extra element and at most one less bit.

## Approximating the number of items in a Bloom filter

The number of items in a Bloom filter can be approximated with the following formula,

:<math> n^* = -\frac{m}{k} \ln \left[ 1 - \frac{X}{m} \right], </math>

where <var><math>n^*</math></var> is an estimate of the number of items in the filter, <var>m</var> is the length (size) of the filter, <var>k</var> is the number of hash functions, and <var>X</var> is the number of bits set to one.

### The union and intersection of sets

Bloom filters are a way of compactly representing a set of items. It is common to try to compute the size of the intersection or union between two sets. Bloom filters can be used to approximate the size of the intersection and union of two sets. For two Bloom filters of length , their counts, respectively can be estimated as

:<math> n(A^*) = -\frac{m}{k} \ln \left[ 1 - \frac{|A|} m \right] </math>

and

:<math> n(B^*) = -\frac{m}{k} \ln \left[ 1 - \frac{|B|} m \right]. </math>

The size of their union can be estimated as

:<math> n(A^*\cup B^*) = -\frac{m}{k} \ln \left[ 1 - \frac{|A \cup B|} m \right], </math>

where <math>n(A \cup B)</math> is the number of bits set to one in either of the two Bloom filters.  Finally, the intersection can be estimated as

:<math> n(A^*\cap B^*) = n(A^*) + n(B^*) - n(A^* \cup B^*),</math>

using the three formulas together.
*The servers of Akamai Technologies, a content delivery provider, use Bloom filters to prevent "one-hit-wonders" from being stored in its disk caches. One-hit-wonders are web objects requested by users just once, something that Akamai found applied to nearly three-quarters of their caching infrastructure. Using a Bloom filter to detect the second request for a web object and caching that object only on its second request prevents one-hit wonders from entering the disk cache, significantly reducing disk workload and increasing disk cache hit rates.
* Google Bigtable, Apache HBase, Apache Cassandra, ScyllaDB and PostgreSQL use Bloom filters to reduce the disk lookups for non-existent rows or columns. Avoiding costly disk lookups considerably increases the performance of a database query operation.
* The Google Chrome web browser previously used a Bloom filter to identify malicious URLs. Any URL was first checked against a local Bloom filter, and only if the Bloom filter returned a positive result was a full check of the URL performed (and the user warned, if that too returned a positive result).
* Mozilla Firefox uses cascading Bloom filters for Certificate Revocation and for blocking malicious addons.
* Microsoft Bing (search engine) uses multi-level hierarchical Bloom filters for its search index, BitFunnel. Bloom filters provided lower cost than the previous Bing index, which was based on inverted files.
* The Squid Web Proxy Cache uses Bloom filters for cache digests.
* Bitcoin used Bloom filters to speed up wallet synchronization until privacy vulnerabilities with the implementation of Bloom filters were discovered.
* The Venti archival storage system uses Bloom filters to detect previously stored data.
* The SPIN model checker uses Bloom filters to track the reachable state space for large verification problems.
* The Cascading analytics framework uses Bloom filters to speed up asymmetric joins, where one of the joined data sets is significantly larger than the other (often called Bloom join in the database literature).
* The Exim mail transfer agent (MTA) uses Bloom filters in its rate-limit feature.
* Medium uses Bloom filters to avoid recommending articles a user has previously read.
* Ethereum uses Bloom filters for quickly finding logs on the Ethereum blockchain.
* Grafana Tempo uses Bloom filters to improve query performance by storing bloom filters for each backend block. These are accessed on each query to determine the blocks containing data that meets the supplied sear
