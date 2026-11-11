In information retrieval, Okapi BM25 (BM is an abbreviation of best matching) is a ranking function used by search engines to estimate the relevance of documents to a given search query. It is based on the probabilistic retrieval framework developed in the 1970s and 1980s by Stephen E. Robertson, Karen Spärck Jones, and others.

The name of the actual ranking function is BM25. The fuller name, Okapi BM25, includes the name of the first system to use it, which was the Okapi information retrieval system, implemented at London's City University in the 1980s and 1990s. BM25 and its newer variants, e.g. BM25F (a version of BM25 that can take document structure and anchor text into account), represent TF-IDF-like retrieval functions used in document retrieval. <math>\text{IDF}(q_i)</math> is the IDF (inverse document frequency) weight of the query term <math>q_i</math>. It is usually computed as:

:<math>\text{IDF}(q_i) = \ln \left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5}+1\right)</math>

where   is the total number of documents in the collection, and <math>n(q_i)</math> is the number of documents containing <math>q_i</math>.

There are several interpretations for IDF and slight variations on its formula. In the original BM25 derivation, the IDF component is derived from the Binary Independence Model.

## IDF information theoretic interpretation
Here is an interpretation from information theory. Suppose a query term <math>q</math> appears in <math>n(q)</math> documents. Then a randomly picked document <math>D</math> will contain the term with probability <math>\frac{n(q)}{N}</math> (where <math>N</math> is again the cardinality of the set of documents in the collection). Therefore, the information content of the message "<math>D</math> contains <math>q</math>" is:

:<math>-\log \frac{n(q)}{N} = \log \frac{N}{n(q)}.</math>

Now suppose we have two query terms <math>q_1</math> and <math>q_2</math>. If the two terms occur in documents entirely independently of each other, then the probability of seeing both <math>q_1</math> and <math>q_2</math> in a randomly picked document <math>D</math> is:

:<math>\frac{n(q_1)}{N} \cdot \frac{n(q_2)}{N},</math>

and the information content of such an event is:

:<math>\sum_{i=1}^{2} \log \frac{N}{n(q_i)}.</math>

With a small variation, this is exactly what is expressed by the IDF component of BM25.

## Modifications
* At the extreme values of the coefficient  BM25 turns into ranking functions known as BM11 (for <math>b=1</math>) and BM15 (for <math>b=0</math>).
* BM25F (or the BM25 model with Extension to Multiple Weighted Fields) is a modification of BM25 in which the document is considered to be composed from several fields (such as headlines, main text, anchor text) with possibly different degrees of importance, term relevance saturation and length normalization. BM25F defines each type of field as a stream, applying a per-stream weighting to scale each stream against the calculated score.

* BM25+ is an extension of BM25. BM25+ was developed to address one deficiency of the standard BM25 in which the component of term frequency normalization by document length is not properly lower-bounded; as a result of this deficiency, long documents which do match the query term can often be scored unfairly by BM25 as having a similar relevancy to shorter documents that do not contain the query term at all. The scoring formula of BM25+ only has one additional free parameter <math>\delta</math> (the default value is ) as compared with BM25:

:<math> \text{score}(D,Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \left[ \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)} + \delta \right]</math>

## References

## General references

*
*
*
*
*

## External links
*

Category:Ranking functions

