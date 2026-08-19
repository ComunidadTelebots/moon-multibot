"""Manifest for Moonbot future-5702..future-5879."""
from resource_energy_abuse_migration_federation_engines import ALL_APIS,ABUSE,ENERGY,FEDERATION,IDS,MIGRATION
from resource_quality_sandbox_governance_impact_manifest import LABELS
RESOURCES=ENERGY+ABUSE+MIGRATION+FEDERATION
def _family(i):
    if i<17:return "energy","Optimización energética de","energy:plan"
    if i<33:return "abuse","Limitación antiabuso de","abuse:evaluate"
    if i<50:return "migration","Migración guiada de","migration:plan"
    return "federation","Compatibilidad federada de","federation:verify"
def _preflight(fid,api,family):
    why={"energy":"sin plan por carga ni intensidad Wh/elemento","abuse":"sin ventana deslizante y burst por sujeto","migration":"sin prechecks, digest, backup y rollback","federation":"sin allowlist de origen, esquema y vigencia"}[family]
    return f"repo_scan_before:{fid}/{api}: ID, API y capacidad exacta ausentes; {why}."
MANIFEST=tuple({"release_channel": "rc", "id":fid,"title":f"{prefix} {LABELS[r]} en Moonbot","capability":f"{prefix} {LABELS[r]}","module":"resource_energy_abuse_migration_federation_engines.py","api":api.__name__,"test":f"tests/test_resource_energy_abuse_migration_federation.py::test_{fid.replace('-','_')}","preflight":_preflight(fid,api.__name__,family),"roles":("master",f"{scope}:{r}")} for i,(fid,r,api) in enumerate(zip(IDS,RESOURCES,ALL_APIS)) for family,prefix,scope in (_family(i),))
CHANGELOG_APIS=tuple(x["api"] for x in MANIFEST)
VERSION_PROPOSAL="v18.23.3"
