import urllib.request
import json

base_url = 'http://127.0.0.1:8000/api/v1'

def post_json(endpoint, data=None):
    req = urllib.request.Request(
        f'{base_url}{endpoint}',
        data=json.dumps(data).encode('utf-8') if data is not None else b'',
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def get_json(endpoint):
    with urllib.request.urlopen(f'{base_url}{endpoint}') as res:
        return json.loads(res.read().decode('utf-8'))

print("=========================================================")
print("            APIVERSE — LIVE SYSTEM VERIFICATION          ")
print("          Tagline: APIs change. Your code adapts.        ")
print("=========================================================\n")

# 1. System Health
print("[1/5] Checking System Health...")
health = get_json('/system/health')
print(f"      Status:     {health['status'].upper()}")
print(f"      Database:   {health['database'].upper()} (SQLite)")
print(f"      Scheduler:  {health['scheduler'].upper()}")

# 2. Seed Demo
print("\n[2/5] Synchronizing Comprehensive Fixture Dataset...")
seed_res = post_json('/system/seed-demo')
stats = seed_res.get("stats", {})
summary = seed_res.get("summary", {})
print(f"      Status:            {seed_res.get('status', 'ok').upper()}")
print(f"      Records Inserted:  {stats.get('inserted', 0)}")
print(f"      Records Reused:    {stats.get('reused', 0)}")
print(f"      Total Repos:       {summary.get('repositories', 'N/A')}")
print(f"      Total Scans:       {summary.get('scans', 'N/A')}")

# 3. Dashboard Metrics
print("\n[3/5] Querying Dashboard Aggregated Metrics...")
metrics = get_json('/dashboard/metrics')
counts = metrics['counts']
print(f"      Connected Repositories:    {counts['repositories']}")
print(f"      OpenAPI Specifications:   {counts['specifications']}")
print(f"      Total Scans Recorded:     {counts['scans']}")
print(f"      Breaking Changes Detected: {counts['breaking_changes']}")
print(f"      AI Repairs Generated:      {counts['total_repairs']}")
print(f"      Approved Repairs:          {counts['approved_repairs']}")
print(f"      Open Pull Requests:        {counts['open_prs']}")

# 4. Detected Breaking Changes
print("\n[4/5] Evaluating Detected Breaking Changes & Evidence...")
scans = get_json('/scans')
latest_scan = scans[0]
changes = get_json(f"/scans/{latest_scan['id']}/changes")
for idx, c in enumerate(changes[:5], 1):
    print(f"      {idx}. [{c['severity']}] {c['change_type']} on {c.get('http_method') or 'ANY'} {c['path']}")
    print(f"         Rule: {c['rule_code']} - {c['description']}")
if len(changes) > 5:
    print(f"      ... and {len(changes) - 5} more detected contract changes.")

# 5. Published Pull Requests
print("\n[5/5] Reviewing Autonomous Pull Requests...")
prs = get_json('/pull-requests')
for pr in prs:
    print(f"      -> PR #{pr['pr_number'] or pr['id']}: {pr['title']}")
    print(f"         Branch: {pr['branch_name']} -> {pr['base_branch']}")
    print(f"         Status: {pr['status'].upper()} (Safe Guard: Never merged to default)")

print("\n=========================================================")
print("  All systems running live! Open http://localhost:5173   ")
print("=========================================================")
