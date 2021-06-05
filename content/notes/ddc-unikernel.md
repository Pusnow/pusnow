---
title: Accelerating Disaggregated Data Centers Using Unikernel
---

# Accelerating Disaggregated Data Centers Using Unikernel

**Wonsup Yoon**, Jinyoung Oh, Sue Moon, and Youngjin Kwon

*Proceedings of the ACM SIGCOMM 2020 Conference Posters and Demos (SIGCOMM '20 Posters and Demos)*

2020

## Abstract

Memory disaggregation is a new hardware and system paradigm to split computation and memory into physical separate nodes. Grouping and pooling hardware resources solves the low resource utilization problem and hide intermittent hardware failures in data centers. In this work we propose a unikernel-based remote paging for memory disaggregation. Unikernels allow fast remote paging without mode switching and ease of application-specific customization. Our new memory system allows developers to take full advantage of application domain knowledge in fetching and evicting remote pages. We use RDMA over Infiniband as an efficient data path between a compute node and a memory node. We have built RDMA frontend and backend drivers for our memory system control path. We have added an RDMA mempool manager to manage local pages, a page fault handers to swap in remote pages, and a background thread fo swap out local pages. Finally, we have written 155 LoC of a prefetcher for Redis, a popular in-memory data structure store. In our benchmark our system shows up to 2.9$\times$ higher throughput compared to the state-of-the-art disaggregated memory system, Infiniswap.

[[Link](https://conferences.sigcomm.org/sigcomm/2020/cf-posters.html)]
