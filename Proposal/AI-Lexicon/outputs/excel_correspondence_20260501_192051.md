# Excel ↔ HTML correspondence audit

_Generated: 2026-05-01T19:20:51_

## Summary

- Analysis records compared: **282** (matched: 250, skipped/no-html: 23, flagged: 105)

- Verbatim Excel rows checked: **259** (matched in HTML: 216, missing: 43)


## Findings by category


### ANALYSIS_DIFF (9)

| Excel sheet | Cell | Concept | Sub-concept | Dim | Juris | Excel value | HTML value |
|---|---|---|---|---|---|---|---|
|  High-risk AI system_ANALYSIS | B4 | model-system | high-risk-ai-system | Definition | eu | AI system placed on the market or put into service that 1) acts as a safety component of a product, or is a product itself, covered by specific Union harmonisation legislation (e.g., machinery, toys, medical devices), and 2) are listed in … | AI system placed on the market or put into service that 1) acts as a safety component of a product, or is a product itself, covered by specific Union harmonisation legislation (e.g., machinery, toys, lifts, equipment and protective systems… |
| GPAI_Frontier_Foundation_Analys | B3 | model-system | general-purpose-ai-model | Definition | eu | Functional (generality + task capability) \nUpon Commission designation\n(Articles 3, 51, 52; GL, (17)) | AIA Article 3(63): "'general-purpose AI model' means an AI model, including where such an AI model is trained with a large amount of data using self-supervision at scale, that displays significant generality and is capable of competently p… |
| GPAI_Frontier_Foundation_Analys | C3 | model-system | general-purpose-ai-model | Definition | ca | Criteria-based (trained on broad data, generality, adaptability) + compute threshold for frontier (§22757.11) | SB 53 §22757.11(f) Foundation model: "means an artificial intelligence model that is all of the following: (1) Trained on a broad data set. (2) Designed for generality of output. (3) Adaptable to a wide range of distinctive tasks."\n\n§227… |
| GPAI_Frontier_Foundation_Analys | D3 | model-system | general-purpose-ai-model | Definition | ny | Criteria-based (trained on broad data, generality, adaptability) + compute threshold for frontier (§1420) | S8828 §1420(6) Foundation model: "means an artificial intelligence model that is all of the following: (a) trained on a broad data set; (b) designed for generality of output; and (c) adaptable to a wide range of distinctive tasks."\n\n§142… |
| Modification_ANALYSIS | B3 | modification | substantial-modification | Definition | eu | A change to an AI system after placing on the market / service which (a) was not planned in the initial conformity assessment and (b) affects compliance with high-risk requirements or changes the intended purpose (Article 3)\nIn the case o… | A change to an AI system after placing on the market / service which (a) was not planned in the initial conformity assessment and (b) affects compliance with high-risk requirements or changes the intended purpose (Article 3)\nIn the case o… |
| Modification_ANALYSIS | B6 | modification | substantial-modification | Scope | eu | High-risk AI systems subject to conformity assessment (Articles 43, 47)\nGPAI models / GPAI models with systemic risks | High-risk AI systems subject to conformity assessment (Articles 43, 47)\nGPAI models / GPAI models with systemic risks |
| Provider_Developer_Analysis | C34 | provider-developer | provider-of-high-risk-ai-systems | Specific information disclosure | co | Make available to the deployer or other developer, documentation describing model evaluation and measures to mitigate risk of algorithmic discrimination, data governance measures and instructions for system use and monitoring (§6-1-1702)\n… | Make available to the deployer or other developer, documentation describing model evaluation and measures to mitigate risk of algorithmic discrimination, data governance measures and instructions for system use and monitoring (§6-1-1702) |
| Provider_Developer_Analysis | C35 | provider-developer | provider-of-high-risk-ai-systems | Risk management | co | Make publicly available statement summarising how risks of algorithmic discrimination are managed (§6-1-1702)\n- | Make publicly available statement summarising how risks of algorithmic discrimination are managed (§6-1-1702) |
| Provider_Developer_Analysis | C40 | provider-developer | provider-of-high-risk-ai-systems | Rebuttal | co | 60-day opportunity to cure violation and compliance with latest NIST AI Risk Management Framework and ISO/IEC 42001 standards rebuts violation  (§6-1-1706)\n- | 60-day opportunity to cure violation and compliance with latest NIST AI Risk Management Framework and ISO/IEC 42001 standards rebuts violation  (§6-1-1706) |

### HTML_MISSING_CELL (23)

| Excel sheet | Cell | Concept | Sub-concept | Dim | Juris | Excel value | HTML value |
|---|---|---|---|---|---|---|---|
| Modification_ANALYSIS | E2 | modification | substantial-modification | Term | ny | (Substantially modified version of a frontier model) – no standalone defined term | (no matching cell in HTML) |
| Modification_ANALYSIS | E3 | modification | substantial-modification | Definition | ny | Developer-defined: the frontier AI framework must include criteria triggering updates and disclosures (§1421) | (no matching cell in HTML) |
| Modification_ANALYSIS | E6 | modification | substantial-modification | Scope | ny | Frontier models (>10²⁶ FLOPs) (§1420) | (no matching cell in HTML) |
| Modification_ANALYSIS | E9 | modification | substantial-modification | Continuous learning | ny | Not addressed at statute level; delegated to developer's framework criteria | (no matching cell in HTML) |
| Modification_ANALYSIS | E10 | modification | substantial-modification | Obligations triggered | ny | Publish transparency report on developer's website; update frontier AI framework if material changes (§1421) | (no matching cell in HTML) |
| Provider_Developer_Analysis | B47 | provider-developer | provider-of-high-risk-ai-systems | Providers of GPAI models / Covered provider / Developer | eu | EU (AIA)  | (no matching cell in HTML) |
| Provider_Developer_Analysis | C47 | provider-developer | provider-of-high-risk-ai-systems | Providers of GPAI models / Covered provider / Developer | co | California (SB 942)  | (no matching cell in HTML) |
| Provider_Developer_Analysis | B60 | provider-developer | provider-of-high-risk-ai-systems | Copyright | eu | Put in place copyright compliance policy (Article 53; CoP CC 1.1)\nPut in place copyright compliance policy (Article 53; CoP CC 1.1) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C60 | provider-developer | provider-of-high-risk-ai-systems | Copyright | co | -\n- | (no matching cell in HTML) |
| Provider_Developer_Analysis | B61 | provider-developer | provider-of-high-risk-ai-systems | Exemptions | eu | Providers of open source models (Article 53)  [1]\nSignatories of the CoP, for safe reference models and similarly safe or safer models (CoP SSC Appendix 2) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C61 | provider-developer | provider-of-high-risk-ai-systems | Exemptions | co | -\n- | (no matching cell in HTML) |
| Provider_Developer_Analysis | B73 | provider-developer | provider-of-high-risk-ai-systems | Providers of GPAI models with systemic risks / Frontier developer / Large frontier developer / Large developer | eu | EU (AIA)  | (no matching cell in HTML) |
| Provider_Developer_Analysis | C73 | provider-developer | provider-of-high-risk-ai-systems | Providers of GPAI models with systemic risks / Frontier developer / Large frontier developer / Large developer | co | California (SB 53)  | (no matching cell in HTML) |
| Provider_Developer_Analysis | B85 | provider-developer | provider-of-high-risk-ai-systems | Notification / Registration | eu | Notify EC when compute threshold achieved or known to be achieved in the future (Article 52) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C85 | provider-developer | provider-of-high-risk-ai-systems | Notification / Registration | co | - | (no matching cell in HTML) |
| Provider_Developer_Analysis | B91 | provider-developer | provider-of-high-risk-ai-systems | Risk management - review | eu | Review Safety and Security Framework at least once per year (CoP SSC 1.3) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C91 | provider-developer | provider-of-high-risk-ai-systems | Risk management - review | co | - | (no matching cell in HTML) |
| Provider_Developer_Analysis | B92 | provider-developer | provider-of-high-risk-ai-systems | Risk management - reporting | eu | - | (no matching cell in HTML) |
| Provider_Developer_Analysis | C92 | provider-developer | provider-of-high-risk-ai-systems | Risk management - reporting | co | - | (no matching cell in HTML) |
| Provider_Developer_Analysis | B94 | provider-developer | provider-of-high-risk-ai-systems | Incident reporting | eu | Within 2 to 15 days, depending on severity (Article 55; CoP SSC 9.3) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C94 | provider-developer | provider-of-high-risk-ai-systems | Incident reporting | co | Within 24 hours to 15 days, depending on severity (22757.13.) | (no matching cell in HTML) |
| Provider_Developer_Analysis | B98 | provider-developer | provider-of-high-risk-ai-systems | Whistleblower protections | eu | Implement of clear reporting channels and whistleblower protections (Article 87)\nSignatories of the CoP commit to putting in place whistleblower protection policy (CoP SSC 8.3) | (no matching cell in HTML) |
| Provider_Developer_Analysis | C98 | provider-developer | provider-of-high-risk-ai-systems | Whistleblower protections | co | - | (no matching cell in HTML) |

### REFERENCE_DIFF (53)

| Excel sheet | Cell | Concept | Sub-concept | Dim | Juris | Excel value | HTML value |
|---|---|---|---|---|---|---|---|
|  High-risk AI system_ANALYSIS | B4 | model-system | high-risk-ai-system | Definition | eu | Article 6, Annex III | AIA Article 6(1), (2) |
|  High-risk AI system_ANALYSIS | C4 | model-system | high-risk-ai-system | Definition | co | §6-1-1701 | Colorado SB24-205, 6-1-1701. (9) |
|  High-risk AI system_ANALYSIS | D4 | model-system | high-risk-ai-system | Definition | ut | §13-75-101 | Utah SB226, 13-75-101 (5) |
|  High-risk AI system_ANALYSIS | C7 | model-system | high-risk-ai-system | Exemptions | co | §6-1-1701 | Colorado SB24-205, 6-1-1701. (9)(b) |
| GPAI_Frontier_Foundation_Analys | B6 | model-system | general-purpose-ai-model | Compute threshold | eu | Article 51 | (GL, (17)) |
| GPAI system_Generative AI_ANALY | C3 | model-system | general-purpose-ai-system | Definition | ca | SB 942 §22757.1; AB 2013 §3110 | CA SB 942 §22757.1(c); CA AB 2013 §3110(c) |
| GPAI system_Generative AI_ANALY | D3 | model-system | general-purpose-ai-system | Definition | ut | §13-75-101 | Utah SB226, 13-75-101 (4) |
| GPAI system_Generative AI_ANALY | B4 | model-system | general-purpose-ai-system | Scope | eu | Article 50 | AIA Recital (100) |
| GPAI system_Generative AI_ANALY | D4 | model-system | general-purpose-ai-system | Scope | ut | §13-75-103 | Utah SB226, 13-75-103 (1) |
| Risk_ANALYSIS | B5 | risk | systemic-risk | Scope | eu | Article 3 | AIA Article 51(1)-(2) |
| Modification_ANALYSIS | B6 | modification | substantial-modification | Scope | eu | Articles 43, 47 | AIA Recital (177); Article 3(23) |
| Incident_ANALYSIS | C5 | incident | serious-incident | Reporting timeline | ca | 22757.13. | CA SB 53 §22757.13 |
| Incident_ANALYSIS | D5 | incident | serious-incident | Reporting timeline | ny | § 1422 | NY S8828 §1422 |
| Incident_ANALYSIS | B8 | incident | serious-incident | Reporting mechanism | eu | Article 55 | AIA Article 73(1), (5) |
| Provider_Developer_Analysis | C4 | provider-developer | provider | Scope | co | §6-1-1701 | Colorado SB24-205, 6-1-1701 |
| Provider_Developer_Analysis | C6 | provider-developer | provider | Provider / developer information | co | §6-1-1702 | Colorado SB24-205, 6-1-1702 |
| Provider_Developer_Analysis | C7 | provider-developer | provider | Transparency | co | §6-1-1704 | Colorado SB24-205, 6-1-1704 |
| Provider_Developer_Analysis | C13 | provider-developer | provider | Rebuttal | co | §6-1-1706 | Colorado SB24-205, 6-1-1706 |
| Provider_Developer_Analysis | D13 | provider-developer | provider | Rebuttal | tx | 552.105. | TX HB 149 §552.104; TX HB 149 §552.105 |
| Provider_Developer_Analysis | D15 | provider-developer | provider | Penalties | tx | 552.105. | Texas HB149 552.105 (a) |
| Provider_Developer_Analysis | B24 | provider-developer | provider-of-high-risk-ai-systems | Scope | eu | Article 51 | EU AI Act, Article 3 (3); AI Act, Article 6; AI Act, Annex III; EU AI Act, Article 25 (1) |
| Provider_Developer_Analysis | C24 | provider-developer | provider-of-high-risk-ai-systems | Scope | co | 22757.11. | Colorado SB24-205, 6-1-1701; Colorado SB24-205, 6-1-1701; Colorado SB24-205, 6-1-1701 |
| Provider_Developer_Analysis | B30 | provider-developer | provider-of-high-risk-ai-systems | Transparency | eu | CoP SSC 10.2 | EU AI Act, Article 50 (1, 2); EU AI Act, Article 13 (1) |
| Provider_Developer_Analysis | C30 | provider-developer | provider-of-high-risk-ai-systems | Transparency | co | 22757.3. | Colorado SB24-205, 6-1-1704 |
| Provider_Developer_Analysis | C33 | provider-developer | provider-of-high-risk-ai-systems | General information disclosure | co | 22757.12. | CO SB 24-205 §6-1-1702 |
| Provider_Developer_Analysis | C35 | provider-developer | provider-of-high-risk-ai-systems | Risk management | co | §6-1-1702 | Colorado SB24-205, 6-1-1702 (4) |
| Provider_Developer_Analysis | B40 | provider-developer | provider-of-high-risk-ai-systems | Rebuttal | eu | Article 52 | EU AI Act, Article 6 (4) |
| Provider_Developer_Analysis | C40 | provider-developer | provider-of-high-risk-ai-systems | Rebuttal | co | §6-1-1706 | Colorado SB24-205, 6-1-1706 |
| Provider_Developer_Analysis | C41 | provider-developer | provider-of-high-risk-ai-systems | Penalties | co | 22757.4. | Colorado Consumer Protection Act |
| Deployer_Supplier_Analysis | C4 | deployer-supplier | deployer | Scope | co | §6-1-1701 | Colorado SB24-205, 6-1-1701. (6) |
| Deployer_Supplier_Analysis | D5 | deployer-supplier | deployer | Regulatory trigger | tx | 552.051. | TX HB 149 §552.103; TX HB 149 §552.051 |
| Deployer_Supplier_Analysis | C8 | deployer-supplier | deployer | Transparency | co | §6-1-1704 | Colorado SB24-205, 6-1-1704. (1) |
| Deployer_Supplier_Analysis | D8 | deployer-supplier | deployer | Transparency | tx | 552.051. | TX HB 149 §552.051 |
| Deployer_Supplier_Analysis | D10 | deployer-supplier | deployer | General information disclosure | tx | 552.103. | TX HB 149 §552.103 |
| Deployer_Supplier_Analysis | D11 | deployer-supplier | deployer | Risk management | tx | 552.103. | TX HB 149 §552.103 |
| Deployer_Supplier_Analysis | C13 | deployer-supplier | deployer | Rebuttal | co | §6-1-1706 | Colorado SB24-205, 6-1-1706 (3) |
| Deployer_Supplier_Analysis | D13 | deployer-supplier | deployer | Rebuttal | tx | 552.105. | TX HB 149 §552.104; TX HB 149 §552.105 |
| Deployer_Supplier_Analysis | D15 | deployer-supplier | deployer | Penalties | tx | 552.105. | Texas HB149 552.105 (a) |
| Deployer_Supplier_Analysis | B23 | deployer-supplier | deployer-of-high-risk-ai-systems | Scope | eu | Articles 3, 6, Annex III | AI Act, Article 6; AI Act, Annex III; EU AI Act, Article 3 (4); EU AI Act, Article 25 (1) |
| Deployer_Supplier_Analysis | C23 | deployer-supplier | deployer-of-high-risk-ai-systems | Scope | co | §6-1-1701 | Colorado SB24-205, 6-1-1701. (9); Colorado SB24-205, 6-1-1701. (3); Colorado SB24-205, 6-1-1701. (6) |
| Deployer_Supplier_Analysis | D23 | deployer-supplier | deployer-of-high-risk-ai-systems | Scope | ut | §13-75-101 | Utah SB226, 13-75-101 (5); Utah SB226, 13-75-101 (8); Utah Code |
| Deployer_Supplier_Analysis | B30 | deployer-supplier | deployer-of-high-risk-ai-systems | Impact assessment | eu | Article 26, GDPR | EU AI Act, Article 27 |
| Deployer_Supplier_Analysis | C30 | deployer-supplier | deployer-of-high-risk-ai-systems | Impact assessment | co | §6-1-1703 | Colorado SB24-205, 6-1-1703. |
| Deployer_Supplier_Analysis | C35 | deployer-supplier | deployer-of-high-risk-ai-systems | Transparency | co | §6-1-1703 | Colorado SB24-205, 6-1-1703. |
| Deployer_Supplier_Analysis | D35 | deployer-supplier | deployer-of-high-risk-ai-systems | Transparency | ut | §13-75-103 | Utah SB226, 13-75-103 (2) |
| Deployer_Supplier_Analysis | C38 | deployer-supplier | deployer-of-high-risk-ai-systems | Risk management | co | §6-1-1703 | Colorado SB24-205, 6-1-1703. |
| Deployer_Supplier_Analysis | C41 | deployer-supplier | deployer-of-high-risk-ai-systems | Right to explanation | co | §6-1-1703 | Colorado SB24-205, 6-1-1703. |
| Deployer_Supplier_Analysis | C45 | deployer-supplier | deployer-of-high-risk-ai-systems | Rebuttal | co | §6-1-1706 | Colorado SB24-205, 6-1-1706 (3) |
| Deployer_Supplier_Analysis | C46 | deployer-supplier | deployer-of-high-risk-ai-systems | Exemptions | co | §6-1-1703 | Colorado SB24-205, 6-1-1703. |
| Deployer_Supplier_Analysis | D47 | deployer-supplier | deployer-of-high-risk-ai-systems | Penalties | ut | §13-75-105 | Utah SB226, 13-75-105 (4) |
| Deployer_Supplier_Analysis | C55 | deployer-supplier | deployer-of-general-purpose-ai-systems | Scope | ut | §13-75-101, §13-75-103; Utah Code | Utah Code; Utah SB226, 13-75-101. (4) |
| Deployer_Supplier_Analysis | C58 | deployer-supplier | deployer-of-general-purpose-ai-systems | Transparency | ut | §13-75-103 | Utah SB226, 13-75-103 (1) |
| Deployer_Supplier_Analysis | C62 | deployer-supplier | deployer-of-general-purpose-ai-systems | Penalties | ut | §13-75-105 | Utah SB226, 13-75-105 (4) |

### REFERENCE_MISSING (20)

| Excel sheet | Cell | Concept | Sub-concept | Dim | Juris | Excel value | HTML value |
|---|---|---|---|---|---|---|---|
| Risk_ANALYSIS | B7 | risk | systemic-risk | Harm thresholds | eu | Article 3 | (empty) |
| Modification_ANALYSIS | B10 | modification | substantial-modification | Obligations triggered | eu | Articles 53, 55 | (empty) |
| Incident_ANALYSIS | B5 | incident | serious-incident | Reporting timeline | eu | CoP SSC 9.3 | (empty) |
| Provider_Developer_Analysis | D6 | provider-developer | provider | Provider / developer information | tx | §6-1-1702. | (empty) |
| Provider_Developer_Analysis | B26 | provider-developer | provider-of-high-risk-ai-systems | Temporal trigger | eu | Article 55; CoP SSC 1.2 | (empty) |
| Provider_Developer_Analysis | B28 | provider-developer | provider-of-high-risk-ai-systems | Provider / developer information | eu | Article 16 | (empty) |
| Provider_Developer_Analysis | B29 | provider-developer | provider-of-high-risk-ai-systems | Compliance check | eu | Article 16 | (empty) |
| Provider_Developer_Analysis | B33 | provider-developer | provider-of-high-risk-ai-systems | General information disclosure | eu | Article 53, Annex XI | (empty) |
| Provider_Developer_Analysis | B34 | provider-developer | provider-of-high-risk-ai-systems | Specific information disclosure | eu | Article 55; CoP SSC 1, 10.1 | (empty) |
| Provider_Developer_Analysis | B35 | provider-developer | provider-of-high-risk-ai-systems | Risk management | eu | Articles 53, 55; CoP SSC 1.1 | (empty) |
| Provider_Developer_Analysis | B36 | provider-developer | provider-of-high-risk-ai-systems | Documentation keeping | eu | Article 18 | (empty) |
| Provider_Developer_Analysis | B37 | provider-developer | provider-of-high-risk-ai-systems | Communication to deployers | eu | Article 25 | (empty) |
| Provider_Developer_Analysis | B38 | provider-developer | provider-of-high-risk-ai-systems | Incident / risk reporting | eu | Article 73 | (empty) |
| Provider_Developer_Analysis | B39 | provider-developer | provider-of-high-risk-ai-systems | AI literacy | eu | Article 4 | (empty) |
| Deployer_Supplier_Analysis | B8 | deployer-supplier | deployer | Transparency | eu | Article 50 | (empty) |
| Deployer_Supplier_Analysis | B26 | deployer-supplier | deployer-of-high-risk-ai-systems | Registration | eu | Article 26 | (empty) |
| Deployer_Supplier_Analysis | B38 | deployer-supplier | deployer-of-high-risk-ai-systems | Risk management | eu | Article 26 | (empty) |
| Deployer_Supplier_Analysis | B39 | deployer-supplier | deployer-of-high-risk-ai-systems | Specific information disclosure | eu | Article 26 | (empty) |
| Deployer_Supplier_Analysis | B43 | deployer-supplier | deployer-of-high-risk-ai-systems | Cooperation with authorities | eu | Article 26 | (empty) |
| Deployer_Supplier_Analysis | B44 | deployer-supplier | deployer-of-high-risk-ai-systems | Incident / risk reporting | eu | Article 26 | (empty) |

### VERBATIM_MISSING_IN_HTML (43)

| Excel sheet | Cell | Concept | Sub-concept | Dim | Juris | Excel value | HTML value |
|---|---|---|---|---|---|---|---|
| Provider_Developer | C5 |  |  |  |  | 4. Providers and deployers of AI systems shall take measures to ensure, to their best extent, a sufficient level of AI literacy of their staff and other persons dealing with the operation and use of AI systems on their behalf, taking into … | (not found in any HTML verbatim cell) |
| Provider_Developer | C6 |  |  |  |  | Additional obligations apply to specific categories of providers, namely to providers of high-risk AI systems and providers of general-purpose AI models. | (not found in any HTML verbatim cell) |
| Provider_Developer | E6 |  |  |  |  | provider of GPAI models; provider of GPAI model with systemic risk; provider of high-risk AI system; general-purpose AI model; high-risk AI system | (not found in any HTML verbatim cell) |
| Provider_Developer | A60 |  |  |  |  | Provider of general-purpose AI models with systemic risk | (not found in any HTML verbatim cell) |
| Provider_Developer | C62 |  |  |  |  | the Commission considers a downstream modifier to become the provider of the modified general-purpose AI model only if the modification leads to a significant change in the model’s generality, capabilities, or systemic risk. | (not found in any HTML verbatim cell) |
| Deployer_Supplier | M34 |  |  |  |  | (1) A person is not subject to an enforcement action for violating Section §13-75-103 if the person's generative artificial intelligence clearly and conspicuously discloses:\n(a) at the outset of any interaction with an individual in conne… | (not found in any HTML verbatim cell) |
| Deployer_Supplier | H42 |  |  |  |  | (1) A person is not subject to an enforcement action for violating Section §13-75-103 if the person's generative artificial intelligence clearly and conspicuously discloses:\n(a) at the outset of any interaction with an individual in conne… | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | E3 |  |  |  |  | Provider of GPAI models; Deployer of GPAI systems | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | H4 |  |  |  |  | §22757.11(f): "Foundation model" means an artificial intelligence model that is all of the following: (1) Trained on a broad data set. (2) Designed for generality of output. (3) Adaptable to a wide range of distinctive tasks.\n\n§22757.11(… | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | I4 |  |  |  |  | CA SB 53 §22757.11(f), (h), (i), (j); §22757.14(a) | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | C5 |  |  |  |  | If a general-purpose AI model meets the criterion from paragraph 17 but, exceptionally, does not display significant generality or is not capable of competently performing a wide range of distinct tasks, it is not a general-purpose AI mode… | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | E9 |  |  |  |  | Providers of GPAI models with systemic risks | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | E10 |  |  |  |  | Providers of GPAI models with systemic risks | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | E11 |  |  |  |  | Providers of GPAI models with systemic risks | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | I11 |  |  |  |  | CA SB 53 §22757.11(h), (i), (j); §22757.12; §22757.13 | (not found in any HTML verbatim cell) |
| GPAI_Frontier_Foundation model | N11 |  |  |  |  | NY S8828 §1420(8), (9), (10); §1425; §1426 | (not found in any HTML verbatim cell) |
| GPAI system_Generative AI | I5 |  |  |  |  | CA SB 942 §22757.1(b); CA AB 2013, Civil Code §3110(b) | (not found in any HTML verbatim cell) |
| GPAI system_Generative AI | H6 |  |  |  |  | A covered provider shall make available an AI detection tool at no cost to the user that meets all of the following criteria: (1) The tool allows a user to assess whether image, video, or audio content, or content that is any combination t… | (not found in any HTML verbatim cell) |
| GPAI system_Generative AI | H7 |  |  |  |  | "Provenance data" means data that is embedded into digital content, or that is included in the digital content's metadata, for the purpose of verifying the digital content's authenticity, origin, or history of modification. | (not found in any HTML verbatim cell) |
| GPAI system_Generative AI | M8 |  |  |  |  | It is not a defense to the violation of any statute administered and enforced by the division under Section 13-2-1 that generative artificial intelligence:\n(1) made the violative statement;\n(2) undertook the violative act; or\n(3) was us… | (not found in any HTML verbatim cell) |
| Incident | E4 |  |  |  |  | Provider of high-risk AI systems, Provider of GPAI models with systemic risk, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Incident | E5 |  |  |  |  | Provider of high-risk AI systems, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Incident | H5 |  |  |  |  | Subject to paragraph (2), a frontier developer shall report any critical safety incident pertaining to one or more of its frontier models to the Office of Emergency Services within 15 days of discovering the critical safety incident.\n\nA … | (not found in any HTML verbatim cell) |
| Incident | E6 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Incident | E7 |  |  |  |  | Provider of high-risk AI systems, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Incident | H7 |  |  |  |  | The Office of Emergency Services shall establish a mechanism to be used by a frontier developer or a member of the public to report a critical safety incident that includes all of the following: (1) The date of the critical safety incident… | (not found in any HTML verbatim cell) |
| Incident | M7 |  |  |  |  | The Office shall establish a mechanism to be used by a frontier developer or a member of the public to report a critical safety incident that includes all of the following: (A) The date of the critical safety incident; (B) The reasons the … | (not found in any HTML verbatim cell) |
| Incident | E8 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Incident | C9 |  |  |  |  | The report shall be made immediately after the provider has established a causal link between the AI system and the serious incident or the reasonable likelihood of such a link, and, in any event, not later than 15 days after the provider … | (not found in any HTML verbatim cell) |
| Incident | E9 |  |  |  |  | Provider of high-risk AI systems, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Incident | H9 |  |  |  |  | Subject to paragraph (2), a frontier developer shall report any critical safety incident pertaining to one or more of its frontier models to the Office of Emergency Services within 15 days of discovering the critical safety incident.\n\nIf… | (not found in any HTML verbatim cell) |
| Incident | E10 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Incident | C11 |  |  |  |  | Following the reporting of a serious incident pursuant to paragraph 1, the provider shall, without delay, perform the necessary investigations in relation to the serious incident and the AI system concerned. This shall include a risk asses… | (not found in any HTML verbatim cell) |
| Incident | E11 |  |  |  |  | Provider of high-risk AI systems, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Incident | E12 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Incident | E13 |  |  |  |  | Provider of high-risk AI systems, Provider of GPAI models with systemic risk, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
|  High-risk AI system | E3 |  |  |  |  | Provider of high-risk AI systems; deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
|  High-risk AI system | E4 |  |  |  |  | Provider of high-risk AI systems; deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Risk | D4 |  |  |  |  | Provider of high-risk AI systems, Provider of GPAI models with systemic risk, Deployer of high-risk AI systems | (not found in any HTML verbatim cell) |
| Risk | D5 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Risk | D6 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Risk | D7 |  |  |  |  | Provider of GPAI models with systemic risk | (not found in any HTML verbatim cell) |
| Substantial modification | C5 |  |  |  |  | "However, changes occurring to the algorithm and the performance of AI systems which continue to 'learn' after being placed on the market or put into service, namely automatically adapting how functions are carried out, should not constitu… | (not found in any HTML verbatim cell) |