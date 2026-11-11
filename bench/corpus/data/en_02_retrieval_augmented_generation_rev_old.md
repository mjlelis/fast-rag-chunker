Retrieval-augmented generation (RAG) is a technique that enables large language models (LLMs) to retrieve and incorporate new information from external data sources. With RAG, LLMs first refer to a specified set of documents, then respond to user queries. These documents supplement information from the LLM's pre-existing training data.

RAG also reduces the need to retrain LLMs with new data, saving on computational and financial costs. The LLM did not "know" or "understand" the context of the title, generating a false statement.

## Process
Retrieval-augmented generation (RAG) enhances large language models (LLMs) by incorporating an information-retrieval mechanism that allows models to access and utilize additional data beyond their original training set. Ars Technica notes that "when new information becomes available, rather than having to retrain the model, all that's needed is to augment the model's external knowledge base with the updated information ("augmentation").

## Improvements
Improvements to the basic process above can be applied at different stages in the RAG flow.

### Encoder
These methods focus on the encoding of text as either dense or sparse vectors. Sparse vectors, which encode the identity of a word, are typically dictionary-length and contain mostly zeros. Dense vectors, which encode meaning, are more compact and contain fewer zeros. Various enhancements can improve the way similarities are calculated in the vector stores (databases).

* Performance improves by optimizing how vector similarities are calculated. Dot products enhance similarity scoring, while approximate nearest neighbor (ANN) searches improve retrieval efficiency over K-nearest neighbors (KNN) searches.
* Accuracy may be improved with Late Interactions, which allow the system to compare words more precisely after retrieval. This helps refine document ranking and improve search relevance.

### Retriever-centric methods
These methods aim to enhance the quality of document retrieval in vector databases:

* Pre-training the retriever using the Inverse Cloze Task (ICT), a technique that helps the model learn retrieval patterns by predicting masked text within documents.
* Reranking techniques can refine retriever performance by prioritizing the most relevant retrieved documents during training.
### Language model

By redesigning the language model with the retriever in mind, a 25-time smaller network can get comparable perplexity as its much larger counterparts.

## Challenges
RAG does not prevent hallucinations in LLMs. According to Ars Technica, "It is not a direct solution because the LLM can still hallucinate around the source material in its response."

On September 2025, Israel paid Clock Tower X $6 million in order to sway public opinion to a more favourable view of the country (hasbara) after support plummeted due to its alleged genocidal conduct during the Gaza war. Clock Tower X used RAG poisoning to flood the information space with sites and content sympathetic to Israel.

## References

</references>

Category:Large language models
Category:Natural language processing
Category:Information retrieval systems
Category:Generative AI

