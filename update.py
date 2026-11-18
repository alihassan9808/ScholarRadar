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
from urllib.parse import urlparse, parse_qs, urlencode
def clean(value):
    return html.unescape(re.sub(r"<[^>]+>"," ",value or "")).strip()[:18000]
ranks=json.loads("{\"Lancaster University\":[\"164\",\"lancaster-university\"],\"University of Surrey\":[\"=246\",\"university-surrey\"],\"University of Southampton\":[\"=111\",\"university-southampton\"],\"University of Leeds\":[\"=77\",\"university-leeds\"],\"University of Kent\":[\"415\",\"university-kent\"],\"University of East London\":[\"1001-1200\",\"university-east-london\"]}")
from html.parser import HTMLParser
class PageText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav","footer","header"): self.skip+=1
        if tag in ("p","div","li","h1","h2","h3","br","tr","td","dt","dd"): self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in ("script","style","nav","footer","header"): self.skip=max(0,self.skip-1)
        if tag in ("p","div","li","h1","h2","h3","tr","td","dt","dd"): self.parts.append("\n")
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)
def enrich(item):
    rank=ranks.get(item.get("university"))
    if rank: item.update(qs_rank=rank[0],qs_year=2027,qs_source="https://www.topuniversities.com/universities/"+rank[1])
    try:
        ref=parse_qs(urlparse(item["url"]).query).get("ref",[""])[0]
        direct="https://"+urlparse(item["url"]).hostname+"/Vacancy.aspx?"+urlencode({"ref":ref}) if ref else item["url"]
        req=urllib.request.Request(direct,headers={"User-Agent":"ScholarRadar/1.0 (academic listings reader)"})
        with urllib.request.urlopen(req,timeout=12) as response:
            if urlparse(response.geturl()).hostname!=urlparse(item["url"]).hostname: return item
            parser=PageText();parser.feed(response.read(2000000).decode("utf-8",errors="replace"))
        lines=[" ".join(t.split()) for t in "".join(parser.parts).splitlines() if t.strip()]
        if ref and not any(ref.lower() in line.lower() for line in lines) and not any(item["title"].split("(")[0].strip().lower() in line.lower() for line in lines):
            print("Could not confirm vacancy identity:",direct)
            return item
        item["country"]="United Kingdom"
        patterns={"deadline":r"closing date|application deadline|apply by","benefits":r"salary|stipend|tuition fee|funding|per annum","eligibility":r"eligible|eligibility|applicants must|candidates must","requirements":r"phd in|degree in|doctorate in|essential criteria|english language|you will have|you should have","documents":r"cover letter|curriculum vitae|\bCV\b|transcripts|references"}
        for field,pattern in patterns.items():
            matches=[]
            for i,line in enumerate(lines):
                if re.search(pattern,line,re.I) and len(line)<1500:
                    value=line
                    if len(line)<45 and i+1<len(lines): value+=" "+lines[i+1]
                    if value not in matches: matches.append(value)
            if matches: item[field]=" • ".join(matches[:3])
        if any(item.get(k) for k in patterns): item["details_source"]=direct
        print("Extracted",sum(bool(item.get(k)) for k in patterns),"fields:",ref)
    except Exception as exc: print("Details unavailable:",item["url"],str(exc))
    return item
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
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as pool:
    items=dict(zip(items.keys(),pool.map(enrich,items.values())))
print("Listings with extracted details:",sum(bool(x.get("details_source")) for x in items.values()),"/",len(items))
Path("opportunities.json").write_text(json.dumps({"updated":datetime.date.today().isoformat(),"items":list(items.values())},indent=2))
print(f"Collected {len(items)} opportunities")
