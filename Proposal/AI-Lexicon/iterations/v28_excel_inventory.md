# v28 — Excel Reference Inventory (US-001)

**Source of truth**: `/Users/robertpraas/Downloads/Cross-checked_AI terminology and taxonomy_analysis_final.xlsx` (87 KB, 2026-04-28).

This document inventories every regulatory text, every term, every per-text article reference, and every terminology resolution the Excel actually contains. Downstream stories (US-002…) must verify the v27 HTML against this baseline before declaring fixes done. Where the Excel and v27 HTML conflict, the **Excel wins** unless the conflict is documented as resolved here.

---

## 1. Workbook structure (echoed back)

13 sheets. Column counts shown are the worksheet `max_column`; data is sparse on the right.

| # | Sheet name | Rows × Cols | Purpose |
|---|---|---|---|
| 1 | `Second edition terminology` | 37 × 4 | 36 background terms inherited from the **2024 EU-U.S. Terminology and Taxonomy** (clusters: AI Lifecycle, Measurement, Technical system attributes, Governance, Trustworthy). NOT the 43 comparative terms — these are the legacy glossary the lexicon should *also* surface. |
| 2 | `About the Digital AI Lexicon` | 14 × 10 | Single prose cell. Authoritative scope statement: **"43 terms across 12 regulatory frameworks and relevant guidance documents"**. |
| 3 | `Methodology` | 29 × 10 | 6-step methodology + the **"Overview of Selected Regulations"** table (the canonical 12-text list with effective dates). |
| 4 | `New concepts` | 27 × 8 | Cluster→Term juxtaposition matrix. EU-AIA term in col C, then California / Colorado / New York / Texas / Utah equivalent terms. The new "Actors" cluster is added here. |
| 5 | ` High-risk AI system_ANALYSIS` | 37 × 13 | (Note leading space in name.) AIA / Colorado SB 24-205 / Utah SB 226. |
| 6 | `GPAI system_Generative AI_ANALY` | 18 × 10 | AIA / California (SB 942 + AB 2013) / Utah SB 226. |
| 7 | `GPAI_Frontier_Foundation_Analys` | 13 × 12 | AIA / California SB 53 / New York S8828. |
| 8 | `Provider_Developer_Analysis` | 106 × 13 | **Four sub-tables stacked vertically** (see §4). |
| 9 | `Deployer_Supplier_Analysis` | 68 × 9 | **Three sub-tables stacked vertically** (see §5). |
| 10 | `Risk_ANALYSIS` | 8 × 6 | AIA Systemic risk / California SB 53 / NY S8828 Catastrophic risk. |
| 11 | `Modification_ANALYSIS` | 13 × 7 | AIA / California (SB 53 + AB 2013) / NY S8828 / Colorado SB 24-205. |
| 12 | `Incident_ANALYSIS` | 10 × 11 | AIA Serious incident / California SB 53 / NY S8828 Critical safety incident. |
| 13 | `Prohibited_Practices` | 44 × 8 | Practice × jurisdiction matrix (only EU + Colorado + Texas have entries). |

**Common analysis-sheet schema**: row 1–2 are jurisdiction headers; col A holds attribute labels (Term / Definition / Scope / Regulatory trigger / Temporal trigger / Transparency / Risk management / Incident reporting / Penalties / Exemptions / Rebuttal / …); rightmost column is **Interpretative notes** as a single multi-line cell. **Article/section references appear inline** within data cells (e.g., `(Article 50)`, `(§6-1-1701)`, `(22757.12.)`), often on continuation rows underneath the main bullet — extraction must walk merged/continuation cells, not assume one cell per attribute.

---

## 2. The 12 regulatory texts (Methodology sheet, "Overview of Selected Regulations")

Pulled directly from rows A18–A33 of `Methodology`. Column 1 = jurisdiction; column 2 = bill/instrument; column 4 = effective-from date.

| # | Jurisdiction | Bill / instrument | Effective from | Excel short-code used in tables | v27 HTML `law-blob` id |
|---|---|---|---|---|---|
| 1 | European Union | **AI Act (2024)** | 2024-08-01 | `AIA` | `eu-ai-act` |
| 2 | European Union | **Code of Practice for GPAI Models (2025)** — three chapters: Copyright (CoP CC), Transparency (CoP TC), Safety & Security for GPAISR (CoP SSC) | 2025-08-02 | `CoP`, `CoP CC`, `CoP TC`, `CoP SSC` | `eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety` (split into 3) |
| 3 | European Union | **Guidelines on the scope of obligations for GPAI models (2025)** | 2025-08-02 | `GL` | `eu-guidelines-gpai-scope` |
| 4 | California | **SB 53 (2025) — Transparency in Frontier AI** | 2026-01-01 | `SB 53` | `ca-sb53` |
| 5 | California | **SB 942 (2024) — California AI Transparency Act** | 2026-08-02 | `SB 942` | `ca-sb942` |
| 6 | California | **AB 2013 (2024) — training-data transparency** | (not stated in overview row, but referenced throughout the Excel) | `AB 2013` | `ca-ab2013` |
| 7 | Colorado | **SN24-205 / SB 24-205 (2024) — Colorado AI Act (CAIA)** | 2026-06-30 | `SB 24-205` | `co-sb24205` |
| 8 | Colorado | **SB 25B-004 (2026) — amends CAIA, extends enforcement to June 2026** | (no date in Excel) | `SB 25B-004` | **MISSING in v27 HTML** |
| 9 | New York | **A6453B (2025) — RAISE Act** | 2026-03-19 | `A6453B` | `ny-a6453` |
| 10 | New York | **S8828 (2025) — amends RAISE** | 2027-01-01 | `S8828` | `ny-s8828` |
| 11 | Texas | **HB 149 (2025) — TRAIGA** | 2027-01-01 | `HB 149` | `tx-hb149` |
| 12 | Utah | **SB 149 (2024) — AIPA** *and* **SB 226 (2025) — amendment** | 2024-05-01 / 2025-05-07 | `SB 149`, `SB 226` | `ut-sb226` (only the amendment is wired up) |

**Counting note**: the "About" sheet states **"12 regulatory frameworks and relevant guidance documents"**. The Methodology table lists 13 distinct rows (counting AB 2013 + SB 25B-004 + SB 149 + SB 226 separately). The "12" almost certainly groups Utah's SB 149 + SB 226 as one "Utah regulatory framework", consistent with the prose framing. Downstream HTML should reflect either 12 frameworks (with Utah collapsed) or label the Methodology table consistently — see §7 conflict #1.

---

## 3. Term inventory — the 43 terms

Derived from `New concepts` (the cluster → term juxtaposition matrix). The Excel groups terms into clusters; each cluster has one EU-AIA "anchor term" that pulls in all U.S.-state equivalents.

### 3.1 Cluster: Technical system attributes — Model / system

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **High-risk AI system** | – | High-risk AI system (SB 24-205) | – | – | High-risk AI interaction (SB 226) |
| **GPAI model** | Foundation model (SB 53) ; Frontier model (SB 53) | – | Foundation model (S8828) ; Frontier model (S8828) | – | – |
| **GPAI system** | Generative AI (SB 942) | – | – | – | Generative AI (SB 226) |

### 3.2 Cluster: Actors — Provider / Developer

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **Provider of limited-risk AI systems** | – | Developer (SB 24-205) | – | Developer (HB 149) | – |
| **Provider of high-risk AI systems** | – | Developer of high-risk AI systems (SB 24-205) | – | – | – |
| **Provider of GPAI models** | Developer (AB 2013) ; Covered provider (SB 942) | – | – | – | – |
| **Provider of GPAI models with systemic risk** | Frontier developer (SB 53) ; Large frontier developer (SB 53) | – | Frontier developer (S8828) ; Large frontier developer (S8828) ; Large developer (A6453B) | – | – |

### 3.3 Cluster: Actors — Deployer / Supplier

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **Deployer of limited-risk AI systems** | – | Deployer (SB 24-205) | – | Deployer (HB 149) | – |
| **Deployer of high-risk AI systems** | – | Deployer of high-risk AI systems (SB 24-205) | – | – | Supplier of high-risk generative AI systems (SB 226) |
| **Deployer of GPAI systems** | – | – | – | – | Supplier of generative AI systems (SB 226) |

### 3.4 Cluster: Measurement — Risk

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **Systemic risk** | Catastrophic risk (SB 53) | – | Catastrophic risk (S8828) | – | – |

### 3.5 Cluster: Measurement — Modification

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **Substantial modification** | Substantial modification (SB 53) (AB 2013) | Intentional and substantial modification (SB 24-205) | Substantial modification (S8828) | – | – |

### 3.6 Cluster: Trustworthy — Incident

| EU AIA anchor term | California | Colorado | New York | Texas | Utah |
|---|---|---|---|---|---|
| **Serious incident** | Critical safety incident (SB 53) | – | Critical safety incident (S8828) | – | – |

**Anchor-term tally** (unique EU-AIA terms): 11 anchors. **Surface-term tally** (every distinct EU + U.S. term row in the matrix above): ~30. The "43 terms" headline figure from the About sheet includes the legacy glossary (sheet 1) terms that aren't in the comparative matrix. Confirm this with the project lead before US-002 if exact term-count parity is required.

---

## 4. `Provider_Developer_Analysis` — the four stacked sub-tables and their per-text article references

Each sub-table starts with a single header row (col A = sub-table title) and ends before the next sub-table's title row.

### 4.1 Limited-risk Provider / Developer (rows 1–19)

| Attribute | EU AIA | Colorado SB 24-205 | Texas HB 149 |
|---|---|---|---|
| Term | Provider of limited-risk AI systems | Developer | Developer |
| Scope | Article 50 | §6-1-1701 | 552.001 |
| Regulatory trigger | Placing on the market | Upon making the AI system available | 552.103 (AG investigative demand) |
| Provider/dev info | – | – | §6-1-1702 |
| Transparency | Article 50 | §6-1-1704 | – |
| General info disclosure | – | – | 552.103 |
| Risk management | – | – | 552.103 |
| AI literacy | Article 4 | – | – |
| Rebuttal | – | §6-1-1706 (60-day cure + NIST/ISO rebuttal) | 552.104 (60-day cure) ; 552.105 (NIST safe harbor) |
| Penalties | Article 99 (€15M / 3%; €7M / 1%) | Up to $20K (Colorado Consumer Protection Act) | 552.105 ($10–12K curable / $80–200K incurable / $2K–40K/day ongoing) |

### 4.2 High-risk Provider / Developer (rows 21–43)

| Attribute | EU AIA | Colorado SB 24-205 |
|---|---|---|
| Term | Provider of high-risk AI systems | Developer of high-risk AI systems |
| Scope | Article 3, Article 6, Annex III | §6-1-1701 |
| Regulatory trigger | Domain-based | Outcome-based |
| Temporal trigger | Prior to placing on market | Upon making available |
| Registration | Article 49 | – |
| Provider/dev info | Article 16 | §6-1-1702 |
| Compliance check | Article 47 (conformity assessment) ; Article 16 (CE marking) | – |
| Transparency | Article 50 ; Article 13 | §6-1-1704 |
| General info disclosure | Article 11, Annex IV | §6-1-1702 |
| Specific info disclosure | Article 11, Annex IV | §6-1-1702 |
| Risk management | Article 16, Article 72, Article 19 | §6-1-1702 |
| Documentation keeping | Article 18 (10 years) | – |
| Communication to deployers | Article 25 | §6-1-1702 |
| Incident / risk reporting | Article 73 (2–15 days) | §6-1-1702 (90 days to AG) |
| AI literacy | Article 4 | – |
| Rebuttal | Article 6 | §6-1-1706 |
| Penalties | Article 99 | Colorado Consumer Protection Act |

### 4.3 GPAI-model Providers / Covered provider / Developer (rows 45–66)

| Attribute | EU AIA | California SB 942 | California AB 2013 |
|---|---|---|---|
| Term | Provider of GPAI models | Covered provider | Developer |
| Scope | Article 3 ; GL (17) ; GL (59), (60) | 22757.1 | 3110 |
| Regulatory trigger | Generality | Synthetic content + monthly visitors | Synthetic content |
| Temporal trigger | Prior to placing on market | Upon deploying | Before/concurrently with deployment |
| Transparency | Article 50 (GPAI systems only) ; CoP SSC 10.2 (signatories) | 22757.3 (latent + manifest) | – |
| General info disclosure | Annex XI | – | – |
| Specific info disclosure | Article 53 ; CoP TC 1.1 | – | 3111 |
| Copyright | Article 53 ; CoP CC 1.1 | – | – |
| Exemptions | Article 53 (open-source, except GPAISR) | – | – |
| Penalties | Article 99 | 22757.4 ($5K/violation) | 22757.15 (up to $1M) |

### 4.4 GPAISR / Frontier developer / Large frontier developer / Large developer (rows 68–106)

| Attribute | EU AIA | California SB 53 (Frontier) | California SB 53 (Large frontier) | NY S8828 (Frontier) | NY S8828 (Large frontier) | NY A6453B (Large developer) |
|---|---|---|---|---|---|---|
| Term | Provider of GPAI models with systemic risk | Frontier developer | Large frontier developer | Frontier developer | Large frontier developer | Large developer |
| Scope | Article 51 ; GL (59), (61) | 22757.11 (>10²⁶ FLOPs) | 22757.11 (+ >$500M revenue) | §1420 (>10²⁶) | §1420 (+ >$500M) | §1420 (>10²⁶ + >$1M compute, or distillation >$5M) |
| Notification / Registration | Article 52 | – | – | – | §1428 (biennial disclosure) | – |
| General info disclosure | Article 53, Annex XI | 22757.12 | 22757.12 | §1421 | §1421 | – |
| Specific info disclosure | Article 53, Annexes XI/XII ; Article 55 ; CoP SSC 1, 10.1 | – | 22757.12 (Frontier AI Framework) | – | 22757.12 / §1421 | §1421 (Safety & Security Protocol) |
| Risk management | Articles 53, 55 ; CoP SSC 1.1 | – | 22757.12 | – | §1421 | §1421 |
| Risk management — review | CoP SSC 1.3 (annual) | – | 22757.12 (annual) | – | §1421 (annual) | §1421 (annual) |
| Risk management — reporting | – | – | 22757.12 (quarterly) | – | §1422 (quarterly) | – |
| Copyright | Article 53 ; CoP CC 1.1 | – | – | – | – | – |
| Incident reporting | Article 55 ; CoP SSC 9.3 (2–15 days) | 22757.13 (24 h–15 days) | 22757.13 | §1422 (24–72 h) | §1422 | §1421 (72 h) |
| Exemptions | CoP SSC Appendix 2 | – | – | Accredited colleges/universities | + Empire AI consortium (§1426) | Accredited colleges (§1420) |
| Rebuttal | Article 52 | – | – | – | – | – |
| Whistleblower | Article 87 ; CoP SSC 8.3 | – | 1107.1 | – | – | – |
| Penalties | Article 99 | – | 22757.15 ($1M/violation) | – | §1427 ($1M / $3M) | §1422 ($10M / $30M) |

---

## 5. `Deployer_Supplier_Analysis` — the three stacked sub-tables

### 5.1 Limited-risk Deployer / Deployer (rows 1–19)

| Attribute | EU AIA | Colorado SB 24-205 | Texas HB 149 |
|---|---|---|---|
| Term | Deployer of limited-risk AI systems | Deployer | Deployer |
| Scope | Article 3 | §6-1-1701 | 552.001 |
| Regulatory trigger | Before putting into service / using | At time of deployment | 552.103 (AG demand) ; 552.051 (gov agencies / healthcare on deploy) |
| Transparency | Article 50 | §6-1-1704 | 552.051 (gov + healthcare only) |
| General info disclosure | – | – | 552.103 |
| Risk management | – | – | 552.103 |
| AI literacy | Article 4 | – | – |
| Rebuttal | – | §6-1-1706 | 552.104 ; 552.105 |
| Penalties | Article 99 | Colorado Consumer Protection Act ($20K, $50K elderly) | 552.105 (same penalty bands as developer) |

### 5.2 High-risk Deployer / Supplier (rows 21–55)

| Attribute | EU AIA | Colorado SB 24-205 | Utah SB 226 |
|---|---|---|---|
| Term | Deployer of high-risk AI systems | Deployer of high-risk AI systems | Supplier of high-risk generative AI systems |
| Scope | Articles 3, 6, Annex III | §6-1-1701 | §13-75-101 |
| Regulatory trigger | Domain-based | Outcome-based | Domain + system-based |
| Temporal trigger | Before putting into service | Before/upon deploying | At start of interaction |
| Registration | Articles 26, 49 (public authorities) ; Article 26 (biometric ID 48 h) | – | – |
| General info disclosure | – | §6-1-1703 | – |
| Impact assessment | Article 27 (FRIA) ; Article 26 + GDPR (DPIA) | §6-1-1703 (broad IA) | – |
| Impact assessment — review | – | §6-1-1703 (annual / 90 days post-modification) | – |
| Notification | Article 27 | – | – |
| Transparency | Article 26 ; Article 50 | §6-1-1703 | §13-75-103 |
| Risk management | Article 26 | §6-1-1703 (Risk Management Policy & Program) | – |
| Specific info disclosure | Article 26 (logs 6 months ; worker reps) | – | – |
| Human oversight | Article 26 | – | – |
| Right to explanation | Article 86 | §6-1-1703 (+ correction + appeal + human review) | – |
| AI literacy | Article 4 | – | – |
| Cooperation w/ authorities | Article 26 | §6-1-1703 (90 days to AG) | – |
| Incident / risk reporting | Article 26 | §6-1-1703 (90 days) | – |
| Rebuttal | – | §6-1-1706 | – |
| Exemptions | – | §6-1-1703 (<50 FTE & no own training data) | – |
| Penalties | Article 99 | Colorado Consumer Protection Act | §13-75-105 ($2.5K/violation) |

### 5.3 GPAI Deployer / Supplier of generative AI (rows 57–68)

| Attribute | EU AIA | Utah SB 226 |
|---|---|---|
| Term | Deployer of GPAI systems | Supplier of generative AI systems |
| Scope | Article 3 | §13-75-101, §13-75-103 |
| Regulatory trigger | System-based | System-based |
| Temporal trigger | Before putting into service | At start of interaction |
| Transparency | Article 26 ; Article 50 | §13-75-103 (upon request only) |
| AI literacy | Article 4 | – |
| Penalties | Article 99 | §13-75-105 |

---

## 6. Single-topic analysis sheets

### 6.1 `_High-risk AI system_ANALYSIS`

| Attribute | EU AIA | Colorado SB 24-205 | Utah SB 226 |
|---|---|---|---|
| Term | High-risk AI system | High-risk artificial intelligence system | High-risk artificial intelligence interaction |
| Definition | Article 6, Annex III | §6-1-1701 | §13-75-101 |
| Regulatory trigger | Domain-based | Outcome-based | Context-based |
| Exemptions | Article 6 (4 carve-outs: narrow procedural; improves prior human activity; detects patterns; preparatory) | §6-1-1701 (narrow procedural; pattern detection; specific tech list) | – |

### 6.2 `GPAI system_Generative AI_ANALY`

| Attribute | EU AIA | California SB 942 + AB 2013 | Utah SB 226 |
|---|---|---|---|
| Term | General-purpose AI system | Generative AI system / Generative AI | Generative AI |
| Definition | Article 3 | SB 942 §22757.1 ; AB 2013 §3110 | §13-75-101 |
| Scope | Article 50 | SB 942 §22757.1 (covered providers ≥1M visitors) | §13-75-103 |

### 6.3 `GPAI_Frontier_Foundation_Analys`

| Attribute | EU AIA | California SB 53 | New York S8828 |
|---|---|---|---|
| Term | GPAI model / GPAI model with systemic risks | Foundation model / Frontier model | Foundation model / Frontier model |
| Definition | Articles 3, 51, 52 ; GL (17) ; Commission designation | §22757.11 (criteria + 10²⁶ FLOPs frontier) | §1420 |
| Compute threshold | GPAI: 10²³ FLOPs (GL (17), indicative) ; GPAISR: 10²⁵ FLOPs (Article 51) | Frontier: 10²⁶ FLOPs (§22757.11) | Frontier: 10²⁶ FLOPs (§1420) |
| Regulatory trigger | Capabilities | Compute | Compute |
| Exemption | R&D / prototyping | – | Accredited colleges/universities (§1426) |

### 6.4 `Risk_ANALYSIS`

| Attribute | EU AIA Systemic risk | CA SB 53 Catastrophic risk | NY S8828 Catastrophic risk |
|---|---|---|---|
| Definition | Article 3 | §22757.11 | §1420 |
| Scope | Article 3 (open-ended) ; CoP Appendix 1 | §22757.11 (closed list of 3) | §1420 (closed list of 3) |
| Approach | Qualitative | Quantitative | Quantitative |
| Harm thresholds | Article 3 | §22757.11 (>50 deaths / >$1B damages) | §1420 (same) |
| Exemptions | – | §22757.11 (publicly accessible info ; lawful gov ; combined-software) | §1420 (same) |

### 6.5 `Modification_ANALYSIS`

| Attribute | EU AIA | CA SB 53 | CA AB 2013 | NY S8828 | CO SB 24-205 |
|---|---|---|---|---|---|
| Term | Substantial modification | (no standalone term — developer-defined) | Substantial modification | (no standalone term — developer-defined) | Intentional and substantial modification |
| Definition | Article 3 ; GL 3.2 (GPAI) | §22757.12 (developer-defined) | §3110 | §1421 (developer-defined) | §6-1-1701 |
| Scope | Articles 43, 47 (high-risk) ; GPAI / GPAISR | §22757.11 (frontier ≥10²⁶) | §3111 (any public GenAI) | §1420 (frontier ≥10²⁶) | §6-1-1701(9) (high-risk consequential) |
| Continuous learning | Recital 128 (pre-determined excluded) | Delegated to developer | §3110 (retraining = sub-mod) | Delegated to developer | §6-1-1701 (pre-determined excluded) |
| Obligations triggered | Article 43 (re-CA) ; Annex IV ; Articles 49, 71, 13 ; Article 53 (GPAI) ; Articles 52, 53, 55 (GPAISR) | §22757.12 (publish report ; update Frontier Framework) | §3111 (update training-data docs) | §1421 (publish report ; update Framework) | §6-1-1703 (new IA in 90 days ; update public summary) |

### 6.6 `Incident_ANALYSIS`

| Attribute | EU AIA Serious incident | CA SB 53 Critical safety incident | NY S8828 Critical safety incident |
|---|---|---|---|
| Definition | Article 3 | §22757.11 | §1420 |
| Scope | High-risk AI systems + GPAISR | Frontier models | Frontier models |
| Reporting timeline | Article 73 (HRAIS: ≤15 d general / ≤2 d widespread / ≤10 d death) ; CoP SSC 9.3 (GPAISR: 2/5/10/15 d by type) | §22757.13 (24 h – 15 d) | §1422 (24 – 72 h) |
| Reporting mechanism | Article 73 (national MSAs) ; Article 55 (AI Office for GPAISR) | §22757.13 (Attorney General) | §1422 (Office of Information Technology Services) |

### 6.7 `Prohibited_Practices`

8 EU AI Act categories (Article 5(1)(a)–(h)) cross-tabulated against 5 U.S. states. Only EU + Colorado + Texas have entries; California, New York, Utah are all "–" everywhere.

| Practice | EU AIA | Colorado | Texas |
|---|---|---|---|
| Subliminal / manipulative techniques | Art. 5(1)(a) | – | – |
| Exploitation of vulnerabilities | Art. 5(1)(b) | – | – |
| Social scoring | Art. 5(1)(c) | – | §552.053 (govt entities only) |
| Predictive criminal profiling | Art. 5(1)(d) | – | – |
| Untargeted facial recognition / biometric capture | Art. 5(1)(e) | – | §552.054 (govt entities only) |
| Emotion recognition (workplace / education) | Art. 5(1)(f) | – | – |
| Biometric categorisation by sensitive attributes | Art. 5(1)(g) | – | – |
| Real-time remote biometric identification | Art. 5(1)(h) (with exceptions) | – | – |
| Incitement to self-harm / harm / criminal activity | – | – | §552.052 (all persons) |
| Unlawful discrimination | Art. 5(1)(b), (c), (g) | §6-1-1702, §6-1-1703 (duty of care, not prohibition) | §552.056 (all persons) |
| Infringement of constitutional rights | – | – | §552.055 (all persons) |
| Sexually explicit content / child exploitation | – | – | §552.057 (all persons) |

---

## 7. Conflicts & ambiguities flagged against v27 HTML

These are the items downstream stories must resolve before declaring v28 done. v27 = `iterations/digital_lexicon_v27.html` (3811 lines).

| # | Severity | Issue | Excel says | v27 HTML says | Resolution |
|---|---|---|---|---|---|
| 1 | **High** | Headline regulatory-text count | About sheet: **"43 terms across 12 regulatory frameworks"** | v27 wires 15 distinct `law-blob-*` ids (CoP split into 3 chapters) and adds two extra Commission Guidelines (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) that are **not** part of the Excel's 12-text scope. | Decide: do the two extra Commission Guidelines stay (they're useful supporting text) or do they get demoted from primary "regulatory frameworks" to "secondary references"? Excel scope = 12. |
| 2 | **High** | Missing law blobs | Methodology lists Colorado **SB 25B-004** and Utah **SB 149** as separate row-entries. | Neither has a `law-blob` in v27. Only `co-sb24205` and `ut-sb226` exist. | Add SB 25B-004 (CAIA enforcement-date amendment) and SB 149 (original AIPA, pre-amendment) as their own blobs, OR add an explanatory note that they are merged into their successor laws. |
| 3 | **Medium** | "Developer" vs "Deployer" disambiguation for limited-risk AI systems | Excel `Provider_Developer_Analysis` §4.1 maps the AIA's **"Provider of limited-risk AI systems"** to Colorado **"Developer"** (SB 24-205) and Texas **"Developer"** (HB 149). Excel `Deployer_Supplier_Analysis` §5.1 maps **"Deployer of limited-risk AI systems"** to Colorado **"Deployer"** and Texas **"Deployer"**. The U.S. terms are *symmetrically* both Developer/Deployer — not "Developer" doing double-duty. | v27 has separate term entries for "Provider of limited-risk AI systems" and "Deployer", but uses **"Developer"** without disambiguation between the two contexts. Risk that downstream UI shows the same "Developer" entry twice with different content. | Tag each Colorado/Texas "Developer" and "Deployer" entry with its parent EU-AIA anchor (limited-risk vs high-risk) so the v28 UI can disambiguate. |
| 4 | **Medium** | "Limited-risk" not a defined legal AIA category | Excel explicitly: *"the term 'limited-risk' is not defined as a legal category in the AIA, it is a classificatory label used by the European Commission of which operative scope lies in Article 50"* + Recital 132. | v27 presents "Provider of limited-risk AI systems" as if it were a defined AIA term. | Add an interpretative footnote (visible in the UI) explaining the limited-risk label and citing Article 50 + Recital 132 + the Commission webpage. |
| 5 | **Medium** | CoP three-chapter handling | Excel cites CoP CC, CoP TC, CoP SSC inline (e.g., `CoP SSC 1.1`, `CoP TC 1.1`, `CoP CC 1.1`) as if they are one instrument with three chapters. | v27 has 3 separate `law-blob`s (`eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety`). | Either group the three blobs under a single "Code of Practice" header in the UI, or keep them split but ensure article-reference parsers route `CoP SSC X` → safety blob, `CoP TC X` → transparency blob, `CoP CC X` → copyright blob automatically. |
| 6 | **Medium** | Frontier model / Foundation model term split | `New concepts` matrix lists **two distinct terms** under "GPAI model": "Foundation model (SB 53)" *and* "Frontier model (SB 53)". | v27 has "Foundation model" as a defined term but "Frontier model" appears 25× as text without a standalone term entry. | Add "Frontier model" as its own term entry mapped to GPAI model with systemic risk. |
| 7 | **Medium** | "Generative AI system" vs "Generative AI" | `GPAI system_Generative AI_ANALY` lists California's term as **"Generative artificial intelligence system / Generative artificial intelligence"** (both forms used in SB 942 §22757.1 and AB 2013 §3110). | v27 has only "Generative artificial intelligence". | Confirm whether to normalise to one label or surface both. |
| 8 | **Low** | Article-reference notation inconsistency | Excel uses inconsistent notation across cells: `(Article 50)`, `Article 50`, `(Art. 5(1)(a))`, `(art. 5(1)(a))` for AIA; `(§6-1-1701)`, `§6-1-1701`, `(§6-1-1701)` for Colorado; `(22757.12.)` with trailing period for California; `(§1420)` and `(§ 1420)` (with space) for New York. | v27 currently uses one canonical form per law. | When extracting article references for v28, normalise to a single canonical form per jurisdiction (e.g., always `Art. 50`, always `§ 6-1-1701`, always `§ 22757.12`). |
| 9 | **Low** | "43 terms" headline | Excel "About" says **43 terms**. The cluster matrix in `New concepts` plus the legacy 36-term glossary in `Second edition terminology` together comfortably exceed 43; the comparative matrix alone yields ~30 surface terms (11 EU anchors + ~19 U.S. equivalents). | v27 has its own term list of ~28 comparative terms. | Reconcile: the "43 terms" likely includes the 11 anchor terms + ~17 U.S. equivalents + ~15 "Second edition terminology" carry-overs that are still present in the lexicon. Confirm before US-002. |
| 10 | **Low** | Sheet 5 has a leading-space name | Sheet 5 is named `" High-risk AI system_ANALYSIS"` (leading space). | n/a | Build scripts must strip whitespace when looking up sheets by name. |
| 11 | **Low** | Empty Section 4.2 column for Texas | High-risk Provider sub-table has no Texas column (HB 149's developer-of-high-risk obligations live in §4.1, since HB 149 doesn't separately classify high-risk providers). | n/a | If v27's Texas-developer view shows duplicate content under both "Developer" and "Developer of high-risk AI systems", de-duplicate. |
| 12 | **Low** | Modification — California has two relevant texts but no standalone defined term for SB 53 | Excel `Modification_ANALYSIS` row 2 for SB 53: *"(Substantially modified version of a frontier model) — no standalone defined term"*. Same for NY S8828. | If v27 shows a SB 53 / S8828 entry under "Substantial modification" that looks like a definition, it's actually developer-defined criteria, not a statutory definition. | Surface this caveat in the UI (and don't quote a definition where Excel says there isn't one). |

---

## 8. How downstream stories should consume this inventory

1. **US-002 (rebuild data layer)**: extract the per-text article references from §4–§6 of this doc as the canonical mapping. For every term × regulatory-text cell, the Excel article reference IS the expected reference. If the v27 HTML quotes a different article number, the Excel wins — verify via the named sheet/sub-table before changing.
2. **Term-anchoring**: every U.S. term in §3 must store its EU-AIA anchor term in its data record (e.g., Colorado "Developer" → anchor "Provider of limited-risk AI systems"). This is the only way to disambiguate the four contexts where "Developer" and "Deployer" appear.
3. **CoP / Guidelines routing**: build a small reference map (`CoP CC` → copyright blob, `CoP TC` → transparency blob, `CoP SSC` → safety blob, `GL` → GPAI-scope blob) so inline citations in term cells route correctly when rendered.
4. **Sheet name handling**: always `sheet_name.strip()` before lookup — sheet 5 has a leading space.
5. **Conflict register (§7) is the gate**: do not start US-003 until §7 issues #1, #2, #3, #4 are explicitly accepted or rejected by the project lead.
