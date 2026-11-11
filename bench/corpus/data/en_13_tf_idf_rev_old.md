In information retrieval, tf–idf (term frequency–inverse document frequency, TF*IDF, TFIDF, TF–IDF, or Tf–idf) is a measure of importance of a word to a document in a collection or corpus, adjusted for the fact that some words appear more frequently in general. Like the bag-of-words model, it models a document as a multiset of words, without word order. It is a refinement over the simple bag-of-words model, by allowing the weight of words to depend on the rest of the corpus.

It was often used as a weighting factor in searches of information retrieval, text mining, and user modeling. A survey conducted in 2015 showed that 83% of text-based recommender systems in digital libraries used tf–idf. Variations of the tf–idf weighting scheme were often used by search engines as a central tool in scoring and ranking a document's relevance given a user query.

One of the simplest ranking functions is computed by summing the tf–idf for each query term; many more sophisticated ranking functions are variants of this simple model.

## Motivations
Karen Spärck Jones (1970) conceived a statistical interpretation of term-specificity called Inverse Document Frequency (idf), which became a cornerstone of term weighting:
For example, the df (document frequency) and idf for some words in Shakespeare's 37 plays might be represented as follows:

! Word
! df
! idf

In the example above, "Romeo", "Falstaff", and "salad" appears in very few plays; since only a handful of plays contain them, their appearance would significantly narrow down the possible list of plays. In contrast, "good" and "sweet" appear in every play and are completely uninformative as to which play it is.

## Definition

# The tf–idf is the product of two statistics, term frequency and inverse document frequency. There are various ways for determining the exact values of both statistics.
# A formula that aims to define the importance of a keyword or phrase within a document or a web page.

! weighting scheme
! tf weight

### Term frequency

Term frequency, , is the relative frequency of term  within document ,
:<math> \mathrm{tf}(t,d) = \frac{f_{t,d}}{{\sum_{t' \in d}{f_{t',d}}}}</math>,
where  is the raw count of a term in a document, i.e., the number of times that term  occurs in document . Note the denominator is simply the total number of terms in document  (counting each occurrence of the same term separately). There are various other ways to define term frequency:

* the raw count itself:
* Boolean "frequencies":  if  occurs in  and 0 otherwise;
* logarithmically scaled frequency: ;
* augmented frequency, to prevent a bias towards longer documents, e.g. raw frequency divided by the raw frequency of the most frequently occurring term in the document:
:<math>\mathrm{tf}(t,d) = 0.5 + 0.5 \cdot  \frac{f_{t, d}}{\max\{f_{t', d}:t' \in d\}}</math>

### Inverse document frequency

! weighting scheme
! idf weight (<math>n_t = |\{d \in D: t \in d\}| </math>)

thumb|Plot of different inverse document frequency functions: standard, smooth, probabilistic.

The inverse document frequency is a measure of how much information the word provides, i.e., how common or rare it is across all documents. It is the logarithmically scaled inverse fraction of the documents that contain the word (obtained by dividing the total number of documents by the number of documents containing the term, and then taking the logarithm of that quotient):

:<math> \mathrm{idf}(t, D) =  \log \frac{N}{n_t}</math>

with
* <math>D</math>: is the set of all documents in the corpus
* <math>N = {|D|}</math>: total number of documents in the corpus
* <math> n_t = |\{d \in D: t \in d\}| </math> : number of documents where the term <math> t </math> appears (i.e., <math> \mathrm{tf}(t,d) \neq 0</math>). If the term is not in the corpus, this will lead to a division-by-zero. It is therefore common to adjust the numerator to <math>1 + N</math> and the denominator to <math>1 + n_t</math>.

### Term frequency–inverse document frequency

! weighting scheme
!tf-idf

Then tf–idf is calculated as

:<math>\mathrm{tfidf}(t,d,D) = \mathrm{tf}(t,d) \cdot \mathrm{idf}(t, D)</math>

A high weight in tf–idf is reached by a high term frequency (in the given document) and a low document frequency of the term in the whole collection of documents; the weights hence tend to filter out common terms. Since the ratio inside the idf's log function is always greater than or equal to 1, the value of idf (and tf–idf) is greater than or equal to 0. As a term appears in more documents, the ratio inside the logarithm approaches 1, bringing the idf and tf–idf closer to 0.

## Justification of idf
Idf was introduced as "term specificity" by Karen Spärck Jones in a 1972 paper. Although it has worked well as a heuristic, its theoretical foundations have been troublesome for at least three decades afterward, with many researchers trying to find information theoretic justifications for it.

Spärck Jones's own explanation did not propose much theory, aside from a connection to Zipf's law. by estimating the probability that a given document  contains a term  as the relative document frequency,

:<math>
P(t|D) = \frac{|\{d \in D: t \in d\}|}{N},
</math>

so that we can define idf as

:<math>
\begin{align}
\mathrm{idf} & = -\log P(t|D) \\
& = \log \frac{1}{P(t|D)} \\
& = \log \frac{N}{|\{d \in D: t \in d\}|}
\end{align}
</math>

Namely, the inverse document frequency is the logarithm of "inverse" relative document frequency.

This probabilistic interpretation in turn takes the same form as that of self-information. However, applying such information-theoretic notions to problems in information retrieval leads to problems when trying to define the appropriate event spaces for the required probability distributions: not only documents need to be taken into account, but also queries and terms.

The conditional entropy of a "randomly chosen" document in the corpus <math>D</math>, conditional to the fact it contains a specific term <math>t</math> (and assuming that all documents have equal probability to be chosen) is:

:<math>
H({\cal D}|{\cal T}=t)=-\sum_d p_{d|t}\log p_{d|t}=-\log \frac{1}{|\{d \in D: t \in d\}|}=\log \frac{|\{d \in D: t \in d\}|}{|D|} + \log |D|=-\mathrm{idf}(t)+\log |D|
</math>

In terms of notation, <math>{\cal D}</math> and <math>{\cal T}</math> are "random variables" corresponding to respectively draw a document or a term. The mutual information can be expressed as

:<math>
M({\cal T};{\cal D}) = H({\cal D}) - H({\cal D}|{\cal T}) = \sum_t p_t\cdot(H({\cal D}) - H({\cal D}|W=t))=\sum_t p_t \cdot \mathrm{idf}(t)
</math>

The last step is to expand <math>p_t</math>, the unconditional probability to draw a term, with respect to the (random) choice of a document, to obtain:

:<math>
M({\cal T};{\cal D})=\sum_{t,d} p_{t|d}\cdot p_d \cdot \mathrm{idf}(t) =  \sum_{t,d} \mathrm{tf}(t,d)\cdot \frac{1}{|D|}\cdot \mathrm{idf}(t) = \frac{1}{|D|} \sum_{t,d} \mathrm{tf}(t,d)\cdot \mathrm{idf}(t).
</math>

This expression shows that summing the Tf–idf of all possible terms and documents recovers the mutual information between documents and term taking into account all the specificities of their joint distribution. More recently, tf–idf variants were shown to arise as components in the test statistic of a penalized likelihood-ratio test for word burstiness based on a beta-binomial statistical language model. In this framework, the null hypothesis models term occurrences using a binomial distribution, while the alternative hypothesis models word burstiness using a beta-binomial distribution with a gamma-distributed penalty term placed on the beta-binomial precision parameter. The resulting test statistic contains the tf–idf variants binary term frequency–inverse document frequency (btf–idf) and term frequency–inverse collection frequency (tf–icf), thereby establishing a direct connection between tf–idf family term-weighting schemes and statistical hypothesis testing. The authors argued that "if a very uncommon citation is shared by two documents, this should be weighted more highly than a citation made by a large number of documents". In addition, tf–idf was applied to "visual words" with the purpose of conducting object matching in videos, and entire sentences. However, the concept of tf–idf did not prove to be more effective in all cases than a plain tf scheme (without idf). When tf–idf was applied to citations, researchers could find no improvement over a simple citation-count weight that had no idf component.

## Derivatives
A number of term-weighting schemes have derived from tf–idf. One of them is TF–PDF (term frequency * proportional document frequency). TF–PDF was introduced in 2001 in the context of identifying emerging topics in the media. The PDF component measures the difference of how often a term occurs in different domains. Another derivate is TF–IDuF. In TF–IDuF, idf is not calculated based on the document corpus that is to be searched or recommended. Instead, idf is calculated on users' personal document collections. The authors report that TF–IDuF was equally effective as tf–idf but could also be applied in situations when, e.g., a user modeling system has no access to a global document corpus. The DELTA TF-IDF  derivative uses the difference in importance of a term across two specific classes, like positive and negative sentiment. For example, it can assign a high score to a word like "excellent" in positive reviews and a low score to the same word in negative reviews. This helps identify words that strongly indicate the sentiment of a document, potentially leading to improved accuracy in text classification tasks.

## See also

* Word embedding
* Kullback–Leibler divergence
* Latent Dirichlet allocation
* Latent semantic analysis
* Mutual information
* Noun phrase
* Okapi BM25
* PageRank
* Vector space model
* Word count
* SMART Information Retrieval System

## References

*
*
*
*

## External links and suggested reading
* Gensim is a Python library for vector space modeling and includes tf–idf weighting.
* [http://www.codeproject.com/KB/IP/AnatomyOfASearchEngine1.aspx Anatomy of a search engine]
* [http://lucene.apache.org/core/3_6_1/api/all/org/apache/lucene/search/Similarity.html tf–idf and related definitions] as used in Lucene
* [http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfTransformer.html#sklearn.feature_extraction.text.TfidfTransformer TfidfTransformer] in scikit-learn
* [https://www.hpclab.ceid.upatras.gr/tmg/ Text to Matrix Generator (TMG)]  MATLAB toolbox that can be used for various tasks in text mining (TM) specifically  i) indexing, ii) retrieval, iii) dimensionality reduction, iv) clustering, v) classification. The indexing step offers the user the ability to apply local and global weighting methods, including tf–idf.
* [https://www.opinosis-analytics.com/knowledge-base/term-frequency-explained/ Term-frequency explained] Explanation of term-frequency

Category:Statistical natural language processing
Category:Ranking functions
Category:Vector space model

