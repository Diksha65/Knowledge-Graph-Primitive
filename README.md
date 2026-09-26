# knowledge-graph-primitives

A minimal knowledge graph engine built on Neo4j and Python. The pipeline ingests structured financial intelligence (executives, documents, companies, acquisitions) into a graph database and traverses multi-hop relationships to surface actionable insights — e.g. "who is the CEO of the company that acquired the startup mentioned in this compliance report?"

---

## Project Structure

```
alphafund-graph/
├── docker-compose.yml      # Neo4j service definition
└── ingestion_pipeline.py   # Graph engine, ingestion, and traversal
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.10+
- `pip` or a virtual environment manager

---

## Setup

### 1. Start Neo4j with Docker

From the `alphafund-graph/` directory:

```bash
cd alphafund-graph
docker compose up -d
```

This starts a Neo4j 5.18.0 container (`alphafund_graph_db`) with:

| Port | Purpose |
|------|---------|
| `7474` | Neo4j Browser (HTTP web UI) |
| `7687` | Bolt protocol (Python driver) |

Credentials are pre-configured:
- **Username:** `neo4j`
- **Password:** `AlphaFund2026!`

Data is persisted locally under `alphafund-graph/neo4j_data/`.

To stop the container:

```bash
docker compose down
```

To verify the container is running:

```bash
docker ps
```

### 2. Verify Neo4j is Ready

Open the Neo4j Browser at [http://localhost:7474](http://localhost:7474) and log in with the credentials above. Wait until the UI loads before running the pipeline (startup takes ~15–20 seconds on first launch).

### 3. Install Python Dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install neo4j
```

### 4. Run the Ingestion Pipeline

```bash
cd alphafund-graph
python ingestion_pipeline.py
```

---

## What the Pipeline Does

The pipeline runs four sequential phases:

**Phase 1 — Connect**
Opens a Bolt connection to Neo4j at `bolt://127.0.0.1:7687`.

**Phase 2 — Constraints**
Creates uniqueness constraints on the three core node labels to prevent duplicate entities:
- `Company.name`
- `Executive.name`
- `Document.title`

**Phase 3 — Ingest**
Merges a sample financial intelligence payload into the graph using idempotent `MERGE` operations:

| Node | Value |
|------|-------|
| Executive | Tony |
| Document | Q3 Compliance Report |
| Company | Alpha AI (startup) |
| Company | Microsoft (acquirer) |
| Executive | Satya Nadella |

Relationships created:

```
Tony -[:WROTE]-> Q3 Compliance Report
Q3 Compliance Report -[:MENTIONS]-> Alpha AI
Microsoft -[:ACQUIRED]-> Alpha AI
Satya Nadella -[:WORKS_FOR {role: 'CEO'}]-> Microsoft
```

**Phase 4 — Traversal**
Executes a 4-hop graph traversal starting from `Tony` to answer the question:
> "Who is the CEO of the company that acquired the startup Tony wrote about?"

Query path:
```
(Tony) -[WROTE]-> (Document) -[MENTIONS]-> (Startup) <-[ACQUIRED]- (Parent) <-[WORKS_FOR]- (CEO)
```

Expected output:

```
Target Found: Satya Nadella (CEO of Microsoft)
```

---

## Key Design Decisions

- **Pinned image version** (`neo4j:5.18.0`) — avoids breaking changes from `latest`.
- **APOC plugin enabled** — required for future LLM-integrated graph operations (export/import procedures).
- **`MERGE` over `CREATE`** — makes ingestion idempotent; safe to re-run without creating duplicate nodes.
- **`execute_read` result consumed inside transaction** — prevents `ResultConsumedError` when the session closes before data is accessed.
