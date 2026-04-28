"""
Build AID/classification_v2/multilateral_cooperation.html.

Signals surfaced:
  - Donor class split per country (bilateral / multilateral / foundation) by $M commit
  - Top multilateral donors globally (with # countries active)
  - Bilateral funds channeled through multilateral delivery orgs (top channels)
  - Co-financed projects (same title across >1 donor)

Scope: 13 priority-target recipients, 2019-2024, digital projects only (v3.1 taxonomy).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

CSV_PATH = Path(
    "/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/"
    "experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv"
)
OUT_DIR = Path(__file__).parent
OUT_HTML = OUT_DIR / "multilateral_cooperation.html"

YEAR_MIN, YEAR_MAX = 2019, 2024
DIGITAL_CATS = {
    "digital_governance_and_rights",
    "digital_human_development",
    "hard_infrastructure",
}

BILATERAL = {
    "United States", "Germany", "France", "Japan", "Canada", "Italy", "Norway", "Sweden",
    "Australia", "Ireland", "Spain", "Finland", "Switzerland", "Denmark", "Korea",
    "United Kingdom", "Netherlands", "Austria", "Portugal", "Belgium", "Luxembourg",
    "Iceland", "New Zealand", "Poland", "Czechia", "Hungary", "Slovak Republic",
    "Slovenia", "Estonia", "Latvia", "Lithuania", "Greece", "Romania", "Bulgaria",
    "Croatia", "Malta", "Cyprus", "Liechtenstein", "Kuwait", "United Arab Emirates",
    "Saudi Arabia", "Qatar", "Chinese Taipei", "Israel", "Russia", "Thailand",
    "Türkiye", "Azerbaijan", "Monaco", "Kazakhstan",
}
FOUNDATIONS = {
    "Gates Foundation", "Ford Foundation",
    "John D. and Catherine T. MacArthur Foundation", "Mastercard Foundation",
    "Wellcome Trust", "William and Flora Hewlett Foundation",
    "David and Lucile Packard Foundation", "LEGO Foundation", "UBS Optimus Foundation",
    "Conrad N. Hilton Foundation", "Bloomberg Philanthropies",
    "Bernard van Leer Foundation", "Oak Foundation", "Rockefeller Foundation",
    "Open Society Foundations", "Howard G. Buffett Foundation", "Arcus Foundation",
    "IKEA Foundation", "Omidyar Network Fund, Inc.", "Postcode Innovation Trust",
    "H&M Foundation", "Jacobs Foundation", "McKnight Foundation",
    "Bill & Melinda Gates Foundation", "Susan T. Buffett Foundation",
    "Children's Investment Fund Foundation", "Fondation Botnar",
}
PUBLIC_FUND_MARKERS = (
    "Global Fund", "Adaptation Fund", "Green Climate Fund", "African Development Fund",
    "International Development Association", "Islamic Development Bank",
    "Private Infrastructure Development Group", "Climate Investment Funds",
    "Joint Sustainable Development Goals Fund", "Global Environment Facility",
)
MULTI_CHANNEL_MARKERS = (
    "United Nations", "World Health Organisation", "UNICEF", "UNDP", "UNFPA", "UNAIDS",
    "World Food Programme", "Food and Agricultural Organisation",
    "International Labour Organisation", "International Bank for Reconstruction",
    "International Development Association", "African Development Bank",
    "African Development Fund", "Asian Development Bank",
    "Inter-American Development Bank", "International Fund for Agricultural Development",
    "Global Fund", "Global Environment Facility", "European Investment Bank",
    "European Bank for Reconstruction", "Islamic Development Bank",
    "Climate Investment Funds", "GAVI", "UNESCO", "UN Women",
    "International Organisation for Migration", "UNHCR", "Delegated co-operation",
    "UN Capital Development Fund", "UN Conference on Trade", "UN Office",
    "United Nations Office",
)


def classify_donor(name: str) -> str:
    if name in BILATERAL:
        return "bilateral"
    if name in FOUNDATIONS:
        return "foundation"
    if any(marker in name for marker in PUBLIC_FUND_MARKERS):
        return "multilateral"
    if name.endswith("Foundation") or name.endswith("Philanthropies"):
        return "foundation"
    if name.endswith("Trust") and "Fund" not in name:
        return "foundation"
    return "multilateral"


def is_multi_channel(name) -> bool:
    if pd.isna(name):
        return False
    return any(marker in name for marker in MULTI_CHANNEL_MARKERS)


def load() -> pd.DataFrame:
    df = pd.read_csv(
        CSV_PATH,
        usecols=[
            "year", "donor_name", "recipient_name", "channel_name", "flow_name",
            "tech_category", "usd_commitment", "usd_disbursement", "project_title",
            "short_description",
        ],
    )
    d = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    d = d[d["tech_category"].isin(DIGITAL_CATS)]
    d["donor_class"] = d["donor_name"].apply(classify_donor)
    d["multi_channel"] = d["channel_name"].apply(is_multi_channel)
    d["usd_commitment"] = d["usd_commitment"].fillna(0.0)
    d["usd_disbursement"] = d["usd_disbursement"].fillna(0.0)
    return d


def donor_mix(df: pd.DataFrame) -> dict:
    """Per-country + global donor class totals ($M commit)."""
    out = {}
    for country, g in df.groupby("recipient_name"):
        parts = g.groupby("donor_class")["usd_commitment"].sum().round(2).to_dict()
        out[country] = {
            "bilateral": float(parts.get("bilateral", 0)),
            "multilateral": float(parts.get("multilateral", 0)),
            "foundation": float(parts.get("foundation", 0)),
            "total": float(sum(parts.values())),
            "n_projects": int(len(g)),
        }
    parts = df.groupby("donor_class")["usd_commitment"].sum().round(2).to_dict()
    out["__all__"] = {
        "bilateral": float(parts.get("bilateral", 0)),
        "multilateral": float(parts.get("multilateral", 0)),
        "foundation": float(parts.get("foundation", 0)),
        "total": float(sum(parts.values())),
        "n_projects": int(len(df)),
    }
    return out


def top_donors_for(df: pd.DataFrame, limit: int = 20) -> list[dict]:
    """For a given df subset, top donors by commit with class + country footprint."""
    g = df.groupby(["donor_name", "donor_class"]).agg(
        commit=("usd_commitment", "sum"),
        rows=("usd_commitment", "size"),
        countries=("recipient_name", "nunique"),
    ).reset_index()
    g = g.sort_values("commit", ascending=False).head(limit)
    return [
        {
            "donor": r.donor_name,
            "cls": r.donor_class,
            "commit": round(float(r.commit), 2),
            "rows": int(r.rows),
            "countries": int(r.countries),
        }
        for r in g.itertuples(index=False)
    ]


def top_donors_per_country(df: pd.DataFrame, per_country: int = 10) -> dict:
    out = {"__all__": top_donors_for(df, per_country)}
    for country, g in df.groupby("recipient_name"):
        out[country] = top_donors_for(g, per_country)
    return out


def channels_for(df_bil: pd.DataFrame, limit: int = 12) -> list[dict]:
    """Top multi-channel destinations used by bilateral donors."""
    c = df_bil[df_bil["multi_channel"]].groupby("channel_name").agg(
        commit=("usd_commitment", "sum"),
        rows=("usd_commitment", "size"),
        donors=("donor_name", "nunique"),
    ).reset_index()
    c = c.sort_values("commit", ascending=False).head(limit)
    return [
        {
            "channel": r.channel_name,
            "commit": round(float(r.commit), 2),
            "rows": int(r.rows),
            "donors": int(r.donors),
        }
        for r in c.itertuples(index=False)
    ]


def bilateral_channeling(df: pd.DataFrame) -> dict:
    df_bil = df[df["donor_class"] == "bilateral"]
    total_bil = float(df_bil["usd_commitment"].sum())
    via_multi = float(df_bil[df_bil["multi_channel"]]["usd_commitment"].sum())
    out = {
        "__all__": {
            "bilateral_total": round(total_bil, 2),
            "via_multi": round(via_multi, 2),
            "share": round(via_multi / total_bil, 4) if total_bil else 0,
            "channels": channels_for(df_bil),
        }
    }
    for country, g in df.groupby("recipient_name"):
        gb = g[g["donor_class"] == "bilateral"]
        bt = float(gb["usd_commitment"].sum())
        vm = float(gb[gb["multi_channel"]]["usd_commitment"].sum())
        out[country] = {
            "bilateral_total": round(bt, 2),
            "via_multi": round(vm, 2),
            "share": round(vm / bt, 4) if bt else 0,
            "channels": channels_for(gb, limit=8),
        }
    return out


def cofinanced_projects(df: pd.DataFrame) -> list[dict]:
    g = df[df["project_title"].fillna("").str.strip() != ""].groupby(
        ["recipient_name", "project_title"]
    ).agg(
        n_donors=("donor_name", "nunique"),
        donors=("donor_name", lambda s: sorted(set(s))),
        classes=("donor_class", lambda s: sorted(set(s))),
        commit=("usd_commitment", "sum"),
        year_min=("year", "min"),
        year_max=("year", "max"),
    ).reset_index()
    g = g[g["n_donors"] > 1].sort_values(["commit", "n_donors"], ascending=False)
    return [
        {
            "recipient": r.recipient_name,
            "title": r.project_title,
            "donors": list(r.donors),
            "classes": list(r.classes),
            "commit": round(float(r.commit), 2),
            "year_first": int(r.year_min),
            "year_last": int(r.year_max),
        }
        for r in g.itertuples(index=False)
    ]


def multilateral_footprint(df: pd.DataFrame, limit: int = 18) -> dict:
    """Top N multilateral donors x country presence matrix ($M commit; 0 if absent)."""
    multi = df[df["donor_class"] == "multilateral"]
    top_names = (
        multi.groupby("donor_name")["recipient_name"].nunique()
        .sort_values(ascending=False).head(limit).index.tolist()
    )
    mat = {}
    countries = sorted(df["recipient_name"].unique())
    for donor in top_names:
        sub = multi[multi["donor_name"] == donor]
        per_country = sub.groupby("recipient_name")["usd_commitment"].sum().round(2).to_dict()
        mat[donor] = {
            "total": round(float(sub["usd_commitment"].sum()), 2),
            "countries": int(sub["recipient_name"].nunique()),
            "per_country": {c: float(per_country.get(c, 0.0)) for c in countries},
        }
    return {"countries": countries, "donors": mat}


def build_payload(df: pd.DataFrame) -> dict:
    return {
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "countries": sorted(df["recipient_name"].unique()),
        "mix": donor_mix(df),
        "top_donors": top_donors_per_country(df),
        "channeling": bilateral_channeling(df),
        "cofinanced": cofinanced_projects(df),
        "footprint": multilateral_footprint(df),
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Multilateral cooperation — digital ODA (2019–2024)</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
:root{
  --bg:#0b1220; --panel:#11192b; --panel2:#162036; --ink:#e6ecf5; --muted:#8a98b2;
  --bil:#4b6ef5; --mul:#22c55e; --fnd:#f59e0b; --line:#1f2a44;
  --accent:#60a5fa;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:28px 24px 56px}
h1{font-size:22px;margin:0 0 6px;font-weight:600;letter-spacing:-0.01em}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 22px}
.pill{background:var(--panel);border:1px solid var(--line);color:var(--ink);padding:6px 12px;border-radius:999px;font-size:12.5px;cursor:pointer;transition:all .12s}
.pill:hover{border-color:var(--accent)}
.pill.active{background:var(--accent);color:#0b1220;border-color:var(--accent);font-weight:600}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(4,1fr)}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi .lab{color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
.kpi .val{font-size:22px;font-weight:600;margin-top:4px}
.kpi .sub2{color:var(--muted);font-size:11.5px;margin-top:2px}
.kpi.bil .val{color:var(--bil)} .kpi.mul .val{color:var(--mul)} .kpi.fnd .val{color:var(--fnd)}
section{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-top:18px}
section h2{font-size:15px;margin:0 0 4px;font-weight:600}
section .h2sub{color:var(--muted);font-size:12px;margin-bottom:14px}
.bar-row{display:grid;grid-template-columns:140px 1fr 120px;gap:10px;align-items:center;padding:4px 0;font-size:12.5px}
.bar-row .lbl{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar-row .lbl .cn{color:var(--muted);font-size:11px;margin-left:6px}
.bar-row .bar{background:var(--panel2);border-radius:4px;height:14px;position:relative;overflow:hidden}
.bar-row .bar .seg{height:100%;display:inline-block;vertical-align:top}
.bar-row .val{color:var(--muted);font-size:12px;text-align:right;font-variant-numeric:tabular-nums}
.seg.bil{background:var(--bil)} .seg.mul{background:var(--mul)} .seg.fnd{background:var(--fnd)}
.legend{display:flex;gap:18px;color:var(--muted);font-size:12px;margin-bottom:10px}
.legend .dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:500;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{display:inline-block;padding:1px 7px;border-radius:4px;font-size:10.5px;margin-right:4px}
.chip.bil{background:rgba(75,110,245,.18);color:#93b1ff}
.chip.mul{background:rgba(34,197,94,.18);color:#6ee7a0}
.chip.fnd{background:rgba(245,158,11,.2);color:#fcb664}
.tt{color:var(--muted);font-size:11.5px}
.empty{color:var(--muted);text-align:center;padding:20px;font-style:italic}
.footprint-wrap{overflow-x:auto}
.footprint{min-width:900px;border-collapse:collapse;font-size:11px}
.footprint th{position:sticky;top:0;background:var(--panel);white-space:nowrap;padding:6px 4px;text-align:center;border-bottom:1px solid var(--line)}
.footprint th.donor-col{text-align:left;min-width:220px;padding-left:10px}
.footprint td{padding:3px 4px;text-align:center;border-bottom:1px solid var(--line)}
.footprint td.donor{text-align:left;font-size:12px;padding-left:10px}
.cell{display:inline-block;width:28px;height:18px;border-radius:2px;vertical-align:middle}
.cell[data-v="0"]{background:transparent;border:1px dashed #26304a}
.meta-num{color:var(--muted);font-size:11px;margin-left:4px}
.hint{color:var(--muted);font-size:11.5px;margin-top:6px}
.country-header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:4px}
.country-header .total{color:var(--muted);font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>Multilateral cooperation in digital ODA</h1>
  <div class="sub">13 priority-target recipients · 2019–2024 · v3.1 ensemble (digital projects only)</div>

  <div class="pills" id="pills"></div>

  <div class="grid kpis" id="kpis"></div>

  <section id="sec-mix">
    <h2>Donor mix by country</h2>
    <div class="h2sub">100% stacked by commit ($M). Total commitment labelled on the right.</div>
    <div class="legend">
      <span><span class="dot" style="background:var(--bil)"></span>Bilateral (donor country)</span>
      <span><span class="dot" style="background:var(--mul)"></span>Multilateral / IGO</span>
      <span><span class="dot" style="background:var(--fnd)"></span>Private foundation</span>
    </div>
    <div id="mix"></div>
  </section>

  <section id="sec-donors">
    <h2 id="donors-title">Top donors</h2>
    <div class="h2sub" id="donors-sub"></div>
    <div id="donors"></div>
  </section>

  <section id="sec-chan">
    <h2 id="chan-title">Bilateral → multilateral channeling</h2>
    <div class="h2sub" id="chan-sub"></div>
    <div id="chan"></div>
  </section>

  <section id="sec-foot">
    <h2>Multilateral footprint</h2>
    <div class="h2sub">Presence of top multilateral donors across the 13 priority-target recipients (square intensity = $M commit, 2019–2024).</div>
    <div class="footprint-wrap"><table class="footprint" id="foot"></table></div>
  </section>

  <section id="sec-cof">
    <h2 id="cof-title">Co-financed projects</h2>
    <div class="h2sub">Projects with the same title funded by more than one donor. Strongest explicit co-financing signal in the data.</div>
    <div id="cof"></div>
  </section>
</div>

<script>
var PAYLOAD = {}; /*END_PAYLOAD*/

var state = { country: "__all__" };

function fmtUsd(m){
  if(!m) return "$0";
  if(m >= 1000) return "$" + (m/1000).toFixed(m>=10000?1:2) + "B";
  if(m >= 1) return "$" + m.toFixed(m>=100?0:1) + "M";
  return "$" + (m*1000).toFixed(0) + "K";
}
function fmtPct(f){ return (f*100).toFixed(1) + "%"; }
function esc(s){ return String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function classLabel(c){ return c==="bilateral"?"Bilateral":c==="multilateral"?"Multilateral":"Foundation"; }
function classShort(c){ return c==="bilateral"?"bil":c==="multilateral"?"mul":"fnd"; }
function countryLabel(c){ return c==="__all__"?"All 13 recipients":c; }

function renderPills(){
  var p = document.getElementById("pills");
  var opts = ["__all__"].concat(PAYLOAD.countries || []);
  p.innerHTML = opts.map(c=>`<span class="pill ${c===state.country?'active':''}" data-c="${esc(c)}">${esc(countryLabel(c))}</span>`).join("");
  p.querySelectorAll(".pill").forEach(el=>{
    el.onclick = ()=>{ state.country = el.dataset.c; renderAll(); };
  });
}

function renderKpis(){
  var m = PAYLOAD.mix[state.country] || {bilateral:0,multilateral:0,foundation:0,total:0,n_projects:0};
  var total = m.total || 1;
  var html = [
    `<div class="kpi"><div class="lab">Total digital commit</div><div class="val">${fmtUsd(m.total)}</div><div class="sub2">${m.n_projects.toLocaleString()} project rows</div></div>`,
    `<div class="kpi bil"><div class="lab">Bilateral</div><div class="val">${fmtPct(m.bilateral/total)}</div><div class="sub2">${fmtUsd(m.bilateral)}</div></div>`,
    `<div class="kpi mul"><div class="lab">Multilateral / IGO</div><div class="val">${fmtPct(m.multilateral/total)}</div><div class="sub2">${fmtUsd(m.multilateral)}</div></div>`,
    `<div class="kpi fnd"><div class="lab">Foundation</div><div class="val">${fmtPct(m.foundation/total)}</div><div class="sub2">${fmtUsd(m.foundation)}</div></div>`
  ];
  document.getElementById("kpis").innerHTML = html.join("");
}

function renderMix(){
  var rows = [];
  var countries = (PAYLOAD.countries || []).slice();
  countries.sort((a,b)=>(PAYLOAD.mix[b].total||0)-(PAYLOAD.mix[a].total||0));
  countries.forEach(c=>{
    var m = PAYLOAD.mix[c]; if(!m) return;
    var t = m.total || 1;
    var pb = m.bilateral/t*100, pm = m.multilateral/t*100, pf = m.foundation/t*100;
    rows.push(`<div class="bar-row">
      <div class="lbl">${esc(c)}</div>
      <div class="bar"><span class="seg bil" style="width:${pb}%" title="Bilateral: ${fmtUsd(m.bilateral)}"></span><span class="seg mul" style="width:${pm}%" title="Multilateral: ${fmtUsd(m.multilateral)}"></span><span class="seg fnd" style="width:${pf}%" title="Foundation: ${fmtUsd(m.foundation)}"></span></div>
      <div class="val">${fmtUsd(m.total)}</div>
    </div>`);
  });
  document.getElementById("mix").innerHTML = rows.join("") || `<div class="empty">No data.</div>`;
}

function renderDonors(){
  var list = PAYLOAD.top_donors[state.country] || [];
  document.getElementById("donors-title").textContent = "Top donors — " + countryLabel(state.country);
  document.getElementById("donors-sub").textContent = list.length ? "Ranked by total commit ($M). Colored chip shows donor class." : "";
  if(!list.length){ document.getElementById("donors").innerHTML = `<div class="empty">No donor data.</div>`; return; }
  var max = Math.max.apply(null, list.map(d=>d.commit));
  var html = list.map(d=>{
    var w = max ? (d.commit/max*100) : 0;
    var cls = classShort(d.cls);
    var meta = state.country === "__all__" ? ` <span class="cn">· ${d.countries} countries</span>` : "";
    return `<div class="bar-row">
      <div class="lbl"><span class="chip ${cls}">${classLabel(d.cls)}</span>${esc(d.donor)}${meta}</div>
      <div class="bar"><span class="seg ${cls}" style="width:${w}%"></span></div>
      <div class="val">${fmtUsd(d.commit)}</div>
    </div>`;
  });
  document.getElementById("donors").innerHTML = html.join("");
}

function renderChan(){
  var c = PAYLOAD.channeling[state.country] || {bilateral_total:0,via_multi:0,share:0,channels:[]};
  document.getElementById("chan-title").textContent = "Bilateral → multilateral channeling — " + countryLabel(state.country);
  var sub = `Of ${fmtUsd(c.bilateral_total)} bilateral commit, ${fmtUsd(c.via_multi)} (${fmtPct(c.share)}) was delivered through multilateral channels (UN agencies, MDBs, IGOs, delegated cooperation).`;
  document.getElementById("chan-sub").textContent = sub;
  if(!c.channels.length){ document.getElementById("chan").innerHTML = `<div class="empty">No channel data.</div>`; return; }
  var max = Math.max.apply(null, c.channels.map(ch=>ch.commit));
  var html = c.channels.map(ch=>{
    var w = max ? (ch.commit/max*100) : 0;
    return `<div class="bar-row">
      <div class="lbl">${esc(ch.channel)}<span class="cn">· ${ch.donors} donor${ch.donors===1?'':'s'}</span></div>
      <div class="bar"><span class="seg mul" style="width:${w}%"></span></div>
      <div class="val">${fmtUsd(ch.commit)}</div>
    </div>`;
  });
  document.getElementById("chan").innerHTML = html.join("");
}

function renderFoot(){
  var fp = PAYLOAD.footprint || {countries:[], donors:{}};
  var countries = fp.countries;
  var donors = fp.donors;
  var names = Object.keys(donors);
  names.sort((a,b)=> donors[b].countries - donors[a].countries || donors[b].total - donors[a].total);
  var maxAny = 0;
  names.forEach(n=>{ countries.forEach(c=>{ var v=donors[n].per_country[c]||0; if(v>maxAny) maxAny=v; }); });
  // scale with log to not let ADB/GlobalFund dominate
  function intensity(v){ if(v<=0) return 0; var lv = Math.log10(v+1), lm = Math.log10(maxAny+1); return Math.max(0.08, lv/lm); }
  var header = ["<thead><tr><th class='donor-col'>Multilateral donor</th><th>Countries</th><th>$M total</th>"];
  countries.forEach(c=>{ header.push(`<th title="${esc(c)}">${esc(c.length>8?c.slice(0,7)+'…':c)}</th>`); });
  header.push("</tr></thead>");
  var body = ["<tbody>"];
  names.forEach(n=>{
    var row = [`<tr><td class='donor'>${esc(n)}</td><td>${donors[n].countries}</td><td class='num'>${fmtUsd(donors[n].total)}</td>`];
    countries.forEach(c=>{
      var v = donors[n].per_country[c] || 0;
      if(v <= 0) { row.push(`<td><span class='cell' data-v='0'></span></td>`); }
      else {
        var a = intensity(v);
        row.push(`<td title="${esc(c)}: ${fmtUsd(v)}"><span class='cell' style='background:rgba(34,197,94,${a.toFixed(2)})'></span></td>`);
      }
    });
    row.push("</tr>"); body.push(row.join(""));
  });
  body.push("</tbody>");
  document.getElementById("foot").innerHTML = header.join("") + body.join("");
}

function renderCof(){
  var all = PAYLOAD.cofinanced || [];
  var list = state.country === "__all__" ? all : all.filter(r=>r.recipient===state.country);
  document.getElementById("cof-title").textContent = "Co-financed projects — " + countryLabel(state.country);
  if(!list.length){ document.getElementById("cof").innerHTML = `<div class="empty">No multi-donor projects found in the data for this scope.</div>`; return; }
  var rows = list.map(r=>{
    var donors = r.donors.map((d,i)=>{ var cls = classShort(r.classes[i] || r.classes[0] || 'multilateral'); return `<span class='chip ${cls}'>${esc(d)}</span>`; }).join(" ");
    return `<tr><td>${esc(r.recipient)}</td><td>${esc(r.title)}</td><td>${donors}</td><td class='num'>${fmtUsd(r.commit)}</td><td class='num'>${r.year_first===r.year_last?r.year_first:r.year_first+'–'+r.year_last}</td></tr>`;
  });
  var html = `<table>
    <thead><tr><th>Recipient</th><th>Project title</th><th>Donors</th><th>$M commit</th><th>Years</th></tr></thead>
    <tbody>${rows.join("")}</tbody></table>`;
  document.getElementById("cof").innerHTML = html;
}

function renderAll(){
  renderPills(); renderKpis(); renderMix(); renderDonors(); renderChan(); renderFoot(); renderCof();
}
renderAll();
</script>
</body>
</html>
"""


def write_html(payload: dict) -> None:
    html = HTML_TEMPLATE
    js = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = re.sub(
        r"var PAYLOAD = \{\};\s*/\*END_PAYLOAD\*/",
        "var PAYLOAD = " + js + "; /*END_PAYLOAD*/",
        html,
        count=1,
    )
    OUT_HTML.write_text(html)


def main() -> None:
    print("Loading", CSV_PATH.name, "...")
    df = load()
    print(f"  rows (digital 2019-2024): {len(df):,}")
    print(f"  countries: {df['recipient_name'].nunique()}")
    payload = build_payload(df)
    write_html(payload)
    size_kb = OUT_HTML.stat().st_size / 1024
    print(f"\nWrote {OUT_HTML.name} ({size_kb:,.0f} KB)")
    print()
    print("Global mix ($M commit):")
    m = payload["mix"]["__all__"]
    for k in ("bilateral", "multilateral", "foundation"):
        pct = m[k] / m["total"] * 100 if m["total"] else 0
        print(f"  {k:13s}  ${m[k]:>9,.1f}M  {pct:5.1f}%")
    print(f"  total         ${m['total']:>9,.1f}M")
    print()
    print("Bilateral channeling global:")
    ch = payload["channeling"]["__all__"]
    print(f"  bilateral total: ${ch['bilateral_total']:,.1f}M")
    print(f"  via multi:       ${ch['via_multi']:,.1f}M ({ch['share']*100:.1f}%)")
    print(f"\nCo-financed projects: {len(payload['cofinanced'])}")
    print(f"Multilateral donors in footprint: {len(payload['footprint']['donors'])}")


if __name__ == "__main__":
    main()
