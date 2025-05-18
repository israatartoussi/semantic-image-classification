import requests
from rdflib import Graph, URIRef, Literal

def query_conceptnet(word):
    """
    Interroge l'API ConceptNet pour récupérer les relations associées à un mot donné.
    """
    url = f"http://api.conceptnet.io/c/en/{word}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Retourne les données sous forme JSON
    else:
        return None

def extract_relations(concept_data):
    """
    Extrait les relations importantes de la réponse JSON de ConceptNet.
    """
    if not concept_data:
        return []

    relations = []
    for edge in concept_data.get('edges', []):
        relation = edge['rel']['label']  # Type de relation (e.g., IsA, UsedFor)
        start = edge['start']['label']  # Sujet
        end = edge['end']['label']      # Objet
        relations.append((start, relation, end))
    return relations


def generate_rdf_triplets(detections, conceptnet_results):
    """
    Generate RDF triplets for YOLO detections and their ConceptNet relations.
    Args:
        detections: List of detected objects from YOLO.
        conceptnet_results: Relations from ConceptNet.
    Returns:
        An RDF graph containing the triplets.
    """
    g = Graph()

    for detection in detections:
        subject = URIRef(f"http://example.org/{detection['class_name'].replace(' ', '_')}")
        
        if detection['class_name'] in conceptnet_results:
            for rel in conceptnet_results[detection['class_name']]:
                predicate = URIRef(f"http://example.org/{rel[1]}")
                obj = Literal(rel[2])
                g.add((subject, predicate, obj))

    return g

# Exemple de test
if __name__ == "__main__":
    concept_data = query_conceptnet("laptop")
    relations = extract_relations(concept_data)
    for r in relations:
        print(f"{r[0]} {r[1]} {r[2]}")
