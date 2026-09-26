from neo4j import GraphDatabase

class AlphaFundGraphEngine:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"[SYSTEM] Connected to Neo4j Engine at {uri} as user '{user}'")

    def close(self):
        self.driver.close()
        print("[SYSTEM] Closed connection to Neo4j Engine")

    def execute_write(self, cypher_query, parameters=None):
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run(cypher_query, parameters).consume())

    def execute_read(self, cypher_query, parameters=None):
        with self.driver.session() as session:
            return session.execute_read(lambda tx: [record.data() for record in tx.run(cypher_query, parameters)])

# Initializing the graph engine with Neo4j connection details
graph_db = AlphaFundGraphEngine(uri="bolt://localhost:7687", user="neo4j", password="password")

# Constraints to ensure uniqueness of nodes based on their identifiers
constraint_queries = [
    "CREATE CONSTRAINT unique_company IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT unique_exec IF NOT EXISTS FOR (e:Executive) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT unique_doc IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS UNIQUE",
]

for query in constraint_queries:
    graph_db.execute_write(query)
    print(f"[SYSTEM] Executed constraint query: {query}")

# Injecting a sample payload into the graph database
graph_payload = {
    "author": "Tony",
    "report_title": "Q3 Compliance Report",
    "startup": "Alpha AI",
    "acquirer": "Microsoft",
    "ceo": "Satya Nadella"
}

# Cypher query to create nodes and relationships based on the payload
ingestion_query = """
MERGE (exec1:Executive {name: $author})
MERGE (doc:Document {title: $report_title})
MERGE (company1:Company {name: $startup})
MERGE (company2:Company {name: $acquirer})
MERGE (exec2:Executive {name: $ceo})
MERGE (exec1)-[:WROTE]->(doc)
MERGE (doc)-[:MENTIONS]->(company1)
MERGE (company2)-[:ACQUIRED]->(company1)
MERGE (exec2)-[:WORKS_FOR {role: 'CEO'}]->(company2)
"""

# Execute the ingestion query with the provided payload
graph_db.execute_write(ingestion_query, graph_payload)


# Traversal query to find the CEO of the acquiring company based on the document authored by Tony
traversal_query = """
MATCH (start:Executive {name: 'Tony'})
      -[w:WROTE]->(doc:Document)
      -[m:MENTIONS]->(startup:Company)
      <-[a:ACQUIRED]-(parent:Company)
      <-[r:WORKS_FOR {role: 'CEO'}]-(ceo:Executive)
RETURN ceo.name AS Target_CEO, parent.name AS Acquiring_Company
"""
results = graph_db.execute_read(traversal_query)

# Displaying the results of the traversal query
for record in results:
    print(f"[RESULT] CEO of the acquiring company: {record['Target_CEO']}, Acquiring Company: {record['Acquiring_Company']}")

graph_db.close()