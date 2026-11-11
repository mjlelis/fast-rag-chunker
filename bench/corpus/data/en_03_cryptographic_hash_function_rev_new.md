thumb|375px|right|A cryptographic hash function (specifically [[SHA-1) at work. A small change in the input (in the word "over") drastically changes the output (digest). This is called the avalanche effect.]]

A cryptographic hash function (CHF) is a hash algorithm (a map of an arbitrary binary string to a binary string with a fixed size of <math>n</math> bits) that has special properties desirable for cryptographic applications.

Hashing is a one-directional mathematical operation which is quick to calculate, yet hard to reverse.
Common uses include password storage and digital signatures.
Even a small change in the input results in a very different hash, meaning that it functions as an efficient and consistent way to  check if two copies of data or software match.
Typically, the operation works on a block of input data; the hash output is then hashed with the next block, creating a new hash reflecting everything to that point; this action is repeated until the hash reflects everything through the final block. or just hash values, even though all these terms stand for more general functions with rather different properties and purposes.

Non-cryptographic hash functions are used in hash tables and to detect accidental errors; their constructions frequently provide no resistance to a deliberate attack. For example, a denial-of-service attack on hash tables is possible if the collisions are easy to find, as in the case of linear cyclic redundancy check (CRC) functions.

## Properties
Most cryptographic hash functions are designed to take a string of any length as input and produce a fixed-length hash value.

A cryptographic hash function must be able to withstand all known types of cryptanalytic attack. In theoretical cryptography, the security level of a cryptographic hash function has been defined using the following properties:

; Pre-image resistance : Given a hash value , it should be difficult to find any message  such that . This concept is related to that of a one-way function. Functions that lack this property are vulnerable to preimage attacks.
; Second pre-image resistance : Given an input , it should be difficult to find a different input  such that . This property is sometimes referred to as weak collision resistance. Functions that lack this property are vulnerable to second-preimage attacks.
; Collision resistance : It should be difficult to find two different messages  and  such that . Such a pair is called a cryptographic hash collision. This property is sometimes referred to as strong collision resistance. It requires a hash value at least twice as long as that required for pre-image resistance; otherwise, collisions may be found by a birthday attack.

Collision resistance implies second pre-image resistance but does not imply pre-image resistance. The weaker assumption is always preferred in theoretical cryptography, but in practice, a hash-function that is only second pre-image resistant is considered insecure and is therefore not recommended for real applications.

Informally, these properties mean that a malicious adversary cannot replace or modify the input data without changing its digest. Thus, if two strings have the same digest, one can be very confident that they are identical. Second pre-image resistance prevents an attacker from crafting a document with the same hash as a document the attacker cannot control. Collision resistance prevents an attacker from creating two distinct documents with the same hash.

A function meeting these criteria may still have undesirable properties. Currently, popular cryptographic hash functions are vulnerable to length-extension attacks: given  and  but not , by choosing a suitable  an attacker can calculate , where  denotes concatenation. This property can be used to break naive authentication schemes based on hash functions. The HMAC construction works around these problems.

In practice, collision resistance is insufficient for many practical uses. In addition to collision resistance, it should be impossible for an adversary to find two messages with substantially similar digests; or to infer any useful information about the data, given only its digest. In particular, a hash function should behave as much as possible like a random function (often called a random oracle in proofs of security) while still being deterministic and efficiently computable. This rules out functions like the SWIFFT function, which can be rigorously proven to be collision-resistant assuming that certain problems on ideal lattices are computationally difficult, but, as a linear function, does not satisfy these additional properties.

Checksum algorithms, such as CRC-32 and other cyclic redundancy checks, are designed to meet much weaker requirements and are generally unsuitable as cryptographic hash functions. For example, a CRC was used for message integrity in the WEP encryption standard, but an attack was readily discovered, which exploited the linearity of the checksum.

### Degree of difficulty
In cryptographic practice, "difficult" generally means "almost certainly beyond the reach of any adversary who must be prevented from breaking the system for as long as the security of the system is deemed important". The meaning of the term is therefore somewhat dependent on the application since the effort that a malicious agent may put into the task is usually proportional to their expected gain. However, since the needed effort usually multiplies with the digest length, even a thousand-fold advantage in processing power can be neutralized by adding a dozen bits to the latter.

For messages selected from a limited set of messages, for example passwords or other short messages, it can be feasible to invert a hash by trying all possible messages in the set. Because cryptographic hash functions are typically designed to be computed quickly, special key derivation functions that require greater computing resources have been developed that make such brute-force attacks more difficult.

In some theoretical analyses "difficult" has a specific mathematical meaning, such as "not solvable in asymptotic polynomial time". Such interpretations of difficulty are important in the study of provably secure cryptographic hash functions but do not usually have a strong connection to practical security. For example, an exponential-time algorithm can sometimes still be fast enough to make a feasible attack. Conversely, a polynomial-time algorithm (e.g., one that requires  steps for -digit keys) may be too slow for any practical use.

## Illustration
An illustration of the potential use of a cryptographic hash is as follows: Alice poses a tough math problem to Bob and claims that she has solved it. Bob would like to try it himself, but would yet like to be sure that Alice is not bluffing. Therefore, Alice writes down her solution, computes its hash, and tells Bob the hash value (whilst keeping the solution secret). Then, when Bob comes up with the solution himself a few days later, Alice can prove that she had the solution earlier by revealing it and having Bob hash it and then check that it matches the hash value given to him before. (This is an example of a simple commitment scheme; in actual practice, Alice and Bob will often be computer programs, and the secret would be something less easily spoofed than a claimed puzzle solution.)

## Applications

### Verifying the integrity of messages and files

An important application of secure hashes is the verification of message integrity. Comparing message digests (hash digests over the message) calculated before, and after, transmission can determine whether any changes have been made to the message or file.

MD5, SHA-1, or SHA-2 hash digests are sometimes published on websites or forums to allow verification of integrity for downloaded files, including files retrieved using file sharing such as mirroring. This practice establishes a chain of trust as long as the hashes are posted on a trusted site – usually the originating site – authenticated by HTTPS. Using a cryptographic hash and a chain of trust detects malicious changes to the file. Non-cryptographic error-detecting codes such as cyclic redundancy checks only prevent against non-malicious alterations of the file, since an intentional spoof can readily be crafted to have the colliding code value.

### Signature generation and verification

Almost all digital signature schemes require a cryptographic hash to be calculated over the message. This allows the signature calculation to be performed on the relatively small, statically sized hash digest. The message is considered authentic if the signature verification succeeds given the signature and recalculated hash digest over the message. So the message integrity property of the cryptographic hash is used to create secure and efficient digital signature schemes.

### Password verification

Password verification commonly relies on cryptographic hashes. Storing all user passwords as cleartext can result in a massive security breach if the password file is compromised. One way to reduce this danger is to only store the hash digest of each password. To authenticate a user, the password presented by the user is hashed and compared with the stored hash. A password reset method is required when password hashing is performed; original passwords cannot be recalculated from the stored hash value.

However, use of standard cryptographic hash functions, such as the SHA series, is no longer considered safe for password storage.

#### Content-addressable storage

## Hash functions based on block ciphers
There are several methods to use a block cipher to build a cryptographic hash function, specifically a one-way compression function.

The methods resemble the block cipher modes of operation usually used for encryption. Many well-known hash functions, including MD4, MD5, SHA-1 and SHA-2, are built from block-cipher-like components designed for the purpose, with feedback to ensure that the resulting function is not invertible. SHA-3 finalists included functions with block-cipher-like components (e.g., Skein, BLAKE) though the function finally selected, Keccak, was built on a cryptographic sponge instead.

A standard block cipher such as AES can be used in place of these custom block ciphers; that might be useful when an embedded system needs to implement both encryption and hashing with minimal code size or hardware area. However, that approach can have costs in efficiency and security. The ciphers in hash functions are built for hashing: they use large keys and blocks, can efficiently change keys every block, and have been designed and vetted for resistance to related-key attacks. General-purpose ciphers tend to have different design goals. In particular, AES has key and block sizes that make it nontrivial to use to generate long hash values; AES encryption becomes less efficient when the key changes each block; and related-key attacks make it potentially less secure for use in a hash function than for encryption.

## Hash function design

### Merkle–Damgård construction

thumb|450px|right|The Merkle–Damgård hash construction

A hash function must be able to process an arbitrary-length message into a fixed-length output. This can be achieved by breaking the input up into a series of equally sized blocks, and operating on them in sequence using a one-way compression function. The compression function can either be specially designed for hashing or be built from a block cipher. A hash function built with the Merkle–Damgård construction is as resistant to collisions as is its compression function; any collision for the full hash function can be traced back to a collision in the compression function.

The last block processed should also be unambiguously length padded; this is crucial to the security of this construction. This construction is called the Merkle–Damgård construction. Most common classical hash functions, including SHA-1 and MD5, take this form.

### Wide pipe versus narrow pipe <span class="anchor" id="wide pipe"></span><span class="anchor" id="narrow pipe"></span>
A straightforward application of the Merkle–Damgård construction, where the size of hash output is equal to the internal state size (between each compression step), results in a narrow-pipe hash design. This design causes many inherent flaws, including length-extension, multicollisions, long message attacks, generate-and-paste attacks, and also cannot be parallelized. As a result, modern hash functions are built on wide-pipe constructions that have a larger internal state size – which range from tweaks of the Merkle–Damgård construction None of the entrants in the NIST hash function competition use a classical Merkle–Damgård construction.

Meanwhile, truncating the output of a longer hash, such as used in SHA-512/256, also defeats many of these attacks.

## Use in building other cryptographic primitives
Hash functions can be used to build other cryptographic primitives. For these other primitives to be cryptographically secure, care must be taken to build them correctly.

Message authentication codes (MACs) (also called keyed hash functions) are often built from hash functions. HMAC is such a MAC.

Just as block ciphers can be used to build hash functions, hash functions can be used to build block ciphers.  Luby-Rackoff constructions using hash functions can be provably secure if the underlying hash function is secure.  Also, many hash functions (including SHA-1 and SHA-2) are built by using a special-purpose block cipher in a Davies–Meyer or other construction.  That cipher can also be used in a conventional mode of operation, without the same security guarantees; for example, SHACAL, BEAR and LION.

Pseudorandom number generators (PRNGs) can be built using hash functions.  This is done by combining a (secret) random seed with a counter and hashing it.

Some hash functions, such as Skein, Keccak, and RadioGatún, output an arbitrarily long stream and can be used as a stream cipher, and stream ciphers can also be built from fixed-length digest hash functions. Often this is done by first building a cryptographically secure pseudorandom number generator and then using its stream of random bytes as keystream. SEAL is a stream cipher that uses SHA-1 to generate internal tables, which are then used in a keystream generator more or less unrelated to the hash algorithm.  SEAL is not guaranteed to be as strong (or weak) as SHA-1. Similarly, the key expansion of the HC-128 and HC-256 stream ciphers makes heavy use of the SHA-256 hash function.

## Concatenation

Concatenating outputs from multiple hash functions provide collision resistance as good as the strongest of the algorithms included in the concatenated result.  For example, older versions of Transport Layer Security (TLS) and Secure Sockets Layer (SSL) used concatenated MD5 and SHA-1 sums. This ensures that a method to find collisions in one of the hash functions does not defeat data protected by both hash functions.

For Merkle–Damgård construction hash functions, the concatenated function is as collision-resistant as its strongest component, but not more collision-resistant. Antoine Joux observed that 2-collisions lead to -collisions: if it is feasible for an attacker to find two messages with the same MD5 hash, then they can find as many additional messages with that same MD5 hash as they desire, with no greater difficulty. Among those  messages with the same MD5 hash, there is likely to be a collision in SHA-1. The additional work needed to find the SHA-1 collision (beyond the exponential birthday search) requires only polynomial time.

## Cryptographic hash algorithms

There are many cryptographic hash algorithms; this section lists a few algorithms that are referenced relatively often. A more extensive list can be found on the page containing a comparison of cryptographic hash functions.

### MD5

MD5 was designed by Ronald Rivest in 1991 to replace an earlier hash function, MD4, and was specified in 1992 as RFC 1321. Collisions against MD5 can be calculated within seconds, which makes the algorithm unsuitable for most use cases where a cryptographic hash is required. MD5 produces a digest of 128 bits (16 bytes).

### SHA-1

SHA-1 was developed as part of the U.S. Government's Capstone project. The original specification – now commonly called SHA-0 – of the algorithm was published in 1993 under the title Secure Hash Standard, FIPS PUB 180, by U.S. government standards agency NIST (National Institute of Standards and Technology). It was withdrawn by the NSA shortly after publication and was superseded by the revised version, published in 1995 in FIPS&nbsp; PUB&nbsp;180-1 and commonly designated SHA-1. Collisions against the full SHA-1 algorithm can be produced using the shattered attack and the hash function should be considered broken. SHA-1 produces a hash digest of 160 bits (20 bytes).

Documents may refer to SHA-1 as just "SHA", even though this may conflict with the other Secure Hash Algorithms such as SHA-0, SHA-2, and SHA-3.

### RIPEMD-160

RIPEMD (RACE Integrity Primitives Evaluation Message Digest) is a family of cryptographic hash functions developed in Leuven, Belgium, by Hans Dobbertin, Antoon Bosselaers, and Bart Preneel at the COSIC research group at the Katholieke Universiteit Leuven, and first published in 1996. RIPEMD was based upon the design principles used in MD4 and is similar in performance to the more popular SHA-1. RIPEMD-160 has, however, not been broken.  As the name implies, RIPEMD-160 produces a hash digest of 160 bits (20 bytes).

### Whirlpool

Whirlpool is a cryptographic hash function designed by Vincent Rijmen and Paulo S. L. M. Barreto, who first described it in 2000. Whirlpool is based on a substantially modified version of the Advanced Encryption Standard (AES). Whirlpool produces a hash digest of 512 bits (64 bytes).

### SHA-2

SHA-2 (Secur
