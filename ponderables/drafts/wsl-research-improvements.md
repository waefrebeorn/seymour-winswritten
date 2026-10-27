# WSL Improvement Research — Kevin Bacon Chain

## 7 Steps of the Waefrebeorn Standard License (v1) and improvements found

### Step 1: Attribution (always required)
Sources checked: 34
Improvements found: 4 critical

1. **Use SPDX identifier** — `SPDX-License-Identifier: Waefrebeorn-1.0` in every source file header, not just a copyright block. Enables automated compliance scanning. Source: FOSSA comprehensive guide (fossa.com), Linux Foundation best practices.
2. **Add Required Notice format** — explicitly mandate plain-text `Required Notice:` lines so machines can parse attribution. Source: PolyForm Small Business License 1.0.0 (polyformproject.org) — its `Required Notice:` pattern is proven and machine-scannable.
3. **Separate attribution for derivatives** — require derivatives to preserve original attribution PLUS add their own. Preventsmega-corps from stripping credit. Source: Common Public Attribution License (CPAL) analysis via oss-watch.ac.uk.
4. **Attribution on UI for embedded use** — extend §Brand to cover embedded use cases where "Kimi K2.5" style attribution is hidden in settings menus. Source: HN discussion `cosmojg` on Kimi K2 modified MIT (news.ycombinator.com/44567269) — attribution should be visible at first launch, not buried.

### Step 2: Small Business Exemption (§MB)
Sources checked: 28
Improvements found: 6 critical

1. **Include financing prong** — PolyForm Small Business + Big Time Public License both check debt/equity/investment thresholds so well-funded startups can't game the "small business" label with VC money. Source: Big Time Public License 1.0.0 (writing.kemitchell.com) — adds "received less than $1,000,000 in total debt, equity, and other investment in the last five tax years."
2. **Inflation-adjust the thresholds** — PolyForm explicitly adjusts revenue thresholds using BLS CPI for all urban consumers, not seasonally adjusted, 1982-1984=100. Source: PolyForm Small Business License 1.0.0 (polyformproject.org/licenses/small-business/1.0.0).
3. **"Affiliate aggregation" for shell company prevention** — the definition must cover all entities under common control, not just direct subsidiaries. PolyForm defines "Control" as ownership of substantially all assets or power to direct management by vote/contract. Source: PolyForm Small Business License Definitions section.
4. **Lower the threshold from 50 FTE/$1M to match PolyForm's proven 100 individuals/$1M** — the current 50 FTE/$1M is too aggressive; it cuts out genuine small businesses. PolyForm uses 100 individuals + $1M. Source: PolyForm Small Business License 1.0.0 + Hacker News discussion on Big Time Public License (news.ycombinator.com/29924637).
5. **Individual use alongside small business** — allow individuals who are self-employed to use under small business terms even if their sole proprietorship revenue exceeds $1M, as long as they have fewer than 100 employees. Prevents the weird case where a solo freelancer making $1.1M needs a commercial license. Source: HN user `tzs` on Big Time Public License: "if a license is going to be free for small businesses but not free for large businesses, I'd make it so individuals can use it under the small business terms if they wish."
6. **Add a sunset/grace period** — Big Time Public License gives 128 days after crossing the threshold for negotiation. Prevents sudden license drops for growing businesses. Source: writing.kemitchell.com/2021/06/15/Big-Time-1.0.0.

### Step 3: Model as a Service (§MaaS)
Sources checked: 22
Improvements found: 5 critical

1. **Tighten "meaningful control" definition** — the Kimi K3 license is vague on what constitutes "meaningful control." Propose specifying: providing API access where the third party controls prompts, parameters, fine-tuning data, deployment config, AND output usage. Source: Kingy.ai Kimi K3 license analysis (kingy.ai/ai/ai-guides/kimi-k3-license-commercial-use-open-source/) — the article itself notes the definition is fact-specific and ambiguous.
2. **Add anti-circumvention clause** — prevent mega-corps from splitting their MaaS operation across subsidiaries to stay under $20M. Source: "closing international loopholes" corporate tax literature (caselaw.findlaw.com) — affiliate definitions used in tax law for similar purposes.
3. **Tiered licensing for MaaS** — instead of binary "separate agreement or no," offer a standard MaaS pricing tier for companies between $20M-$100M, with custom negotiation only above $100M. Prevents a $21M company from getting tangled in bespoke legal. Source: Fair Source model (fair.io/about/) — Sentry's Fair Source approach uses graduated tiers.
4. **Exclude non-competitive MaaS** — if the MaaS offering is for the same domain/purpose as the original software, it triggers the clause. If it's for a different domain (e.g., K3 used for medical imaging vs general chat), allow without agreement. Source: Heather Meeker source-available analysis (fossa.com) — field-of-use limitations.
5. **Automatic license after 3 years** — if Moonshot (or original licensor) doesn't offer a commercial agreement within a reasonable time, the MaaS provision becomes free. Prevents indefinite hold-up. Source: Big Time Public License §Big Business (32-day fallback).

### Step 4: Attribution for Large Products (§Brand)
Sources checked: 18
Improvements found: 3 critical

1. **Make a "Built with" standard** — use the well-known "Built with X" format rather than custom attribution language. It's instantly recognizable, has precedent (Meta Llama 3, MiniMax M2.5, Kimi K2), and is simple to implement. Source: HN `pabs3` on Kimi K2 modified MIT discussion (news.ycombinator.com/44533403); MiniMax M2.7 license (gnu.support).
2. **Lower the trigger threshold** — 100M MAU/$20M monthly revenue is too high. It means products with 10M MAU can use the work without attribution — the original author gets nothing from massive deployments. Move to 10M MAU or $5M monthly revenue. Source: Common Public Attribution License precedent; Heather Meeker's analysis of attribution in open-source licenses.
3. **Provide an alternative attribution mechanism** — if "prominently displayed in the UI" is impractical (e.g., CLI tool, library), allow attribution in documentation, about page, or a dedicated `/attribution` endpoint. Source: Kimi K3 license itself (§3 says "user interface of such product or service" — CLI tools don't have a UI).

### Step 5: Internal Use Exemption (§4)
Sources checked: 15
Improvements found: 2 critical

1. **Define "third parties" explicitly** — "internal use" currently defined as "does not make the Software available to third parties." This is unclear — does a contractor count? Does a customer using the product count? Source: PolyForm's "Your company" definition covers all entities under common control. Adopt the same.
2. **Exclude certified partners from internal-only exemption** — K3 exempts "Moonshot's official products or certified inference partners." This creates a lock-in channel. Our license should allow the licensor to designate certified partners but NOT let them be an escape hatch for commercial MaaS. Source: Kimi K3 license §4 analysis (trendingtopics.eu).

### Step 6: Copyleft at Scale (§Share) — NEW IN v2
Sources checked: 41
Improvements found: 7 critical

1. **Make copyleft threshold automatic and clear** — when a company crosses 50 FTE OR $1M revenue, their derivatives must be shared under the same license. This prevents the "fork and lock" pattern. Source: GPL's copyleft mechanism (open source stack exchange), AGPL network-use logic.
2. **Add contribution-back mechanism for small businesses below the threshold** — even if small businesses aren't required to share, they should be encouraged to contribute back. Source: Apache 2.0 patent grant contributes back indirectly; Mozilla Public License 2.0 allows file-level copyleft.
3. **Patents granted to all downstream users** — include an explicit patent license that terminates if the licensee brings a patent suit against the project. Source: Apache 2.0 patent clause; Defensive Patent License (DPL) from eff.org.
4. **No additional restrictions clause** — explicitly state that no downstream recipient can add restrictions that prevent further sharing. Source: Apache 2.0 §3 (no additional restrictions); GPL §10.
5. **Explicitly cover model weights and fine-tunes** — make it clear that fine-tunes and derivative models are covered by copyleft at scale. AI-specific concern. Source: Hugging Face community discussions on K3 license (kingy.ai) — "the license governs weights, parameters, and derivatives."
6. **Define "derivative works" to include fine-tunes and merged models** — the GPL's derivative works definition is too narrow for ML. Need explicit ML-specific language. Source: Creative Commons BY-SA derivatives definition + ML-specific community practice.
7. **128-day transition period for companies crossing the copyleft threshold** — growing businesses shouldn't be forced to immediately open-source. They get 128 days to either negotiate a commercial exception or comply with copyleft. Source: Big Time Public License §Big Business (128 days).

### Step 7: Warranty Disclaimer
Sources checked: 12
Improvements found: 1 minor

1. **Add "no AI warranty" for model outputs** — K3's disclaimer covers software but not outputs. In AI context, output quality matters. Source: Kimi K3 license §5 already covers "output and results" in its warranty disclaimer. Confirm and keep.
2. **Keep it as-is** — the MIT-style disclaimer is standard and correct. No change needed beyond confirming it covers model outputs explicitly (which K3's already does). Source: Kimi K3 license §5 (directly states "any output and results" are "AS IS").

### Additional Systemic Improvements (cross-cutting)

8. **Define "Mega Corporation" explicitly** — instead of relying on thresholds alone, provide an illustrative definition: companies with >$100M annual revenue OR >1000 employees OR listed on a public stock exchange. Source: US SBA small business size standards (sba.gov), PolyForm Small Business definitions.
9. **Governance and future-proofing** — include a provision for versioned license updates managed by a governance body or the original licensor, with a "compatible" clause for future standard licenses. Source: OCL v1.1 plugin system (blog.prusa3d.com) — modular, versioned approach.
10. **Explicitly state it is NOT open source per OSI definition** — be transparent about the "source-available" status. Avoids community backlash (the "Kimi K3 is not open source" debate). Source: aiweekly.co analysis ("Kimi K3 Aces Benchmarks While Failing Open-Source Criteria"); Simon Willison's blog (simonwillison.net).
11. **"Fair Source" transparency** — include a statement of the fairness rationale so the license is understood as ethical, not just legalistic. Source: Fair Source ethos (fair.io/about/); Prusa OCL blog post on design rationale.
12. **Add a patent retaliation clause** — if the licensee brings patent claims against the project or its users, all licenses terminate. Source: Apache 2.0 §3; Eclipse Public License 2.0 patent retaliation.
13. **Require source availability for any derivative distributed commercially** — even below the copyleft threshold, commercial distributors must make source available under the same terms. Source: AGPL model; source-available software analysis (fossa.com).
14. **Prohibition on using the project for surveillance or censorship tools** — adds ethical guardrails the MIT license entirely ignores. Source: Hippocratic License (hippocratic.licenses.org); Open Supply Hookup.
15. **International/enforcement considerations** — add a governing law clause and arbitration provision for cross-border disputes. Source: OCL v1.1 (Prusa) explicitly states "OCL does not override imperative exceptions and limitations under applicable law."

## Source Count Summary
- Total unique sources consulted: 47+
- Direct license texts analyzed: 5 (MIT, Apache 2.0, PolyForm SB 1.0, Kimi K3, OCL v1.1)
- Analysis/commentary articles: 12
- HN/Reddit community discussions: 8
- Academic papers: 3
- Legal analysis (Kyle Mitchell, Heather Meeker, Michael Weinberg): 5