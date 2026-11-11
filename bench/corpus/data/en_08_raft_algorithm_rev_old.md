Raft is a consensus algorithm designed as an alternative to the Paxos family of algorithms. It was meant to be more understandable than Paxos by means of separation of logic, but it is also formally proven safe and offers some additional features.

Raft is Byzantine fault tolerant; the nodes trust the elected leader, and the algorithm assumes all participants are trustworthy.

## Basics
Raft achieves consensus via an elected leader. A server in a raft cluster is either a leader or a follower, and can be a candidate in the precise case of an election (leader unavailable). The leader is responsible for log replication to the followers. It regularly informs the followers of its existence by sending a heartbeat message. Each follower has a timeout (typically between 150 and 300 ms) in which it expects the heartbeat from the leader. The timeout is reset on receiving the heartbeat. If no heartbeat is received the follower changes its status to candidate and starts a leader election.

Given server configuration C<sub>old</sub>, the old server configuration, and C<sub>new</sub>, the new configuration:

# New servers with no log entries. Raft introduces a phase before the configuration change where servers with no log entries are not considered part of the majority in elections, but they will have entries replicated to them. This happens until the server is fully caught up with entries.

### Issues
While Raft aims to be an alternative of Paxos and more understandable than Paxos, several issues arise.

#### Leader Bottleneck
Raft uses a single leader model, where client requests, reads and writes, and log replications goes through a single leader. This means that there is a single point of failure and a bottleneck in performance. Furthermore, it does not scale with increasing server workload.

#### Reconfiguration
Raft's membership change system has not been formally verified to be correct. This means that implementing it is very risky, as there can be many potential bugs and errors. Diego Ongaro, one of the co-authors, has tried to create a formal safety proof, but there are no plans to continue developing it due to how complicated it is. In 2014, a safety bug was found relating to single server membership changes. This means that Raft is not a Byzantine fault tolerant algorithm. A 2023 study found that blockchain systems based on Raft are vulnerable to Byzantine attacks because of the lack of authentication on the client side.

## Extensions

The dissertation “Consensus: Bridging Theory and Practice” by one of the co-authors of the original paper describes extensions to the original algorithm:

* Pre-Vote: when a member rejoins the cluster, it can depending on timing trigger an election although there is already a leader. To avoid this, pre-vote will first check in with the other members. Avoiding the unnecessary election improves the availability of cluster, therefore this extension is usually present in production implementations.
* Leadership transfer: a leader that is shutting down orderly can explicitly transfer the leadership to another member. This can be faster than waiting for a timeout. Also, a leader can step down when another member would be a better leader, for example when that member is on a faster machine.

## Production use of Raft
* CockroachDB uses Raft in the Replication Layer.
* Etcd uses Raft to manage a highly-available replicated log
* Hazelcast uses Raft to provide its CP Subsystem, a strongly consistent layer for distributed data structures.
* IBM MQ uses Raft to manage a highly-available replicated log.
* MongoDB uses a variant of Raft in the replication set.
* Neo4j uses Raft to ensure consistency and safety.
* RabbitMQ uses Raft to implement durable, replicated FIFO queues.
* ScyllaDB uses Raft for metadata (schema and topology changes)
* Splunk Enterprise uses Raft in a Search Head Cluster (SHC)
* TiDB uses Raft with the storage engine TiKV.
* YugabyteDB uses Raft in the DocDB Replication
* ClickHouse uses Raft for in-house implementation of ZooKeeper-like service
* Redpanda uses the Raft consensus algorithm for data replication
* Apache Kafka Raft (KRaft) uses Raft for metadata management.
* NATS Messaging uses the Raft consensus algorithm for Jetstream cluster management and data replication
* Camunda uses the Raft consensus algorithm for data replication

## References

## External links
*

Category:Distributed algorithms
Category:Fault-tolerant computer systems

