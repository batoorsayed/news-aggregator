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
┌─────────┐     ┌─────────▼─────────┐     ┌─────────┐
│  Timer  │───▶│  Azure Function   │───▶│WordPress│
│ Trigger │     │     (Python)      │     │   Site  │
└─────────┘     └─────────▲─────────┘     └─────────┘
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

1. **[Timer](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L152)** triggers **[Function](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L155C1-L155C4)** daily
2. **Function** [fetches articles from **NewsAPI**](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L204)
3. **Function** [sends articles to **AI Summary**](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L246)
4. **Function** [stores results in **Database**](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L261)
5. **Function** posts formatted ([step 1](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L284), [step 2](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L309)) content to **[WordPress](https://github.com/batoorsayed/news-aggregator/blob/3e0046ba09451c09c8f35379c379ae3f242b46d1/function_app.py#L309)**  (for now its [batoorsayed.com/daily-headlines](https://www.batoorsayed.com/daily-headlines/))
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
- [ ] Root cause analysis & historical context
- [ ] Add more sources (? maybe NewsAPI is enough)
- [ ] Set up a proper domain
