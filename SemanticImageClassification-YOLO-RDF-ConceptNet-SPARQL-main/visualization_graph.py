import networkx as nx
from rdflib import Graph
import matplotlib.pyplot as plt

def visualize_rdf_graph(rdf_file):
    """
    Visualize RDF data as a graph using NetworkX.
    
    Args:
        rdf_file (str): Path to the RDF file to visualize.
    """
    # Charger les données RDF
    g = Graph()
    g.parse(rdf_file, format="turtle")  # Assurez-vous que le format est correct

    # Créer un graphe NetworkX
    nx_graph = nx.DiGraph()
    for s, p, o in g:
        nx_graph.add_edge(s, o, label=p)

    # Visualiser le graphe
    pos = nx.spring_layout(nx_graph)  # Layout du graphe
    nx.draw(nx_graph, pos, with_labels=True, node_size=3000, font_size=10, node_color="lightblue")
    edge_labels = nx.get_edge_attributes(nx_graph, 'label')
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=edge_labels, font_size=8)
    plt.title("RDF Graph Visualization")
    plt.show()

if __name__ == "__main__":
    # Spécifiez le chemin du fichier RDF
    rdf_file = "output.rdf"
    visualize_rdf_graph(rdf_file)
