from resource_federation_continuity_assistance_engines import *
from resource_quality_sandbox_governance_impact_manifest import LABELS
RESOURCES=FED+CONT+ASSIST
def fam(i):return ("federation","Compatibilidad federada de","federation:verify") if i<7 else ("continuity","Continuidad operativa de","continuity:plan") if i<23 else ("assistance","Asistencia contextual para","assistance:read")
MANIFEST=tuple({"release_channel": "prealfa", "id":fid,"title":f"{prefix} {LABELS[r]} en Moonbot","capability":f"{prefix} {LABELS[r]}","module":"resource_federation_continuity_assistance_engines.py","api":api.__name__,"roles":("master",f"{scope}:{r}"),"preflight":f"repo_scan_before:{fid}/{api.__name__}: ID, API y capacidad exacta ausentes; contrato {family} específico no existente.","test":f"tests/test_resource_federation_continuity_assistance.py::test_{fid.replace('-','_')}"} for i,(fid,r,api) in enumerate(zip(IDS,RESOURCES,ALL_APIS)) for family,prefix,scope in (fam(i),))
CHANGELOG_APIS=tuple(x["api"] for x in MANIFEST);VERSION_PROPOSAL="v18.23.4"
