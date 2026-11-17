import json, datetime, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
url="https://www.jobs.ac.uk/jobs/academic/rss"
req=urllib.request.Request(url,headers={"User-Agent":"ScholarRadar/1.0 (public RSS reader)"})
with urllib.request.urlopen(req,timeout=30) as response:
    root=ET.fromstring(response.read())
items=[]
for entry in root.findall(".//item"):
    title=entry.findtext("title","").strip()
    link=entry.findtext("link","").strip()
    if link.startswith("https://") and any(w in title.lower() for w in ("phd","studentship","research assistant","postdoctoral","scholarship")):
        items.append({"title":title,"url":link,"country":"See listing","kind":"Research vacancy — funding not verified"})
if not root.findall(".//item"):
    raise RuntimeError("No RSS items; retaining previous data")
Path("opportunities.json").write_text(json.dumps({"updated":datetime.date.today().isoformat(),"items":items},indent=2))
