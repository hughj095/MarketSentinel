# MarketSentinel
Agentic AI network that monitors the markets (DJIA, Nasdaq, S&amp;P500) and economic news

This repository contains modular AI agents for stock market monitoring and analysis. The system architecture is as follows:

# AI Trading Agent Architecture (Mermaid)

```mermaid
flowchart TD
    A[Agent 1: Market Scanner] --> B[Edge Processor / Integrator]
    C[Agent 2: News Scanner] --> B
    B --> D[LLM / Decision Maker]
    D --> E[Structured Insights / Suggested Actions JSON]

    subgraph Agents
        A
        C
    end

    subgraph Edge
        B
    end

    subgraph AI
        D
    end

    subgraph Output
        E
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#bfb,stroke:#333,stroke-width:2px
    style E fill:#ffb,stroke:#333,stroke-width:2px
