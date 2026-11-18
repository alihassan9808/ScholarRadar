import json, datetime, urllib.request, html, re
from pathlib import Path
import feedparser
sources=[
("https://www.jobs.ac.uk/jobs/academic/rss","See listing"),
("https://www.jobs.ac.uk/jobs/phd/rss","United Kingdom / see listing"),
("https://academicpositions.com/rss","See listing"),
]
items={}
successful=0
for url,country in sources:
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ScholarRadar/1.0 (public feed reader)"})
        with urllib.request.urlopen(req,timeout=30) as response:
            data=feedparser.parse(response.read())
        if not data.entries:
            raise ValueError("No recognizable feed entries")
        successful+=1
        for e in data.entries:
            title=html.unescape(re.sub(r"<[^>]+>","",e.get("title",""))).strip()
            link=e.get("link","")
            if link.startswith("https://") and any(w in title.lower() for w in ("phd","ph.d","doctoral","studentship","research assistant","postdoc","scholarship")):
                items[link]={"title":title,"url":link,"country":country,"kind":"Research vacancy"}
        print(f"{url}: {len(data.entries)} entries")
    except Exception as exc:
        print(f"Feed unavailable: {url}: {exc}")
if not successful or not items:
    raise RuntimeError("No qualifying entries from available feeds; previous data preserved")
Path("opportunities.json").write_text(json.dumps({"updated":datetime.date.today().isoformat(),"items":list(items.values())},indent=2))
print(f"Collected {len(items)} opportunities")
