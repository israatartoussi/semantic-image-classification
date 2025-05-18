from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import matplotlib.pyplot as plt

# Blazegraph SPARQL endpoint
ENDPOINT_URL = "http://localhost:9999/blazegraph/namespace/rdf_data/sparql"

def execute_query(query):
    """Execute SPARQL query and return results as a DataFrame."""
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    data = []
    for result in results["results"]["bindings"]:
        data.append({key: result[key]["value"] for key in result})
    return pd.DataFrame(data)

def visualize_results(df, title="Query Results"):
    """Visualize query results as a table and bar chart."""
    print(df)  # Print to console
    if not df.empty:
        df.plot(kind='bar', x=df.columns[0], y=df.columns[1:], title=title)
        plt.show()

# Optimized Query with LIMIT
query = """
SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object .
}
LIMIT 50
"""

# Execute the Query and Visualize
try:
    df = execute_query(query)
    visualize_results(df, "RDF Data Visualization")
except Exception as e:
    print("Error during query execution or visualization:", e)
