#!/usr/bin/env python3
"""Autoscaler conservador para las réplicas web de Moonbot en un host Docker."""
import argparse
import json
import subprocess
import time
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.scale.yml"]

def run(*args):
    return subprocess.run([*COMPOSE, *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout

def replicas():
    return len([line for line in run("ps", "-q", "moonbot").splitlines() if line.strip()])

def load():
    ids = [line for line in run("ps", "-q", "moonbot").splitlines() if line.strip()]
    if not ids: return 0.0, 0.0
    raw = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{json .}}", *ids], text=True, capture_output=True, check=True).stdout
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    percent = lambda value: float(str(value).replace("%", "").strip() or 0)
    return sum(percent(row.get("CPUPerc")) for row in rows) / len(rows), sum(percent(row.get("MemPerc")) for row in rows) / len(rows)

def request_node(action, pressure, replicas_count):
    """Call a provider-owned provisioner; credentials never enter Moonbot."""
    url=os.getenv("MOON_SCALE_PROVIDER_WEBHOOK","").strip();token=os.getenv("MOON_SCALE_PROVIDER_TOKEN","").strip()
    if not url: return False
    payload=json.dumps({"action":action,"cluster":"moonbot","pressure":round(pressure,2),"web_replicas":replicas_count,"at":int(time.time())}).encode()
    request=urllib.request.Request(url,data=payload,method="POST",headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"})
    with urllib.request.urlopen(request,timeout=15) as response:
      if response.status//100!=2: raise RuntimeError(f"provider HTTP {response.status}")
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument("--min",type=int,default=1);p.add_argument("--max",type=int,default=4);p.add_argument("--up",type=float,default=72);p.add_argument("--down",type=float,default=28);p.add_argument("--interval",type=int,default=30);p.add_argument("--cooldown",type=int,default=180);p.add_argument("--once",action="store_true");a=p.parse_args()
    last_change=0;saturated_since=0;provider_requested=False
    while True:
      try:
        count=max(a.min,replicas());cpu,mem=load();pressure=max(cpu,mem);target=count
        if time.time()-last_change>=a.cooldown:
          if pressure>=a.up and count<a.max: target=count+1
          elif pressure<=a.down and count>a.min: target=count-1
        if target!=count:
          run("up","-d","--no-build","--scale",f"moonbot={target}","moonbot");last_change=time.time()
          print(f"[autoscale] web {count}->{target}; cpu={cpu:.1f}% mem={mem:.1f}%",flush=True)
        else: print(f"[autoscale] web={count}; cpu={cpu:.1f}% mem={mem:.1f}%",flush=True)
        if pressure>=a.up and count>=a.max:
          saturated_since=saturated_since or time.time()
          if not provider_requested and time.time()-saturated_since>=a.cooldown:
            provider_requested=request_node("scale_out",pressure,count)
            if provider_requested: print("[autoscale] nodo externo solicitado al proveedor",flush=True)
        else: saturated_since=0;provider_requested=False
      except Exception as error: print(f"[autoscale] error: {error}",flush=True)
      if a.once: break
      time.sleep(max(10,a.interval))
if __name__=="__main__": main()
