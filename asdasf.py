from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno (opcional, si prefieres usar .env)
load_dotenv()

# URI de conexión - Agregué el nombre de la base de datos en la URI
uri = "mongodb+srv://mauriciocorrea1015_db_user:NjxlC1khEAkYeR7S@cluster0.digxzrf.mongodb.net/agora_database?retryWrites=true&w=majority&appName=Cluster0"

# Crear cliente y conectar al servidor
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    # Verificar conexión
    client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB Atlas!")
    
    # Seleccionar base de datos y colección
    db = client['agora_database']
    collection = db['research_papers']
    
    # Limpiar la colección antes de insertar (opcional)
    # collection.delete_many({})
    # print("Colección limpiada")
    
    # Cargar datos desde el archivo JSON
    with open('base_de_datos.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Verificar si ya existen documentos
    existing_count = collection.count_documents({})
    print(f"Documentos existentes en la colección: {existing_count}")
    
    # Insertar los datos
    if isinstance(data, list):
        # Si el JSON es un array de documentos
        if len(data) > 0:
            result = collection.insert_many(data)
            print(f"✅ Se insertaron {len(result.inserted_ids)} documentos")
        else:
            print("⚠️ El archivo JSON está vacío")
    else:
        # Si el JSON es un objeto
        print(f"Estructura del JSON: {list(data.keys())}")
        
        # Intentar encontrar un array en el objeto
        inserted = False
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                result = collection.insert_many(value)
                print(f"✅ Se insertaron {len(result.inserted_ids)} documentos desde la clave '{key}'")
                inserted = True
                break
        
        if not inserted:
            print("⚠️ No se encontró un array de documentos para insertar")
    
    # Verificar la inserción
    final_count = collection.count_documents({})
    print(f"Total de documentos en la colección: {final_count}")
    
    # Mostrar un ejemplo de documento insertado
    sample = collection.find_one()
    if sample:
        print("\nEjemplo de documento insertado:")
        print(json.dumps(sample, indent=2, default=str))
    
except FileNotFoundError:
    print("❌ Error: No se encontró el archivo 'base_de_datos.json'")
except json.JSONDecodeError as e:
    print(f"❌ Error al decodificar el JSON: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    # Cerrar la conexión
    client.close()
    print("\nConexión cerrada")