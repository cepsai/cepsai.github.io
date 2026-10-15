# AI coding harnesses: sources

Companion to `harnesses.json` (44 rows). Access date for every number: 2026-10-14 (first collected 2026-09-02, refreshed 2026-10-14).

GitHub star counts were fetched from the REST API (`https://api.github.com/repos/OWNER/REPO`, field `stargazers_count`), authenticated via `gh api`. Repo creation dates and first-release dates come from the same API (`/releases`, oldest page).

OpenRouter token volumes come from the `globalRankingMap` payload embedded in https://openrouter.ai/apps (the 'Apps' ranking, same data as the Apps tab on https://openrouter.ai/rankings). Windows: `month` = trailing 30 days, `week` = trailing 7 days. Ranks are the position in the 30-day list; rank numbers skip where OpenRouter hides private apps (on 2026-10-14 ranks 1, 4, 7, 16, 17, 20 etc. are hidden). Only the top 200 rows are exposed, so 'null' means the app was below the cut or does not report to OpenRouter.

Refresh method 2026-10-14: same payload, read from the server-rendered HTML of https://openrouter.ai/apps (curl, then parse `globalRankingMap` with its `day`, `week` and `month` arrays of 200 rows each). Apps were matched by OpenRouter `app_id`, not by title. The 2026-09-02 app ids came from the Wayback Machine copy of the page taken 2026-09-02 15:55 UTC (https://web.archive.org/web/20260902155529/https://openrouter.ai/apps), which reproduces every 2026-09-02 figure in this file exactly. The app with id 4137556 was titled 'Zazen (Freebuff fork)' then and 'Freebuff' now. Same origin and id, so it is the same app.

Note on OpenRouter: an app appears there only when traffic is routed through OpenRouter with an app header. Vendor-locked tools (Gemini CLI, Copilot CLI, Amp, Antigravity) never appear. Claude Code appears because users point ANTHROPIC_BASE_URL at OpenRouter.

## Per-harness data points

### Claude Code (Anthropic)
- type: terminal CLI (+ IDE extensions, web, desktop) | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-02 (confidence 0.95): https://www.scriptbyai.com/claude-code-timeline/ (research preview 2025-02-24 with Claude 3.7 Sonnet; GA 2025-05-22)
- GitHub stars 150,778 (repo created 2025-02-22): https://api.github.com/repos/anthropics/claude-code accessed 2026-10-14
- GitHub note: Repo hosts issues, changelog and plugins only; LICENSE.md says all rights reserved. Stars are for a non-source repo.
- OpenRouter 30d rank 3, 32,622,523,164,080 tokens (7d: 10,067,295,146,805): https://openrouter.ai/apps accessed 2026-10-14

### Codex CLI (OpenAI)
- type: terminal CLI (+ IDE extension, cloud agent) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-04 (confidence 0.95): https://api.github.com/repos/openai/codex (repo created 2025-04-13; first GitHub release 2025-04-30); launch announced 2025-04-16 with o3/o4-mini
- GitHub stars 129,188 (repo created 2025-04-13): https://api.github.com/repos/openai/codex accessed 2026-10-14
- OpenRouter 30d rank 9, 11,878,351,751,632 tokens (7d: 2,994,539,948,013): https://openrouter.ai/apps accessed 2026-10-14

### Gemini CLI (Google)
- type: terminal CLI | license: Apache-2.0 | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-06 (confidence 0.95): https://github.com/google-gemini/gemini-cli/releases (first release tag 'early-access' 2025-06-24)
- GitHub stars 107,351 (repo created 2025-04-17): https://api.github.com/repos/google-gemini/gemini-cli accessed 2026-10-14
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Qwen Code (Alibaba (Qwen team))
- type: terminal CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-07 (confidence 0.95): https://rits.shanghai.nyu.edu/ai/introducing-qwen-code-alibabas-open%E2%80%91source-cli-for-agentic-coding-with-qwen3%E2%80%91coder/ (released with Qwen3-Coder, July 2025; repo created 2025-06-26, first GitHub release 2025-08-01)
- GitHub stars 28,479 (repo created 2025-06-26): https://api.github.com/repos/QwenLM/qwen-code accessed 2026-10-14
- OpenRouter 30d rank 91, 131,487,079,854 tokens (7d: 26,071,236,895): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Fork of Google Gemini CLI

### OpenCode (Anomaly (formerly SST; Dax Raad, Adam Doty))
- type: terminal CLI (+ desktop, IDE extension) | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-05 (confidence 0.95, first GitHub release, per red-team round 1): https://bex.co/blog/2026/08/22/sst-maintenance-mode-opencode-650k-agent-pivot (public launch June 2025); first GitHub release 0.0.45 on 2025-05-14
- GitHub stars 213,428 (repo created 2025-04-30): https://api.github.com/repos/anomalyco/opencode accessed 2026-10-14
- GitHub note: Repo moved sst/opencode -> anomalyco/opencode (Anomaly rebrand, see https://x.com/thdxr/status/2007199285251842478). GitHub redirects the old URL.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)
- lineage: Not related to Kujtim Hoxha's opencode-ai/opencode (that codebase became Charm Crush); the SST team kept the OpenCode name.

### Aider (Paul Gauthier (Aider AI))
- type: terminal CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2023-05 (confidence 0.95): https://api.github.com/repos/Aider-AI/aider (repo created 2023-05-09; first release v0.5.0 2023-06-07)
- GitHub stars 49,547 (repo created 2023-05-09): https://api.github.com/repos/Aider-AI/aider accessed 2026-10-14
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)
- OpenRouter note: Not in the 30-day list of 200 apps. Appears in the 7-day list at rank 232 (app 'Aider', origin https://aider.chat/) on 2026-10-14.
- note: Oldest still-active harness in the set.

### Cline (Cline Bot Inc. (Saoud Rizwan))
- type: IDE extension (VS Code, JetBrains) + CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-07 (confidence 0.95): https://github.com/cline/cline/releases (first release v1.0.4 2024-07-28, then named Claude Dev)
- GitHub stars 70,306 (repo created 2024-07-06): https://api.github.com/repos/cline/cline accessed 2026-10-14
- OpenRouter 30d rank 6, 19,991,603,468,681 tokens (7d: 3,833,451,543,071): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Originally 'Claude Dev'; parent of Roo Code and, via Roo, Kilo Code.

### Roo Code (Roo Code Inc. (now Roomote))
- type: IDE extension (VS Code) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-11 (confidence 0.85): https://api.github.com/repos/RooCodeInc/Roo-Code (repo created 2024-10-31; 'Prepare for release' commit 2024-11-13; launched as Roo Cline)
- GitHub stars 24,278 (repo created 2024-10-31): https://api.github.com/repos/RooCodeInc/Roo-Code accessed 2026-10-14
- OpenRouter 30d rank 61, 225,076,670,495 tokens (7d: 46,417,317,109): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Fork of Cline (as Roo Cline). Parent of Kilo Code and Zoo Code.
- status: archived 2026-05-15
- note: Repo archived 2026-05-15; team pivoted to Roomote cloud agent (https://kilo.ai/compare/roo-code-shutdown-roomote). Still shows 225B tokens/30d (2026-10-14) on OpenRouter from installed base.

### Kilo Code (Kilo AI)
- type: IDE extension (VS Code, JetBrains) + CLI | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-03 (confidence 0.95): https://tessl.io/blog/inside-kilo-code-an-open-source-ai-coding-agent-with-plans-to-reshape-software-development (launched March 2025 as a Roo Code fork; repo created 2025-03-10)
- GitHub stars 27,601 (repo created 2025-03-10): https://api.github.com/repos/Kilo-Org/kilocode accessed 2026-10-14
- OpenRouter 30d rank 5, 23,249,839,024,511 tokens (7d: 5,579,072,227,472): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Fork of Roo Code (itself a fork of Cline).

### Zoo Code (Zoo Code community (ex-Roo contributors))
- type: IDE extension (VS Code) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-05 (confidence 0.95): https://github.com/Zoo-Code-Org/Zoo-Code/releases (v3.54.0 published 2026-05-16; repo created 2026-04-23)
- GitHub stars 1,995 (repo created 2026-04-23): https://api.github.com/repos/Zoo-Code-Org/Zoo-Code accessed 2026-10-14
- OpenRouter 30d rank 44, 489,969,657,771 tokens (7d: 103,355,621,182): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Community fork of Roo Code after its 2026-05 shutdown, with official handoff.

### goose (Block, donated to Agentic AI Foundation (Linux Foundation))
- type: terminal CLI + desktop app | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-01 (confidence 0.85): https://github.com/aaif-goose/goose/releases (pre-releases from 2024-09-10; public 'codename goose' launch and v1.0 January 2025)
- GitHub stars 55,279 (repo created 2024-08-23): https://api.github.com/repos/aaif-goose/goose accessed 2026-10-14
- GitHub note: Repo moved block/goose -> aaif-goose/goose in April 2026 (https://goose-docs.ai/blog/2026/04/07/goose-moves-to-aaif/).
- OpenRouter 30d rank 58, 290,769,084,748 tokens (7d: 60,613,535,631): https://openrouter.ai/apps accessed 2026-10-14

### OpenHands (OpenHands (formerly All Hands AI))
- type: cloud agent + CLI + web GUI | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-03 (confidence 0.95): https://api.github.com/repos/OpenHands/OpenHands (repo created 2024-03-13 as OpenDevin; first release 0.6.1 2024-06-04)
- GitHub stars 90,878 (repo created 2024-03-13): https://api.github.com/repos/OpenHands/OpenHands accessed 2026-10-14
- GitHub note: Repo moved All-Hands-AI/OpenHands -> OpenHands/OpenHands.
- OpenRouter 30d rank 15, 3,364,506,093,687 tokens (7d: 915,808,971,781): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Started as OpenDevin, an open re-implementation of Devin.

### Cursor (Anysphere)
- type: IDE fork (VS Code) + CLI + cloud agents | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2023-03 (confidence 0.9): https://en.wikipedia.org/wiki/Cursor_(code_editor) ; repo cursor/cursor created 2023-03-12 (issues-only)
- GitHub stars 33,274 (repo created 2023-03-12): https://api.github.com/repos/cursor/cursor accessed 2026-10-14
- GitHub note: Issues-only repo, no source.
- OpenRouter 30d rank 28, 1,098,549,432,945 tokens (7d: 222,790,990,200): https://openrouter.ai/apps accessed 2026-10-14

### Devin Desktop (formerly Windsurf) (Cognition (acquired Windsurf from Codeium, July 2025))
- type: IDE fork (VS Code) | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-11 (confidence 0.9): Windsurf Editor launched 2024-11-13 (Codeium); rebranded Devin Desktop 2026-06-02 https://devin.ai/blog/windsurf-is-now-devin-desktop
- GitHub: none. No public source repo.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Devin (Cognition)
- type: cloud agent | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-03 (confidence 0.95): https://siliconangle.com/2024/03/12/cognition-launches-devin-generative-ai-powered-coding-engineer/ (announced 2024-03-12; GA Dec 2024)
- GitHub: none. No public source repo.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Continue (Continue Dev Inc.)
- type: IDE extension (VS Code, JetBrains) + CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2023-07 (confidence 0.85): https://api.github.com/repos/continuedev/continue (repo created 2023-05-24; public launch July 2023)
- GitHub stars 36,222 (repo created 2023-05-24): https://api.github.com/repos/continuedev/continue accessed 2026-10-14
- OpenRouter 30d rank 179, 56,286,433,597 tokens (7d: 10,889,810,943): https://openrouter.ai/apps accessed 2026-10-14

### Zed (Agent Panel) (Zed Industries)
- type: native editor with built-in agent (+ ACP host) | license: GPL-3.0 (editor), AGPL-3.0 (server), Apache-2.0 (GPUI) | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-05 (confidence 0.95): https://zed.dev/blog/fastest-ai-code-editor (Agentic Editing launched 2025-05-07; editor itself open-sourced Jan 2024)
- GitHub stars 91,705 (repo created 2021-02-20): https://api.github.com/repos/zed-industries/zed accessed 2026-10-14
- GitHub note: Stars are for the whole editor, not only the agent.
- OpenRouter 30d rank 33, 926,196,754,667 tokens (7d: 209,487,352,673): https://openrouter.ai/apps accessed 2026-10-14

### Amp (Amp (spun out of Sourcegraph))
- type: terminal CLI + IDE extension | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-05 (confidence 0.95): https://tessl.io/blog/sourcegraph-spins-out-ai-coding-agent-amp-as-a-standalone-company (research preview May 2025; Amp Free 2025-10-21)
- GitHub: none. No public source repo (only ampcode/amp-examples-and-guides).
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Kiro (IDE + CLI) (Amazon Web Services)
- type: IDE fork (VS Code) + terminal CLI | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-07 (confidence 0.95): https://siliconangle.com/2025/11/17/aws-launches-kiro-general-availability-team-features-cli-support/ (preview 2025-07-15, GA 2025-11-17)
- GitHub stars 4,367 (repo created 2025-06-17): https://api.github.com/repos/kirodotdev/Kiro accessed 2026-10-14
- GitHub note: Issues-only repo, no source. Kiro CLI is the renamed Amazon Q Developer CLI (aws/amazon-q-developer-cli, Apache-2.0, 1,983 stars).
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)
- lineage: Kiro CLI = Amazon Q Developer CLI renamed 2025-11-17 (https://kiro.dev/docs/upgrade-guides/migrating-from-q/).

### Junie (JetBrains)
- type: IDE plugin (JetBrains IDEs) + terminal CLI | license: proprietary | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-01 (confidence 0.95): https://blog.jetbrains.com/junie/2025/01/meet-junie-your-coding-agent-by-jetbrains/ (early access Jan 2025; CLI beta 2026-03; GA 2026-06-17)
- GitHub stars 477 (repo created 2025-04-07): https://api.github.com/repos/JetBrains/junie accessed 2026-10-14
- GitHub note: Repo holds install scripts and registry only; LICENSE.md all rights reserved.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### GitHub Copilot CLI (GitHub (Microsoft))
- type: terminal CLI | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-09 (confidence 0.95): https://github.blog/changelog/2025-09-25-github-copilot-cli-is-now-in-public-preview/ (public preview 2025-09-25; GA 2026-02-25)
- GitHub stars 11,252 (repo created 2023-01-06): https://api.github.com/repos/github/copilot-cli accessed 2026-10-14
- GitHub note: Repo holds README, install.sh and release binaries; custom 'GitHub Copilot CLI License'. Repo created 2023-01 for an earlier gh-copilot tool.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Crush (Charm)
- type: terminal CLI | license: FSL-1.1-MIT (source-available, converts to MIT after 2 years) | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-07 (confidence 0.95): https://charm.land/blog/crush-comes-home/ (announced 2025-07-31; first release v0.1.6 2025-07-29)
- GitHub stars 28,632 (repo created 2025-05-21): https://api.github.com/repos/charmbracelet/crush accessed 2026-10-14
- OpenRouter 30d rank 85, 151,982,765,329 tokens (7d: 28,725,661,355): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Successor to Kujtim Hoxha's opencode-ai/opencode (MIT, archived, 13,806 stars) after Charm hired him; renamed to avoid clash with SST's OpenCode.

### Trae (ByteDance)
- type: IDE fork (VS Code) + SOLO agent | license: proprietary (IDE); MIT for trae-agent research CLI | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-01 (confidence 0.95): https://visualstudiomagazine.com/articles/2025/01/27/ai-powered-trae-ide-ships.aspx (launched 2025-01-20)
- GitHub stars 915 (repo created 2024-12-26): https://api.github.com/repos/Trae-AI/TRAE accessed 2026-10-14
- GitHub note: Trae-AI/TRAE is a README-only repo. Related open-source research CLI bytedance/trae-agent has 12,143 stars (MIT).
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Auggie (Augment Code) (Augment Code)
- type: terminal CLI + IDE extension | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-09 (confidence 0.95): https://ai.miraheze.org/wiki/Auggie (released 2025-09-01 to enterprise, then everyone)
- GitHub stars 285 (repo created 2025-09-08): https://api.github.com/repos/augmentcode/auggie accessed 2026-10-14
- GitHub note: Repo holds plugins and changelog; custom license.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Warp (Agentic Development Environment) (Warp)
- type: terminal / ADE with built-in agents | license: AGPL-3.0 (client), MIT (UI crates); cloud agent platform Oz proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-06 (confidence 0.8): Warp 2.0 'Agentic Development Environment' launched June 2025; client open-sourced 2026-04-28 https://www.helpnetsecurity.com/2026/04/30/warp-open-source-client/
- GitHub stars 65,456 (repo created 2021-07-08): https://api.github.com/repos/warpdotdev/warp accessed 2026-10-14
- GitHub note: Repo created 2021 as issues tracker; source landed 2026-04-28 and it gained ~60k stars in days.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Droid (Factory AI)
- type: terminal CLI (+ cloud droids) | license: proprietary | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-09 (confidence 0.95): https://siliconangle.com/2025/09/25/factory-unleashes-droids-software-agents-50m-fresh-funding/ (Droid CLI GA 2025-09-25)
- GitHub stars 53 (repo created 2026-07-29): https://api.github.com/repos/Factory-AI/factory accessed 2026-10-14
- GitHub note: Docs-only repo, 53 stars; not meaningful.
- OpenRouter 30d rank 172, 58,373,918,027 tokens (7d: not in 7d top-200): https://openrouter.ai/apps accessed 2026-10-14

### Mistral Vibe (Mistral AI)
- type: terminal CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-12 (confidence 0.95): https://mistral.ai/news/devstral-2-vibe-cli/ (2025-12-09, with Devstral 2)
- GitHub stars 5,117 (repo created 2025-12-08): https://api.github.com/repos/mistralai/mistral-vibe accessed 2026-10-14
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Kimi Code CLI (Moonshot AI)
- type: terminal CLI | license: MIT (kimi-code); Apache-2.0 (legacy kimi-cli) | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-10 (confidence 0.95): https://github.com/MoonshotAI/kimi-cli/releases (first release 0.33 on 2025-10-21 as Kimi CLI; renamed Kimi Code CLI Jan 2026; TypeScript rewrite repo kimi-code first release 2026-05-26)
- GitHub stars 7,868 (repo created 2026-05-22): https://api.github.com/repos/MoonshotAI/kimi-code accessed 2026-10-14
- GitHub note: Successor repo MoonshotAI/kimi-code 7,868 stars; legacy MoonshotAI/kimi-cli 11,423 stars, archived by 2026-10-14 (was not archived on 2026-09-03).
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### pi (Earendil (Mario Zechner / badlogic))
- type: terminal CLI + agent toolkit | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-08 (confidence 0.95): https://en.wikipedia.org/wiki/Pi_(AI_agent) (first released August 2025; repo created 2025-08-09)
- GitHub stars 115,102 (repo created 2025-08-09): https://api.github.com/repos/earendil-works/pi accessed 2026-10-14
- GitHub note: Repo moved badlogic/pi-mono -> earendil-works/pi after Zechner joined Earendil (April 2026).
- OpenRouter 30d rank 8, 12,337,753,716,607 tokens (7d: 2,833,422,885,888): https://openrouter.ai/apps accessed 2026-10-14
- note: Ships only 4 built-in tools; everything else is an extension.

### omp (Oh My Pi) (Can Bölük (can1357))
- type: terminal CLI | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-01 (confidence 0.95): https://github.com/can1357/oh-my-pi/releases (forked 2025-12-31; first release 2026-01-02)
- GitHub stars 35,408 (repo created 2025-12-31): https://api.github.com/repos/can1357/oh-my-pi accessed 2026-10-14
- OpenRouter 30d rank 10, 10,415,057,136,217 tokens (7d: 1,588,802,977,525): https://openrouter.ai/apps accessed 2026-10-14
- lineage: Fork of pi (badlogic/pi-mono).

### Hermes Agent (Nous Research)
- type: terminal CLI / general-purpose agent (coding is one use) | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-02 (confidence 0.95): https://app.dealroom.co/news/note/hermes-agent-hits-99k-github-stars-in-8-weeks-fastest-growing-open-source-agent-framework-of-2026 (launched 2026-02-25; repo created 2025-07-22)
- GitHub stars 253,680 (repo created 2025-07-22): https://api.github.com/repos/NousResearch/hermes-agent accessed 2026-10-14
- OpenRouter 30d rank 2, 52,598,392,583,225 tokens (7d: 12,085,414,388,356): https://openrouter.ai/apps accessed 2026-10-14
- note: Not a pure coding harness: persistent memory, skills, 40+ tools. Included because it is the #1 app on OpenRouter by tokens.

### OpenClaw (OpenClaw Foundation (Peter Steinberger))
- type: terminal / messaging personal agent (coding is one use) | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-11 (confidence 0.95): https://en.wikipedia.org/wiki/OpenClaw (Clawdbot Nov 2025 -> Moltbot 2026-01-27 -> OpenClaw 2026-01-30); first GitHub release v0.1.1 2025-11-25
- GitHub stars 391,963 (repo created 2025-11-24): https://api.github.com/repos/openclaw/openclaw accessed 2026-10-14
- OpenRouter 30d rank 12, 6,962,598,512,494 tokens (7d: 2,565,356,910,858): https://openrouter.ai/apps accessed 2026-10-14
- note: Most-starred repo on GitHub. Personal assistant, borderline for a coding-harness list.

### DeepSeek Harness (dsh) (DeepSeek)
- type: terminal CLI + web UI, plugin framework | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-08 (confidence 0.95): https://thenewstack.io/deepseek-harness-open-source-plugins/ (developer preview 2026-08-13)
- GitHub stars 249,511 (repo created 2026-08-13): https://api.github.com/repos/deepseek-ai/deepseek-harness accessed 2026-10-14
- OpenRouter 30d rank 13, 5,912,445,313,770 tokens (7d: 1,143,298,534,128): https://openrouter.ai/apps accessed 2026-10-14
- note: 209k stars in under 3 weeks; 250k by 2026-10-14.

### Grok Build (xAI)
- type: terminal CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-05 (confidence 0.85): https://devops.com/xai-enters-the-coding-agent-race-with-grok-build/ (beta 2026-05-14 for SuperGrok Heavy, wider 2026-05-25); source published 2026-07-15
- GitHub stars 27,369 (repo created 2026-07-14): https://api.github.com/repos/xai-org/grok-build accessed 2026-10-14
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)
- note: 1.3M lines of Rust across 77 crates.

### Antigravity (Google)
- type: IDE fork (VS Code) with agent manager | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-11 (confidence 0.95): https://techcrunch.com/2025/11/18/google-launches-gemini-3-with-new-coding-app-and-record-benchmark-scores/ (2025-11-18)
- GitHub: none. No public repo.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Freebuff (Codebuff) (Codebuff (YC F24, James Grugett))
- type: terminal CLI + SDK | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-10 (confidence 0.75): https://github.com/CodebuffAI/freebuff/releases (first GitHub release 2025-10-19; Codebuff CLI launched Oct 2024 on Product Hunt; Freebuff free tier March 2026 per https://freebuff.com/)
- GitHub stars 13,526 (repo created 2024-07-09): https://api.github.com/repos/CodebuffAI/freebuff accessed 2026-10-14
- GitHub note: Repo renamed CodebuffAI/codebuff -> CodebuffAI/freebuff.
- OpenRouter 30d rank 11, 8,945,502,936,474 tokens (7d: 2,967,209,180,530): https://openrouter.ai/apps accessed 2026-10-14. This is the Freebuff app, app id 4137556.
- OpenRouter note: Chart label is 'Freebuff (Codebuff)' since 2026-10-14 because the bubble is the Freebuff app. The Codebuff app (origin https://codebuff.com/, app id 1275184) is no longer among the 200 listed apps in the 30-day or 7-day window on 2026-10-14.
- note: Freebuff app (origin https://freebuff.com/, OpenRouter app id 4137556, listed as 'Zazen (Freebuff fork)' on 2026-09-02 and renamed 'Freebuff' by 2026-10-14): rank 11, 8,945,502,936,474 tokens/30d (7d: 2,967,209,180,530). Recorded here since it has no separate repo. On 2026-09-02 it was rank 7, 8,251,828,022,227 tokens/30d.

### Plandex (Plandex Inc. (Dane Schneider))
- type: terminal CLI | license: MIT | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2024-03 (confidence 0.95): https://github.com/plandex-ai/plandex/releases (first release cli/v0.7.0 2024-03-14)
- GitHub stars 15,717 (repo created 2023-10-24): https://api.github.com/repos/plandex-ai/plandex accessed 2026-10-14
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Forge (forgecode) (Tailcall)
- type: terminal CLI | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-01 (confidence 0.95): https://github.com/tailcallhq/forgecode/releases (first release v0.1.0 2025-01-30)
- GitHub stars 7,638 (repo created 2024-12-08): https://api.github.com/repos/tailcallhq/forgecode accessed 2026-10-14
- GitHub note: Repo moved antinomyhq/forge -> tailcallhq/forgecode.
- OpenRouter: null. not among OpenRouter's 200 listed apps (30d window) on access date (https://openrouter.ai/apps accessed 2026-10-14)

### Command Code (Command Code AI)
- type: terminal CLI | license: proprietary | model-agnostic: False (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-03 (confidence 0.85): https://commandcode.ai/launch (released 2026-03-21)
- GitHub stars 4,127 (repo created 2017-12-20): https://api.github.com/repos/CommandCodeAI/command-code accessed 2026-10-14
- GitHub note: README-only repo renamed from a 2017 project (created 2017-12-20), so the star count is inherited. Fetched for the first time in JSON on 2026-10-14; the chart used 3,865 from the 2026-09-02 red-team pass.
- OpenRouter 30d rank 14, 4,177,484,629,020 tokens (7d: not in 7d top-200): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: Rank 14 in the 30-day list, but absent from the 7-day and 1-day lists on 2026-10-14 (7-day cut is about 9.4B tokens). Its traffic stopped or collapsed in the last week.

### ZCode (Z.ai (Zhipu AI))
- type: desktop app (+ browser, terminal agent) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-07 (confidence 0.8): Kept from the viz row (red-team round 2, 2026-09-03). OpenRouter app created 2026-02-12, so the app id predates the public release.
- GitHub stars 7,817 (repo created 2026-09-20): https://api.github.com/repos/zai-org/ZCode accessed 2026-10-14
- GitHub note: Real source: 17,876 tree entries, 8,623 .ts/.tsx/.js files, desktop client, backend, shared UI and the agent CLI (apps/zcode-cli). History is 4 commits: 'Initial commit' and 'feat: open source' on 2026-09-20, then version drops v3.14.3 (2026-09-23) and v3.15.1 (2026-10-10). 2 contributors.
- OpenRouter 30d rank 19, 1,903,218,078,881 tokens (7d: 210,603,366,536): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: App 'ZCode', app id 2823243, origin https://zcode.z.ai/. 7-day rank 35.
- model policy: Built-in provider templates in config/provider/zcode-builtin.json cover Z.ai, BigModel, Moonshot, MiniMax, DeepSeek, Qwen, Xiaomi MiMo, OpenAI, Anthropic, xAI, OpenRouter and OpenCode Zen. GLM Coding Plan is the default.
- note: Code published 2026-09-20 as version snapshots (4 commits, no outside pull requests). The app itself shipped 2026-07.

### Strix (Strix (usestrix))
- type: security agent (pentest CLI) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-08 (confidence 0.95): https://pypi.org/project/strix-agent/ (first upload 0.1.1 on 2025-08-08); repo created 2025-08-05; first GitHub release v0.3.1 on 2025-11-01
- GitHub stars 68,527 (repo created 2025-08-05): https://api.github.com/repos/usestrix/strix accessed 2026-10-14
- OpenRouter 30d rank 21, 1,842,750,325,016 tokens (7d: 549,952,804,543): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: App 'Strix', app id 3003505, origin https://strix.ai/. 7-day rank 19.
- model policy: Bring your own LLM provider key. Any model the provider config accepts.
- note: Open-source AI penetration testing agent. Runs in a Docker sandbox with proxy, browser and terminal tools. Excluded from the Coding only view.

### CodeGPT (maker shown as CodeGPT)
- type: IDE extension (VS Code, JetBrains, Visual Studio) + CLI | license: proprietary | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2022-12 (confidence 0.9): https://marketplace.visualstudio.com/items?itemName=DanielSanMedium.dscodegpt (publishedDate 2022-12-25 via the Marketplace extensionquery API; 2,534,390 installs on 2026-10-14)
- GitHub stars 670 (repo created 2023-01-08): https://api.github.com/repos/JudiniLabs/code-gpt-docs accessed 2026-10-14
- GitHub note: Docusaurus docs site only (MIT, 6 JS files). It is the repo the Marketplace listing links as 'Source'. No extension source.
- OpenRouter 30d rank 25, 1,278,449,161,122 tokens (7d: 302,785,859,758): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: App 'CodeGPT', app id 4780809, origin https://codegpt.co/, app created 2026-08-21. 7-day rank 26.
- model policy: Claude, GPT, Gemini, Grok, or open models via Ollama and LM Studio. Bring your own keys or buy CodeGPT credits (https://codegpt.co/).
- note: Maker per https://www.promptquorum.com/power-local-llm/codegpt-review (Judini Inc., founded around December 2022 by Daniel Ávila, Alvaro Chávez and Gustavo Espíndola).
- 2026-10-15: maker label dropped to "CodeGPT" because the docs repo now redirects to diffbot/code-gpt-docs and the Judini link is unverified. Plotted on the no-repo row, since the 670 stars are for a docs repo.

### Proto Agent (ERP•AI (erp.ai, binaries signed by Deskera Holdings Ltd.))
- type: general-purpose agent (desktop app, business ops) | license: proprietary | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2026-08 (confidence 0.7): https://github.com/erphq/proto-releases/releases (oldest published release v0.2.60 on 2026-08-03; repo created 2026-04-19 as neo-releases, release drafts from 2026-05-29); OpenRouter app created 2026-08-16
- GitHub stars 1 (repo created 2026-04-19): https://api.github.com/repos/erphq/proto-releases accessed 2026-10-14
- GitHub note: Release binaries and README only. README: 'Proto is proprietary, closed-source software'.
- OpenRouter 30d rank 27, 1,269,226,119,480 tokens (7d: 464,430,646,891): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: App 'Proto Agent', app id 4725308, origin https://proto.erp.ai/. OpenRouter categories: personal-agent, general-chat, cli-agent, programming-app, native-app-builder. 7-day rank 22.
- model policy: README: works on Claude, Gemini, GLM, Llama, Ollama and more. First run asks for an OpenRouter or Fireworks key.
- lineage: Renamed from Neo. The first README (2026-04-19) called Neo 'a local-first AI coding assistant' with source in erphq/neo, which is now private or gone.
- note: https://proto.erp.ai/ pitches it as 'The AI agent for business teams' (reports, records, no-code ERP/CRM builds). Typed general-purpose, so it drops out of the Coding only view.

### Letta Code (Letta)
- type: terminal CLI (+ desktop, web) | license: Apache-2.0 | model-agnostic: True (assessment from vendor docs, see model_policy in JSON)
- first public release 2025-10 (confidence 0.95): https://registry.npmjs.org/@letta-ai/letta-code (package created 2025-10-24, v0.1.0); repo created 2025-10-25, first GitHub release v0.1.7 on 2025-10-25
- GitHub stars 3,605 (repo created 2025-10-25): https://api.github.com/repos/letta-ai/letta-code accessed 2026-10-14
- OpenRouter 30d rank 37, 788,062,491,651 tokens (7d: 295,036,765,653): https://openrouter.ai/apps accessed 2026-10-14
- OpenRouter note: App 'Letta', app id 2368812, origin https://letta.com/, main_url https://letta.com/agent (the repo homepage). App created 2025-08-10, before Letta Code, so it may also carry other Letta platform traffic. 7-day rank 27.
- model policy: Runs on Claude, GPT, Gemini or other models (https://docs.letta.com/letta-code).
- note: Memory-first coding agent. Local mode keeps agent state on the machine.

## Extra OpenRouter rows relevant to harnesses (30d, not given their own JSON row)

Values as of 2026-10-14. ZCode, Strix, CodeGPT and Letta (as Letta Code) got their own rows on 2026-10-14. The Freebuff app is the 'Freebuff (Codebuff)' bubble. App ids from the same payload: Freebuff 4137556, ZCode 2823243, Strix 3003505, CodeGPT 4780809, Proto Agent 4725308, Letta 2368812.

- Freebuff (listed as Zazen (Freebuff fork) on 2026-09-02): rank 11, 8,945,502,936,474 tokens, origin https://freebuff.com/
- Strix: rank 21, 1,842,750,325,016 tokens, origin https://strix.ai/
- Traycer: rank 130, 87,304,224,612 tokens, origin https://traycer.ai/
- mimocode: rank 72, 188,869,763,659 tokens, origin https://mimo.xiaomi.com/coder
- ZCode: rank 19, 1,903,218,078,881 tokens, origin https://zcode.z.ai/
- Codebuff: not among the 200 listed apps on 2026-10-14, origin https://codebuff.com/
- Poolside: not among the 200 listed apps on 2026-10-14, origin https://poolside.ai/
- Letta: rank 37, 788,062,491,651 tokens, origin https://letta.com/
- Agent Zero: rank 113, 100,908,189,670 tokens, origin https://agent-zero.ai/
- CodeGPT: rank 25, 1,278,449,161,122 tokens, origin https://codegpt.co/
- Proto Agent: rank 27, 1,269,226,119,480 tokens, origin https://proto.erp.ai/
- Roomote: rank 141, 75,805,400,085 tokens, origin https://roomote.dev/
- Hermes Web UI: not among the 200 listed apps on 2026-10-14, origin https://hermes-studio.ai/

## Rows with confidence under 0.90

- Roo Code: first release 2024-11 at 0.85. https://api.github.com/repos/RooCodeInc/Roo-Code (repo created 2024-10-31; 'Prepare for release' commit 2024-11-13; launched as Roo Cline)
- goose: first release 2025-01 at 0.85. https://github.com/aaif-goose/goose/releases (pre-releases from 2024-09-10; public 'codename goose' launch and v1.0 January 2025)
- Continue: first release 2023-07 at 0.85. https://api.github.com/repos/continuedev/continue (repo created 2023-05-24; public launch July 2023)
- Warp (Agentic Development Environment): first release 2025-06 at 0.8. Warp 2.0 'Agentic Development Environment' launched June 2025; client open-sourced 2026-04-28 https://www.helpnetsecurity.com/2026/04/30/warp-open-source-client/
- Grok Build: first release 2026-05 at 0.85. https://devops.com/xai-enters-the-coding-agent-race-with-grok-build/ (beta 2026-05-14 for SuperGrok Heavy, wider 2026-05-25); source published 2026-07-15
- Freebuff (Codebuff): first release 2024-10 at 0.75. https://github.com/CodebuffAI/freebuff/releases (first GitHub release 2025-10-19; Codebuff CLI launched Oct 2024 on Product Hunt; Freebuff free tier March 2026 per https://freebuff.com/)
- ZCode: first release 2026-07 at 0.8. Kept from the 2026-09-03 viz row. Code published 2026-09-20.
- Proto Agent: first release 2026-08 at 0.7. Oldest published GitHub release 2026-08-03. It existed as Neo from 2026-04, and earlier releases may have been removed.
- Command Code: first release 2026-03 at 0.85. https://commandcode.ai/launch (released 2026-03-21)
- Command Code: stars fetched on 2026-10-14. The repo is README-only and was renamed from a 2017 project, so the count is inherited.
- Warp: 'first public release' is ambiguous. The terminal dates to 2021, Agent Mode to 2024, the ADE branding to June 2025, open source to April 2026. JSON uses 2025-06.
- Freebuff (Codebuff): Codebuff CLI launch month (2024-10) is from memory of the Product Hunt launch and was not re-verified; repo created 2024-07-09.
- Model-agnostic flags for proprietary tools (Cursor, Kiro, Antigravity, Warp, Devin Desktop) reflect vendor docs as of the access date; BYO-key options change often.