# Data Models

## Supported Data Models Called Out In Docs

- document
- graph and record links
- vector
- full-text search
- time-series
- geospatial

SurrealDB’s pitch is not “pick exactly one forever” but combine these inside one database and query language.

## Selection Heuristics

- nested, flexible records -> document
- highly connected traversals and relationship metadata -> graph
- semantic similarity / embeddings / RAG -> vector
- lexical keyword/text ranking -> full-text search
- ordered event streams / measurements -> time-series
- coordinates / spatial queries -> geospatial

## Document Model

Think in records with nested objects and arrays.

Use when:

- most reads are centered on one aggregate/object
- nested data belongs naturally to one entity
- you want flexible shape and straightforward retrieval

Typical SurrealDB shape:

```surql
CREATE product:1 CONTENT {
  name: "Apple",
  details: {
    color: "red",
    nutrition: { calories: 52 }
  },
  tags: ["fruit", "fresh"]
};
```

## Graph Model

Docs frame graphs as nodes plus edges, where edges are first-class and can hold their own properties.

Use when:

- relationships matter as much as entities
- you need traversal queries
- edge metadata matters, such as timestamp, quantity, strength, status

Typical edge:

```surql
RELATE person:brian->order->product:crystal_cave
  SET quantity = 2;
```

Querying through graph edges:

```surql
SELECT ->wrote->post.* AS userPosts
FROM users:alice;
```

## Record Links Vs Graph Edges

Docs explicitly distinguish these.

### Record links

- simple pointer from one record to another
- efficient direct link
- good when a unidirectional field reference is enough

Example:

```surql
UPDATE user:one SET comments += comment:abc;
SELECT comments.{ created_at, text } FROM user:one;
```

### Graph edges

- use `RELATE`
- relationship becomes a real table
- can store edge properties
- better for explicit bidirectional traversal and relationship semantics

Rule of thumb:

- use record links for lightweight references
- use graph edges when the relationship itself has meaning or data

## Vector Model

Docs frame vectors as high-dimensional embeddings used for semantic similarity search.

Use when:

- recommendation/search is semantic rather than exact keyword
- storing embeddings from text, images, audio, or structured features
- building AI retrieval or similarity systems

Storage shape:

```surql
CREATE Document:1 CONTENT {
  items: [{
    content: "apple",
    embedding: [0.00995, -0.02680, -0.01881, -0.08697]
  }]
};
```

Docs emphasize:

- embedding generation happens outside the DB
- embedding length is flexible but larger vectors cost more
- vector functions exist under `vector::...`

### Vector search choices

- brute force: exact, simpler, good for small datasets
- HNSW index: approximate nearest neighbor, faster on larger/high-dimensional data

Example HNSW index:

```surql
DEFINE INDEX mt_pts ON liquidsVector
FIELDS embedding
HNSW DIMENSION 4 DIST COSINE TYPE F32;
```

Example distance reuse:

```surql
SELECT id, vector::distance::knn() AS distance
FROM actor
WHERE embedding <|2,40|> $person_embedding
ORDER BY distance;
```

## Full-Text Search

Use when:

- exact terms, stemming, tokenization, BM25 ranking matter
- ambiguity is acceptable or even useful
- lexical search quality matters more than semantic similarity

Docs position FTS as analyzer/tokenizer/filter driven.

Typical setup:

```surql
DEFINE ANALYZER liquid_analyzer TOKENIZERS blank,class,camel,punct FILTERS snowball(english);
DEFINE INDEX liquid_content ON liquids FIELDS content FULLTEXT ANALYZER liquid_analyzer BM25 HIGHLIGHTS;
```

Rule of thumb:

- full-text search for lexical relevance
- vector search for semantic similarity
- combine both when needed

## Time-Series

The multi-model overview includes time-series as a first-class use case.

Use when:

- records are naturally ordered by time
- measurements/events/log-style writes dominate
- queries frequently slice by timestamp windows

In practice, pair this with:

- explicit datetime fields
- indexes suited to time-range access
- retention/aggregation logic in application or SurrealQL

## Geospatial

Use when:

- data contains coordinates/shapes
- you need spatial relationships or filtering

The docs position geospatial as another native model rather than a separate store.

## Practical Advice

- Start with the query pattern, not ideology.
- If the same entity needs nested state plus graph relations plus embeddings, keep them in one SurrealDB design rather than splitting stores by habit.
- When uncertain between graph edges and record links, ask whether the relation needs its own fields and traversal semantics.
- When uncertain between full-text and vector, ask whether the user means keyword match or semantic match.
