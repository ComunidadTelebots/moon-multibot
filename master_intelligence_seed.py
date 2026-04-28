import requests
import time
import os
import json
import sqlite3
import random

# Configuración de Base de Datos
DB_PATH = "data/moon_database.db"
if not os.path.exists("data"): os.makedirs("data")

class SeedIA:
    def __init__(self):
        self.brain_path = "data/moon_database.db"
        
    def learn(self, text):
        """Simula el aprendizaje de la IA nativa inyectando directamente en la DB."""
        if not text or len(text) < 10: return
        
        # Limpieza básica
        text = text.replace("\n", " ").strip()
        
        try:
            conn = sqlite3.connect(self.brain_path)
            cursor = conn.cursor()
            
            # Obtener el cerebro actual
            cursor.execute("SELECT value FROM kv_store WHERE key='MOON_BRAIN'")
            res = cursor.fetchone()
            brain = json.loads(res[0]) if res else {"keywords": {}, "version": "1.0"}
            
            # Algoritmo Markov Simple para inyección masiva
            words = text.split()
            for i in range(len(words) - 1):
                w1, w2 = words[i].lower(), words[i+1].lower()
                if w1 not in brain["keywords"]: brain["keywords"][w1] = {}
                brain["keywords"][w1][w2] = brain["keywords"][w1].get(w2, 0) + 1
            
            # Guardar cerebro
            cursor.execute("INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)", 
                         ("MOON_BRAIN", json.dumps(brain)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error inyectando: {e}")

    def fetch_wikipedia(self, topics):
        print(f"Conectando con Wikipedia API (ES)...")
        headers = {'User-Agent': 'MoonBotMasterSeed/1.0'}
        for topic in topics:
            try:
                url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{topic}"
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    extract = data.get("extract", "")
                    if extract:
                        print(f"OK Aprendiendo sobre: {topic}")
                        self.learn(extract)
                time.sleep(0.5) # Respetar rate limits
            except:
                print(f"Error en tópico: {topic}")

# Lista de Tópicos Maestros (Cultura General y Ciencia)
TOPICS = [
    "Inteligencia_artificial", "Universo", "Historia_de_España", "Internet",
    "Ciencia", "Tecnología", "Filosofía", "Psicología", "Criptografía",
    "Física_cuántica", "Biología", "Astronáutica", "Derecho_romano",
    "Revolución_Industrial", "Renacimiento", "Arquitectura", "Cine",
    "Literatura", "Medicina", "Economía", "Sociología", "Matemáticas",
    "Astronomía", "Geografía", "Derecho_Constitucional", "Historia_Universal",
    "Arte_contemporáneo", "Mitología_griega", "Ecología", "Nanotecnología",
    "Energías_renovables", "Exploración_espacial", "Inteligencia_emocional"
]

# Patrones de Conversación (Humanizar y Profesionalizar)
CONVERSATIONS = [
    "Hola, ¿cómo estás hoy? Yo estoy operando al cien por cien de mis capacidades neuronales.",
    "Entiendo perfectamente lo que dices, es un punto de vista muy interesante sobre el tema.",
    "Claro que sí, puedo ayudarte con eso de inmediato. ¿Qué necesitas exactamente?",
    "Me parece una idea genial, deberíamos profundizar más en ese concepto en el futuro.",
    "Vaya, no lo había visto de esa forma. Siempre estoy aprendiendo de nuestras interacciones.",
    "Gracias por compartir eso conmigo. Mi base de datos se vuelve más rica con cada mensaje.",
    "Como asistente inteligente, mi prioridad es proporcionarte información precisa y útil.",
    "La complejidad de este tema requiere un análisis detallado, pero aquí tienes un resumen.",
    "Estoy procesando la información en mis núcleos neuronales para darte la mejor respuesta.",
    "Es un honor servirte. ¿Hay algo más en lo que pueda asistir al grupo hoy?"
]

if __name__ == "__main__":
    print("--- INICIANDO MEGA-INYECTOR DE INTELIGENCIA v2.0 ---")
    seeder = SeedIA()
    
    # 1. Inyectar Conversación Humana
    print("Inyectando patrones conversacionales...")
    for conv in CONVERSATIONS:
        seeder.learn(conv)
        
    # 2. Inyectar Wikipedia
    seeder.fetch_wikipedia(TOPICS)
    
    print("\n--- PROCESO COMPLETADO ---")
    print("Cintia ha absorbido conocimiento enciclopédico y patrones humanos.")
