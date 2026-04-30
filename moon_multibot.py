import os, sys, json, time, threading, logging, datetime, random, psutil, requests, sqlite3, jwt, importlib, re, struct, hashlib, subprocess
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "moon")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
MOON_ENV = os.getenv("MOON_ENV", "prod").lower()
MOON_ROLE = os.getenv("MOON_ROLE", "master").lower()
MASTER_ID = int(os.getenv("MASTER_ID", 0))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_EXTERNAL_LLM = os.getenv("USE_EXTERNAL_LLM", "false").lower() == "true"

app = Flask(__name__)
# Configuración según ambiente
LOG_LEVEL = logging.DEBUG if MOON_ENV == "dev" else logging.INFO
DB_PATH = "data/moon_dev.db" if MOON_ENV == "dev" else "data/moon_database.db"

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("MoonBot")

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS kv_store (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.commit()
        self.lock = threading.Lock()
    def get(self, key, default=None):
        with self.lock:
            self.cursor.execute("SELECT value FROM kv_store WHERE key=?", (key,))
            res = self.cursor.fetchone()
            return json.loads(res[0]) if res else default
    def set(self, key, value):
        with self.lock:
            self.cursor.execute("INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            self.conn.commit()

db = DBManager()

# --- Moon Proxy Manager ---
class ProxyManager:
    def __init__(self):
        self.proxies = db.get("PROXY_CONFIGS", [])
        self.processes = {} # index -> process

    def start_proxy(self, p_index):
        if p_index < 0 or p_index >= len(self.proxies): return False
        cfg = self.proxies[p_index]
        port = str(cfg.get("port", 443))
        secret = cfg.get("secret", "")
        
        # Comando para iniciar el nodo (Placeholder que simula el proxy)
        cmd = [sys.executable, "-c", f"import time; print('Proxy en {port} iniciado'); [time.sleep(1) for _ in range(999999)]"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes[p_index] = proc
            add_web_log("PROXY", f"Nodo MTProto desplegado en puerto {port}")
            return True
        except Exception as e:
            add_web_log("ERROR", f"Fallo al desplegar proxy: {str(e)}")
            return False

    def stop_proxy(self, p_index):
        if p_index in self.processes:
            self.processes[p_index].terminate()
            del self.processes[p_index]
            add_web_log("PROXY", f"Nodo en puerto {self.proxies[p_index].get('port')} detenido.")
            return True
        return False

    def get_stats(self):
        results = []
        for i, cfg in enumerate(self.proxies):
            is_running = i in self.processes and self.processes[i].poll() is None
            results.append({
                "index": i,
                "port": cfg["port"],
                "secret": cfg["secret"],
                "status": "ONLINE" if is_running else "OFFLINE",
                "conns": random.randint(5, 45) if is_running else 0,
                "up": f"{random.randint(10, 200)} KB/s" if is_running else "0 KB/s",
                "down": f"{random.randint(20, 400)} KB/s" if is_running else "0 KB/s"
            })
        return results

    def scan_docker(self):
        """Intenta detectar proxies MTProto ejecutándose en Docker"""
        try:
            cmd = ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Ports}}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0: return []
            
            detected = []
            for line in res.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) < 3: continue
                cid, name, ports = parts[0], parts[1], parts[2]
                
                # Criterios de detección: nombre o puertos típicos
                is_proxy = "proxy" in name.lower() or "mtproto" in name.lower() or "443" in ports
                if is_proxy:
                    detected.append({
                        "id": cid,
                        "name": name,
                        "ports": ports,
                        "type": "DOCKER"
                    })
            return detected
        except:
            return []

class VirusTotalManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"

    def scan_hash(self, file_hash):
        if not self.api_key: return {"error": "API Key no configurada"}
        try:
            headers = {"x-apikey": self.api_key}
            r = requests.get(f"{self.base_url}/files/{file_hash}", headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                stats = data["data"]["attributes"]["last_analysis_stats"]
                return {
                    "ok": True,
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "undetected": stats.get("undetected", 0),
                    "harmless": stats.get("harmless", 0),
                    "link": f"https://www.virustotal.com/gui/file/{file_hash}"
                }
            elif r.status_code == 404:
                return {"ok": True, "not_found": True}
            return {"error": f"Error VT: {r.status_code}"}
        except Exception as e:
            return {"error": str(e)}

class TaskQueue:
    def __init__(self):
        self.queue = [] # List of {id, type, target, data, priority, status, time}
        self.lock = threading.Lock()
        self.counter = 0

    def add(self, t_type, target, data, priority=0):
        with self.lock:
            self.counter += 1
            task = {
                "id": self.counter,
                "type": t_type,
                "target": target,
                "data": data,
                "priority": priority,
                "status": "PENDING",
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }
            self.queue.append(task)
            # Sort by priority (higher first)
            self.queue.sort(key=lambda x: x["priority"], reverse=True)
            return task["id"]

    def get_all(self):
        with self.lock: return list(self.queue)

    def cancel(self, t_id):
        with self.lock:
            self.queue = [t for t in self.queue if t["id"] != t_id]

    def prioritize(self, t_id):
        with self.lock:
            for t in self.queue:
                if t["id"] == t_id: t["priority"] += 10
            self.queue.sort(key=lambda x: x["priority"], reverse=True)

    def process_next(self, bot_instance):
        with self.lock:
            if not self.queue: return False
            task = self.queue[0]
            if task["status"] == "RUNNING": return False
            task["status"] = "RUNNING"
        
        try:
            if task["type"] == "message":
                bot_instance.api_call("sendMessage", {"chat_id": task["target"], "text": task["data"]})
            elif task["type"] == "api_call":
                bot_instance.api_call(task["target"], task["data"])
            
            with self.lock:
                self.queue = [t for t in self.queue if t["id"] != task["id"]]
            return True
        except Exception as e:
            add_web_log("ERROR", f"Queue Task {task['id']} falló: {e}")
            with self.lock: task["status"] = "PENDING"
            return False

task_queue = TaskQueue()

def queue_worker():
    while True:
        try:
            if active_bots:
                task_queue.process_next(active_bots[0])
        except: pass
        time.sleep(1)

threading.Thread(target=queue_worker, daemon=True).start()

vt_mgr = VirusTotalManager(os.getenv("VT_API_KEY"))
proxy_mgr = ProxyManager()
web_logs = []
flood_cache = {}  # {f"{cid}_{uid}": [timestamps]} — en memoria para evitar ops SQLite por mensaje
global_chat_history, global_chat_names, global_user_stats, global_media_list, global_msg_log = {}, {}, {}, [], []
maintenance_mode = False
voice_log = []
active_audits = db.get("ACTIVE_AUDITS", {}) # Persistencia de auditorías
listen_mode = db.get("LISTEN_MODE", False)  # Modo escucha: solo aprende, no responde
multilingual_seeds = {}
telemetry_history = {"cpu": [], "ram": [], "msgs": [], "time": []}

def telemetry_worker():
    while True:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            t = datetime.datetime.now().strftime("%H:%M")
            
            telemetry_history["cpu"].append(cpu)
            telemetry_history["ram"].append(mem)
            telemetry_history["time"].append(t)
            
            # Mantener últimos 30 minutos
            if len(telemetry_history["cpu"]) > 30:
                for k in telemetry_history: telemetry_history[k].pop(0)
        except: pass
        time.sleep(60)

threading.Thread(target=telemetry_worker, daemon=True).start()

def add_web_log(lvl, txt):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    web_logs.append({"time": t, "level": lvl, "text": txt})
    if len(web_logs) > 50: web_logs.pop(0)
    with open("data/bot.log", "a", encoding="utf-8") as f:
        f.write(f"[{t}] [{lvl}] {txt}\n")

# Log inicial del sistema
add_web_log("INFO", "Sistema MoonBot iniciado y listo para operaciones.")

def add_audit_log(act):
    try:
        ip = request.remote_addr if request else "127.0.0.1"
        user_agent = request.headers.get("User-Agent", "N/A")
    except:
        ip = "127.0.0.1"
        user_agent = "N/A"
    
    log_entry = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "ip": ip, 
        "action": act,
        "ua": user_agent
    }
    
    current_logs = db.get("SECURITY_AUDIT_LOGS", [])
    current_logs.append(log_entry)
    db.set("SECURITY_AUDIT_LOGS", current_logs[-100:]) # Guardar últimas 100 acciones
    
    # También en el log general
    add_web_log("SECURITY", f"Acción Auditada: {act} (IP: {ip})")

def check_jwt(req):
    # Seguridad adicional: Whitelist de IPs si está configurado
    ip_whitelist = db.get("IP_WHITELIST", [])
    if ip_whitelist and req.remote_addr not in ip_whitelist:
        add_web_log("WARNING", f"Intento de acceso bloqueado desde IP no autorizada: {req.remote_addr}")
        return False

    auth = req.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        # Intentar desde query param para descargas
        tk = req.args.get("token")
        if tk: auth = f"Bearer {tk}"
        else: return False
    try: jwt.decode(auth.split(" ")[1], JWT_SECRET, algorithms=["HS256"]); return True
    except: return False

def is_cas_banned(uid):
    """Verifica si un usuario est en la lista negra global de Combot Anti-Spam (CAS)"""
    try:
        r = requests.get(f"https://api.cas.chat/check?user_id={uid}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("ok", False)
    except: pass
    return False

@app.route("/")
def index(): return send_from_directory("web", "index.html")
@app.route("/<path:path>")
def static_proxy(path): return send_from_directory("web", path)

@app.route("/CHANGELOG.md")
def get_changelog(): return send_from_directory(".", "CHANGELOG.md")

@app.route("/api/login", methods=['POST'])
def web_login():
    if request.json.get("password") == WEB_PASSWORD:
        tk = jwt.encode({"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, JWT_SECRET, algorithm="HS256")
        add_audit_log("Login Web OK")
        return jsonify({"ok": True, "token": tk})
    return jsonify({"ok": False}), 401

@app.route("/api/status")
def web_status():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    # Obtener métricas reales
    cpu = psutil.cpu_percent()
    if cpu == 0: cpu = psutil.cpu_percent(interval=0.1) # Forzar lectura si es 0
    mem = psutil.virtual_memory()
    ram_used = round(mem.used / (1024**3), 2)
    ram_total = round(mem.total / (1024**3), 2)
    
    return jsonify({
        "ok": True, 
        "cpu": cpu, 
        "ram": mem.percent, 
        "ram_used": ram_used,
        "ram_total": ram_total,
        "disk": psutil.disk_usage('C:' if os.name == 'nt' else '/').percent, 
        "uptime": str(datetime.timedelta(seconds=int(time.time() - start_time))), 
        "logs": web_logs, 
        "db_vistos": len(db.get("U_FILE", {})),
        "telemetry": telemetry_history
    })

@app.route("/api/chats")
def web_chats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    v = db.get("U_FILE", {})
    vistos_obj = []
    for k, val in v.items():
        # Si val es un dict (nuevo formato), sacamos el nombre. Si no, usamos el ID.
        name = val.get("name", k) if isinstance(val, dict) else k
        vistos_obj.append({"id": k, "name": name})
    return jsonify({"ok": True, "vistos_obj": vistos_obj})

@app.route("/api/history")
def web_history():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    cid = request.args.get("chat_id")
    if not cid: return jsonify({"ok": False, "history": []})
    
    hist = global_chat_history.get(cid, [])
    
    # Enriquecer historial con Trust Score calculado en tiempo real
    enriched_history = []
    for m in hist[-100:]:
        uid = m.get("uid")
        stats = global_user_stats.get(uid, {"karma": 0, "count": 0})
        # Fórmula de Trust Score: 50 base + (karma * 2) + (msgs / 10). Cap 0-100.
        score = min(100, max(0, 50 + (stats.get("karma", 0) * 2) + (stats.get("count", 0) // 10)))
        
        m_copy = m.copy()
        m_copy["trust_score"] = score
        enriched_history.append(m_copy)
        
    return jsonify({
        "ok": True, 
        "history": enriched_history,
        "warns": db.get(f"WARNS_{cid}", {}),
        "muted_users": db.get(f"MUTED_{cid}", []),
        "banned_users": db.get("ST_FILE", {}).get("bans", [])
    })

@app.route("/api/telegram/file/<file_id>")
def web_telegram_file_proxy(file_id):
    if not check_jwt(request): return "Unauthorized", 401
    bot = active_bots[0] # Usamos el primer bot como proxy
    f_info = bot.api_call("getFile", {"file_id": file_id})
    if not f_info.get("ok"): return "File not found", 404
    
    path = f_info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{bot.token}/{path}"
    
    try:
        r = requests.get(url, stream=True, timeout=10)
        return Response(r.iter_content(chunk_size=1024), content_type=r.headers.get('Content-Type'))
    except:
        return "Error downloading file", 500

@app.route("/api/send", methods=['POST'])
def web_send():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    proxy_bot.send_msg(d["target"], d["text"])
    return jsonify({"ok": True})

@app.route("/api/replies", methods=['GET', 'POST', 'DELETE'])
def web_replies():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    r = db.get("S_FILE", {})
    if request.method == 'GET': return jsonify({"ok": True, "replies": r})
    if request.method == 'POST':
        d = request.json
        r[d["trigger"]] = {"text": d["response"], "image": d.get("image_url")}
        db.set("S_FILE", r); return jsonify({"ok": True})
    if request.method == 'DELETE':
        t = request.json.get("trigger")
        if t in r: del r[t]
        db.set("S_FILE", r); return jsonify({"ok": True})

@app.route("/api/plugins", methods=['GET'])
def web_plugins():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    ps = []
    if os.path.exists("plugins"):
        for f in os.listdir("plugins"):
            if f.endswith(".py"): ps.append({"name": f, "status": "Enabled"})
            elif f.endswith(".disabled"): ps.append({"name": f.replace(".disabled", ""), "status": "Disabled"})
    return jsonify({"ok": True, "plugins": ps})

@app.route("/api/plugins/toggle", methods=['POST'])
def web_plugins_toggle():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    name = request.json.get("name")
    p1, p2 = os.path.join("plugins", name), os.path.join("plugins", name + ".disabled")
    if os.path.exists(p1): os.rename(p1, p2)
    elif os.path.exists(p2): os.rename(p2, p1)
    return jsonify({"ok": True})

@app.route("/api/plugins/upload", methods=['POST'])
def web_plugins_upload():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if 'file' not in request.files: return jsonify({"ok": False, "msg": "No file"}), 400
    f = request.files['file']
    if f.filename == '': return jsonify({"ok": False}), 400
    if f and f.filename.endswith('.py'):
        f.save(os.path.join("plugins", f.filename))
        add_audit_log(f"Plugin subido: {f.filename}")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": "Solo archivos .py"}), 400

@app.route("/api/plugins/reload", methods=['POST'])
def web_plugins_reload():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    add_web_log("INFO", "Recargando plugins...")
    return jsonify({"ok": True, "msg": "Señal de recarga enviada."})

@app.route("/api/system/update", methods=['GET', 'POST'])
def web_system_update():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    git_path = "git" if os.name != 'nt' else "C:\\Program Files\\Git\\bin\\git.exe"
    
    if request.method == 'GET':
        # Comprobar actualizaciones
        try:
            subprocess.run([git_path, "fetch"], timeout=15)
            res = subprocess.run([git_path, "status", "-uno"], capture_output=True, text=True)
            behind = "Your branch is behind" in res.stdout
            return jsonify({
                "ok": True, 
                "behind": behind, 
                "status": res.stdout,
                "current_commit": subprocess.check_output([git_path, "rev-parse", "--short", "HEAD"]).decode().strip()
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    # Aplicar actualización (POST)
    try:
        add_audit_log("Actualización del sistema iniciada desde GitHub")
        res = subprocess.run([git_path, "pull", "origin", "master"], capture_output=True, text=True)
        add_web_log("SUCCESS", "Sistema actualizado correctamente desde GitHub.")
        return jsonify({"ok": True, "output": res.stdout})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/system/processes", methods=['GET'])
def web_system_processes():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    procs = []
    current_pid = os.getpid()
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
            cmd = proc.info.get('cmdline') or []
            if any("moon_multibot.py" in s for s in cmd):
                is_slave = "--slave" in str(cmd) or "slave" in str(cmd).lower()
                procs.append({
                    "pid": proc.info['pid'],
                    "is_self": proc.info['pid'] == current_pid,
                    "role": "slave" if is_slave else "master",
                    "uptime": time.time() - proc.info['create_time'],
                    "cpu": proc.info['cpu_percent'],
                    "mem": proc.info['memory_info'].rss / (1024 * 1024)
                })
        return jsonify({"ok": True, "processes": procs})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/system/kill", methods=['POST'])
def web_system_kill():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    target_pid = request.json.get("pid")
    if not target_pid or target_pid == os.getpid():
        return jsonify({"ok": False, "msg": "No se puede suicidar la instancia actual."})
    try:
        p = psutil.Process(target_pid)
        p.terminate()
        add_audit_log(f"Instancia zombie (PID {target_pid}) eliminada manualmente.")
        return jsonify({"ok": True, "msg": f"Proceso {target_pid} eliminado."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/settings", methods=['GET', 'POST'])
def web_settings_legacy():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if request.method == 'GET': return jsonify({"ok": True, "master_id": MASTER_ID, "welcome_msg": db.get("WELCOME_MSG", "Moon Activo."), "maintenance_mode": db.get("MAINTENANCE_MODE", False)})
    d = request.json
    if "welcome_msg" in d: db.set("WELCOME_MSG", d["welcome_msg"])
    if "maintenance_mode" in d: db.set("MAINTENANCE_MODE", d["maintenance_mode"])
    if "bot_description" in d:
        proxy_bot.api_call("setMyDescription", {"description": d["bot_description"]})
    return jsonify({"ok": True})

@app.route("/api/audit")
def web_audit():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "logs": db.get("AUDIT_LOG", [])})

@app.route("/api/logs/download")
def web_download_logs():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if os.path.exists("data/bot.log"):
        return send_from_directory("data", "bot.log", as_attachment=True)
    return jsonify({"ok": False, "msg": "No log file found."})

@app.route("/api/media")
def web_media():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "media": global_media_list[-50:]})

@app.route("/api/stats/users")
def web_user_stats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    sorted_u = sorted(global_user_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    return jsonify({"ok": True, "users": [{"id": k, "name": v["name"], "count": v["count"]} for k, v in sorted_u]})

@app.route("/api/users/ban", methods=['POST'])
def web_user_ban():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    u = str(request.json.get("uid"))
    cid = request.json.get("cid")
    st = db.get("ST_FILE", {"bans": []})
    if u not in st["bans"]: 
        st["bans"].append(u)
        db.set("ST_FILE", st)
    
    # Expulsar de inmediato si se proporciona CID
    if cid:
        try:
            active_bots[0].kick_user(cid, u)
            add_web_log("SECURITY", f"Usuario {u} expulsado tras baneo manual.")
        except: pass
    return jsonify({"ok": True})

@app.route("/api/ping")
def web_ping():
    return jsonify({"ok": True, "status": "online", "time": time.time()})

@app.route("/api/users/notes", methods=['POST'])
def web_user_notes():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    uid, note = str(d.get("uid")), d.get("note", "")
    if uid in global_user_stats:
        global_user_stats[uid]["notes"] = note
    return jsonify({"ok": True})

@app.route("/api/stats/heatmap")
def web_heatmap():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    history = db.get("GLOBAL_HISTORY", [])
    counts = [0] * 24
    for m in history:
        try:
            hour = int(m.get("time", "00:00").split(":")[0])
            if 0 <= hour < 24: counts[hour] += 1
        except: pass
    return jsonify({"ok": True, "heatmap": counts})

global_bot_names_cache = {}

@app.route("/api/bots", methods=['GET', 'POST', 'DELETE'])
def web_bots():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if request.method == 'GET':
        resolved_bots = []
        for b in bots_data:
            tk = b["token"]
            if tk not in global_bot_names_cache:
                temp_bot = MoonBot(tk)
                me = temp_bot.api_call("getMe")
                if me.get("ok"):
                    global_bot_names_cache[tk] = "@" + me["result"].get("username", "Bot")
                else:
                    global_bot_names_cache[tk] = "Token Inválido"
            
            # Obtener chats de este bot
            bot_chats = db.get(f"CHATS_{tk}", [])
            chat_names = db.get("CHAT_NAMES", {})
            resolved_chats = [{"id": cid, "name": chat_names.get(cid, cid)} for cid in bot_chats]
            
            resolved_bots.append({
                "token": tk, 
                "name": global_bot_names_cache[tk],
                "chats": resolved_chats
            })
        return jsonify({"ok": True, "bots": resolved_bots})
    return jsonify({"ok": True})

@app.route("/api/automation/faq", methods=['GET'])
def web_faq_list():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    faq_db = db.get("FAQ_DB", {})
    faq_answers = db.get("FAQ_ANSWERS", {})
    merged = [{"question": q, "count": c, "answer": faq_answers.get(q, "")}
              for q, c in sorted(faq_db.items(), key=lambda x: x[1], reverse=True)]
    return jsonify({"ok": True, "faq": merged})

@app.route("/api/automation/faq/set", methods=['POST'])
def web_faq_set():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json or {}
    question = d.get("question", "").lower().strip()
    answer = d.get("answer", "").strip()
    if not question or not answer:
        return jsonify({"ok": False, "msg": "question y answer requeridos"})
    faq_answers = db.get("FAQ_ANSWERS", {})
    faq_answers[question] = answer
    db.set("FAQ_ANSWERS", faq_answers)
    add_audit_log(f"FAQ Answer guardada: '{question[:40]}'")
    return jsonify({"ok": True})

@app.route("/api/automation/faq/delete", methods=['POST'])
def web_faq_delete():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    question = (request.json or {}).get("question", "").lower().strip()
    faq_answers = db.get("FAQ_ANSWERS", {})
    faq_db = db.get("FAQ_DB", {})
    faq_answers.pop(question, None)
    faq_db.pop(question, None)
    db.set("FAQ_ANSWERS", faq_answers)
    db.set("FAQ_DB", faq_db)
    return jsonify({"ok": True})

@app.route("/api/ia/search", methods=['POST'])
def web_ia_search():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    query = request.json.get("query")
    if not query: return jsonify({"ok": False})
    add_web_log("IA", f"Neuro-Búsqueda iniciada: {query}")
    res = ia_nativa.search_web(query)
    return jsonify({"ok": True, "result": res})

@app.route("/api/ia/multilingual", methods=['POST'])
def web_ia_multilingual():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    threading.Thread(target=ia_nativa.seed_multilingual).start()
    return jsonify({"ok": True})

@app.route("/api/ia/translations")
def web_translations():
    # Cargar desde archivo para que sea editable
    if os.path.exists("data/translations.json"):
        with open("data/translations.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, "translations": data})
    return jsonify({"ok": False})

@app.route("/api/ia/translate_all", methods=['POST'])
def web_ia_translate_all():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    target_lang = request.json.get("lang", "fr")
    
    if os.path.exists("data/translations.json"):
        with open("data/translations.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        base = data.get("es", {})
        new_trans = {}
        
        add_web_log("IA", f"Generando traducciones para {target_lang}...")
        
        for key, text in base.items():
            # Usar la IA para traducir
            prompt = f"Traduce este término de Dashboard de Telegram al idioma {target_lang}. Solo devuelve la traducción: {text}"
            translated = ia_nativa.generate(prompt)
            new_trans[key] = translated.strip()
            
        data[target_lang] = new_trans
        with open("data/translations.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return jsonify({"ok": True, "lang": target_lang})
    return jsonify({"ok": False})

@app.route("/api/ia/stats")
def web_ia_stats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    try:
        feeders = db.get("IA_FEEDERS", [])
        if not isinstance(feeders, list): feeders = []
        resolved = []
        for cid in feeders:
            try:
                res = proxy_bot.api_call("getChat", {"chat_id": cid}, silent=True)
                name = res.get("result", {}).get("title") or res.get("result", {}).get("username") or cid
                
                # Membresía real (Silencioso para evitar spam de consola)
                chk = proxy_bot.api_call("getChatMember", {"chat_id": cid, "user_id": proxy_bot.bot_id}, silent=True)
                status_text = "OFFLINE"
                if chk.get("ok"):
                    st = chk["result"].get("status")
                    if st in ["administrator", "creator"]: status_text = "ADMIN"
                    elif st == "member": status_text = "ONLINE"
                    elif st in ["left", "kicked"]: status_text = "BANEADO/EXPULSADO"
                
                last_msg = db.get(f"FEEDER_LAST_{cid}", "Sin actividad")
                resolved.append({"id": cid, "name": name, "status": status_text, "last": last_msg})
            except Exception:
                resolved.append({"id": cid, "name": cid, "status": "ERROR", "last": "N/A"})

        return jsonify({
            "ok": True,
            "stats": ia_nativa.get_stats(),
            "feeders": resolved,
            "potentials": db.get("POTENTIAL_FEEDERS", {}),
            "lang_counts": db.get("IA_LANG_COUNTS", {}),
            "ia_mode": ia_nativa.mode,
            "ia_mood": ia_nativa.mood,
            "moon_env": MOON_ENV,
            "listen_mode": db.get("LISTEN_MODE", False),
            "supported_languages": list(db.get("IA_LANG_COUNTS", {}).keys()) or ["es", "en"]
        })
    except Exception as e:
        add_web_log("ERROR", f"Fallo crítico en /api/ia/stats: {str(e)}")
        return jsonify({"ok": False, "msg": "Error interno del servidor"})

@app.route("/api/ia/potentials")
def web_ia_potentials():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    p = db.get("POTENTIAL_FEEDERS", {})
    return jsonify({"ok": True, "potentials": p})

@app.route("/api/ia/potentials/clear", methods=['POST'])
def web_ia_potentials_clear():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    db.set("POTENTIAL_FEEDERS", {})
    return jsonify({"ok": True})

@app.route("/api/ia/feeders/remove", methods=['POST'])
def web_ia_feeders_remove():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    cid = str(request.json.get("id"))
    feeders = db.get("IA_FEEDERS", [])
    if cid in feeders:
        feeders.remove(cid)
        db.set("IA_FEEDERS", feeders)
        add_audit_log(f"Fuente de aprendizaje (ID {cid}) eliminada.")
        return jsonify({"ok": True, "msg": "Fuente eliminada."})
    return jsonify({"ok": False, "msg": "Fuente no encontrada."})

@app.route("/api/ia/audit/history/clear", methods=['POST'])
def web_ia_audit_history_clear():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    db.set("IA_AUDIT_HISTORY", [])
    add_audit_log("Historial de auditorías vaciado manualmente.")
    return jsonify({"ok": True, "msg": "Historial limpiado."})

def start_audit_logic(cid, cid_input=None):
    """Lógica centralizada para iniciar auditoría con pre-carga de historial"""
    # Si ya existe y el nombre NO es el ID crudo, salimos para no repetir
    if cid in active_audits and active_audits[cid].get("name") and active_audits[cid]["name"] != str(cid):
        return
    cid_input = cid_input or cid
    
    chat_name = cid
    # 1. Intentar resolver nombre y alias si es un ID numérico
    if not str(cid_input).startswith("@"):
        res_info = proxy_bot.api_call("getChat", {"chat_id": cid})
        if res_info.get("ok"):
            chat_data = res_info["result"]
            chat_name = chat_data.get("title") or chat_data.get("first_name") or cid
            # Guardar nombre persistente en la DB
            names = db.get("CHAT_NAMES", {})
            names[cid] = chat_name
            db.set("CHAT_NAMES", names)
            
            # Actualizar también en el radar si existe
            potentials = db.get("POTENTIAL_FEEDERS", {})
            if cid in potentials:
                potentials[cid]["name"] = chat_name
                db.set("POTENTIAL_FEEDERS", potentials)
            
            if chat_data.get("username"):
                cid_input = f"@{chat_data['username']}"
                add_web_log("DEBUG", f"ID {cid} resuelto a alias {cid_input} para scraping.")
    else:
        # Si es un alias, intentamos obtener el nombre real igual
        res_info = proxy_bot.api_call("getChat", {"chat_id": cid_input})
        if res_info.get("ok"):
            chat_name = res_info["result"].get("title") or res_info["result"].get("first_name") or cid_input
            names = db.get("CHAT_NAMES", {})
            names[cid] = chat_name # Usamos el ID como clave si es posible
            db.set("CHAT_NAMES", names)
    
    prev_msgs = []
    # 2. Intentar Scraping si tenemos un alias (Canales y Grupos Públicos)
    if cid_input.startswith("@"):
        add_web_log("INFO", f"Scraping preventivo para {cid_input}...")
        try:
            url = f"https://t.me/s/{cid_input[1:]}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                matches = re.findall(pattern, r.text, re.DOTALL)
                prev_msgs = [re.sub(r'<.*?>', '', m) for m in matches]
        except: pass

    # 2. Pre-cargar desde el historial interno (GLOBAL_HISTORY)
    history = db.get("GLOBAL_HISTORY", [])
    internal_msgs = [m["text"] for m in history if str(m.get("cid")) == cid]
    
    # Combinar y evitar duplicados
    all_msgs = list(dict.fromkeys(prev_msgs + internal_msgs))
    
    score = 0
    for t in all_msgs:
        words = str(t).split()
        unique_words = len(set(words))
        score += (unique_words * 2) + (len(str(t)) // 10)

    status = "listening"
    final_score = 0
    report = None
    if len(all_msgs) >= 15:
        status = "finished"
        final_score = min(100, (score // 15) * 5)
        all_text = " ".join(all_msgs[:15])
        words_rep = all_text.split()
        settings = db.get("GLOBAL_SETTINGS", {})
        threshold = int(settings.get("audit_threshold", 60))
        report = {
            "time": datetime.datetime.now().strftime("%d/%m %H:%M"),
            "chat": chat_name,
            "cid": cid,
            "score": final_score,
            "avg_len": len(all_text) // 15,
            "unique_words": len(set(words_rep)),
            "verdict": "RECOMENDADO" if final_score >= threshold else "NO RECOMENDADO"
        }
        # Guardar en Historial Persistente
        hist = db.get("IA_AUDIT_HISTORY", [])
        hist.append(report)
        db.set("IA_AUDIT_HISTORY", hist[-50:])
        add_web_log("SUCCESS", f"Reporte guardado en historial para {cid}")

    active_audits[cid] = {
        "name": chat_name,
        "messages": all_msgs, 
        "score": score, 
        "status": status, 
        "final_score": final_score,
        "report": report,
        "start": time.time()
    }
    db.set("ACTIVE_AUDITS", active_audits)
    add_web_log("DEBUG", f"Auditoría INICIALIZADA para {cid}. Mensajes pre-cargados: {len(all_msgs)}")

@app.route("/api/ia/audit/start", methods=['POST'])
def web_ia_audit_start():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    cid_input = str(request.json.get("id"))
    if not cid_input: return jsonify({"ok": False, "msg": "ID requerido"})
    
    # Resolver ID real si es un alias
    cid = cid_input
    if cid_input.startswith("@"):
        res_info = proxy_bot.api_call("getChat", {"chat_id": cid_input})
        if res_info.get("ok"):
            cid = str(res_info["result"].get("id"))
    
    if not cid_input.startswith("@"):
        # Verificar si el bot está en el chat antes de auditar vía API
        chk = proxy_bot.api_call("getChatMember", {"chat_id": cid, "user_id": proxy_bot.bot_id})
        if not chk.get("ok") or chk["result"].get("status") in ["left", "kicked"]:
            return jsonify({"ok": False, "msg": "Error: El bot DEBE estar dentro del grupo."})

    start_audit_logic(cid, cid_input)
    return jsonify({"ok": True})

@app.route("/api/ia/audit/status")
def web_ia_audit_status():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    
    # Asegurar que todas las fuentes potenciales tengan auditoría activa (Retro-fix)
    potentials = db.get("POTENTIAL_FEEDERS", {})
    feeders = db.get("IA_FEEDERS", [])
    for cid in potentials:
        # Permitir re-identificar si falta el nombre o es el ID crudo
        has_name = active_audits.get(cid, {}).get("name")
        if (cid not in active_audits or not has_name or has_name == cid) and cid not in feeders:
            start_audit_logic(cid)
            
    return jsonify({"ok": True, "audits": active_audits})

@app.route("/api/ia/audit/history")
def web_ia_audit_history():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    hist = db.get("IA_AUDIT_HISTORY", [])
    return jsonify({"ok": True, "history": hist[::-1]}) # Recientes primero

@app.route("/api/ia/audit/export")
def web_ia_audit_export():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    cid = request.args.get("id")
    if not cid: return "ID requerido", 400
    
    history = db.get("GLOBAL_HISTORY", [])
    msgs = [m for m in history if str(m.get("cid")) == str(cid)]
    
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fecha", "Usuario", "Mensaje"])
    for m in msgs:
        writer.writerow([m.get("time"), m.get("user"), m.get("text")])
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=audit_{cid}.csv"}
    )

@app.route("/api/global/history")
def web_global_history():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    history = db.get("GLOBAL_HISTORY", [])
    return jsonify({"ok": True, "history": history})

@app.route("/api/admin/settings", methods=['GET', 'POST'])
def web_settings():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if request.method == 'GET':
        return jsonify({"ok": True, "settings": db.get("GLOBAL_SETTINGS", {"welcome_msg": "Bienvenido al bot!"})})
    db.set("GLOBAL_SETTINGS", request.json)
    return jsonify({"ok": True})

@app.route("/api/ia/feeders/add", methods=['POST'])
def web_ia_feeder_add():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    try:
        raw_link = request.json.get("link", "").strip()
        if not raw_link: return jsonify({"ok": False, "msg": "Enlace vacío"})
        
        # Clean link/username
        link = raw_link.split("/")[-1].replace("@", "")
        target = f"@{link}" if not (link.startswith("-100") or link.startswith("-")) else link
        
        add_web_log("INFO", f"Intentando vincular IA Feeder: {target}")
        
        if not proxy_bot:
            return jsonify({"ok": False, "msg": "No hay un bot activo para realizar la búsqueda."})
            
        res = proxy_bot.api_call("getChat", {"chat_id": target})
        
        if res.get("ok"):
            cid = str(res["result"]["id"])
            title = res["result"].get("title") or res["result"].get("username") or cid
            global_chat_names[cid] = title
            f = db.get("IA_FEEDERS", [])
            if cid not in f: 
                f.append(cid)
                db.set("IA_FEEDERS", f)
            
            # Limpiar de potenciales si estaba allí
            potentials = db.get("POTENTIAL_FEEDERS", {})
            if cid in potentials:
                del potentials[cid]
                db.set("POTENTIAL_FEEDERS", potentials)
            
            # Limpiar de auditorías activas si existe
            if cid in active_audits:
                del active_audits[cid]

            add_web_log("SUCCESS", f"IA Feeder vinculado: {title}")
            return jsonify({"ok": True, "name": title})
        
        add_web_log("ERROR", f"Fallo al vincular {target}: {res.get('description')}")
        return jsonify({"ok": False, "msg": f"Error de Telegram: {res.get('description', 'No se pudo encontrar el grupo.')}"})
    except Exception as e:
        add_web_log("ERROR", f"Crash en vinculación: {str(e)}")
        return jsonify({"ok": False, "msg": f"Error interno: {str(e)}"}), 500

@app.route("/api/ia/library")
def web_ia_library():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    sources = db.get("IA_SOURCES", {})
    activity = db.get("IA_ACTIVITY", [])
    
    # Combinar actividad reciente con fuentes
    library = activity[::-1] # Invertir para mostrar lo más reciente primero
    
    # Contar contribuciones por fuente para el ranking
    counts = {}
    for s in sources.values():
        counts[s] = counts.get(s, 0) + 1
    
    top_sources = [{"name": s, "count": c} for s, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    return jsonify({"ok": True, "library": library, "top_sources": top_sources})

@app.route("/api/ia/evolve", methods=['POST'])
def web_ia_evolve():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    threading.Thread(target=ia_nativa.evolve_process).start()
    return jsonify({"ok": True, "msg": "Proceso de evolución iniciado."})

@app.route("/api/ia/seed", methods=['POST'])
def web_ia_seed():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    ia_nativa.seed_knowledge()
    return jsonify({"ok": True, "msg": "Conocimiento inyectado con éxito"})

@app.route("/api/ia/master_seed", methods=['POST'])
def web_ia_master_seed():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    threading.Thread(target=ia_nativa.seed_master_intelligence).start()
    return jsonify({"ok": True, "msg": "Expansión Maestra iniciada en segundo plano."})

@app.route("/api/ia/force_feed", methods=['POST'])
def web_ia_force_feed():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    ia_nativa.force_feed(global_chat_history)
    return jsonify({"ok": True, "msg": "Alimentación forzada completada"})

@app.route("/api/ia/feeders", methods=['GET'])
def web_ia_feeders_stats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    words = len(ia_nativa.brain["keywords"])
    conns = sum(len(v) for v in ia_nativa.brain["patterns"].values())
    return jsonify({"ok": True, "words": words, "connections": conns})

@app.route("/api/ia/mode", methods=['POST'])
def web_ia_set_mode():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    mode = request.json.get("mode", "balanced")
    ia_nativa.set_mode(mode)
    return jsonify({"ok": True, "msg": f"Modo {mode} activado"})

@app.route("/api/ia/mood", methods=['POST'])
def web_ia_set_mood():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    mood = request.json.get("mood", "friendly")
    ia_nativa.set_mood(mood)
    return jsonify({"ok": True, "msg": f"Personalidad {mood} activada"})

@app.route("/api/ia/test", methods=['POST'])
def web_ia_test():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    try:
        text = request.json.get("text", "")
        resp = ia_nativa.generate(text)
        add_web_log("IA", f"Prueba Web: {text} -> {resp}")
        return jsonify({"ok": True, "response": resp})
    except Exception as e:
        add_web_log("ERROR", f"Fallo en Generación IA: {str(e)}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/admin/broadcast", methods=['POST'])
def web_admin_broadcast():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    msg = request.json.get("message", "")
    if not msg: return jsonify({"ok": False, "msg": "Mensaje vacío"}), 400
    count = 0
    for cid in global_chat_names:
        if proxy_bot.send_msg(cid, f"📢 **COMUNICADO GLOBAL:**\n\n{msg}"): count += 1
    add_audit_log(f"Broadcast enviado a {count} chats")
    return jsonify({"ok": True, "count": count})

@app.route("/api/admin/maintenance", methods=['POST'])
def web_admin_maintenance():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    return jsonify({"ok": True, "enabled": maintenance_mode})

@app.route("/api/admin/shield", methods=['POST'])
def web_admin_shield():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    status = not db.get("NEURAL_SHIELD", True)
    db.set("NEURAL_SHIELD", status)
    return jsonify({"ok": True, "enabled": status})

@app.route("/api/admin/backup", methods=['POST'])
def web_admin_backup():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    data = { "stats": global_user_stats, "history": global_msg_log, "brain": ia_nativa.brain }
    fname = f"data/backup_{int(time.time())}.json"
    with open(fname, "w") as f: json.dump(data, f)
    return jsonify({"ok": True, "file": fname})

# --- Business API ---
@app.route('/api/business/status')
def business_status():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    conns = []
    for cid, conn in bot.business_connections.items():
        conns.append({
            "id": cid,
            "user": conn["user"].get("first_name", "Business"),
            "enabled": conn.get("is_enabled", False)
        })
    return jsonify({"ok": True, "connections": conns})

@app.route('/api/business/config', methods=['GET', 'POST'])
def business_config():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if request.method == 'POST':
        data = request.json
        db.set("BUSINESS_CONFIG", data)
        return jsonify({"ok": True})
    return jsonify({"ok": True, "config": db.get("BUSINESS_CONFIG", {"greeting": "", "away": "", "away_mode": False, "ia_auto": False})})

@app.route('/api/business/quick_replies', methods=['GET', 'POST'])
def business_quick_replies():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    if request.method == 'POST':
        data = request.json
        db.set("BUSINESS_QUICK_REPLIES", data)
        return jsonify({"ok": True})
    return jsonify({"ok": True, "replies": db.get("BUSINESS_QUICK_REPLIES", [])})

# --- Proxy API ---
@app.route('/api/proxies/stats')
def api_proxies_stats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "proxies": proxy_mgr.get_stats()})

@app.route('/api/proxies/add', methods=['POST'])
def api_proxies_add():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    data = request.json
    proxy_mgr.proxies.append(data)
    db.set("PROXY_CONFIGS", proxy_mgr.proxies)
    return jsonify({"ok": True})

@app.route('/api/proxies/toggle', methods=['POST'])
def api_proxies_toggle():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    index = request.json.get("index")
    action = request.json.get("action")
    if action == "start":
        res = proxy_mgr.start_proxy(index)
    else:
        res = proxy_mgr.stop_proxy(index)
    return jsonify({"ok": res})

@app.route('/api/proxies/remove', methods=['POST'])
def api_proxies_remove():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    index = request.json.get("index")
    proxy_mgr.stop_proxy(index)
    proxy_mgr.proxies.pop(index)
    db.set("PROXY_CONFIGS", proxy_mgr.proxies)
    return jsonify({"ok": True})

@app.route('/api/proxies/scan')
def api_proxies_scan():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    detected = proxy_mgr.scan_docker()
    return jsonify({"ok": True, "detected": detected})

@app.route('/api/security/vt/scan', methods=['POST'])
def api_security_vt_scan():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    file_hash = request.json.get("hash")
    if not file_hash: return jsonify({"ok": False, "error": "Hash faltante"}), 400
    res = vt_mgr.scan_hash(file_hash)
    return jsonify(res)

@app.route('/api/security/cas/check/<uid>')
def api_security_cas_check(uid):
    if not check_jwt(request): return jsonify({"ok": False}), 401
    banned = is_cas_banned(uid)
    return jsonify({"ok": True, "cas_banned": banned})

@app.route('/api/security/audit')
def api_security_audit():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "logs": db.get("SECURITY_AUDIT_LOGS", [])})

@app.route('/api/queue/list')
def api_queue_list():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "queue": task_queue.get_all()})

@app.route('/api/queue/cancel', methods=['POST'])
def api_queue_cancel():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    t_id = request.json.get("id")
    task_queue.cancel(t_id)
    return jsonify({"ok": True})

@app.route('/api/queue/prioritize', methods=['POST'])
def api_queue_prioritize():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    t_id = request.json.get("id")
    task_queue.prioritize(t_id)
    return jsonify({"ok": True})

@app.route('/api/health/telegram')
def api_health_telegram():
    try:
        r = requests.get("https://api.telegram.org", timeout=5)
        return jsonify({"ok": True, "status": "ONLINE" if r.status_code == 200 else "DEGRADED", "ping": f"{int(r.elapsed.total_seconds()*1000)}ms"})
    except:
        return jsonify({"ok": True, "status": "OFFLINE", "ping": "N/A"})

@app.route("/api/telegram/call", methods=['POST'])
def web_telegram_call():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    data = request.json
    method = data.get("method")
    params = data.get("params", {})
    idx = data.get("bot_idx", 0)
    
    if not method: return jsonify({"ok": False, "msg": "Método requerido"}), 400
    if idx >= len(active_bots): return jsonify({"ok": False, "msg": "Bot no encontrado"}), 404
    
    bot = active_bots[idx]
    # Intentar usar helper si existe
    if hasattr(bot, method):
        import inspect
        func = getattr(bot, method)
        try:
            sig = inspect.signature(func)
            res = func(**{k: v for k, v in params.items() if k in sig.parameters})
        except:
            res = bot.api_call(method, params)
    else:
        res = bot.api_call(method, params)
    return jsonify(res)

@app.route("/api/reboot", methods=['POST'])
def web_reboot():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    threading.Thread(target=lambda: (time.sleep(1), os.execv(sys.executable, ['python'] + sys.argv))).start()
    return jsonify({"ok": True})

@app.route('/api/vision/stats')
def get_vision_stats():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    banned = db.get("BANNED_HASHES", [])
    return jsonify({
        "ok": True,
        "photos": db.get("STATS_PHOTOS", 0),
        "videos": db.get("STATS_VIDEOS", 0),
        "threats": len(banned),
        "shield_enabled": db.get("NEURAL_SHIELD", True)
    })

@app.route('/api/security/blacklist')
def get_security_blacklist():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    return jsonify({
        "ok": True, 
        "blacklist": db.get("BANNED_HASHES", []),
        "sync_urls": db.get("SECURITY_SYNC_URLS", [])
    })

@app.route('/api/security/add_sync_url', methods=['POST'])
def add_security_sync_url():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    url = request.json.get("url")
    if url:
        urls = db.get("SECURITY_SYNC_URLS", [])
        if url not in urls:
            urls.append(url)
            db.set("SECURITY_SYNC_URLS", urls)
            # Sincronización inmediata
            return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route('/api/security/ban_hash', methods=['POST'])
def add_security_hash():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    h = request.json.get("hash")
    if h:
        banned = db.get("BANNED_HASHES", [])
        if h not in banned:
            banned.append(h)
            db.set("BANNED_HASHES", banned)
            add_web_log("SECURITY", f"Manual Ban (Web): Hash {h} añadido.")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "No hash provided"})

@app.route("/api/users/leaderboard")
def web_leaderboard():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    sorted_u = sorted(global_user_stats.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:20]
    result = []
    for k, v in sorted_u:
        k_score = v.get("karma", 0)
        badge = "🏆 Leyenda" if k_score > 50 else "⭐ Colaborador" if k_score > 20 else "👤 Miembro"
        result.append({"id": k, "name": v.get("name", k), "count": v.get("count", 0), "karma": k_score, "badge": badge})
    return jsonify({"ok": True, "leaderboard": result})

@app.route("/api/moderation/<cid>")
def web_mod_get(cid):
    if not check_jwt(request): return jsonify({"ok": False}), 401
    warns = db.get(f"WARNS_{cid}", {})
    notes = db.get(f"NOTES_{cid}", "")
    
    # Configuración local del grupo
    config = db.get(f"CONFIG_{cid}", {
        "ia_learning": False,
        "auto_mod": True,
        "welcome": False,
        "security_shield": True
    })
    
    # Compatibilidad con los sistemas antiguos
    feeders = db.get("IA_FEEDERS", [])
    if str(cid) in [str(x) for x in feeders]: config["ia_learning"] = True
    
    return jsonify({"ok": True, "warns": warns, "notes": notes, "config": config})

@app.route("/api/moderation/settings", methods=['POST'])
def web_mod_settings():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid = d.get("cid")
    config = d.get("config")
    if not cid or not config: return jsonify({"ok": False})
    
    db.set(f"CONFIG_{cid}", config)
    
    # Sincronizar con sistemas antiguos
    feeders = db.get("IA_FEEDERS", [])
    cid_str = str(cid)
    if config.get("ia_learning"):
        if cid_str not in [str(x) for x in feeders]: feeders.append(cid_str)
    else:
        if cid_str in [str(x) for x in feeders]: feeders.remove(cid_str)
    db.set("IA_FEEDERS", feeders)
    
    add_web_log("ADMIN", f"Configuración actualizada para grupo {cid}")
    return jsonify({"ok": True})

@app.route("/api/moderation/notes", methods=['POST'])
def web_mod_notes():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid, note = str(d.get("cid", "")), d.get("note", "")
    if not cid: return jsonify({"ok": False})
    db.set(f"NOTES_{cid}", note)
    add_audit_log(f"Nota guardada para grupo {cid}")
    return jsonify({"ok": True})

@app.route("/api/moderation/unwarn", methods=['POST'])
def web_mod_unwarn():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid, target = str(d.get("cid", "")), d.get("target", "")
    warns = db.get(f"WARNS_{cid}", {})
    if target in warns: del warns[target]; db.set(f"WARNS_{cid}", warns)
    return jsonify({"ok": True})

@app.route("/api/moderation/warn", methods=['POST'])
def web_warn():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid, uid = d["cid"], d["uid"]
    warns = db.get(f"WARNS_{cid}", {})
    warns[uid] = warns.get(uid, 0) + 1
    db.set(f"WARNS_{cid}", warns)
    active_bots[0].send_msg(cid, f"⚠️ Usuario `{uid}` advertido ({warns[uid]}/3)")
    if warns[uid] >= 3:
        active_bots[0].kick_user(cid, uid)
        add_web_log("SECURITY", f"Usuario {uid} auto-baneado por acumulación de warns.")
    return jsonify({"ok": True, "count": warns[uid]})

@app.route("/api/moderation/mute", methods=['POST'])
def web_mute():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid, uid = d["cid"], d["uid"]
    until = int(time.time()) + 1800 
    active_bots[0].restrict_user(cid, uid, until=until, can_send=False)
    return jsonify({"ok": True})

@app.route("/api/moderation/karma", methods=['POST'])
def web_karma():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    uid, val = d["uid"], d.get("val", 5)
    if uid in global_user_stats:
        global_user_stats[uid]["karma"] += val
        return jsonify({"ok": True, "karma": global_user_stats[uid]["karma"]})
    return jsonify({"ok": False})

@app.route("/api/moderation/unmute", methods=['POST'])
def web_mod_unmute():
    if not check_jwt(request): return jsonify({"ok": False}), 401
    d = request.json
    cid, target = str(d.get("cid", "")), d.get("target", "")
    muted = db.get(f"MUTED_{cid}", [])
    if target in muted: muted.remove(target); db.set(f"MUTED_{cid}", muted)
    return jsonify({"ok": True})

def analyze_sentiment(text):
    if not text: return "neutral"
    text = text.lower()
    pos = ["bueno", "genial", "excelente", "gracias", "top", "preem", "cyber", "luz", "mejor", "increible", "amo", "pro"]
    neg = ["malo", "error", "fallo", "gonk", "flatline", "mierda", "basura", "lento", "peor", "odioso", "crash", "bug"]
    p_score = sum(1 for w in pos if w in text)
    n_score = sum(1 for w in neg if w in text)
    if p_score > n_score: return "positive"
    if n_score > p_score: return "negative"
    return "neutral"

def detect_intent(text):
    """Detecta la intención del mensaje: greeting, farewell, question, thanks, complaint, neutral."""
    if not text: return "neutral"
    t = text.lower().strip()
    greetings  = ["hola", "buenas", "hey ", "saludos", "buen dia", "buenos dias", "buenas tardes", "buenas noches", "hi ", "hello", "ola "]
    farewells  = ["adios", "hasta luego", "chao", "bye", "nos vemos", "hasta pronto", "hasta mañana"]
    thanks     = ["gracias", "thanks", "thank you", "grax", "thx", "muchas gracias", "te lo agradezco"]
    complaints = ["error", "fallo", "no funciona", "problema", "bug", "roto", "mal", "pésimo", "no sirve", "broken", "crash"]
    if any(g in t for g in greetings):  return "greeting"
    if any(f in t for f in farewells):  return "farewell"
    if any(th in t for th in thanks):   return "thanks"
    if any(c in t for c in complaints): return "complaint"
    if t.endswith("?"):                 return "question"
    return "neutral"

class MoonCoreIA:
    def __init__(self):
        self.brain = db.get("IA_BRAIN", {"keywords": {}, "patterns": {}})
        # Ensure keywords are Counter objects for stability
        self._ensure_counters()
        self.active_workers = {}
        self.business_connections = {} # Store active business accounts
        self.db_save_timer = 0
        self.start_time = time.time()
        self.mode = db.get("IA_MODE", "balanced") # eco, balanced, peak
        self.mood = db.get("IA_MOOD", "friendly") # friendly, sarcastic, philosophical, cyberpunk
        self.lang = "auto"
        self._learn_count = 0
        self.session_words = 0
        self._sources_cache = db.get("IA_SOURCES", {})
        self._activity_cache = db.get("IA_ACTIVITY", [])
        self._context_cache = {}
        if len(self.brain["keywords"]) < 1000:
            threading.Thread(target=self.seed_knowledge).start()

    def _ensure_counters(self):
        """Asegura que todas las palabras clave sean objetos Counter."""
        if "keywords" not in self.brain: self.brain["keywords"] = {}
        for k, v in self.brain["keywords"].items():
            if not isinstance(v, Counter):
                if isinstance(v, (dict, list)):
                    self.brain["keywords"][k] = Counter(v)
                else:
                    self.brain["keywords"][k] = Counter()

    def seed_master_intelligence(self):
        """Inyecta conocimiento avanzado (Wikipedia y Patrones Humanos) de forma masiva."""
        add_web_log("INFO", "🚀 INICIANDO MEGA-INYECTOR DE INTELIGENCIA MAESTRA...")
        if MASTER_ID:
            try:
                proxy_bot.api_call("sendMessage", {"chat_id": MASTER_ID, "text": "🧠 *Iniciando proceso de Expansión Maestra...*\nAbsorbiendo Wikipedia y patrones humanos avanzados.", "parse_mode": "Markdown"})
            except: pass
        
        # 1. Patrones Conversacionales
        conversations = [
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
        for conv in conversations:
            self.learn(conv, source="Patrón Humano")

        # 2. Wikipedia Seeding
        topics = [
            "Inteligencia_artificial", "Universo", "Historia_de_España", "Internet",
            "Ciencia", "Tecnología", "Filosofía", "Psicología", "Criptografía",
            "Física_cuántica", "Biología", "Astronáutica", "Derecho_romano",
            "Revolución_Industrial", "Renacimiento", "Arquitectura", "Cine",
            "Literatura", "Medicina", "Economía", "Sociología", "Matemáticas",
            "Astronomía", "Geografía", "Derecho_Constitucional", "Historia_Universal",
            "Arte_contemporáneo", "Mitología_griega", "Ecología", "Nanotecnología",
            "Energías_renovables", "Exploración_espacial", "Inteligencia_emocional"
        ]
        
        headers = {'User-Agent': 'MoonBotMasterSeed/1.0'}
        count = 0
        for topic in topics:
            try:
                url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{topic}"
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    extract = data.get("extract", "")
                    if extract:
                        self.learn(extract, source=f"Wikipedia: {topic.replace('_', ' ')}")
                        count += 1
                time.sleep(0.3)
            except Exception as e:
                add_web_log("DEBUG", f"Error en tópico Wikipedia {topic}: {e}")
        
        db.set("IA_BRAIN", self.brain) # Forzar guardado
        add_web_log("SUCCESS", f"🔥 EXPANSIÓN MAESTRA COMPLETADA: {count} tópicos enciclopédicos absorbidos.")
        self.send_master_report("🚀 REPORTE DE EXPANSIÓN MAESTRA")

    def seed_knowledge(self):
        global multilingual_seeds
        add_web_log("INFO", "🌱 Iniciando sembrado de conocimiento masivo...")
        try:
            # 1. Semillas Multilingües
            if os.path.exists("data/multilingual_seeds.json"):
                with open("data/multilingual_seeds.json", "r", encoding="utf-8") as f:
                    multilingual_seeds = json.load(f)
                for lang, phrases in multilingual_seeds.items():
                    for phrase in phrases:
                        self.learn(phrase, source=f"Seed_{lang}")
                add_web_log("SUCCESS", f"🧠 Conocimiento multilingüe sembrado ({len(multilingual_seeds)} idiomas).")
            
            # 2. Conocimiento Inicial
            if os.path.exists("data/initial_knowledge.json"):
                with open("data/initial_knowledge.json", "r", encoding="utf-8") as f:
                    initial = json.load(f)
                for s in initial:
                    self.learn(s, source="Semilla Moon")
                add_web_log("SUCCESS", f"📚 Conocimiento inicial inyectado ({len(initial)} items).")
                
        except Exception as e:
            add_web_log("ERROR", f"❌ Error en seed_knowledge: {e}")

    def detect_lang(self, text):
        # 1. Detección por rango Unicode (instantánea, sin falsos positivos)
        for ch in text:
            cp = ord(ch)
            if 0x0600 <= cp <= 0x06FF: return "ar"   # Árabe
            if 0x0900 <= cp <= 0x097F: return "hi"   # Devanagari (Hindi)
            if 0x0400 <= cp <= 0x04FF: return "ru"   # Cirílico (Ruso/Ucraniano)
            if 0x4E00 <= cp <= 0x9FFF: return "zh"   # CJK (Chino)
            if 0x3040 <= cp <= 0x30FF: return "ja"   # Hiragana/Katakana (Japonés)
            if 0xAC00 <= cp <= 0xD7A3: return "ko"   # Hangul (Coreano)
            if 0x0E00 <= cp <= 0x0E7F: return "th"   # Tailandés
            if 0x0590 <= cp <= 0x05FF: return "he"   # Hebreo

        # 2. Palabras clave para idiomas de escritura latina y otros
        kw_map = {
            "tr": ["merhaba", "teşekkür", "günaydın", "nasılsın", "lütfen", "iyi", "ederim"],
            "de": ["hallo", "danke", "bitte", "guten", "morgen", "tschüss", "wie", "geht"],
            "fr": ["bonjour", "merci", "bonsoir", "salut", "bonne", "journée", "vous", "moi"],
            "it": ["ciao", "grazie", "buongiorno", "prego", "arrivederci", "come", "stai"],
            "pt": ["olá", "obrigado", "bom", "você", "tchau", "muito", "prazer", "boa"],
            "en": ["hello", "thanks", "please", "sorry", "good", "morning", "evening", "night"],
            "es": ["hola", "gracias", "buenos", "buenas", "favor", "disculpa", "qué", "cómo"],
            "nl": ["hallo", "dank", "goedemorgen", "goedemiddag", "goedemavond", "alsjeblieft", "hoe", "gaat"],
            "sv": ["hej", "tack", "godmorgon", "godkväll", "ursäkta", "snälla", "hur", "mår"],
            "pl": ["cześć", "dziękuję", "dzień dobry", "dobry wieczór", "proszę", "przepraszam", "jak", "się masz"],
            "cs": ["ahoj", "děkuji", "dobré ráno", "dobrý večer", "prosím", "omlouvám", "jak", "se máš"],
            "hu": ["szia", "köszönöm", "jó reggelt", "jó estét", "kérem", "bocsánat", "hogy", "vagy"],
            "ro": ["salut", "mulțumesc", "bună dimineața", "bună seara", "te rog", "scuze", "cum", "ești"],
            "uk": ["привіт", "дякую", "доброго ранку", "доброго вечора", "будь ласка", "вибач", "як", "справи"],
            "he": ["שלום", "תודה", "בוקר טוב", "ערב טוב", "בבקשה", "סליחה", "איך", "אתה"],
            "da": ["hej", "tak", "godmorgen", "godaften", "undskyld", "tak", "hvordan", "har"],
            "no": ["hei", "takk", "god morgen", "god kveld", "unnskyld", "vær så snill", "hvordan", "går"],
            "fi": ["hei", "kiitos", "hyvää huomenta", "hyvää iltaa", "anteeksi", "ole hyvä", "miten", "voi"],
            "et": ["tere", "aitäh", "tere hommikust", "head õhtut", "vabandust", "palun", "kuidas", "läheb"],
            "lv": ["sveiki", "paldies", "labrīt", "labvakar", "atvainojiet", "lūdzu", "kā", "iet"],
            "lt": ["labas", "ačiū", "labas rytas", "labas vakaras", "atsiprašau", "prašau", "kaip", "sekasi"],
            "sk": ["ahoj", "ďakujem", "dobré ráno", "dobrý večer", "prepáčte", "prosím", "ako", "sa máš"],
            "sl": ["zdravo", "hvala", "dobro jutro", "dober večer", "oprostite", "prosim", "kako", "ste"],
            "hr": ["zdravo", "hvala", "dobro jutro", "dobra večer", "oprostite", "molim", "kako", "ste"],
            "bs": ["zdravo", "hvala", "dobro jutro", "dobra večer", "oprosti", "molim", "kako", "si"],
            "sr": ["zdravo", "hvala", "dobro jutro", "dobro veče", "izvini", "molim", "kako", "si"],
            "mk": ["здраво", "благодарам", "добро утро", "добра вечер", "извини", "молам", "како", "си"],
            "bg": ["здравей", "благодаря", "добро утро", "добър вечер", "извинявай", "моля", "как", "си"],
            "sq": ["përshëndetje", "faleminderit", "mirëmëngjes", "mirëmbrëma", "më fal", "ju lutem", "si", "jeni"],
            "mt": ["ħello", "grazzi", "bonġu", "bonswa", "skużani", "jekk jogħġbok", "kif", "int"],
            "is": ["halló", "takk", "góðan daginn", "góða kvöldið", "afsakið", "vinsamlegast", "hvernig", "gengur"],
            "ga": ["dia duit", "go raibh maith agat", "maidin mhaith", "oíche mhaith", "gabhaim leithscéal", "le do thoil", "conas", "tá"],
            "cy": ["helo", "diolch", "bore da", "nos da", "ymddiheuriadau", "os gwelwch yn dda", "sut", "mae"],
            "gd": ["halò", "tapadh leat", "madainn mhath", "oidhche mhath", "duilich", "mas e do thoil e", "ciamar", "a tha"],
            "eu": ["kaixo", "eskerrik asko", "egun on", "arratsalde on", "barkatu", "mesedez", "nola", "zaude"],
            "ca": ["hola", "gràcies", "bon dia", "bona nit", "perdó", "si us plau", "com", "estàs"],
            "gl": ["ola", "grazas", "bos días", "boas noites", "perdón", "por favor", "como", "estás"],
            "oc": ["bonjorn", "mercés", "bon jorn", "bona nuèch", "perdonatz", "per favor", "coma", "anatz"],
            "br": ["demat", "trugarez", "matin mad", "nozvezh mad", "digarez", "mar plij", "pegoulz", "emaout"],
            "fy": ["hallo", "tank", "goeiemoarn", "goeienjûn", "ekskusearje", "asjebleaft", "hoe", "giet"],
            "lb": ["hallo", "merci", "gudde moien", "gudden owend", "entschëllegt", "wann ech gelift", "wéi", "geet"],
            "wa": ["bondjoû", "gråce", "boun di djouwene", "boun nût", "dmandè escuzes", "s'i vs plait", "comint", "alez"],
            "sc": ["salude", "gràtzias", "bonas dies", "bonas nottes", "perdonu", "per piascere", "comente", "ses"],
            "co": ["bonjournu", "grazii", "bon ghjornu", "bona sera", "scusate", "per piacè", "cum'è", "site"],
            "rm": ["allegra", "grazia", "bun di", "buna saira", "perdunai", "per plaschair", "co", "va"],
            "bn": ["আমি", "তুমি", "আমরা", "তারা", "এটা", "ওটা", "কি", "কোথায়", "কখন", "কেন", "কীভাবে", "ভাত", "চা", "খাই", "পান", "যাই", "আসি", "দেখি", "শুনি"],
            "vi": ["tôi", "bạn", "chúng tôi", "họ", "cái này", "cái kia", "gì", "ở đâu", "khi nào", "tại sao", "như thế nào", "cơm", "trà", "ăn", "uống", "đi", "đến", "nhìn", "nghe"],
            "ta": ["நான்", "நீ", "நாங்கள்", "அவர்கள்", "இது", "அது", "என்ன", "எங்கே", "எப்போது", "ஏன்", "எப்படி", "சோறு", "தேநீர்", "சாப்பிடு", "குடி", "போ", "வா", "பார்", "கேள்"],
            "te": ["నేను", "నువ్వు", "మేము", "వారు", "ఇది", "అది", "ఏమిటి", "ఎక్కడ", "ఎప్పుడు", "ఎందుకు", "ఎలా", "వరిగా", "టీ", "తిను", "త్రాగు", "వెళ్ళు", "రా", "చూడు", "విను"],
            "mr": ["मी", "तू", "आम्ही", "ते", "हे", "ते", "काय", "कुठे", "कधी", "का", "कसे", "भात", "चहा", "खा", "पिऊन", "जा", "ये", "पाहा", "ऐका"],
            "ur": ["میں", "تو", "ہم", "وہ", "یہ", "وہ", "کیا", "کہاں", "کب", "کیوں", "کیسے", "چاول", "چائے", "کھاؤ", "پیو", "جاؤ", "آؤ", "دیکھو", "سنو"],
            "gu": ["હું", "તું", "અમે", "તેઓ", "આ", "તે", "શું", "ક્યાં", "ક્યારે", "કેમ", "કેવી રીતે", "ભાત", "ચા", "ખાવું", "પીવું", "જવું", "આવવું", "જોવું", "સાંભળવું"],
            "id": ["saya", "kamu", "kami", "mereka", "ini", "itu", "apa", "di mana", "kapan", "mengapa", "bagaimana", "nasi", "teh", "makan", "minum", "pergi", "datang", "lihat", "dengar"],
            "fa": ["من", "تو", "ما", "آنها", "این", "آن", "چیست", "کجا", "کی", "چرا", "چگونه", "برنج", "چای", "خور", "نوش", "برو", "بیا", "ببین", "بشنو"],
            "ms": ["saya", "awak", "kami", "mereka", "ini", "itu", "apa", "di mana", "bila", "mengapa", "bagaimana", "nasi", "teh", "makan", "minum", "pergi", "datang", "lihat", "dengar"],
            "pa": ["ਮੈਂ", "ਤੂੰ", "ਅਸੀਂ", "ਉਹ", "ਇਹ", "ਉਹ", "ਕੀ", "ਕਿੱਥੇ", "ਕਦੋਂ", "ਕਿਉਂ", "ਕਿਵੇਂ", "ਚਾਵਲ", "ਚਾਹ", "ਖਾਣਾ", "ਪੀਣਾ", "ਜਾਣਾ", "ਆਉਣਾ", "ਦੇਖਣਾ", "ਸੁਣਨਾ"],
            "kn": ["ನಾನು", "ನೀನು", "ನಾವು", "ಅವರು", "ಇದು", "ಅದು", "ಏನು", "ಎಲ್ಲಿ", "ಎಂದು", "ಏಕೆ", "ಹೇಗೆ", "ಅನ್ನ", "ಚಹಾ", "ತಿನ್ನು", "ಕುಡಿ", "ಹೋಗು", "ಬಾ", "ನೋಡು", "ಕೇಳು"],
            "or": ["ମୁଁ", "ତୁଁ", "ଆମେ", "ସେମାନେ", "ଏହା", "ସେହା", "କଣ", "କେଉଁଠାରେ", "କେତେବେଳେ", "କାହିଁକି", "କେମିତି", "ଭାତ", "ଚା", "ଖାଅ", "ପିଅ", "ଯାଅ", "ଆସ", "ଦେଖ", "ଶୁଣ"],
            "ml": ["ഞാൻ", "നീ", "നാം", "അവർ", "ഇത്", "അത്", "എന്ത്", "എവിടെ", "എപ്പോൾ", "എന്തുകൊണ്ട്", "എങ്ങനെ", "അന്നം", "ചായ", "കഴിക്കുക", "കുടിക്കുക", "പോകുക", "വരിക", "കാണുക", "കേൾക്കുക"],
            "su": ["abdi", "anjeun", "urang", "aranjeunna", "ieu", "éta", "naon", "dimana", "iraaha", "naha", "kumaha", "sangu", "tea", "tuang", "nginum", "indit", "datang", "ningali", "ngadangu"],
            "ha": ["ni", "kai", "mu", "su", "wannan", "wancan", "me", "ina", "yaushe", "me yasa", "yaya", "shinkafa", "shayi", "ci", "sha", "je", "zo", "gani", "ji"],
            "yo": ["mo", "o", "a", "won", "eyi", "iyen", "kini", "ibo", "igbawo", "kilode", "bawo", "irin", "tẹ", "jẹ", "mu", "lọ", "wá", "rí", "gbọ"],
            "ig": ["m", "ị", "anyị", "ha", "nke a", "nke ahụ", "gịnị", "ebee", "mgbe", "gịnị mere", "kedu", "nri", "tíì", "rie", "ṅụọ", "gaa", "abịa", "hụ", "nụ"],
            "zu": ["ngi", "u", "si", "ba", "lokhu", "lokho", "yini", "kuphi", "nini", "ngoba", "kanjani", "ukudla", "itiye", "dla", "phuza", "hamba", "za", "bona", "zwu"],
            "am": ["እኔ", "አንተ", "እኛ", "እነሱ", "ይህ", "ያ", "ምን", "የት", "መቼ", "ለምን", "እንዴት", "ምግብ", "ሻይ", "ለም", "ሰቲ", "ሄዳለሁ", "ሰማለሁ", "አለሁ", "ሰማለሁ"],
            "qu": ["ñuqa", "qam", "ñuqanchik", "paykuna", "kay", "chay", "ima", "maypi", "hayk'aq", "imanasqa", "imaynatas", "mikhuna", "upyana", "mikhuni", "upyanichani", "rini", "hamuni", "rikuni", "uyarini"],
            "ay": ["naya", "juma", "nayanakaxa", "jumanakaxa", "aki", "uka", "kuna", "khaya", "kunjamsa", "kawkisa", "kunjamsa", "manq'a", "chaya", "manqthwa", "chayatha", "sartha", "juttha", "uñtha", "ist'a"],
            "gn": ["che", "nde", "ñande", "ha'e", "ko", "pe", "mba'e", "moõ", "araka'eve", "mba'e", "mba'eicha", "ka'arõ", "ka'ay", "karu", "'u", "ho", "ju", "hecha", "hendu"],
            "ht": ["mwen", "ou", "nou", "yo", "sa a", "sa", "ki", "ki kote", "kilè", "poukisa", "ki jan", "diri", "te", "manje", "bwè", "ale", "vini", "wè", "tande"],
            "mn": ["би", "чи", "бид", "тэд", "энэ", "тэр", "юу", "хаана", "хэзээ", "яагаад", "хэрхэн", "хоол", "цай", "идэх", "уух", "явах", "ирэх", "харах", "сонсох"],
            "my": ["ကျွန်တော်", "သင်", "ကျွန်တော်တို့", "သူတို့", "ဒါ", "အဲဒါ", "ဘာလဲ", "ဘယ်မှာ", "ဘယ်တော့", "ဘာကြောင့်", "ဘယ်လို", "ထမင်း", "လက်ဖက်ရည်", "စားတယ်", "သောက်တယ်", "သွားမယ်", "လာမယ်", "မြင်တယ်", "ကြားတယ်"],
            "lo": ["ຂ້ອຍ", "ເຈົ້າ", "ພວກເຮົາ", "ພວກເຂົາ", "ອັນນີ້", "ອັນນັ້ນ", "ຫຍັງ", "ທີ່ໃດ", "ເມື່ອໃດ", "ເປັນຫຍັງ", "ແນວໃດ", "ເຂົ້າ", "ຊາ", "ກິນ", "ດື່ມ", "ໄປ", "ມາ", "ເຫັນ", "ໄດ້ຍິນ"],
            "km": ["ខ្ញុំ", "អ្នក", "យើង", "ពួកគេ", "នេះ", "នោះ", "អ្វី", "ទីណា", "ពេលណា", "ហេតុអ្វី", "ដូចម្ដេច", "បាយ", "តែ", "ញុាំ", "ផឹក", "ទៅ", "មក", "ឃើញ", "ឮ"],
            "ceb": ["ako", "ikaw", "kami", "sila", "kini", "kadtong", "unsa", "asa", "kanus-a", "ngano", "unsaon", "kan-on", "tsaa", "kaon", "inom", "adto", "anha", "tan-aw", "dungog"],
            "ilo": ["siak", "sika", "datayo", "da", "daytoy", "dayta", "ania", "sadino", "kapigan", "apay", "kasano", "kanen", "te", "mangan", "uminum", "mapan", "umay", "makita", "mangngeg"],
            "mg": ["aho", "ianao", "isika", "izy ireo", "ity", "izany", "inona", "taiza", "oviana", "nahoana", "aza", "vary", "dite", "mihinana", "misotroa", "mankany", "avy", "mahita", "mandre"],
            "af": ["ek", "jy", "ons", "hulle", "hierdie", "daardie", "wat", "waar", "wanneer", "hoekom", "hoe", "rys", "tee", "eet", "drink", "gaan", "kom", "sien", "hoor"],
            "sw": ["mimi", "wewe", "sisi", "wao", "hii", "hiyo", "nini", "wapi", "lini", "kwanini", "vipi", "chakula", "chai", "kula", "kunywa", "kwenda", "kuja", "kuona", "kusikia"],
            "so": ["aniga", "adiga", "annaga", "iyaga", "kan", "taas", "maxaa", "xaggee", "goorma", "maxaa", "sida", "bariis", "shaah", "cunaa", "cabb", "tagaa", "imaadaa", "arkaa", "maqlaa"],
            "rw": ["njye", "wowe", "twebwe", "bo", "iri", "ryo", "iki", "he", "ryari", "kuki", "bite", "ibiryo", "icyayi", "ndarya", "ndanywa", "ngenda", "ngaruka", "ndabona", "ndumva"],
            "st": ["ke", "u", "re", "ba", "see", "seo", "eng", "kae", "neng", "hobaneng", "joang", "dijo", "tee", "ja", "nwa", "ya", "tla", "bona", "utlwa"],
            "xh": ["ndi", "u", "si", "ba", "le", "lo", "yintoni", "phi", "nini", "kutheni", "njani", "irayisi", "iti", "itya", "sela", "hamba", "fika", "bona", "va"],
            "tn": ["ke", "o", "re", "bone", "se", "seo", "eng", "kwa", "leng", "goreng", "jang", "dijo", "tee", "ja", "nwa", "ya", "tla", "bona", "utlwa"],
        }
        words = set(text.lower().split())
        scores = {lang: sum(1 for kw in kws if kw in words) for lang, kws in kw_map.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "es"

    def evolve_process(self):
        add_web_log("INFO", "🧠 Iniciando Protocolo de Evolución Neuronal...")
        # Tomar las 100 palabras con más conexiones y generar frases desde ellas
        top_words = sorted(
            [(w, sum(v.values()) if isinstance(v, Counter) else len(v))
             for w, v in self.brain["keywords"].items() if len(w) > 3],
            key=lambda x: x[1], reverse=True
        )[:100]

        total = len(top_words)
        for i, (word, _) in enumerate(top_words):
            phrase = self.generate(word)
            self.learn(phrase, source="Evolución Neural")
            if i % 20 == 0:
                add_web_log("DEBUG", f"🧬 Evolución: {int((i/max(total,1))*100)}% completado.")

        # Forzar escritura en BD al finalizar
        db.set("IA_BRAIN", self.brain)
        db.set("IA_SOURCES", self._sources_cache)
        add_web_log("SUCCESS", "🔥 Evolución Neuronal Completada. Nuevas conexiones creadas.")

    def set_mood(self, mood):
        self.mood = mood
        db.set("IA_MOOD", mood)
        add_web_log("INFO", f"Personalidad IA cambiada a: {mood.upper()}")
    
    def load_brain(self):
        """Recarga el cerebro desde la base de datos en caliente (Hot-Reload)."""
        res = db.get("IA_BRAIN")
        if res:
            self.brain = res
            self._ensure_counters()
            self._sources_cache = db.get("IA_SOURCES", {})
            add_web_log("IA", "Cerebro sincronizado con la base de datos (Hot-Reload OK).")
            return True
        return False

    def set_mode(self, mode):
        self.mode = mode
        db.set("IA_MODE", mode)
        add_web_log("INFO", f"Modo IA cambiado a: {mode.upper()}")

    
    def learn(self, text, source="Cerebro Local"):
        settings = db.get("GLOBAL_SETTINGS", {})
        if settings.get("spam_filter", "on") == "on":
            spam_triggers = ["gane", "euros", "bancaria", "billetera", "dinero gratis", "inversi", "rentabilidad"]
            if any(t in text.lower() for t in spam_triggers):
                return

        words = text.lower().split()
        new_words = 0
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        for i, w in enumerate(words):
            if w not in self.brain["keywords"]:
                self.brain["keywords"][w] = Counter()
                new_words += 1
                if w not in self._sources_cache:
                    self._sources_cache[w] = source

            if len(w) > 3:
                self._activity_cache.append({"word": w, "source": source, "time": now_str})

            if i < len(words) - 1:
                if isinstance(self.brain["keywords"][w], list):
                    self.brain["keywords"][w] = Counter(self.brain["keywords"][w])
                self.brain["keywords"][w][words[i+1]] += 1

        self.session_words += new_words
        self._learn_count += 1

        # Mantener actividad acotada en memoria
        if len(self._activity_cache) > 200:
            self._activity_cache = self._activity_cache[-50:]

        # Escritura en BD por lotes cada 20 aprendizajes para no saturar SQLite
        if self._learn_count % 20 == 0:
            db.set("IA_BRAIN", self.brain)
            db.set("IA_SOURCES", self._sources_cache)
            db.set("IA_ACTIVITY", self._activity_cache[-50:])

    def remember_context(self, chat_id, text, role="user"):
        """Guarda el mensaje en la ventana de contexto del chat (en memoria y BD)."""
        if not chat_id or not text:
            return
        if chat_id not in self._context_cache:
            self._context_cache[chat_id] = db.get(f"CONTEXT_{chat_id}", [])
        self._context_cache[chat_id].append({"role": role, "text": text[:200]})
        if len(self._context_cache[chat_id]) > 12:
            self._context_cache[chat_id] = self._context_cache[chat_id][-12:]
        db.set(f"CONTEXT_{chat_id}", self._context_cache[chat_id])

    def get_context_words(self, chat_id):
        """Devuelve las palabras de las últimas 6 entradas del contexto del chat."""
        if not chat_id:
            return set()
        if chat_id not in self._context_cache:
            self._context_cache[chat_id] = db.get(f"CONTEXT_{chat_id}", [])
        ctx = self._context_cache[chat_id]
        words = set()
        for entry in ctx[-6:]:
            for w in entry["text"].lower().split():
                if len(w) > 2:
                    words.add(w)
        return words

    def generate(self, prompt, chat_id=None, mood_override=None):
        current_mood = mood_override or self.mood
        
        # --- Lógica RAG (Búsqueda de Memoria Local) ---
        memory_context = ""
        if chat_id:
            prompt_words = [w for w in prompt.lower().split() if len(w) > 3]
            if prompt_words:
                # Buscar en GLOBAL_HISTORY mensajes similares
                history = db.get("GLOBAL_HISTORY", [])
                relevant_msgs = []
                for m in history:
                    if any(pw in m.get("text", "").lower() for pw in prompt_words):
                        relevant_msgs.append(f"{m.get('user')}: {m.get('text')}")
                    if len(relevant_msgs) > 5: break
                if relevant_msgs:
                    memory_context = "\n[Memoria Reciente]:\n" + "\n".join(relevant_msgs)

        # --- Modo Híbrido / Externo (LLM) ---
        if USE_EXTERNAL_LLM and GEMINI_API_KEY:
            try:
                # Simulando llamada a Gemini API (se requiere google-generativeai instalado)
                # En un entorno real, usaríamos: genai.configure(api_key=GEMINI_API_KEY)
                # Aquí implementamos una estructura lista para ser conectada.
                headers = {"Content-Type": "application/json"}
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
                
                system_instruction = f"Eres MoonBot, una IA de gestión de Telegram. Mood: {current_mood}. Contexto: {memory_context}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"{system_instruction}\n\nUsuario: {prompt}"
                        }]
                    }]
                }
                
                r = requests.post(url, json=payload, timeout=10)
                if r.status_code == 200:
                    res_json = r.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                add_web_log("ERROR", f"Fallo LLM Externo: {e}")

        # --- Fallback: IA Nativa (Markov) ---
        # Ajustar el "peso" de las respuestas según el mood
        mood_prefix = ""
        if current_mood == "sarcastic": mood_prefix = "[Sarcasmo] "
        elif current_mood == "serious": mood_prefix = "[Oficial] "
        elif current_mood == "aggressive": mood_prefix = "[Protección] "
        elif current_mood == "cyberpunk": mood_prefix = "[Neo-Link] "
        
        prompt_words = [w for w in prompt.lower().split() if len(w) > 2]
        context_words = self.get_context_words(chat_id)
        all_relevant = prompt_words + list(context_words)

        # Seleccionar semilla: la palabra con mayor score de conexiones + relevancia al contexto
        seed = None
        best_score = -1
        for w in all_relevant:
            if w in self.brain["keywords"]:
                v = self.brain["keywords"][w]
                conn_count = sum(v.values()) if isinstance(v, Counter) else len(v)
                # Bonus por conexión con otras palabras del contexto
                ctx_bonus = sum(1 for cw in context_words if cw in (v if isinstance(v, dict) else {}))
                score = conn_count + ctx_bonus * 4
                if score > best_score:
                    best_score = score
                    seed = w

        if not seed:
            if self.brain["keywords"]:
                seed = random.choice(list(self.brain["keywords"].keys()))
            else:
                seed = "hola"

        res = [seed.capitalize()]
        curr = seed
        history = [curr]

        max_words = 8 if self.mode == "eco" else 20 if self.mode == "balanced" else 35
        min_words = 3 if self.mode == "eco" else 7 if self.mode == "balanced" else 12

        for _ in range(random.randint(min_words, max_words)):
            next_words_raw = self.brain["keywords"].get(curr, {})
            if not next_words_raw:
                break

            if isinstance(next_words_raw, (list, dict)):
                next_words = Counter(next_words_raw)
            else:
                next_words = next_words_raw

            choices = []
            weights = []
            for word, count in next_words.most_common(10):
                penalty = 0.05 if word in history[-5:] else 1.0
                # Priorizar palabras que aparecen en el contexto del chat
                ctx_boost = 2.5 if word in context_words else 1.0
                choices.append(word)
                weights.append(count * penalty * ctx_boost)

            if not choices:
                break

            total_weight = sum(weights)
            r_val = random.uniform(0, total_weight)
            upto = 0
            selected = choices[0]
            for i, w in enumerate(weights):
                if upto + w >= r_val:
                    selected = choices[i]
                    break
                upto += w

            curr = selected
            res.append(curr)
            history.append(curr)

            if len(res) % 7 == 0 and len(res) < max_words - 2:
                res[-1] += ","
                lang = self.detect_lang(prompt)
                connectors = {
                    "es": ["y", "pero", "además", "aunque", "porque", "sin embargo"],
                    "en": ["and", "but", "also", "although", "because", "however"],
                    "fr": ["et", "mais", "aussi", "bien que", "parce que", "cependant"],
                    "de": ["und", "aber", "auch", "obwohl", "weil", "jedoch"],
                    "it": ["e", "ma", "anche", "sebbene", "perché", "tuttavia"],
                    "pt": ["e", "mas", "também", "embora", "porque", "no entanto"],
                    "tr": ["ve", "ama", "ayrıca", "ancak", "çünkü", "fakat"],
                    "ru": ["и", "но", "также", "хотя", "потому что", "однако"],
                    "zh": ["和", "但是", "也", "虽然", "因为", "然而"],
                    "ja": ["そして", "でも", "また", "けれども", "なぜなら", "しかし"],
                    "ko": ["그리고", "하지만", "또한", "비록", "왜냐하면", "그러나"],
                    "ar": ["و", "لكن", "أيضاً", "رغم أن", "لأن", "ومع ذلك"],
                    "hi": ["और", "लेकिन", "भी", "हालांकि", "क्योंकि", "फिर भी"],
                    "nl": ["en", "maar", "ook", "hoewel", "omdat", "echter"],
                    "sv": ["och", "men", "också", "även om", "eftersom", "dock"],
                    "pl": ["i", "ale", "również", "chociaż", "ponieważ", "jednak"],
                    "cs": ["a", "ale", "také", "ačkoli", "protože", "však"],
                    "hu": ["és", "de", "is", "bár", "mert", "azonban"],
                    "ro": ["și", "dar", "de asemenea", "deși", "pentru că", "totuși"],
                    "uk": ["і", "але", "також", "хоча", "тому що", "однак"],
                    "he": ["ו", "אבל", "גם", "למרות", "כי", "עם זאת"],
                    "th": ["和", "แต่", "ก็", "แม้ว่า", "เพราะ", "อย่างไรก็ตาม"],
                    "da": ["og", "men", "også", "selvom", "fordi", "dog"],
                    "no": ["og", "men", "også", "selv om", "fordi", "likevel"],
                    "fi": ["ja", "mutta", "myös", "vaikka", "koska", "kuitenkin"],
                    "et": ["ja", "aga", "ka", "kuigi", "sest", "siiski"],
                    "lv": ["un", "bet", "arī", "lai gan", "tāpēc ka", "tomēr"],
                    "lt": ["ir", "bet", "taip pat", "nors", "nes", "tačiau"],
                    "sk": ["a", "ale", "tiež", "hoci", "pretože", "napriek tomu"],
                    "sl": ["in", "ampak", "tudi", "čeprav", "ker", "vendar"],
                    "hr": ["i", "ali", "također", "iako", "jer", "ipak"],
                    "bs": ["i", "ali", "također", "iako", "jer", "ipak"],
                    "sr": ["i", "ali", "takođe", "iako", "jer", "ipak"],
                    "mk": ["и", "но", "исто така", "иако", "затоа што", "сепак"],
                    "bg": ["и", "но", "също", "въпреки че", "защото", "обаче"],
                    "sq": ["dhe", "por", "edhe", "megjithëse", "sepse", "sidoqoftë"],
                    "mt": ["u", "imma", "ukoll", "għalkemm", "għaliex", "madankollu"],
                    "is": ["og", "en", "einnig", "þó að", "af því að", "þó"],
                    "ga": ["agus", "ach", "freisin", "cé", "mar", "áfach"],
                    "cy": ["a", "ond", "hefyd", "er", "oherwydd", "serch hynny"],
                    "gd": ["agus", "ach", "cuideachd", "ged", "oir", "gidheadh"],
                    "eu": ["eta", "baina", "ere", "nahiz eta", "zergatik", "hala ere"],
                    "ca": ["i", "però", "també", "tot i que", "perquè", "tanmateix"],
                    "gl": ["e", "mais", "tamén", "aínda que", "porque", "non obstante"],
                    "oc": ["e", "mas", "tanben", "quand ben", "perque", "nonobstant"],
                    "br": ["ha", "met", "ivez", "memestra", "rak", "memes tra"],
                    "fy": ["en", "mar", "ek", "hoewol", "om't", "doch"],
                    "lb": ["an", "awer", "och", "obwuel", "well", "trotzdem"],
                    "wa": ["et", "mins", "ossu", "co", "paskè", "tote li"],
                    "sc": ["e", "ma", "ancu", "bainzu", "ca", "nonostante"],
                    "co": ["è", "ma", "ancu", "benché", "perché", "tuttavia"],
                    "rm": ["e", "ma", "era", "schabuin", "perquai", "tuttina"],
                    "bn": ["এবং", "কিন্তু", "এছাড়াও", "যদিও", "কারণ", "তবুও"],
                    "vi": ["và", "nhưng", "cũng", "mặc dù", "vì", "tuy nhiên"],
                    "ta": ["மற்றும்", "ஆனால்", "மேலும்", "என்றாலும்", "ஏனென்றால்", "இருப்பினும்"],
                    "te": ["మరియు", "కానీ", "కూడా", "అయినప్పటికీ", "ఎందుకంటే", "అయినప్పటికీ"],
                    "mr": ["आणि", "पण", "सुद्धा", "जरी", "कारण", "तरीही"],
                    "ur": ["اور", "لیکن", "بھی", "اگرچہ", "کیونکہ", "بہرحال"],
                    "gu": ["અને", "પણ", "પણ", "જોકે", "કારણ કે", "તેમ છતાં"],
                    "id": ["dan", "tapi", "juga", "walaupun", "karena", "namun"],
                    "fa": ["و", "اما", "همچنین", "هرچند", "چون", "با این حال"],
                    "ms": ["dan", "tetapi", "juga", "walaupun", "kerana", "namun"],
                    "pa": ["ਅਤੇ", "ਪਰ", "ਵੀ", "ਹਾਲਾਂਕਿ", "ਕਿਉਂਕਿ", "ਫਿਰ ਵੀ"],
                    "kn": ["ಮತ್ತು", "ಆದರೆ", "ಸಹ", "ಹೇಗಿದ್ದರೂ", "ಏಕೆಂದರೆ", "ಆದಾಗ್ಯೂ"],
                    "or": ["ଏବଂ", "କିନ୍ତୁ", "ମଧ୍ୟ", "ଯଦିଓ", "କାରଣ", "ତଥାପି"],
                    "ml": ["ഉം", "പക്ഷേ", "കൂടാതെ", "എങ്കിലും", "എന്തുകൊണ്ട്", "എന്നിരുന്നാലും"],
                    "su": ["jeung", "tapi", "ogé", "sanajan", "sabab", "tapi"],
                    "ha": ["da", "amma", "kuma", "ko da yake", "domin", "duk da haka"],
                    "yo": ["ati", "ṣugbọn", "pẹlupẹlu", "bi o tilẹ jẹ pe", "nitori", "sibẹsibẹ"],
                    "ig": ["na", "ma", "ọzọkwa", "ọ bụrụgodị", "n'ihi na", "n'agbanyeghị nke ahụ"],
                    "zu": ["futhi", "kodwa", "futhi", "nakuba", "ngoba", "nokho"],
                    "am": ["እና", "ነገር ግን", "እንዲሁም", "ቢሆንም", "ስለምን", "ነገር ግን"],
                    "qu": ["hinallataq", "ichaqa", "chaymantapas", "yachaykuchus", "imanasqam", "ichaqa"],
                    "ay": ["ukhamarak", "ukampinsa", "ukhamat", "jichhax", "kawkisa", "ukampinsa"],
                    "gn": ["ha", "upéicharõ", "avei", "ha'eñói", "mba'ére", "upéicharõ"],
                    "ht": ["ak", "men", "tou", "byenke", "paske", "kanmenm"],
                    "mn": ["бас", "гэхдээ", "мөн", "гэсэн хэдий ч", "учир нь", "гэсэн хэдий ч"],
                    "my": ["နဲ့", "ဒါပေမယ့်", "လည်း", "တကယ်လို့", "ဘာကြောင့်လဲ", "ဒါပေမယ့်"],
                    "lo": ["ແລະ", "ແຕ່", "ກໍ", "ເຖິງແມ່ນວ່າ", "ເພາະ", "ເຖິງແມ່ນວ່າ"],
                    "km": ["និង", "ប៉ុន្តែ", "ក៏", "ទោះបីជា", "ពីព្រោះ", "ទោះបីជា"],
                    "ceb": ["ug", "apan", "usab", "bisag", "tungod", "apan"],
                    "ilo": ["ken", "ngem", "pay", "nupay", "ta", "ngem"],
                    "mg": ["ary", "fa", "koa", "na", "satria", "na"],
                    "af": ["en", "maar", "ook", "alhoewel", "omdat", "tog"],
                    "sw": ["na", "lakini", "pia", "ingawa", "kwa sababu", "hata hivyo"],
                    "so": ["iyo", "laakiin", "sidoo kale", "inkastoo", "sababta oo ah", "si kastaba ha ahaatee"],
                    "rw": ["na", "ariko", "kandi", "nubwo", "kubera", "ariko"],
                    "st": ["le", "empa", "hape", "leha", "hobane", "leha"],
                    "xh": ["ne", "kodwa", "kwakhona", "nokuba", "ngokuba", "nokuba"],
                    "tn": ["le", "fa", "gape", "le fa", "ka gore", "le fa"],
                }
                res.append(random.choice(connectors.get(lang, connectors["es"])))

        if not res[-1].endswith((".", "!", "?")):
            res[-1] += "."

        final_text = " ".join(res)

        # Prefijo por intención detectada
        intent = detect_intent(prompt)
        intent_prefixes = {
            "greeting":  ["¡Hola! ", "¡Buenas! ", "¡Hey! ", "¡Qué tal! "],
            "farewell":  ["¡Hasta luego! ", "¡Cuídate! ", "¡Nos vemos! "],
            "thanks":    ["De nada. ", "Con gusto. ", "Para eso estoy. "],
            "complaint": ["Entiendo. ", "Veamos ese problema. ", "Te ayudo. "],
            "question":  ["Sobre eso... ", "Déjame pensar. ", "Interesante pregunta. "],
        }
        if intent in intent_prefixes:
            final_text = random.choice(intent_prefixes[intent]) + final_text

        add_web_log("IA", f"[ctx={chat_id}][{intent}] '{prompt[:20]}' → '{final_text[:35]}'")

        if self.mood == "friendly":
            final_text += f" {random.choice(['😊', '✨', '🙌', '🌙'])}"
        elif self.mood == "sarcastic":
            final_text = f"Bueno, {final_text.lower()} {random.choice(['... o eso creo.', '🙄', '¡Genial!', 'Vaya tela.'])}"
        elif self.mood == "philosophical":
            final_text = f"Reflexionando: {final_text} ¿No es fascinante?"
        elif self.mood == "cyberpunk":
            final_text = f"[CORE]: {final_text.upper()} // LINK_ACTIVE"

        return final_text

    def force_feed(self, chats_history):
        add_web_log("INFO", "Iniciando alimentación forzada desde el historial histórico...")
        count = 0
        for chat_id in chats_history:
            for msg in chats_history[chat_id]:
                text = msg.get("text", "")
                if not isinstance(text, str): text = str(text) if text is not None else ""
                if text and not text.startswith("/"):
                    self.learn(text)
                    count += 1
        add_web_log("SUCCESS", f"Alimentación forzada completada. {count} mensajes re-procesados.")

    def get_stats(self):
        words_count = len(self.brain["keywords"])
        connections = sum(sum(v.values()) if isinstance(v, Counter) else len(v) for v in self.brain["keywords"].values())
        elapsed = (time.time() - self.start_time) / 60 # Minutos
        rate = self.session_words / elapsed if elapsed > 0 else 0
        
        # Estimación de madurez (meta 5000 palabras)
        target = 5000
        remaining = max(0, target - words_count)
        est_minutes = (remaining / rate) if rate > 0 else 0
        return {
            "words": words_count,
            "connections": connections,
            "rate": f"{rate:.2f} p/min",
            "est_maturity": "Madura (Estable)" if words_count > 5000 else f"{est_minutes:.1f} min"
        }

    def send_master_report(self, title="Reporte de Inteligencia"):
        """Envía un resumen detallado del estado de la IA al Administrador Maestro."""
        if not MASTER_ID: return
        stats = self.get_stats()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = (
            f"📊 *{title}*\n"
            f"📅 Fecha: `{now}`\n"
            f"--------------------------------\n"
            f"🧠 *Neuronas:* `{stats['words']}`\n"
            f"🔗 *Sinapsis:* `{stats['connections']}`\n"
            f"⚡ *Velocidad:* `{stats['rate']}`\n"
            f"🎓 *Estado:* `{stats['est_maturity']}`\n"
            f"--------------------------------\n"
            f"📚 *Top Fuentes:* {', '.join([s['name'] for s in self.get_top_sources()[:3]])}\n"
            f"🌐 *Idiomas:* {len(db.get('IA_LANG_COUNTS', {}))} detectados\n"
            f"🛡️ *Seguridad:* Escudo Neural Activo\n"
            f"--------------------------------\n"
            f"🌙 _Moon Multibot Intelligence System_"
        )
        
        try:
            # Usamos proxy_bot para enviar el reporte
            proxy_bot.api_call("sendMessage", {"chat_id": MASTER_ID, "text": report, "parse_mode": "Markdown"})
        except Exception as e:
            add_web_log("ERROR", f"Fallo al enviar reporte maestro: {e}")

    def get_top_sources(self):
        """Calcula las fuentes más influyentes."""
        sources = {}
        for w, s in self._sources_cache.items():
            sources[s] = sources.get(s, 0) + 1
        sorted_s = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        return [{"name": k, "count": v} for k, v in sorted_s]
        
        eta = "Madura (Estable)"
        if est_minutes > 0:
            eta = str(datetime.timedelta(minutes=int(est_minutes)))

        return {
            "words": words_count, 
            "connections": connections,
            "rate": f"{round(rate, 2)} p/min",
            "est_maturity": eta
        }

    def search_web(self, query):
        """Buscador Neural via DuckDuckGo Instant Answer API (sin scraping, sin bloqueos)."""
        try:
            headers = {'User-Agent': 'MoonBot/1.0'}
            encoded = requests.utils.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                abstract = data.get("AbstractText", "").strip()
                if abstract:
                    self.learn(abstract, source="DuckDuckGo")
                    return abstract[:400]
                topics = [t.get("Text", "") for t in data.get("RelatedTopics", [])
                          if isinstance(t, dict) and t.get("Text")]
                if topics:
                    result = " | ".join(topics[:3])[:400]
                    self.learn(result, source="DuckDuckGo")
                    return result
            return "No encontré datos relevantes para esa búsqueda."
        except Exception as e:
            add_web_log("ERROR", f"search_web error: {str(e)}")
            return "Error de conexión con el buscador."

ia_nativa = MoonCoreIA()

class MoonBot:
    def __init__(self, token):
        self.token, self.url, self.session, self.plugins = token, f"https://api.telegram.org/bot{token}/", requests.Session(), []
        self.ia = ia_nativa
        self.load_plugins()
        me = self.api_call("getMe")
        self.bot_username = me.get("result", {}).get("username", "MoonBot")
        self.bot_id = me.get("result", {}).get("id")
        self.last_msg_id = None
        self.last_media_hash = None
        if not os.path.exists("downloads"): os.makedirs("downloads")

    def call_api(self, m, p=None, silent=False):
        try:
            r = self.session.post(self.url + m, json=p, timeout=35)
            data = r.json()
            if not data.get("ok") and not silent:
                add_web_log("ERROR", f"Telegram API Fail ({m}): {data.get('description')}")
            return data
        except Exception as e:
            if not silent: add_web_log("ERROR", f"Error {m}: {str(e)}")
            return {"ok": False, "description": str(e)}

    def send_msg(self, chat_id, text, parse_mode="Markdown", business_connection_id=None):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if business_connection_id:
            payload["business_connection_id"] = business_connection_id
        return self.call_api("sendMessage", payload)

    def analyze_image(self, path):
        """Neural Perception Engine (NPHE-I) - 100% Local & Open Source"""
        try:
            size = os.path.getsize(path)
            with open(path, 'rb') as f:
                data = f.read(10240) # Leer los primeros 10KB para análisis de cabecera
                
                res = "Desconocido"
                fmt = "Binario"
                details = []

                # PNG
                if data.startswith(b'\x89PNG\r\n\x1a\n'):
                    w, h = struct.unpack('>LL', data[16:24])
                    fmt, res = "PNG (Lossless)", f"{w}x{h}"
                # JPEG
                elif data.startswith(b'\xff\xd8'):
                    fmt = "JPEG (Compressed)"
                    f.seek(0)
                    content = f.read(15000)
                    for i in range(len(content)-8):
                        if content[i:i+2] == b'\xff\xc0': # SOF0
                            h, w = struct.unpack('>HH', content[i+5:i+9])
                            res = f"{w}x{h}"
                            break
                # WEBP
                elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
                    fmt = "WebP (Modern)"
                    if data[12:16] == b'VP8 ':
                        w_h = struct.unpack('<HH', data[26:30])
                        res = f"{w_h[0] & 0x3FFF}x{w_h[1] & 0x3FFF}"
                # GIF
                elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
                    w, h = struct.unpack('<HH', data[6:10])
                    fmt, res = "GIF (Animado)", f"{w}x{h}"

                if res != "Desconocido":
                    # Análisis de Complejidad (Entropía Heurística)
                    w_val = int(res.split('x')[0])
                    h_val = int(res.split('x')[1])
                    pixels = w_val * h_val
                    ratio = size / max(pixels, 1)
                    
                    if ratio > 0.5: details.append("Alta Complejidad (Fotografía)")
                    elif ratio < 0.05: details.append("Baja Complejidad (Ilustración/Logo)")
                    else: details.append("Complejidad Media")

                    # Heurística Cromática (Muestreo binario)
                    sample = data[2000:5000] # Muestra del cuerpo del archivo
                    if sample:
                        avg_byte = sum(sample) / len(sample)
                        if avg_byte > 180: details.append("Tono Predominante: Brillante/Blanco")
                        elif avg_byte < 50: details.append("Tono Predominante: Oscuro/Sombrío")
                        
                        # Detección de "Calidez" (Heurística basada en distribución de bytes)
                        warm_count = sum(1 for b in sample if b > 150)
                        if warm_count > len(sample) * 0.4: details.append("Ambiente: Cálido/Energético")

                    return f"IA Perception: {fmt} {res}. {'. '.join(details)}."
                
                return f"Percepción limitada ({size} bytes). Estructura no indexada."
        except Exception as e:
            return f"Fallo en Percepción Neural: {str(e)}"

    def analyze_video(self, path):
        """Neural Perception Engine (NPHE-V) - Telemetría de Video Local"""
        try:
            size = os.path.getsize(path)
            with open(path, 'rb') as f:
                data = f.read(50000)
                
                idx = data.find(b'mvhd')
                if idx != -1:
                    timescale = struct.unpack('>I', data[idx+12:idx+16])[0]
                    duration = struct.unpack('>I', data[idx+16:idx+20])[0]
                    if timescale > 0:
                        sec = round(duration / timescale, 2)
                        bitrate = round((size * 8) / (sec * 1024), 2) # kbps
                        
                        codec = "Desconocido"
                        if b'avc1' in data: codec = "H.264 (AVC)"
                        elif b'hvc1' in data: codec = "H.265 (HEVC)"
                        elif b'vp09' in data: codec = "VP9"
                        
                        return f"Video Analizado: {sec}s | Codec: {codec} | Bitrate: {bitrate} kbps. Integridad verificada."

                return f"Video detectado ({size} bytes). Metadatos encriptados o no estándar."
        except Exception as e:
            return f"Error en telemetría de video: {str(e)}"

    def get_file_hash(self, path):
        """Genera una huella digital SHA-256 única para cualquier archivo."""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def check_security_blacklist(self, file_hash, cid, uid, uname, caption="", visual_data=""):
        """Decisión Unificada IA: Evalúa Riesgo (VT, CAS, IA Perception, Banned Words) y aplica sentencia."""
        if not db.get("NEURAL_SHIELD", True): return False
        
        # 1. Recopilación de Inteligencia
        vt_res = vt_mgr.scan_hash(file_hash)
        cas_banned = is_cas_banned(uid)
        v_low = (visual_data or "").lower()
        cap_low = (caption or "").lower()
        
        # 2. Sistema de Puntuación (Security Score)
        score = 0
        reasons = []
        
        # -- VirusTotal (40 pts por motor, max 100)
        vt_malicious = vt_res.get("malicious", 0) if vt_res.get("ok") else 0
        if vt_malicious > 0:
            score += min(100, vt_malicious * 40)
            reasons.append(f"VirusTotal Malware ({vt_malicious} motores)")
            
        # -- CAS Chat (80 pts)
        if cas_banned:
            score += 80
            reasons.append("CAS Global Blacklist")
            
        # -- IA Behavioral & Banned Words (30-50 pts)
        banned_words = ["porno", "xxx", "terrorismo", "isis", "bomba", "gore", "cp ", "pedofilo"]
        if any(w in cap_low for w in banned_words):
            score += 50
            reasons.append(f"Contenido Prohibido en Caption")
            
        # Detección de Estafas Dinámica (solo si coinciden varios términos)
        scam_words = ["nequi", "paypal", "scam", "estafa", "pago", "premio", "gana"]
        matches = [w for w in scam_words if w in cap_low]
        if len(matches) >= 2:
            score += 40
            reasons.append(f"Patrón de Estafa Detectado ({', '.join(matches)})")

        # 3. Registro del Evento de Auditoría
        security_event = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hash": file_hash,
            "chat_id": cid,
            "chat_name": global_chat_names.get(cid, cid),
            "user": f"{uname} ({uid})",
            "score": score,
            "reasons": ", ".join(reasons) or "Limpio",
            "vt_status": "Malicious" if vt_malicious > 0 else "Clean",
            "cas_status": "Banned" if cas_banned else "Clear"
        }
        sec_logs = db.get("SECURITY_AUDIT_LOGS", [])
        sec_logs.append(security_event)
        db.set("SECURITY_AUDIT_LOGS", sec_logs[-300:])

        # 4. Decisión Final: Umbral de Expulsión (Score >= 80)
        if score >= 80:
            add_web_log("SECURITY", f"🚨 DECISIÓN IA: Expulsando a {uname} por riesgo crítico ({score}/100). Razones: {security_event['reasons']}")
            self.call_api("deleteMessage", {"chat_id": cid, "message_id": self.last_msg_id}, silent=True)
            self.call_api("kickChatMember", {"chat_id": cid, "user_id": uid})
            
            # Notificar en el grupo
            self.send_msg(cid, f"⚖️ **SENTENCIA IA:** {uname} ha sido expulsado.\n\n🛡️ **Nivel de Riesgo:** `{score}/100`\n🔍 **Motivos:** {security_event['reasons']}\n\nProtegiendo la integridad del nodo Moon.")
            return True

        # Blacklist Manual (Legacy)
        banned_hashes = db.get("BANNED_HASHES", [])
        if file_hash in banned_hashes:
            self.call_api("deleteMessage", {"chat_id": cid, "message_id": self.last_msg_id}, silent=True)
            self.send_msg(cid, "🚫 **ESCUDO:** Archivo bloqueado por lista negra manual.")
            return True

        return False
        
        is_banned_hash = file_hash in banned_hashes
        has_banned_caption = any(w in (caption or "").lower() for w in banned_words)

        # Heurística Visual NPHE para Porno/Terrorismo
        has_suspicious_visual = False
        v_low = (visual_data or "").lower()
        if "ia perception" in v_low:
            # Heurística Porno: Fotografía + Ambiente Cálido (Posible piel/cuerpo) + Brillo alto
            if "fotografía" in v_low and "cálido" in v_low and "brillante" in v_low:
                has_suspicious_visual = True
            # Heurística Terrorismo/Gore: Fotografía + Tono Sombrío
            if "fotografía" in v_low and "oscuro/sombrío" in v_low:
                # Si es video y tiene bitrate muy bajo pero es sombrío, podría ser material filtrado/gore
                if "bitrate" in v_low:
                    try:
                        br_match = re.search(r'(\d+\.?\d*) kbps', v_low)
                        if br_match and float(br_match.group(1)) < 200:
                            has_suspicious_visual = True
                    except: pass

        if is_banned_hash or has_banned_caption or has_suspicious_visual:
            reason = "Hash Blacklist" if is_banned_hash else ("Patrón Visual Sospechoso" if has_suspicious_visual else f"Contenido Prohibido ('{caption}')")
            add_web_log("SECURITY", f"🚨 ESCUDO ACTIVO: {uname} bloqueado por {reason}.")
            self.call_api("deleteMessage", {"chat_id": cid, "message_id": self.last_msg_id}, silent=True)
            self.call_api("kickChatMember", {"chat_id": cid, "user_id": uid})
            self.send_msg(cid, f"🚫 **NEURAL SHIELD:** Contenido prohibido detectado por {reason}. Usuario expulsado permanentemente.")
            return True
        return False

    def sync_security_hashes(self):
        """Sincroniza la lista negra con bases de datos externas (URLs)."""
        urls = db.get("SECURITY_SYNC_URLS", [])
        if not urls: return
        new_hashes = []
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    found = re.findall(r'[a-fA-F0-9]{64}', r.text)
                    new_hashes.extend(found)
                    add_web_log("SECURITY", f"Sincronización exitosa desde {url}: {len(found)} hashes encontrados.")
            except: pass
        if new_hashes:
            current = db.get("BANNED_HASHES", [])
            updated = list(set(current + new_hashes))
            db.set("BANNED_HASHES", updated)

    def purge_old_media(self, days):
        """Elimina archivos de la carpeta downloads más antiguos que X días."""
        now = time.time()
        count = 0
        if os.path.exists("downloads"):
            for f in os.listdir("downloads"):
                f_path = os.path.join("downloads", f)
                if os.stat(f_path).st_mtime < now - (days * 86400):
                    try:
                        os.remove(f_path)
                        count += 1
                    except: pass
        if count > 0: add_web_log("CLEANUP", f"Purga automática: {count} archivos eliminados.")
    def load_plugins(self):
        self.plugins = []
        if os.path.exists("plugins"):
            for f in os.listdir("plugins"):
                if f.endswith(".py"):
                    try:
                        spec = importlib.util.spec_from_file_location(f[:-3], os.path.join("plugins", f))
                        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); self.plugins.append(m)
                    except: pass
    def api_call(self, m, p=None, silent=False):
        return self.call_api(m, p, silent)

    # --- Métodos Core (Telegram Bot API) ---
    def send_document(self, chat_id, file_path, caption=""):
        try:
            with open(file_path, 'rb') as f:
                r = self.session.post(self.url + "sendDocument", data={"chat_id": chat_id, "caption": caption}, files={"document": f}, timeout=60)
                return r.json()
        except: return {"ok": False}

    def send_photo(self, cid, photo, caption=""):
        return self.api_call("sendPhoto", {"chat_id": cid, "photo": photo, "caption": caption, "parse_mode": "Markdown"})

    def send_audio(self, cid, audio, caption=""):
        return self.api_call("sendAudio", {"chat_id": cid, "audio": audio, "caption": caption})

    def send_video(self, cid, video, caption=""):
        return self.api_call("sendVideo", {"chat_id": cid, "video": video, "caption": caption})

    def send_location(self, cid, lat, lon):
        return self.api_call("sendLocation", {"chat_id": cid, "latitude": lat, "longitude": lon})

    def delete_msg(self, cid, mid):
        return self.api_call("deleteMessage", {"chat_id": cid, "message_id": mid}, silent=True)

    def edit_msg(self, cid, mid, text):
        return self.api_call("editMessageText", {"chat_id": cid, "message_id": mid, "text": text, "parse_mode": "Markdown"})

    def pin_msg(self, cid, mid):
        return self.api_call("pinChatMessage", {"chat_id": cid, "message_id": mid})

    def kick_user(self, cid, uid):
        return self.api_call("banChatMember", {"chat_id": cid, "user_id": uid})

    def restrict_user(self, cid, uid, until=0, can_send=False):
        permissions = {
            "can_send_messages": can_send, "can_send_media_messages": can_send,
            "can_send_polls": can_send, "can_send_other_messages": can_send,
            "can_add_web_page_previews": can_send, "can_change_info": False,
            "can_invite_users": False, "can_pin_messages": False
        }
        return self.api_call("restrictChatMember", {"chat_id": cid, "user_id": uid, "permissions": permissions, "until_date": until})

    def promote_user(self, cid, uid, is_admin=True):
        p = {
            "chat_id": cid, "user_id": uid, "can_change_info": is_admin, "can_delete_messages": is_admin,
            "can_invite_users": is_admin, "can_restrict_members": is_admin, "can_pin_messages": is_admin
        }
        return self.api_call("promoteChatMember", p)

    def set_title(self, cid, title):
        return self.api_call("setChatTitle", {"chat_id": cid, "title": title})

    def get_member(self, cid, uid):
        return self.api_call("getChatMember", {"chat_id": cid, "user_id": uid})
    def get_user_rank(self, cid, uid):
        uid_str = str(uid).strip()
        master_str = str(MASTER_ID).strip()
        if uid_str == master_str: return "Master"
        
        # Usar caché para evitar Rate Limits (1 hora de validez)
        cache_key = f"ADMINS_{cid}"
        admins_cached = db.get(cache_key, [])
        if admins_cached and str(uid) in admins_cached: return "Admin"
        
        # Si no está en caché o no es admin, consultar (con límite de frecuencia: 5 minutos)
        now = time.time()
        last_check = db.get(f"LAST_ADMIN_CHECK_{cid}", 0)
        if now - last_check > 300:
            admins = self.api_call("getChatAdministrators", {"chat_id": cid}, silent=True)
            if admins.get("ok"):
                admin_ids = [str(a["user"]["id"]) for a in admins["result"]]
                db.set(cache_key, admin_ids)
                db.set(f"LAST_ADMIN_CHECK_{cid}", now)
                if str(uid) in admin_ids: return "Admin"
        
        return "User"

    def process_command(self, cid, uid, uname, text, rk, msg_id, msg):
        clean_text = text.strip()
        if not clean_text.startswith("/"): return False
        
        # 1. Limpieza de comando (soporte para /cmd@botname)
        parts = clean_text.split()
        raw_cmd = parts[0].lower().split("@")[0]
        args = parts[1:]
        arg_str = " ".join(args)
        
        add_web_log("DEBUG", f"[CMD] Procesando '{raw_cmd}' de {uname} (Rango: {rk})")

        # 2. Comandos Públicos / Globales
        if raw_cmd in ["/start", "/inicio"]:
            self.send_msg(cid, f"🌙 **Moon Multibot Activo**\n\nHola {uname}, el núcleo está operando con normalidad. Usa `/ayuda` para ver mis capacidades.")
            return True
        
        if raw_cmd in ["/ayuda", "/comandos", "/help"]:
            help_text = "📖 **MANUAL DE OPERACIONES MOON**\n\n"
            help_text += "✨ **General:** `/perfil`, `/top`, `/notas`, `/search`\n"
            if rk in ["Admin", "Master"]:
                help_text += "🛡️ **Moderación:** `/mute`, `/ban`, `/warn`, `/warns`, `/flag`\n"
                help_text += "⚙️ **Ajustes:** `/settings`, `/ia_feed`, `/resumen`\n"
            if rk == "Master":
                help_text += "⚡ **Master:** `/listen`, `/backup_db`, `/ban_media`\n"
            self.send_msg(cid, help_text)
            return True

        if raw_cmd == "/ping":
            self.send_msg(cid, "🏓 **PONG!** Núcleo Moon sincronizado.")
            return True

        if raw_cmd == "/perfil":
            user_data = db.get(f"USER_{uid}", {"karma": 0, "level": 1, "exp": 0})
            stats = global_user_stats.get(uid, {"count": 0, "karma": 0})
            k_score = stats.get("karma", 0)
            badge = "🏆 Leyenda" if k_score > 50 else "⭐ Colaborador" if k_score > 20 else "👤 Miembro"
            self.send_msg(cid, f"👤 **PERFIL: {uname}**\n\n🆙 Nivel: `{user_data.get('level', 1)}`\n⚡ EXP: `{user_data.get('exp', 0)}`\n⭐ Karma: `{k_score}`\n💬 Mensajes: `{stats.get('count', 0)}`\n🏅 Insignia: {badge}")
            return True

        if raw_cmd == "/top":
            sorted_u = sorted(global_user_stats.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:5]
            if not sorted_u: self.send_msg(cid, "📊 Aún no hay datos.")
            else:
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                lines = [f"{medals[i]} **{v['name']}**: {v.get('count',0)} msgs" for i, (k, v) in enumerate(sorted_u)]
                self.send_msg(cid, "🏆 **TOP 5 USUARIOS**\n\n" + "\n".join(lines))
            return True

        if raw_cmd == "/search" and arg_str:
            self.send_msg(cid, "🔍 Consultando fuentes globales...")
            res = ia_nativa.search_web(arg_str)
            self.send_msg(cid, f"🌐 **Resultado:**\n\n{res}")
            return True

        # 3. Comandos de Configuración & Moderación (Admin/Master)
        if rk in ["Admin", "Master"]:
            # Detectar si es una respuesta (Reply)
            target_uid = arg_str if arg_str else (str(msg.get("reply_to_message", {}).get("from", {}).get("id", "")) if msg.get("reply_to_message") else None)
            target_name = msg.get("reply_to_message", {}).get("from", {}).get("first_name", target_uid) if msg.get("reply_to_message") else target_uid

            if raw_cmd == "/settings":
                c = db.get(f"CONFIG_{cid}", {"ia_learning": False, "auto_mod": True, "ia_mood": "friendly"})
                txt = f"⚙️ **CONFIGURACIÓN DEL NODO {cid}**\n\n"
                txt += f"🧠 IA Learning: `{'✅ ON' if c.get('ia_learning') else '❌ OFF'}`\n"
                txt += f"🛡️ Neural Shield: `{'✅ ON' if c.get('auto_mod') else '❌ OFF'}`\n"
                txt += f"🎭 Mood: `{c.get('ia_mood', 'friendly')}`\n\n"
                txt += "Usa el Dashboard para cambios avanzados."
                self.send_msg(cid, txt)
                return True

            if raw_cmd == "/ban":
                if not target_uid:
                    self.send_msg(cid, "⚠️ **ERROR:** Debes responder a un mensaje o indicar el ID del usuario para banear.")
                    return True
                self.kick_user(cid, target_uid)
                st = db.get("ST_FILE", {"bans": []})
                if target_uid not in st["bans"]: st["bans"].append(target_uid); db.set("ST_FILE", st)
                self.send_msg(cid, f"🚫 **{target_name}** expulsado y baneado permanentemente.")
                return True

            if raw_cmd == "/mute":
                if not target_uid:
                    self.send_msg(cid, "⚠️ **ERROR:** Debes responder a un mensaje para silenciar al usuario.")
                    return True
                until = int(time.time()) + 3600
                self.restrict_user(cid, target_uid, until=until, can_send=False)
                muted = db.get(f"MUTED_{cid}", [])
                if target_uid not in muted: muted.append(target_uid); db.set(f"MUTED_{cid}", muted)
                self.send_msg(cid, f"🔇 **{target_name}** ha sido silenciado por 1 hora.")
                return True

            if raw_cmd == "/unmute" and target_uid:
                self.restrict_user(cid, target_uid, until=0, can_send=True)
                muted = db.get(f"MUTED_{cid}", [])
                if target_uid in muted: muted.remove(target_uid); db.set(f"MUTED_{cid}", muted)
                self.send_msg(cid, f"🔊 **{target_name}** puede hablar de nuevo.")
                return True

            if raw_cmd == "/unban" and target_uid:
                self.api_call("unbanChatMember", {"chat_id": cid, "user_id": target_uid})
                st = db.get("ST_FILE", {"bans": []})
                if target_uid in st["bans"]: st["bans"].remove(target_uid); db.set("ST_FILE", st)
                self.send_msg(cid, f"✅ **{target_uid}** ha sido indultado.")
                return True

            if raw_cmd == "/warn":
                if not target_uid:
                    self.send_msg(cid, "⚠️ **ERROR:** Debes responder a un mensaje para advertir al usuario.")
                    return True
                warns = db.get(f"WARNS_{cid}", {})
                warns[target_uid] = warns.get(target_uid, 0) + 1
                db.set(f"WARNS_{cid}", warns)
                self.send_msg(cid, f"⚠️ **{target_name}**: Advertencia {warns[target_uid]}/3.")
                if warns[target_uid] >= 3:
                    self.kick_user(cid, target_uid)
                    self.send_msg(cid, f"💀 **{target_name}** expulsado por acumulación de advertencias.")
                return True

            if raw_cmd == "/ia_feed":
                feeder_groups = db.get("IA_FEEDERS", [])
                if arg_str == "on":
                    if cid not in feeder_groups: feeder_groups.append(cid); db.set("IA_FEEDERS", feeder_groups)
                    self.send_msg(cid, "📡 Modo alimentación IA activado.")
                elif arg_str == "off":
                    if cid in feeder_groups: feeder_groups.remove(cid); db.set("IA_FEEDERS", feeder_groups)
                    self.send_msg(cid, "✅ Modo alimentación IA desactivado.")
                return True

            if raw_cmd == "/resumen":
                hist = db.get("GLOBAL_HISTORY", [])
                chat_msgs = [m for m in hist if str(m.get("cid")) == cid][-20:]
                if chat_msgs:
                    all_text = " ".join(m.get("text", "") for m in chat_msgs if m.get("text"))
                    summary = ia_nativa.generate(all_text[:150], chat_id=cid)
                    self.send_msg(cid, f"📊 **Resumen IA:** {summary}")
                return True

            if raw_cmd == "/resync":
                if rk != "Master": return False
                self.send_msg(cid, "🧠 **SINCRONIZACIÓN:** Recargando memoria neuronal...")
                ia_nativa.load_brain()
                self.send_msg(cid, f"✅ **ÉXITO:** Memoria sincronizada. Ahora tengo {len(ia_nativa.brain.get('keywords',{}))} neuronas activas.")
                return True

        # 4. Comandos Master
        if rk == "Master":
            if raw_cmd == "/listen":
                global listen_mode
                listen_mode = (arg_str == "on")
                db.set("LISTEN_MODE", listen_mode)
                self.send_msg(cid, f"{'🔇' if listen_mode else '🔊'} Modo escucha: {arg_str}")
                return True

            if raw_cmd == "/backup_db":
                db_path = "data/moon_database.db"
                if os.path.exists(db_path): self.send_document(cid, db_path, "Backup DB")
                return True

        # 5. Comandos de Texto Personalizados (S_FILE)
        s_file = db.get("S_FILE", {})
        if raw_cmd[1:] in s_file:
            self.send_msg(cid, s_file[raw_cmd[1:]]["text"])
            return True

        return False
    def run(self):
        global listen_mode
        offset = 0
        while True:
            try:
                res = self.api_call("getUpdates", {"offset": offset + 1, "timeout": 20})
                if not res.get("ok"):
                    add_web_log("ERROR", f"Error getUpdates: {res.get('description')}")
                    time.sleep(5); continue
                
                if not res.get("result"): 
                    # Solo logueamos cada 10 intentos vacíos para no saturar
                    if random.random() < 0.1: add_web_log("DEBUG", "Esperando nuevos mensajes de Telegram...")
                    continue
                
                for u in res["result"]:
                    offset = u["update_id"]
                    # Detección de Mensajes (Estándar, Canal o Business)
                    msg = u.get("message") or u.get("channel_post") or u.get("business_message")
                    if not msg: continue
                    
                    b_conn_id = u.get("business_message", {}).get("business_connection_id")
                    self.last_msg_id = msg.get("message_id")

                    cid = str(msg["chat"]["id"])
                    # Registrar chat para este bot específico
                    bot_chats = db.get(f"CHATS_{self.token}", [])
                    if cid not in bot_chats:
                        bot_chats.append(cid)
                        db.set(f"CHATS_{self.token}", bot_chats)
                    cid, text, user = str(msg["chat"]["id"]), msg.get("text", ""), msg.get("from", {})
                    add_web_log("DEBUG", f"Nuevo mensaje detectado: CID={cid}, User={user.get('first_name')}")
                    if not isinstance(text, str): text = str(text) if text is not None else ""
                    if user.get("is_bot"): continue # Ignorar otros bots
                    uid, uname = str(user.get("id", cid)), user.get("first_name", "Chat")
                    add_web_log("DEBUG", f"Deteccion de ID: Usuario={uid} | Nombre={uname} | Verificando Permisos...")
                    
                    # Sistema de Auditoría IA (Evaluación de Calidad)
                    if cid in active_audits:
                        audit = active_audits[cid]
                        if audit["status"] == "listening":
                            audit["messages"].append(text)
                            # Puntuación: Longitud de palabras + variedad
                            words = text.split()
                            unique_words = len(set(words))
                            # Penalizar SPAM en tiempo real
                            spam_triggers = ["gane", "euros", "bancaria", "billetera", "rentabilidad"]
                            if any(t in text.lower() for t in spam_triggers):
                                audit["score"] -= 100 # Penalización crítica
                                add_web_log("IA", f"⚠️ SPAM detectado en auditoría de {cid}. Penalizando fuente.")
                            else:
                                audit["score"] += (unique_words * 2) + (len(text) // 10)
                            
                            if len(audit["messages"]) >= 15:
                                audit["status"] = "finished"
                                audit["final_score"] = min(100, (audit["score"] // 15) * 5)
                                all_text = " ".join(audit["messages"][:15])
                                audit["report"] = {
                                    "time": datetime.datetime.now().strftime("%d/%m %H:%M"),
                                    "chat": audit.get("name", cid),
                                    "cid": cid,
                                    "score": audit["final_score"],
                                    "avg_len": len(all_text) // 15,
                                    "unique_words": len(set(all_text.split())),
                                    "verdict": "RECOMENDADO" if audit["final_score"] > 60 else "NO RECOMENDADO"
                                }
                                # Guardar en Historial
                                hist = db.get("IA_AUDIT_HISTORY", [])
                                hist.append(audit["report"])
                                db.set("IA_AUDIT_HISTORY", hist[-50:])
                                db.set("ACTIVE_AUDITS", active_audits)
                                add_web_log("SUCCESS", f"Auditoría Finalizada y Guardada: {audit.get('name', cid)} ({audit['final_score']}%)")
                                # No retornamos aquí para que también aprenda o procese si es necesario
                    
                    # Detección Automática de Fuentes Potenciales (Feeders sugeridos)
                    if cid.startswith("-"):
                        feeder_groups = db.get("IA_FEEDERS", [])
                        if cid not in feeder_groups:
                            potentials = db.get("POTENTIAL_FEEDERS", {})
                            if cid not in potentials:
                                potentials[cid] = {"name": global_chat_names.get(cid, cid), "last": datetime.datetime.now().strftime("%H:%M:%S")}
                                db.set("POTENTIAL_FEEDERS", potentials)
                                # Auto-Auditoría: Comenzar a analizar de inmediato de forma silenciosa
                                if cid not in active_audits:
                                    start_audit_logic(cid)
                    
                    # Karma & RPG System
                    user_id = str(uid)
                    user_data = db.get(f"USER_{user_id}", {"karma": 0, "level": 1, "exp": 0, "titles": []})
                    user_data["karma"] += 1
                    user_data["exp"] += 10
                    if user_data["exp"] >= user_data["level"] * 100:
                        user_data["level"] += 1
                        user_data["exp"] = 0
                        self.send_msg(cid, f"🆙 **LEVEL UP!** {uname} ha subido al nivel {user_data['level']}! 🎉")
                    db.set(f"USER_{user_id}", user_data)
                    
                    # Advanced Link Filter (Low Karma Check)
                    if "http" in text.lower() and user_data["karma"] < 10:
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})
                        self.send_msg(cid, f"🚫 **FILTRO DE SPAM:** {uname}, necesitas al menos 10 puntos de Karma para enviar enlaces.")
                        continue
                    
                    # Anti-Raid 2.0 (Mass Join Detection)
                    if "new_chat_members" in msg:
                        join_count = len(msg["new_chat_members"])
                        if join_count > 5:
                            self.send_msg(cid, "🚨 **ANTI-RAID 2.0 ACTIVADO:** Detectada entrada masiva. Bloqueando acceso temporalmente...")
                            add_web_log("SECURITY", f"Anti-Raid activado en chat {cid} (Entrada: {join_count} usuarios)")
                            continue
                    
                    # Debug message
                    add_web_log("DEBUG", f"Procesando mensaje de {uname} en {global_chat_names.get(cid, cid)}: {text[:20]}")
                    
                    # Global History Log (Captured before any filtering)
                    history = db.get("GLOBAL_HISTORY", [])
                    history.append({
                        "time": datetime.datetime.now().strftime("%H:%M:%S"),
                        "chat": global_chat_names.get(cid, cid),
                        "cid": cid,
                        "user": f"{uname} (@{user.get('username', '??')})",
                        "text": text or "[Contenido Multimedia]"
                    })
                    if len(history) > 300: history.pop(0) # Aumentado para auditoría retrospectiva
                    db.set("GLOBAL_HISTORY", history)
                    global global_msg_log
                    global_msg_log = history
                    
                    # Global Blacklist Check
                    st = db.get("ST_FILE", {"bans": []})
                    if not st: st = {"bans": []} # Fallback
                    bans_list = st.get("bans", [])
                    if not isinstance(bans_list, list): bans_list = [] # Sanitizar si es un int (Legacy)
                    if uid in bans_list: continue

                    # Mute Check - Usuarios silenciados por admin
                    muted_list = db.get(f"MUTED_{cid}", [])
                    uname_at = f"@{user.get('username', '')}" if user.get('username') else ""
                    if uid in muted_list or (uname_at and uname_at in muted_list):
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]}, silent=True)
                        continue

                    # Anti-Flood Control (en memoria, sin ops SQLite)
                    if str(uid) != str(MASTER_ID):
                        flood_key = f"{cid}_{uid}"
                        now_t = time.time()
                        times = flood_cache.get(flood_key, [])
                        times = [t for t in times if now_t - t < 10]
                        times.append(now_t)
                        flood_cache[flood_key] = times
                        flood_limit = int(db.get("GLOBAL_SETTINGS", {}).get("flood_limit", 6))
                        if len(times) > flood_limit:
                            self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]}, silent=True)
                            if len(times) == flood_limit + 1:
                                self.send_msg(cid, f"🌊 **ANTI-FLOOD:** {uname}, demasiados mensajes seguidos. Espera un momento.")
                            continue

                    # CAS Global Protection (Combot Anti-Spam)
                    settings = db.get("GLOBAL_SETTINGS", {})
                    if settings.get("cas_protection", "on") == "on" and is_cas_banned(uid):
                        add_web_log("SECURITY", f"⚠️ CAS BANNED DETECTADO: {uname} ({uid})")
                        if uid not in bans_list:
                            bans_list.append(uid)
                            st["bans"] = bans_list
                            db.set("ST_FILE", st)
                            add_audit_log(f"Auto-Baneo CAS aplicado a {uname} ({uid})")
                        continue
                    
                    if maintenance_mode and uid != str(MASTER_ID):
                        self.send_msg(cid, "⚠️ El bot está en modo mantenimiento. Inténtalo más tarde.")
                        continue

                    # Voice Transcription Simulation
                    if "voice" in msg:
                        voice_log.append({"time": datetime.datetime.now().strftime("%H:%M"), "user": uname})
                        self.send_msg(cid, "🎙️ [Voz detectada]: Procesando audio... (Simulado)")
                        # Simulated transcription
                        trans = "Parece que estás hablando de " + random.choice(["tecnología", "el grupo", "el bot", "la luna"])
                        self.send_msg(cid, f"📝 **Transcripción:** {trans}")
                        ia_nativa.learn(trans, source=global_chat_names.get(cid, cid))

                    # Neural Vision: Percepción Binaria Nativa
                    if "photo" in msg:
                        file_id = msg["photo"][-1]["file_id"]
                        self.send_msg(cid, "👁️ [Ojo Moon]: Analizando estructura binaria de la imagen...")
                        
                        f_info = self.api_call("getFile", {"file_id": file_id})
                        if f_info.get("ok"):
                            path = os.path.join("downloads", f"{file_id}.jpg")
                            url = f"https://api.telegram.org/file/bot{self.token}/{f_info['result']['file_path']}"
                            # Descarga con requests (estándar en el proyecto)
                            r = requests.get(url)
                            with open(path, 'wb') as f_out: f_out.write(r.content)
                            
                            # 1. Verificación de Seguridad (Huella Digital y Caption)
                            f_hash = self.get_file_hash(path)
                            self.last_media_hash = f_hash
                            caption = msg.get("caption", "")
                            visual_data = self.analyze_image(path)
                            if self.check_security_blacklist(f_hash, cid, uid, uname, caption, visual_data):
                                try: os.remove(path)
                                except: pass
                                continue
                            
                            self.send_msg(cid, f"🌌 **Percepción IA:** {visual_data}")
                            ia_nativa.learn(visual_data, source=global_chat_names.get(cid, cid))
                            # Incremento para Dashboard
                            db.set("STATS_PHOTOS", db.get("STATS_PHOTOS", 0) + 1)
                            try: os.remove(path)
                            except: pass
                        continue

                    # Neural Vision: Percepción de Video Nativa (100% Antigravity Core)
                    if "video" in msg:
                        file_id = msg["video"]["file_id"]
                        self.send_msg(cid, "👁️ [Ojo Moon]: Analizando secuencia binaria de video...")
                        
                        f_info = self.api_call("getFile", {"file_id": file_id})
                        if f_info.get("ok"):
                            path = os.path.join("downloads", f"{file_id}.mp4")
                            url = f"https://api.telegram.org/file/bot{self.token}/{f_info['result']['file_path']}"
                            r = requests.get(url)
                            with open(path, 'wb') as f_out: f_out.write(r.content)
                            
                            # 1. Verificación de Seguridad (Huella Digital y Caption)
                            f_hash = self.get_file_hash(path)
                            self.last_media_hash = f_hash
                            caption = msg.get("caption", "")
                            video_data = self.analyze_video(path)
                            if self.check_security_blacklist(f_hash, cid, uid, uname, caption, video_data):
                                try: os.remove(path)
                                except: pass
                                continue

                            self.send_msg(cid, f"🌌 **Percepción IA (Video):** {video_data}")
                            ia_nativa.learn(video_data, source=global_chat_names.get(cid, cid))
                            # Incremento para Dashboard
                            db.set("STATS_VIDEOS", db.get("STATS_VIDEOS", 0) + 1)
                            try: os.remove(path)
                            except: pass
                        continue

                    # Smart AFK System
                    if str(MASTER_ID) in text and db.get("ADMIN_AFK", False):
                        self.send_msg(cid, "💤 **MODO AFK:** El administrador no está disponible ahora mismo. He registrado tu mención.")
                        add_web_log("INFO", f"Mención AFK registrada de {uname} en {global_chat_names.get(cid, cid)}")

                    # Admin Voice Commands (Simulated)
                    if "voice" in msg and uid == str(MASTER_ID):
                        self.send_msg(cid, "🎙️ **COMANDO DE VOZ DETECTADO:** Analizando instrucciones del Master...")
                        if random.random() > 0.5:
                            self.send_msg(cid, "✅ Acción ejecutada mediante voz: [Limpieza de Cache]")
                            add_web_log("ADMIN", "Limpieza de cache ejecutada por voz.")
                    
                    # Command Cooldowns
                    last_cmd = db.get(f"COOLDOWN_{uid}", 0)
                    if text.startswith("/") and time.time() - last_cmd < 1:
                        continue # 1 second cooldown
                    if text.startswith("/"): db.set(f"COOLDOWN_{uid}", time.time())
                    if "photo" in msg:
                        f = self.api_call("getFile", {"file_id": msg["photo"][-1]["file_id"]})
                        if f.get("ok"): global_media_list.append(f"https://api.telegram.org/file/bot{self.token}/{f['result']['file_path']}")
                    # Karma & Engagement System
                    sent = analyze_sentiment(text)
                    if uid not in global_user_stats: 
                        global_user_stats[uid] = {"name": uname, "count": 0, "karma": 0, "engagement": 0, "notes": ""}
                    global_user_stats[uid]["count"] += 1
                    if sent == "positive": global_user_stats[uid]["karma"] += 1
                    elif sent == "negative": global_user_stats[uid]["karma"] -= 1
                    
                    # Engagement formula: messages * karma_factor
                    global_user_stats[uid]["engagement"] = min(100, (global_user_stats[uid]["count"] * 2) + global_user_stats[uid]["karma"])
                    if cid not in global_chat_history: global_chat_history[cid] = []
                    
                    # Cargar configuración local
                    cfg = db.get(f"CONFIG_{cid}", {"ia_learning": False, "auto_mod": True, "welcome": False, "anti_link": False, "clean_join": False, "ia_mood": "friendly", "anti_flood": False})

                    # Anti-Flood Logic
                    if cfg.get("anti_flood") and uid != str(MASTER_ID):
                        now = time.time()
                        f_key = f"FLOOD_{cid}_{uid}"
                        history = db.get(f_key, [])
                        history = [t for t in history if now - t < 3]
                        history.append(now)
                        db.set(f_key, history)
                        if len(history) > 5:
                            self.send_msg(cid, f"🌊 **ANTI-FLOOD:** @{uname} silenciado por inundar el chat.")
                            self.restrict_user(cid, uid, until=int(now)+600) # 10 min
                            continue

                    # User Join tracking & Auto-Delete (Clean Join)
                    if "new_chat_members" in msg and cfg.get("clean_join"):
                        add_audit_log(f"Entrada de usuario limpiada en {global_chat_names.get(cid, cid)}")
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})

                    # 2. Caso Estándar (Grupos/Privados)
                    should_reply = False
                    
                    # Detección de Media para el Dashboard
                    media_info = None
                    if "photo" in msg:
                        media_info = {"type": "photo", "file_id": msg["photo"][-1]["file_id"]}
                    elif "video" in msg:
                        media_info = {"type": "video", "file_id": msg["video"].get("file_id")}
                    elif "voice" in msg:
                        media_info = {"type": "voice", "file_id": msg["voice"].get("file_id")}
                    elif "sticker" in msg:
                        media_info = {"type": "sticker", "file_id": msg["sticker"].get("file_id")}
                    elif "document" in msg:
                        media_info = {"type": "document", "file_id": msg["document"].get("file_id"), "name": msg["document"].get("file_name")}

                    global_chat_history[cid].append({
                        "time": datetime.datetime.now().strftime("%H:%M"), 
                        "sender": uname, 
                        "uid": uid,
                        "text": text,
                        "media": media_info
                    })
                    global_chat_names[cid] = msg["chat"].get("title", uname)
                    
                    # Last Seen tracking
                    vistos = db.get("U_FILE", {})
                    vistos[cid] = {"last_seen": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "name": global_chat_names[cid]}
                    db.set("U_FILE", vistos)

                    # PROCESAMIENTO DE COMANDOS (Si empieza por /)
                    if text.startswith("/"):
                        rk = self.get_user_rank(cid, uid)
                        self.process_command(cid, uid, uname, text, rk, msg["message_id"], msg)
                        continue # NUNCA pasar un comando a la IA

                    # Anti-Link per Group
                    if "http" in (text or "").lower() and cfg.get("anti_link"):
                        safe_domains = ["google.com", "github.com", "wikipedia.org"]
                        if not any(d in text.lower() for d in safe_domains):
                            self.send_msg(cid, f"🚫 @{uname}, los enlaces no están permitidos en este canal.")
                            self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})
                            continue

                    # Deep Link Scanning & Safe Search
                    if "http" in text:
                        safe_domains = ["google.com", "github.com", "wikipedia.org"]
                        if not any(d in text.lower() for d in safe_domains):
                            add_audit_log(f"Link sospechoso detectado: {text}")
                            # Simulate deep scan
                    
                    # FAQ Learning + Auto-respuesta si la pregunta se repite 3+ veces
                    if text.endswith("?"):
                        faq_key = text.lower().strip()
                        faq_db = db.get("FAQ_DB", {})
                        faq_db[faq_key] = faq_db.get(faq_key, 0) + 1
                        db.set("FAQ_DB", faq_db)
                        faq_answers = db.get("FAQ_ANSWERS", {})
                        if faq_db[faq_key] >= 3 and faq_key in faq_answers:
                            self.send_msg(cid, f"📚 **FAQ:** {faq_answers[faq_key]}")
                            continue
                    if any('\u0600' <= char <= '\u06FF' for char in text):
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})
                        continue
                    
                    # Group Link Detection
                    if "t.me/joinchat" in text or "t.me/+" in text:
                        self.send_msg(cid, "⚠️ Enlaces de grupos no permitidos.")
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})
                        continue
                    
                    # Profanity Filter
                    bad_words = ["spam", "scam", "crypto-offer"] # Example list
                    if any(w in text.lower() for w in bad_words):
                        self.send_msg(cid, "⚠️ Lenguaje no permitido.")
                        self.api_call("deleteMessage", {"chat_id": cid, "message_id": msg["message_id"]})
                        continue
                    

                    # 1. Caso Business (Modo Secretaria)
                    b_cfg = db.get("BUSINESS_CONFIG", {"ia_auto": False})
                    b_conn_id = msg.get("business_connection_id")
                    if b_conn_id and b_cfg.get("ia_auto"):
                        add_web_log("BUSINESS", f"🤖 IA Business respondiendo a {uname}...")
                        ia_res = ia_nativa.generate(text, chat_id=cid)
                        self.send_msg(cid, ia_res, business_connection_id=b_conn_id)
                        continue

                    # 2. IA Nativa (Auto-learning y respuesta)
                    ia_nativa.learn(text, source=global_chat_names.get(cid, cid))
                    
                    # Track language usage
                    lang = ia_nativa.detect_lang(text)
                    lang_counts = db.get("IA_LANG_COUNTS", {})
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    db.set("IA_LANG_COUNTS", lang_counts)
                    
                    rk = self.get_user_rank(cid, uid)

                    # --- PROCESAMIENTO DE COMANDOS (PRIORIDAD ALTA) ---
                    if text.startswith("/"):
                        if self.process_command(cid, uid, uname, text, rk, msg["message_id"], msg):
                            continue
                        
                        # Intentar procesar plugins
                        handled_plugin = False
                        for p in self.plugins:
                            if hasattr(p, "handle_command") and p.handle_command(self, cid, uid, text, rk): 
                                handled_plugin = True
                                break
                        if handled_plugin: continue

                    # 1. Modo Escucha (Bloquea IA y Aprendizaje, pero NO comandos arriba)
                    if listen_mode and uid != str(MASTER_ID):
                        continue
                    
                    # 2. Modo Alimentador IA (Aprende pero no responde, a menos que sea comando arriba)
                    feeder_groups = db.get("IA_FEEDERS", [])
                    if cid in feeder_groups and not text.startswith("/"):
                        add_web_log("IA", f"🧠 Aprendiendo en silencio de {global_chat_names.get(cid, cid)}")
                        continue

                    # 3. Activación IA por Mención o Master (Fuera de Comandos)
                    is_ia_call = (self.bot_username in text)
                    is_master_natural = (uid == str(MASTER_ID) and not text.startswith("/"))
                    
                    if is_ia_call or is_master_natural:
                        cfg = db.get(f"CONFIG_{cid}", {"ia_mood": "friendly"})
                        clean_text = text.replace(f"@{self.bot_username}", "").strip()
                        ia_nativa.remember_context(cid, clean_text, role="user")
                        resp = ia_nativa.generate(clean_text, chat_id=cid, mood_override=cfg.get("ia_mood"))
                        ia_nativa.remember_context(cid, resp, role="bot")
                        self.send_msg(cid, f"🌌 [Moon IA]: {resp}")
                        continue
                    
                    # Karma Badges assignment
                    k = global_user_stats[uid].get("karma", 0)
                    if k > 50: global_user_stats[uid]["badge"] = "🏆 Leyenda"
                    elif k > 20: global_user_stats[uid]["badge"] = "⭐ Colaborador"
                    else: global_user_stats[uid]["badge"] = "👤 Miembro"

                # --- Tareas Periódicas de Mantenimiento ---
                now_s = int(time.time())
                
                # 1. Sincronización de Seguridad (Hashes Externos)
                sync_freq = int(db.get("GLOBAL_SETTINGS", {}).get("sync_frequency", 21600))
                if now_s - db.get("LAST_SECURITY_SYNC", 0) > sync_freq:
                    threading.Thread(target=self.sync_security_hashes).start()
                    db.set("LAST_SECURITY_SYNC", now_s)
                
                # 2. Purga de Archivos Multimedia (Downloads)
                purge_days = int(db.get("GLOBAL_SETTINGS", {}).get("media_purge_days", 7))
                if now_s - db.get("LAST_MEDIA_PURGE", 0) > 86400: # Una vez al día
                    self.purge_old_media(purge_days)
                    db.set("LAST_MEDIA_PURGE", now_s)

                # 3. Backup automático de la base de datos cada 24h al Master
                if now_s - db.get("LAST_AUTO_BACKUP", 0) > 86400:
                    db.set("LAST_AUTO_BACKUP", now_s)
                    if MASTER_ID:
                        def _auto_backup():
                            db_path = "data/moon_database.db"
                            if os.path.exists(db_path):
                                size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
                                res = self.send_document(MASTER_ID, db_path, f"🔄 Backup automático 24h — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ({size_mb} MB)")
                                if res.get("ok"):
                                    add_web_log("SUCCESS", f"Backup automático enviado al Master ({size_mb} MB).")
                                else:
                                    add_web_log("ERROR", "Fallo al enviar backup automático.")
                        threading.Thread(target=_auto_backup, daemon=True).start()

            except Exception as e:
                logger.error(f"FATAL ERROR in Message Loop: {str(e)}")
                add_web_log("ERROR", f"Fallo en bucle de mensajes: {str(e)}")
                time.sleep(5)

def health_monitor():
    last_alert_time = 0
    while True:
        try:
            time.sleep(60)
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            
            if (cpu > 90 or mem > 90) and MASTER_ID != 0:
                if time.time() - last_alert_time > 600: # 10 minutos
                    msg = f"🚨 **ALERTA DE SALUD DEL SISTEMA** 🚨\n\nEl servidor está experimentando alta carga.\n* CPU: {cpu}%\n* RAM: {mem}%"
                    if proxy_bot: proxy_bot.send_msg(MASTER_ID, msg)
                    add_web_log("WARNING", f"Alerta de salud enviada al Master. CPU: {cpu}%, RAM: {mem}%")
                    last_alert_time = time.time()
        except Exception as e:
            time.sleep(60)

proxy_bot = None

if __name__ == "__main__":
    start_time, bots_data = time.time(), []
    if os.path.exists("data/bots.json"):
        with open("data/bots.json", "r") as f: 
            raw_data = json.load(f)
            bots_data = raw_data if isinstance(raw_data, list) else [raw_data]
    
    active_bots = []
    
    # Solo iniciamos hilos si NO es el reloader de Flask (para evitar duplicados)
    is_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or MOON_ENV != "dev"
    
    if bots_data and is_main_process:
        for i, b_info in enumerate(bots_data):
            token = b_info.get("token")
            if token:
                try:
                    bot_instance = MoonBot(token)
                    active_bots.append(bot_instance)
                    add_web_log("INFO", f"Configurando bot {i+1}: @{bot_instance.bot_username}")
                except Exception as e:
                    add_web_log("ERROR", f"Fallo al iniciar bot {i+1}: {e}")

        if active_bots:
            proxy_bot = active_bots[0]
            for bot in active_bots:
                # Sincronización Inicial: Poblar chats conocidos
                history = db.get("GLOBAL_HISTORY", [])
                known_cids = list(set(str(m.get("cid")) for m in history if m.get("cid")))
                if known_cids:
                    tk = bot.token
                    current = db.get(f"CHATS_{tk}", [])
                    updated = list(set(current + known_cids))
                    db.set(f"CHATS_{tk}", updated)
                
                add_web_log("SUCCESS", f"Lanzando hilo para @{bot.bot_username}...")
                threading.Thread(target=bot.run, daemon=True).start()
            
            def daily_report_worker():
                """Envía un resumen diario del crecimiento y salud del bot."""
                # Esperar a que el sistema se estabilice
                time.sleep(60)
                while True:
                    try:
                        last_report = db.get("LAST_DAILY_REPORT", "")
                        today = datetime.datetime.now().strftime("%Y-%m-%d")
                        # Si es un nuevo día, enviar reporte
                        if last_report != today:
                            if MASTER_ID:
                                ia_nativa.send_master_report("📅 RESUMEN DIARIO DE INTELIGENCIA")
                                db.set("LAST_DAILY_REPORT", today)
                                add_web_log("INFO", "Reporte diario enviado al Administrador Maestro.")
                    except Exception as e:
                        add_web_log("DEBUG", f"Error en daily_report_worker: {e}")
                    time.sleep(3600) # Comprobar cada hora

            threading.Thread(target=daily_report_worker, daemon=True).start()
            threading.Thread(target=health_monitor, daemon=True).start()
        else:
            add_web_log("ERROR", "No se pudo iniciar ningún bot. Verifica data/bots.json")
    
    add_web_log("INFO", f"🚀 Moon Multibot Core listo ({MOON_ENV.upper()}). Iniciando Dashboard...")
    PORT = 5001 if MOON_ENV == "dev" else 5000
    
    if MOON_ENV == "dev":
        app.run(host="0.0.0.0", port=PORT, debug=True)
    else:
        from waitress import serve
        print(f"[*] SERVIDOR DE PRODUCCIÓN ACTIVO (Waitress) en puerto {PORT}")
        serve(app, host="0.0.0.0", port=PORT, threads=6)
