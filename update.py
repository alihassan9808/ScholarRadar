import json, datetime, urllib.request, html, re
from pathlib import Path
import feedparser
sources=[
("https://hr-jobs.lancs.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
("https://jobs.surrey.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
("https://jobs.soton.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
("https://jobs.leeds.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
("https://jobs.kent.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
("https://jobs.uel.ac.uk/RSS/rss.aspx","United Kingdom / see listing"),
]
universities={"hr-jobs.lancs.ac.uk":"Lancaster University","jobs.surrey.ac.uk":"University of Surrey","jobs.soton.ac.uk":"University of Southampton","jobs.leeds.ac.uk":"University of Leeds","jobs.kent.ac.uk":"University of Kent","jobs.uel.ac.uk":"University of East London"}
from urllib.parse import urlparse
def clean(value):
    return html.unescape(re.sub(r"<[^>]+>"," ",value or "")).strip()[:18000]
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
            if re.search(r"\b(manager|administrator|coordinator|officer|librarian)\b", title, re.I):
                continue
            if link.startswith("https://") and any(w in title.lower() for w in ("phd","ph.d","doctoral","studentship","research assistant","postdoc","scholarship","research fellow","research associate","researcher")):
                items[link]={"title":title,"url":link,"country":country,"kind":"Research vacancy","category":("PhD / studentship" if re.search(r"\b(phd|ph\.d|studentship|doctoral candidate)\b",title,re.I) else "Postdoctoral" if re.search(r"postdoc|research fellow",title,re.I) else "Research position"),"funding":"Check source","university":universities.get(urlparse(url).hostname),"description":clean(e.get("summary","")),"published":e.get("published",""),"source":url}
        print(f"{url}: {len(data.entries)} entries")
    except Exception as exc:
        print(f"Feed unavailable: {url}: {exc}")
if not successful or not items:
    raise RuntimeError("No qualifying entries from available feeds; previous data preserved")
Path("opportunities.json").write_text(json.dumps({"updated":datetime.date.today().isoformat(),"items":list(items.values())},indent=2))
print(f"Collected {len(items)} opportunities")
