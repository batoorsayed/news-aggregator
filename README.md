# news-aggregator
Aggregates news articles from various sources and provides historical context and root cause analysis using AI.

## Goal
- News aggregation from multiple trusted sources.
    - Daily
- Summarization of articles using NLP.
- Historical context generation for each article.
- Root cause analysis for each article.
- Related articles and sources.
- Display of information.
    - Blog-like interface
    - RSS feed
    - Newsletters

### Architecture
```
                    ┌─────────┐
                    │NewsAPI  │
                    │         │
                    └────┬────┘
                         │
┌─────────┐    ┌─────────▼─────────┐    ┌─────────┐
│  Timer  │───▶│  Azure Function   │───▶│WordPress│
│ Trigger │    │     (Python)      │    │   Site  │
└─────────┘    └─────────┬─────────┘    └─────────┘
                         │
                    ┌────▼──────┐
                    │Azure      │
                    │Abstractive│
                    │Summary    │
                    └───────────┘
                         │
                    ┌────▼────┐
                    │Database │
                    │(Cosmos) │
                    └─────────┘
```

### Flow Description

1. **Timer** triggers **Function** daily
2. **Function** fetches articles from **NewsAPI**
3. **Function** sends articles to **AI Summary**
4. **Function** stores results in **Database**
5. **Function** posts formatted content to **WordPress**
6. **Users** read the daily digest


## Plan
### Phase 1: Skeleton
- [x] Fetch sample articles from NewsAPI SDK
- [x] Summarize using Foundry SDK
- [x] Initially to a text file -> save to db

### Phase 2: Backend
- [x] DB

### Phase 3: Frontend
- [x] RSS Feed
- [ ] Newsletter
- [x] Blog

### Phase 4: Feature Completion
- [x] Daily automation
- Root cause analysis & historical context
- Add more sources (? maybe NewsAPI is enough)
