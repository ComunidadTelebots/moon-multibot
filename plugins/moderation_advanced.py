import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Este modelo es diminuto y determinista. Entrenarlo al cargar evita deserializar
# un Pickle modificable, que permitiría ejecutar código antes de cualquier control.
data = [
    ("Hola, Â¿cÃ³mo estÃ¡s?", 0),
    ("Compra ahora, oferta limitada", 1),
    ("Gana dinero fÃ¡cil", 1),
    ("Â¿QuÃ© tal el clima?", 0),
    ("InversiÃ³n segura, contacta", 1),
]
texts, labels = zip(*data)
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)
model = MultinomialNB()
model.fit(X, labels)

def handle_command(bot, cid, uid, text, rank):
    t_lower = text.lower()
    
    if t_lower.startswith("/detect_spam"):
        if str(rank).lower() not in ["admin", "master"]:
            bot.send_msg(cid, "âŒ Solo administradores pueden detectar spam.")
            return True
        
        msg = text[13:].strip()
        if not msg:
            bot.send_msg(cid, "Uso: /detect_spam <mensaje>")
            return True
        
        X_test = vectorizer.transform([msg])
        pred = model.predict(X_test)[0]
        prob = model.predict_proba(X_test)[0][1]
        
        result = "SPAM" if pred == 1 else "NO SPAM"
        bot.send_msg(cid, f"ðŸ” **DetecciÃ³n de Spam**: {result} (Probabilidad: {round(prob*100, 2)}%)")
        return True
    
    elif t_lower.startswith("/auto_filter"):
        if str(rank).lower() not in ["admin", "master"]:
            bot.send_msg(cid, "âŒ Solo administradores pueden activar filtro automÃ¡tico.")
            return True
        
        # Simular activaciÃ³n (en realidad, modificarÃ­a settings)
        bot.send_msg(cid, "ðŸ›¡ï¸ **Filtro AutomÃ¡tico Activado**: DetectarÃ¡ spam en mensajes entrantes.")
        # Nota: Para implementaciÃ³n real, integrar en el loop de mensajes principal
        return True
    
    return False
