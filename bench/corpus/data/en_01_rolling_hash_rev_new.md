A rolling hash (also known as recursive hashing or rolling checksum) is a hash function where the input is hashed in a window that moves through the input.

A few hash functions allow a rolling hash to be computed very quickly—the new hash value is rapidly calculated given only the old hash value, the old value removed from the window, and the new value added to the window—similar to the way a moving average function can be computed much more quickly than other low-pass filters; and similar to the way a Zobrist hash can be rapidly updated from the old hash value.

One of the main applications is the Rabin–Karp string search algorithm, which uses the rolling hash described below. Another popular application is the rsync program, which uses a checksum based on Mark Adler's adler-32 as its rolling hash. Low Bandwidth Network Filesystem (LBFS) uses a Rabin fingerprint as its rolling hash. FastCDC (Fast Content-Defined Chunking) uses a compute-efficient Gear fingerprint as its rolling hash.

At best, rolling hash values are pairwise independent or strongly universal. They cannot be 3-wise independent, for example.

## Polynomial rolling hash

The Rabin–Karp string search algorithm is often explained using a rolling hash function that only uses multiplications and additions:
:<math>H = c_1 a^{k-1} + c_2 a^{k-2} + c_3 a^{k-3} + ... + c_k a^{0}</math>,
where <math>a</math> is a constant, and <math>c_1, ..., c_k</math> are the input characters (but this function is not a Rabin fingerprint, see below).

In order to avoid manipulating huge <math>H</math> values, all math is done modulo <math>n</math>. The choice of <math>a</math> and <math>n</math> is critical to get good hashing; in particular, the modulus <math>n</math> is typically a prime number.  See linear congruential generator for more discussion.

Removing and adding characters simply involves adding or subtracting the first or last term. Shifting all characters by one position to the left requires multiplying the entire sum <math>H</math> by <math>a</math>. Shifting all characters by one position to the right requires dividing the entire sum <math>H</math> by <math>a</math>. Note that in modulo arithmetic, <math>a</math> can be chosen to have a multiplicative inverse <math>a^{-1}</math> by which <math>H</math> can be multiplied to get the result of the division without actually performing a division.

## Rabin fingerprint

The Rabin fingerprint is another hash, which also interprets the input as a polynomial, but over the Galois field GF(2). Instead of seeing the input as a polynomial of bytes, it is seen as a polynomial of bits, and all arithmetic is done in GF(2) (similarly to CRC-32). The hash is the remainder after the division of that polynomial by an irreducible polynomial over GF(2). It is possible to update a Rabin fingerprint using only the entering and the leaving byte, making it effectively a rolling hash.

Because it shares the same author as the Rabin–Karp string search algorithm, which is often explained with another, simpler rolling hash, and because this simpler rolling hash is also a polynomial, both rolling hashes are often mistaken for each other.

## Cyclic polynomial

Hashing by cyclic polynomial&mdash;sometimes called Buzhash&mdash;is also simple and it has the benefit of avoiding multiplications, using circular shift instead. It is a form of tabulation hashing: it presumes that there is some substitution function <math>s</math> from characters to integers in the interval <math>[0,2^L)</math>, essentially a lookup table (each of the 32 bit-positions of the values of s should be balanced, i.e. have as many 1s as there are 0s). Let the function <math>\operatorname{rol}</math> be bitwise rotation. E.g., <math>\operatorname{rol}(101) = 011</math>. Let <math>\oplus</math> be the bitwise exclusive or. Let <math>c_i</math> be the i-th byte in a stream, and <math>w</math> be the window size in use.

We precalculate <math>s'</math> for removing the contribution of a byte that is out of the window:

## Gear hashing
Gear chunking is another type of tabulation hashing. Let s be an unchanging table of 256 random unsigned 32-bit integers, H be the hash accumulator (unsigned integer, at least 32 bits), and f be the file represented as an array of bytes (8-bit integers, 1-based subscript). Let <math>\ll</math> be the left-shift operator. The recurrence relation is:

: <math>H_0 = 0</math>
: <math>H_i = (H_{i-1} \ll 1) + s[f[i]]</math>

Compared to the cyclic polynomial hash, the left-rotate operation is replaced by left-shift, which removes the need to remove the contribution of an out-of-window byte. Xor is also replaced by addition. Chunking is done based on the top bits of H. This type of chunking generates results comparable with the Rabin fingerprint in one-third of the time.

A simple approach to making dynamic chunks is to calculate a rolling hash, and if the hash value matches an arbitrary pattern (e.g. all zeroes) in the lower N bits (with a probability of <math display="inline">{1 \over 2^n}</math>, given the hash has a uniform probability distribution) then it’s chosen to be a chunk boundary.  Each chunk will thus have an average size of <math display="inline">2^n</math> bytes. This approach ensures that unmodified data (more than a window size away from the changes) will have the same boundaries. Once the boundaries are known, the chunks need to be compared by cryptographic hash value to detect changes.

Such content-defined chunking (CDC) or content-based chunking (CBC) is often used for data deduplication. It uses a 4095-byte window
* Chunking on any collection of bits
** A gear hash.

Content-based chunking has the advantage that in most cases, local changes to a file only affects the chunk it is in and possibly the next chunk, but no other chunk. Different choices of algorithms and hashes offer different strengths of this guarantee.

### Content-based slicing using moving sum

Several programs, including gzip (with the <code>--rsyncable</code> option) and rsyncrypto, do content-based slicing based on this specific (unweighted) moving sum:

:<math>H(n) = \sum_{i = n - 8195}^{n} c_i \mod 4096</math>

where
* <math>c_i</math> is byte <math>i</math> of the file,
* <math>H(n)</math> is a "hash value" consisting of the bottom 12 bits of the sum of 8196 consecutive bytes ending with byte <math>n</math>.

Shifting the window by one byte simply involves adding the new character to the sum and subtracting the oldest character (no longer in the window) from the sum. Because of the properties of modulo arithmetic, the storage required is only 12 bits.

For every <math>n</math> where <math>H(n) == 0</math>, these programs cut the file between <math>n</math> and <math>n+1</math>.

### FastCDC
FastCDC optimizes Gear-based CDC The new scheme approximately doubles the speed over the olg Gear-based algorithm and is 10&times; as fast as the Rabin-based CDC approach.

The basic version pseudocode is provided as follows:

algorithm FastCDC
input: data buffer src,
data length n,
output: cut point i

MinSize &larr; 2KB     // split minimum chunk size is 2 KB
MaxSize &larr; 64KB    // split maximum chunk size is 64 KB
Mask &larr; 0x0000d93003530000 // 13 bits set -> desired average size is 2^13 bytes = 8 KB
fp &larr; 0        // uint64
i &larr; 0

// buffer size is less than minimum chunk size
if n ≤ MinSize then
return n
if n ≥ MaxSize then
n &larr; MaxSize

// Skip the first MinSize bytes, and kickstart the hash
while i < MinSize do
fp &larr; (fp << 1 ) + Gear[src[i]]
i &larr; i + 1

while i < n do
fp &larr; (fp << 1 ) + Gear[src[i]]
if !(fp & Mask) then
return i
i &larr; i + 1

return i

Where the Gear array is equivalent to the s table above.

An advanced version uses two different masks derived from the above Mask, one with 15 set bits and the other with 11 set bits. The former is used when i < 8 KB; afterwards the latter takes over. This tightens the chunk-size distribution around the desired average and improves deduplication.

## Computational complexity

All rolling hash functions can be computed in linear time for the number of characters and updated in constant time when characters are shifted by one position.  In particular, computing the Rabin–Karp rolling hash of a string of length <math>k</math> requires <math>O(k)</math> modular arithmetic operations, and hashing by cyclic polynomials requires <math>O(k)</math> bitwise exclusive ors and circular shifts.

## See also

*
*

## References

## External links
*[https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/recitation-9-rolling-hashes-amortized-analysis/ MIT 6.006: Introduction to Algorithms 2011- Recitation 9 - Rolling Hash]

Category:Hash functions

