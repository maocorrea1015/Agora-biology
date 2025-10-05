from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bs4 import BeautifulSoup
import requests
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Obtener variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME") 
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Validar que las variables existan
if not MONGO_URI:
    print("❌ ERROR CRÍTICO: MONGO_URI no está definida en .env")
    print("Asegúrate de tener un archivo .env con la URI de MongoDB Atlas")
    exit(1)

print(f"Intentando conectar a: {MONGO_URI[:50]}...")  # Muestra solo el inicio por seguridad

# Conectar a MongoDB
try:
    client = MongoClient(
        MONGO_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=5000  # Timeout de 5 segundos
    )
    
    # Forzar una conexión para verificar que funciona
    client.admin.command('ping')
    
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Verificar que la colección tenga documentos
    doc_count = collection.count_documents({})
    print(f"✅ Conectado a MongoDB Atlas")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"📁 Colección: {COLLECTION_NAME}")
    print(f"📄 Documentos en colección: {doc_count}")
    
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    print(f"URI utilizada: {MONGO_URI[:50]}...")
    collection = None
    exit(1)  # Detener la aplicación si no hay conexión

def scrape_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"Haciendo scraping de: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_selectors = ['h1', '.article-title', '.title', 'h1.content-title']
        article_title = "Título no encontrado"
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                article_title = title_element.get_text().strip()
                break
        
        paragraphs = []
        content_selectors = [
            'div.abstract p',
            'div#abstract p', 
            '.abstract-content p',
            '.article-content p',
            '.body p',
            'div.sec p'
        ]
        
        for selector in content_selectors:
            found_paragraphs = soup.select(selector)
            for p in found_paragraphs:
                text = p.get_text().strip()
                if len(text) > 80 and not text.startswith('©'):
                    paragraphs.append(text)
                    if len(paragraphs) >= 3:
                        break
            if paragraphs:
                break
        
        if not paragraphs:
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text().strip()
                if len(text) > 150:
                    paragraphs.append(text)
                    if len(paragraphs) >= 2:
                        break
        
        return {
            "titulo_extraido": article_title,
            "parrafos_extraidos": paragraphs,
            "url_scraped": url,
            "scraping_exitoso": True,
            "parrafos_encontrados": len(paragraphs)
        }
        
    except Exception as e:
        print(f"Error en scraping: {e}")
        return {
            "titulo_extraido": "Error en scraping",
            "parrafos_extraidos": [f"No se pudo extraer contenido: {str(e)}"],
            "url_scraped": url,
            "scraping_exitoso": False
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/buscar', methods=['POST'])
def buscar():
    if collection is None:
        return jsonify({"error": "Base de datos no disponible"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió JSON"}), 400
            
        query = data.get('query', '').strip()
        nivel = data.get('nivel', 'basic')
        
        if not query:
            return jsonify({"error": "Query vacía"}), 400
        
        print(f"Búsqueda: '{query}' | Nivel: {nivel}")
        
        resultados_db = collection.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"organism": {"$regex": query, "$options": "i"}},
                {"keyTopic": {"$regex": query, "$options": "i"}},
                {"relevance": {"$regex": query, "$options": "i"}}
            ]
        }).limit(10)
        
        resultados = []
        
        for item in resultados_db:
            item_dict = {
                "id": str(item.get("_id", "")), 
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "organism": item.get("organism", ""),
                "keyTopic": item.get("keyTopic", ""),
                "relevance": item.get("relevance", "")
            }
            
            if nivel == "advanced" and item.get("link"):
                scraped_data = scrape_article_content(item["link"])
                item_dict.update(scraped_data)
                time.sleep(1) 
            
            resultados.append(item_dict)
        
        print(f"Encontrados {len(resultados)} resultados")
        return jsonify({
            "resultados": resultados,
            "total": len(resultados),
            "query": query,
            "nivel": nivel
        })
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500

#if __name__ == "__main__":
#    app.run(debug=False, port=433)