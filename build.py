#!/usr/bin/env python3
"""Regenerates static HTML (home table rows, JSON-LD, FAQ, per-tool pages, sitemap) from data.json.
Run after editing data.json:  python3 build.py"""
import json, re, html, os
E=lambda s: html.escape(str(s if s is not None else ""), quote=True)
D=json.load(open("data.json")); T=D["tools"]; FX=D["fx"]
SITE="https://freetierwatch.co.uk"
def slug(n): return re.sub(r"[^a-z0-9]+","-",n.lower()).strip("-")
def month(d):
    import datetime; return datetime.date.fromisoformat(d).strftime("%b %Y")
BEEHIIV='<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="9023118a-54b2-4146-827a-5ed26d0013e0"></script>'
def free_txt(t): return "Unclear (not shown on the pricing page when checked)" if t["free"]=="unclear" else t["free"]
def row(t):
    f='<span class="unclear">Unclear</span>' if t["free"]=="unclear" else E(t["free"])
    n=f'<div class="note">{E(t["note"])}</div>' if t["note"] else ""
    return (f'<tr><td><a href="{E(t["url"])}" rel="nofollow noopener" target="_blank">{E(t["tool"])}</a>'
            f'<div class="note"><a href="/{slug(t["tool"])}/">{E(t["tool"])} free plan details</a></div></td>'
            f'<td>{f}{n}</td><td>£{t["paid_gbp"]:.2f}<div class="note">{E(t["paid_plan"])}</div></td>'
            f'<td>${t["paid_usd"]}</td><td>{E(t["checked"])}<div class="note"><a href="{E(t["source"])}" target="_blank" rel="noopener">source</a></div></td></tr>')
rows="".join(row(t) for t in sorted(T,key=lambda t:t["tool"].lower()))
fxline=f'£ prices converted at 1 USD = {FX["usd_gbp"]} GBP (mid-market, {E(FX["date"])}, <a href="{E(FX["source"])}">source</a>). Prices exclude VAT unless stated.'
log="".join(f'<li><strong>{E(c["date"])}</strong> · {E(c["tool"])}: {E(c["change"])} '+(f'<a href="{E(c["source"])}">source</a>' if c["source"] else "")+'</li>' for c in D["changelog"])
by={t["tool"]:t for t in T}; cheap=min(T,key=lambda t:t["paid_gbp"]); checked=max(t["checked"] for t in T)
def faqa(name):
    t=by[name]
    if t["free"]=="unclear": return f'Unclear. When we last checked ({t["checked"]}), {name}\'s pricing page did not show free plan details. Its cheapest paid plan is {t["paid_plan"]} at ${t["paid_usd"]} (about £{t["paid_gbp"]:.2f}) a month.'
    return f'Yes, {name} has a free plan: {t["free"]}. The cheapest paid plan is {t["paid_plan"]} at ${t["paid_usd"]} (about £{t["paid_gbp"]:.2f}) a month. Checked {t["checked"]}.'
faq=[("Which AI app builder has the best free plan?",
      "It depends what you are building. As of "+checked+": "+"; ".join(f'{t["tool"]}: {free_txt(t)}' for t in T if t["free"]!="unclear")+". Compare them in the table above."),
     ("Which AI app builder is cheapest to upgrade?",
      f'{cheap["tool"]} has the lowest cheapest paid plan in our table: {cheap["paid_plan"]} at ${cheap["paid_usd"]} (about £{cheap["paid_gbp"]:.2f}) a month.'+(f' Note: {cheap["note"]}' if cheap["note"] else "")),
     ("Is Lovable free?",faqa("Lovable")),("Is Bolt.new free?",faqa("Bolt.new")),("Is Replit free?",faqa("Replit"))]
faqhtml='<section id="faq"><h2>FAQ</h2>'+"".join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q,a in faq)+'</section>'
ld=[{"@context":"https://schema.org","@type":"WebSite","name":"FreeTierWatch","url":SITE+"/","inLanguage":"en-GB",
     "description":"Independent, dated tracker of free plans and cheapest paid plans for AI app builders, with prices in GBP."},
    {"@context":"https://schema.org","@type":"ItemList","name":"AI app builder free plans and prices in £","itemListElement":
     [{"@type":"ListItem","position":i+1,"name":t["tool"],"url":f'{SITE}/{slug(t["tool"])}/'} for i,t in enumerate(T)]},
    {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}]
ldhtml="".join('<script type="application/ld+json">'+json.dumps(x,ensure_ascii=False).replace("</","<\\/")+'</script>' for x in ld)
OG=('<meta property="og:image" content="https://freetierwatch.co.uk/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
    '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://freetierwatch.co.uk/og.png">')
# --- home
h=open("index.html").read()
def between(h,a,b,new):
    i=h.index(a)+len(a); j=h.index(b,i); return h[:i]+new+h[j:]
h=re.sub(r'<meta name="twitter:card" content="summary">','',h)
h=re.sub(r'<!--og-->.*?<!--/og-->','',h,flags=re.S); h=re.sub(r'<!--ld-->.*?<!--/ld-->','',h,flags=re.S)
h=h.replace("<style>",f"<!--og-->{OG}<!--/og--><!--ld-->{ldhtml}<!--/ld-->\n<style>",1)
h=between(h,"<tbody>","</tbody>",rows)
h=between(h,'<p class="note" id="fx">',"</p>",fxline)
h=between(h,'<ul id="log">',"</ul>",log)
h=re.sub(r'<section id="faq">.*?</section>','',h,flags=re.S)
h=h.replace('<section><h2>About</h2>',faqhtml+'\n<section><h2>About</h2>',1)
h=h.replace('<a href="${esc(t.url)}" rel="nofollow noopener" target="_blank">${esc(t.tool)}</a></td>',
            '<a href="${esc(t.url)}" rel="nofollow noopener" target="_blank">${esc(t.tool)}</a><div class="note"><a href="/${t.tool.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")}/">${esc(t.tool)} free plan details</a></div></td>')
open("index.html","w").write(h)
css=re.search(r"<style>.*?</style>",h,re.S).group(0)
# --- tool pages
for t in T:
    s=slug(t["tool"]); title=f'{t["tool"]} free plan & price in £ ({month(t["checked"])})'
    desc=f'{t["tool"]} free plan: {free_txt(t)}. Cheapest paid: {t["paid_plan"]}, ${t["paid_usd"]} (about £{t["paid_gbp"]:.2f})/month. Checked {t["checked"]}.'
    pl={"@context":"https://schema.org","@type":"WebPage","name":title,"url":f"{SITE}/{s}/","dateModified":t["checked"],"description":desc,
        "isPartOf":{"@type":"WebSite","name":"FreeTierWatch","url":SITE+"/"}}
    page=f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{SITE}/{s}/">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{SITE}/{s}/">{OG}
<script type="application/ld+json">{json.dumps(pl,ensure_ascii=False)}</script>
{css}</head><body>
<header><p class="note"><a href="/">← All AI app builder free plans</a></p><h1>{E(title)}</h1></header>
<main><div class="box">
<h2>Free plan</h2><p>{'<span class="unclear">Unclear</span>: not shown on the pricing page when checked.' if t["free"]=="unclear" else E(t["free"])}</p>
<h2>Cheapest paid plan</h2><p><strong>£{t["paid_gbp"]:.2f}/month</strong> (${t["paid_usd"]} US) · {E(t["paid_plan"])}</p>
{f'<p class="note">{E(t["note"])}</p>' if t["note"] else ""}
<p class="note">Last checked: {E(t["checked"])}. Converted at 1 USD = {FX["usd_gbp"]} GBP ({E(FX["date"])}). Prices change often, so check before you pay.</p>
<p><a href="{E(t["source"])}" target="_blank" rel="noopener">Official {E(t["tool"])} pricing page</a> · <a href="/">Compare all tools in the table</a></p>
</div>
<section class="box"><h2>Newsletter</h2><p>Get a weekly email when a free plan changes.</p>
{BEEHIIV}</section></main>
<footer class="note"><a href="/">FreeTierWatch</a> is independent and not affiliated with {E(t["tool"])}.<br>Made by Caro at <a href="https://www.instagram.com/ainofluff/" target="_blank" rel="noopener">Ainofluff</a><br>© 2026 FreeTierWatch</footer>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "f608d8c7c07c493081b69d69a6787c76"}}'></script><!-- End Cloudflare Web Analytics -->
</body></html>
'''
    os.makedirs(s,exist_ok=True); open(f"{s}/index.html","w").write(page)
urls=[("/",checked)]+[(f"/{slug(t['tool'])}/",t["checked"]) for t in T]
open("sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>\n" for u,d in urls)+"</urlset>\n")
print("\n".join(SITE+u for u,_ in urls))
