"""Resource-specific Telegram WebApp home engines, future-0668..0687."""

import hashlib, hmac, json, math, re
from collections import Counter

def home_usage_forecast(daily_sessions, days=3):  # 0668
    xs=[int(x) for x in daily_sessions]
    if len(xs)<3 or any(x<0 for x in xs): raise ValueError("three non-negative days required")
    velocity=sum(b-a for a,b in zip(xs,xs[1:]))/(len(xs)-1)
    return {"resource":"webapp_home_sessions","forecast":[max(0,round(xs[-1]+velocity*i)) for i in range(1,days+1)],"method":"session_velocity"}

def home_onboarding_step(profile, completed):  # 0669
    steps=[("identify",bool(profile.get("user_id"))),("secure",bool(profile.get("security_reviewed"))),("personalize",bool(profile.get("preferences")))]
    pending=[name for name,ready in steps if not ready and name not in set(completed)]
    return {"resource":"webapp_home_onboarding","next_step":pending[0] if pending else None,"complete":not pending,"automatic_action":False}

def home_connectivity_alert(latencies, current_ms):  # 0670
    vals=[float(x) for x in latencies]
    if not vals or current_ms<0: raise ValueError("latency samples required")
    threshold=max(500,(sum(vals)/len(vals))*2)
    return {"resource":"webapp_home_connectivity","alert":current_ms>threshold,"threshold_ms":round(threshold),"current_ms":current_ms}

def home_quick_action_plan(event, actions):  # 0671
    allowed=[a for a in actions if a.get("trigger")==event.get("type") and a.get("enabled") is True]
    return {"resource":"webapp_home_quick_actions","planned":[a["id"] for a in allowed],"requires_confirmation":True,"executed":False}

def home_period_comparison(current, previous):  # 0672
    required={"visits","actions","errors"}
    if not required<=current.keys() or not required<=previous.keys(): raise ValueError("home metrics incomplete")
    return {"resource":"webapp_home_period","deltas":{k:int(current[k])-int(previous[k]) for k in sorted(required)},"periods_compared":2}

def sign_home_snapshot(widgets, secret):  # 0673
    if not isinstance(secret,bytes) or len(secret)<32: raise ValueError("32-byte key required")
    payload=json.dumps({"widgets":widgets},sort_keys=True,separators=(",",":")); sig=hmac.new(secret,payload.encode(),hashlib.sha256).hexdigest()
    return {"resource":"webapp_home_snapshot","payload":payload,"signature":sig,"algorithm":"HMAC-SHA256"}

def preview_home_layout(current_widgets, proposed_order):  # 0674
    current_ids=[x["id"] for x in current_widgets]
    if set(current_ids)!=set(proposed_order) or len(proposed_order)!=len(set(proposed_order)): raise ValueError("order must contain every widget once")
    return {"resource":"webapp_home_layout","before":current_ids,"after":list(proposed_order),"applied":False}

class HomePreferenceHistory:  # 0675
    def __init__(self): self.versions=[]
    def append(self, preferences):
        digest=hashlib.sha256(json.dumps(preferences,sort_keys=True).encode()).hexdigest()
        if self.versions and self.versions[-1]["digest"]==digest:return {**self.versions[-1],"changed":False}
        row={"version":len(self.versions)+1,"preferences":dict(preferences),"digest":digest};self.versions.append(row);return {**row,"changed":True}

def search_home_navigation(query, destinations):  # 0676
    terms=set(re.findall(r"\w+",str(query).casefold()))
    rows=[]
    for item in destinations:
        words=set(re.findall(r"\w+",f"{item.get('label','')} {item.get('description','')}".casefold()));rows.append({"route":item["route"],"score":len(terms&words)/max(1,len(terms))})
    return sorted(rows,key=lambda x:(-x["score"],x["route"]))

def explain_home_summary(counts):  # 0677
    allowed={"channels","pending_alerts","tasks"}
    if set(counts)-allowed: raise ValueError("unsupported home count")
    facts={k:max(0,int(v)) for k,v in counts.items()}
    return {"resource":"webapp_home_summary","facts":facts,"text":" · ".join(f"{k}: {v}" for k,v in sorted(facts.items())),"hallucination_free":True}

def authorize_home_widget(role, widget, action):  # 0678
    matrix={"member":{"view"},"admin":{"view","configure"},"master":{"view","configure","remove"}}
    allowed=action in matrix.get(role,set()) and widget.get("protected") is not True or role=="master" and action in matrix["master"]
    return {"resource":"webapp_home_widget","allowed":bool(allowed),"default_deny":True,"role":role,"action":action}

class HomeTemplates:  # 0679
    def __init__(self): self.items={}
    def save(self,name,widgets):
        ids=[x["id"] for x in widgets]
        if not name or len(ids)!=len(set(ids)):raise ValueError("invalid template")
        self.items[name]=json.loads(json.dumps(widgets));return {"name":name,"widget_count":len(ids)}
    def instantiate(self,name): return json.loads(json.dumps(self.items[name]))

def plan_home_batch_visibility(widgets, visible):  # 0680
    before={x["id"]:x.get("visible",True) for x in widgets};after={key:(key in set(visible)) for key in before}
    return {"resource":"webapp_home_visibility","before":before,"after":after,"undo":before,"applied":False}

def home_calendar(reminders, timezone):  # 0681
    if not re.fullmatch(r"[A-Za-z_]+/[A-Za-z_]+|UTC",timezone):raise ValueError("IANA timezone required")
    rows=sorted(reminders,key=lambda x:x["at"])
    conflicts=[a["id"] for a,b in zip(rows,rows[1:]) if a["at"]==b["at"]]
    return {"resource":"webapp_home_reminders","timezone":timezone,"reminders":rows,"conflicts":conflicts}

def protect_home_private_data(state):  # 0682
    sensitive={"email","phone","token","session"};redacted={k:("[redacted]" if k in sensitive else v) for k,v in state.items()}
    return {"resource":"webapp_home_private_state","data":redacted,"redacted":sum(k in sensitive for k in state),"persistent_copy":False}

def diagnose_home_readiness(checks):  # 0683
    required={"telegram_session","api","storage","clock"}
    missing=required-set(checks);failed=sorted(missing|{k for k in required if checks.get(k) not in {True,"ok"}})
    return {"resource":"webapp_home_readiness","ready":not failed,"failed_checks":failed,"repair_executed":False}

def recommend_home_shortcuts(activity, available, limit=4):  # 0684
    counts=Counter(activity);rows=[{"id":x["id"],"score":counts[x["id"]],"because":"recent_usage"} for x in available]
    return {"resource":"webapp_home_shortcuts","recommendations":sorted(rows,key=lambda x:(-x["score"],x["id"]))[:limit],"applied":False}

def review_home_change(change, approvals, required=2):  # 0685
    votes={a["actor"]:a["decision"] for a in approvals};approved=sum(v=="approve" for v in votes.values());rejected=any(v=="reject" for v in votes.values())
    return {"resource":"webapp_home_change","change_id":change["id"],"status":"rejected" if rejected else "approved" if approved>=required else "pending","unique_approvers":approved}

def home_collaboration_presence(participants):  # 0686
    unique={str(x["user_id"]):x for x in participants}
    return {"resource":"webapp_home_presence","online":sum(x.get("online") is True for x in unique.values()),"participants":sorted(unique),"personal_data":"ids_only"}

class HomeRealtimeMetrics:  # 0687
    def __init__(self,max_samples=60):self.max_samples=max_samples;self.samples=[]
    def record(self,timestamp,load_ms,error=False):
        if load_ms<0:raise ValueError("invalid load")
        self.samples.append({"at":timestamp,"load_ms":float(load_ms),"error":bool(error)});self.samples=self.samples[-self.max_samples:]
        return {"resource":"webapp_home_runtime","sample_count":len(self.samples),"latest_ms":float(load_ms),"error_rate":sum(x["error"] for x in self.samples)/len(self.samples)}
