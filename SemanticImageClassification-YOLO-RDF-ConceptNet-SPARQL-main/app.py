from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Autoriser les requêtes cross-origin
import os
from ultralytics import YOLO
from conceptnet_queries import query_conceptnet, extract_relations , generate_rdf_triplets # Import des fonctions ConceptNet
from SPARQLWrapper import SPARQLWrapper, JSON ,POST

from rdflib import Graph, URIRef, Literal, Namespace
import requests
import re


app = Flask(__name__)
CORS(app)  # Configurer CORS
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = YOLO('yolov8n.pt')

@app.route('/')
def home():
   # return "Flask server is running "
    return send_file("HtmlPart.html")

with open("coco.names", "r") as f:
    class_names = [line.strip() for line in f.readlines()]


# Global variable to store the namespace
global_namespace = None


def sanitize_namespace(namespace):
    """
    Nettoie le nom du namespace pour s'assurer qu'il est valide.
    - Remplace les caractères interdits par un underscore `_`
    - Assure que le nom commence par une lettre
    """
    namespace = re.sub(r'[^a-zA-Z0-9_-]', '_', namespace)  # Remplace les caractères interdits
    if namespace[0].isdigit():
        namespace = "ns_" + namespace  # Ajoute un préfixe si le nom commence par un chiffre
    return namespace

def create_namespace_if_not_exists(namespace="rdf_data"):
    """
    Crée un namespace dans Blazegraph avec les options nécessaires pour éviter les erreurs.
    """
    try:
        endpoint_url = f"http://localhost:9999/blazegraph/namespace/{namespace}/sparql"
        response = requests.get(endpoint_url)

        if response.status_code == 200:
            print(f"Namespace '{namespace}' existe déjà.")
            return

        print(f" Namespace '{namespace}' introuvable. Tentative de création...")

        create_ns_url = "http://localhost:9999/blazegraph/namespace"
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
        <properties>
            <entry key="com.bigdata.rdf.store.AbstractTripleStore.textIndex">true</entry>
            <entry key="com.bigdata.rdf.store.AbstractTripleStore.lexicalIndex">true</entry>
            <entry key="com.bigdata.rdf.store.AbstractTripleStore.geoSpatialIndex">true</entry>
            <entry key="com.bigdata.rdf.sail.isolatableIndices">true</entry>
            <entry key="com.bigdata.rdf.sail.truthMaintenance">false</entry>  <!-- Désactivé -->
            <entry key="com.bigdata.rdf.store.AbstractTripleStore.axiomsClass">com.bigdata.rdf.axioms.NoAxioms</entry> <!-- Désactive l'inférence -->
            <entry key="com.bigdata.rdf.store.AbstractTripleStore.justify">false</entry> <!-- Désactive la justification -->
            <entry key="com.bigdata.rdf.sail.namespace">{namespace}</entry>
        </properties>"""

        headers = {"Content-Type": "application/xml"}
        response = requests.post(create_ns_url, data=xml_data, headers=headers)

        if response.status_code == 201:
            print(f"Namespace '{namespace}' créé avec succès !")
        else:
            print(f" Échec de la création du namespace '{namespace}'. "
                  f"Réponse HTTP: {response.status_code}, Message: {response.text}")

    except Exception as e:
        print(f"Erreur lors de la création du namespace '{namespace}': {e}")

def insert_rdf_to_blazegraph(graph, namespace_name): #image_name
    """
    Insère dynamiquement les triplets RDF dans Blazegraph.
    """
    try:
        #namespace_name = f"namespace_{image_name.replace('.', '_')}"  # Exemple : namespace_image1_jpg
        '''
        namespace_name = sanitize_namespace(f"namespace_{image_name.replace('.', '_')}")

        global global_namespace 
        global_namespace= namespace_name
        '''
        print(f" Utilisation du namespacenanoo '{namespace_name}' pour l'insertion RDF.")
  
        # Vérifier et créer le namespace si nécessaire
        create_namespace_if_not_exists(namespace_name)

        endpoint_url = f"http://localhost:9999/blazegraph/namespace/{namespace_name}/sparql"
        print(f" Connexion à Blazegraph : {endpoint_url}")

        sparql = SPARQLWrapper(endpoint_url)
        sparql.setMethod(POST)

        # Sérialiser les données RDF
        rdf_dataxx = graph.serialize(format='nt')
        print(f" Données RDF préparées pour insertion (aperçu) : {rdf_dataxx[:300]}...")  # Affiche les 300 premiers caractères

        query = f"INSERT DATA {{ {rdf_dataxx} }}"
        sparql.setQuery(query)
        sparql.query()

        print(f"Données RDF insérées avec succès dans Blazegraph (Namespace: {namespace_name})")
        # enu hon 3ayt ll visualizatin 

    except requests.exceptions.RequestException as e:
        print(f" Erreur réseau lors de la connexion à Blazegraph : {e}")

    except Exception as e:
        print(f" Erreur lors de l'insertion des données RDF dans Blazegraph : {e}")


@app.route('/detect', methods=['POST'])
def detect_objects():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # YOLO : détecter les objets
    results = model(filepath)
    detections = []
    for result in results[0].boxes.data:
        class_id = int(result[5].item())  # Extraire l'ID de la classe détectée
        confidence = float(result[4].item())  # Extraire la confiance
        class_name = class_names[class_id] if class_id < len(class_names) else "unknown"
        detections.append({"class_name": class_name, "confidence": confidence})

         # Interroger ConceptNet pour chaque objet détecté
    conceptnet_results = {}
    for detection in detections:
        concept_data = query_conceptnet(detection["class_name"])
        relations = extract_relations(concept_data)
        conceptnet_results[detection["class_name"]] = relations

   # Generate RDF triplets
    rdf_graph = generate_rdf_triplets(detections, conceptnet_results)
    #rdf_file = "output.rdf"
    #rdf_file = f"rdf_output_{file.filename}.rdf"
    
    
    # Ensure the 'output' directory exists
    OUTPUT_FOLDER = "output"
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Save RDF with a unique filename per image inside 'output' folder
    rdf_file = os.path.join(OUTPUT_FOLDER, f"rdf_output_{file.filename}.rdf")
    
    rdf_graph.serialize(rdf_file, format="turtle")  # Save RDF graph to file
    print(f"RDF data saved to {rdf_file}")

    # Envoi des données RDF vers Blazegraph

    namespace_name = sanitize_namespace(f"namespace_{(file.filename).replace('.', '_')}")

    global global_namespace 
    global_namespace= namespace_name

    insert_rdf_to_blazegraph(rdf_graph, namespace_name)

    return jsonify({
        "detections": detections,
        "conceptnet": conceptnet_results ,
        "namespace":namespace_name ,

    }), 200
    # return jsonify({"detections": detections}), 200

@app.route('/detect', methods=['GET'])
def detect_get():
    return "This endpoint only supports POST requests for file uploads."

@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/query', methods=['POST'])
def sparql_query():
    try:
        query = request.json.get('query', "")
        print(f"Received SPARQL queryxx11: {query}")  # Log the received query
        
        #sparql = SPARQLWrapper("http://localhost:9999/blazegraph/namespace/rdf_data/sparql")
        #image_name = request.json.get('image_name', "")
        global global_namespace
        namespace_name = global_namespace #f"namespace_{image_name.replace('.', '_')}"
        endpoint_url = f"http://localhost:9999/blazegraph/namespace/{namespace_name}/sparql"

        print(f"🔎 Querying namespace: {namespace_name}")

        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        results = sparql.query().convert()
        print(f"Query Resultsxx22: {results}")  # Log the query results
        
        return jsonify(results)
    except Exception as e:
        print(f"Error during query executionxx33: {e}")  # Log any errors
        return jsonify({"error": str(e)}), 500
    
@app.route('/store', methods=['POST'])
def store_to_rdf():
    data = request.json  # Les données doivent contenir un label et une description
    label = data.get('label')
    description = data.get('description')

    if not label or not description:
        return jsonify({"error": "Invalid data"}), 400

    subject = URIRef(ns[label])
    predicate = URIRef(ns['description'])
    obj = Literal(description)

    rdf_graph.add((subject, predicate, obj))
    return jsonify({"message": f"Data added: {label} -> {description}"}), 200

if __name__ == '__main__':
    app.run(debug=True)  # Port par défaut #True, port=5000 False
