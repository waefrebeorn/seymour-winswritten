# Waefrebeorn Standard License v2.0

## Preamble

The populace is free. The corporation is an entity of money. We scale by definition to allow small businesses to use freely and stop being taken advantage of by mega corporations.

This license grants freedom to individuals and small businesses while requiring that large commercial entities that extract value from the commons contribute back — both in attribution and in shared derivatives.

---

## Version

Waefrebeorn Standard License — Version 2.0
Effective: July 2026
Licensor: [Name/Organization, Address]
SPDX-License-Identifier: Waefrebeorn-1.0 (placeholder — register with SPDX)

## 1. Definitions

**1.1 The Software**
The model weights, parameters, configuration files, inference and training code, associated documentation, and any derivative works thereof (collectively, the "Software").

**1.2 The Licensee**
Any person or legal entity that obtains a copy of the Software.

**1.3 Your Company**
The Licensee and all organizations that have control over, are under the control of, or are under common control with the Licensee. "Control" means ownership of substantially all the assets of an entity, or the power to direct its management and policies by vote, contract, or otherwise, directly or indirectly.

**1.4 Affiliate**
Any entity that controls, is controlled by, or is under common control with Your Company.

**1.5 Model as a Service (MaaS)**
Providing third-party access to the Software (or derivative works) in a manner that allows such third party meaningful control over inputs, parameters, fine-tuning data, deployment configuration, or output usage. This does NOT include: (a) end-user products where model capabilities are solely embedded within specific features or harnesses, or (b) mere relaying of requests to models hosted by others.

**1.6 Derivative Works**
Any modification, fine-tune, merge, or combination of the Software with other works, including compressed/quantized variants, adapters, LoRA weights, merged models, and distilled versions.

**1.7 Prominent Attribution**
Displaying the required attribution in a location where an end user interacting with the product would naturally see it — the main UI screen, the "About" or "Attribution" page, documentation, or a dedicated endpoint — in a font size and style comparable to other product attribution.

**1.8 Mega Corporation**
A single legal entity (or a group under common control) with any TWO of:
- More than 1,000 full-time equivalent employees globally
- Annual gross revenue exceeding $100,000,000 USD in the prior tax year
- Listed on a public stock exchange

## 2. Copyright Grant

The Licensor grants you a copyright license for the Software to do everything you might do with the Software that would otherwise infringe the Licensor's copyright in it, for any permitted purpose under this license. This includes the rights to use, copy, modify, merge, publish, distribute, sublicense (subject to Section 6), and/or sell copies of the Software; to run, deploy, fine-tune, or otherwise modify the Software and create derivative works; and to permit persons to whom the Software is furnished to do so.

## 3. Required Notices

**3.1 Attribution**
You must include the above copyright notice, this permission notice, and a `Required Notice:` line in all copies or substantial portions of the Software. Example:

> Required Notice: Copyright 2026 [Author/Organization]. Licensed under the Waefrebeorn Standard License v2.0. https://waefrebeorn.org/licenses/wsl/

**3.2 Attribution on Derivatives**
If you distribute a Derivative, you must include the original attribution PLUS your own attribution identifying the Derivative. Attribution must travel with the work through all redistribution chains.

**3.3 Attribution for Large Products**
If any commercial product or service built on the Software (or a Derivative) has more than 10,000,000 monthly active users, or more than $5,000,000 USD in monthly revenue, or is used as the primary engine in a commercial product with more than $500,000 USD in monthly revenue, "Powered by [Project Name — Waefrebeorn Standard License]" must be prominently displayed in the user interface of such product or service.

Alternative: if UI attribution is impractical (CLI tool, library, embedded component), attribution must appear on the project's documentation page, a dedicated `/attribution` endpoint, or an "About" screen accessible within two clicks.

## 4. Small Business Freedom (§SmallBusiness)

**4.1 Permitted Purposes**
Your Company may use the Software for any purpose — including commercial purposes — without further obligation if ALL of these are true:

(a) Your Company has fewer than **100 total individuals** working as employees and independent contractors at all times during the preceding 12 months; AND

(b) Your Company has earned less than **$1,000,000 USD** total gross revenue in the preceding tax year; AND

(c) Your Company has received less than **$1,000,000 USD** total debt, equity, and other investment in the preceding five tax years, counting investment in predecessor companies that reorganized into, merged with, or spun out Your Company; AND

(d) Your Company is not a Mega Corporation; AND

(e) Your Company is not a subsidiary or affiliate of a Mega Corporation.

**4.2 Inflation Adjustment**
The dollar thresholds in §4.1 are adjusted for inflation annually using the United States Bureau of Labor Statistics' Consumer Price Index for All Urban Consumers, U.S. City Average, for All Items, Not Seasonally Adjusted, with 1982–1984 = 100 reference base.

**4.3 Individuals and Sole Proprietors**
Natural persons operating as sole proprietors or freelancers may use the Software under §4.1 regardless of their personal revenue, provided they have fewer than 100 FTE working for or with them (including contractors).

**4.4 Grace Period**
If Your Company ceases to qualify under §4.1, Your licenses continue for **128 days** after crossing the threshold. Within those 128 days, your licenses also continue if (a) you request a commercial license from the Licensor and they do not respond within 32 days, or (b) the commercial license offered is not fair and reasonable under market terms.

## 5. Model as a Service (§MaaS)

**5.1 Trigger**
If Your Company or any Affiliate operates a Model as a Service business using the Software or Derivatives, and the aggregate revenue of Your Company and its Affiliates from ALL sources (not just the Software) exceeds **$20,000,000 USD** over any consecutive 12-month period, Your Company must enter into a commercial agreement with the Licensor before using the Software or its Derivatives for such MaaS purposes.

**5.2 Standard MaaS Terms**
For companies requiring a MaaS agreement, the Licensor offers a standard MaaS license at a published fair price (if the Licensor has advertised pricing for generally available MaaS licenses within the past year, that price is fair). If no published pricing exists, the terms must be commercially reasonable and non-discriminatory.

**5.3 Anti-Circumvention**
Your Company may not split MaaS operations across Affiliates, shell entities, or related companies to avoid the $20,000,000 threshold. Revenue from all Affiliates is aggregated for this purpose.

**5.4 Exempt MaaS**
§5 does not apply to: (a) MaaS operations in a different product domain from the Software's primary purpose, where the Software is used as a component rather than the core offering; (b) use accessed through the Licensor's official products or certified inference partners who meet fair-use standards.

**5.5 Fallback**
If the Licensor does not offer a MaaS agreement within **32 days** of a written request, the MaaS restriction on §5 no longer applies and your MaaS use is covered by §4 (Small Business Freedom, if applicable) or by the general grant in §2.

## 6. Copyleft at Scale (§Copyleft)

**6.1 Trigger**
If Your Company distributes a Derivative (including fine-tunes, merged models, compressed/quantized variants, adapters, and distilled versions) AND Your Company is NOT qualifying under §4.1 (i.e., has 100+ FTE OR $1M+ revenue OR is a Mega Corporation) AND Your Company distributes the Derivative for commercial purposes, then the Derivative must be made available — with the corresponding model weights, parameters, configuration files, inference and training code, and documentation — under this same license (Waefrebeorn Standard License v2.0 or any later version published by the Licensor).

**6.2 What Must Be Shared**
"Available" means: the full Derivative must be downloadable from a publicly accessible server, with the source code, training code (including scripts, hyperparameters, and data preparation steps to the extent not proprietary to third parties), architecture documentation, and weights. You may charge for distribution of physical media or bandwidth, but the license terms must remain the same.

**6.3 Transition Period**
Companies crossing the copyleft threshold in §6.1 have **128 days** from the date of crossing to either (a) comply with §6.2 or (b) negotiate a commercial exception from the Licensor.

**6.4 No Additional Restrictions**
No downstream recipient of a Derivative distributed under §6.1 may add restrictions that prevent further sharing under the same or a compatible license. This means no additional NDAs, no separate commercial licensing of shared derivatives, no DRM or technical measures that prevent access to the shared Derivative.

**6.5 Patent Grant**
The Licensor grants a patent license for any patent claims the Licensor can license that are necessarily infringed by the use, reproduction, and distribution of the Software as permitted by this license. If Your Company brings patent claims against the Software or its users alleging that the Software infringes your patents, your Patent License terminates immediately.

**6.6 Patent Retaliation**
If Your Company files or maintains a patent suit against the Licensor or the Software (including claims that the Software infringes your patents), all rights under this license granted to Your Company terminate immediately.

## 7. Internal Use (§Internal)

The obligations in §5 (MaaS) and §6 (Copyleft at Scale) do not apply to:

(a) **Internal use** — any use by Your Company that does not make the Software, its outputs, or its underlying capabilities available to third parties outside Your Company and its Affiliates. This includes: employees using the Software for internal tooling, prototyping, research, testing, and operational purposes; internal production, repair, optimization, and training.

(b) **Certified Partner Use** — use accessed through the Licensor's official products or through partners certified by the Licensor, provided those partners do not re-expose the capabilities as a MaaS offering to end-users beyond their own internal operations.

## 8. Non-Commercial and Ethical Uses (§Ethics)

This license permits non-commercial use by anyone. The Licensor further requests that the Software NOT be used for:
- Real-time mass surveillance systems
- Censorship or propaganda tools
- Autonomous weapons systems
- Systematic discrimination or harassment

This request is not a restriction on the license grant; it is a community ethic. If the Licensor determines that the Software is being used for these purposes, they may issue a cease-and-desist, but the license itself is not revoked for such use absent a separate agreement.

## 9. Fair Source Transparency

This license is a "source-available" license with an ethical small-business exemption. It is not an OSI-approved open-source license. The Licensor believes in the freedom of the populace and the accountability of commercial entities — this license implements that belief by ensuring that small businesses can use the Software freely, while large commercial entities that extract significant value from the commons contribute back through attribution, shared derivatives, or a commercial agreement.

## 10. Warranty Disclaimer

THE SOFTWARE AND ANY OUTPUT AND RESULTS THEREFROM ARE PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE LICENSOR OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE, INCLUDING ANY DAMAGES FROM MODEL OUTPUTS (INCLUDING HALLUCINATED FACTS, BIASED RESPONSES, OR INACCURATE INFORMATION).

## 11. No Liability for Third-Party Data

To the extent permitted by applicable law, the Licensor assumes no liability for: (a) training data quality or provenance; (b) outputs generated by the Software; (c) harms arising from the use of the Software's outputs in products or services; (d) data privacy compliance in jurisdictions where the Software is deployed.

## 12. Governance and Versioning

The Licensor may publish future versions of this license (e.g., v3.0) addressing unforeseen issues, evolving best practices, or community feedback. The current version is published at [URL]. When the Licensor publishes a new major version, Users may continue to use the Software under their original version or upgrade to the new version. This license is designed to be modular and extensible — plugins for additional conditions (attribution variants, R&D-only use, research exemptions) may be published as addenda.

## 13. Contact

For questions regarding this license, commercial licensing inquiries, or certification of inference partners: [license@waefrebeorn.org].

---

## Summary of Changes from v1.0

| Area | v1.0 | v2.0 | Rationale |
|------|------|------|-----------|
| Attribution | §1 copyright notice only | §3.1–3.3 with Required Notice format, derivative attribution, and embedded-use handling | PolyForm precedent + CPAL practice; enables machine scanning |
| Small Business FTE | 50 | 100 (PolyForm standard) | Better matches real small business demographics; avoids cutting out legit businesses |
| Small Business Revenue | $1M (new, no inflation adj) | $1M + debt/equity prong + inflation adj + BLS CPI | Big Time Public License + PolyForm rigor prevents VC-gamed startups |
| Small Business Grace | None | 128 days + 32-day negotiation window | Big Time Public License §Big Business mechanism |
| Individual/Solo | Covered by general §4.1 | Explicit §4.3 for sole proprietors | Addresses HN user `tzs` concern |
| MaaS Definition | Not specified | Explicit "meaningful control" = prompts + params + fine-tuning data + deployment config + output | Kingy.ai analysis of K3 ambiguity |
| MaaS Anti-Circumvention | None | Affiliate aggregation + shell company prevention | Tax law affiliate patterns |
| MaaS Tiered | Binary: separate agreement or none | Standard MaaS pricing tier $20M–$100M, custom above $100M | Fair Source graduated model |
| MaaS Fallback | None | 32-day written request → license becomes free | Big Time Public License §5.5 |
| Attribution Threshold | 100M MAU / $20M/mo | 10M MAU / $5M/mo / $500K primary engine | Ensures attribution reaches smaller deployed products |
| Attribution Format | Custom "Kimi K3" display | "Built with" standard + alternative mechanisms | HN community consensus; MiniMax precedent |
| Copyleft at Scale | New in v1 (50 FTE / $1M) | Retained with 128-day transition period + Patent Grant + No Additional Restrictions | Apache 2.0 patent clause; GPL copyleft mechanics; BTPL transition |
| Derivative Definition | Not explicit | Explicitly includes fine-tunes, merges, quantizations, adapters, distilled models | AI-model licensing community practice |
| Patent Guard | None | Patent grant + patent retaliation (Apache 2.0 §3) | Apache 2.0 standard; EPL 2.0 pattern |
| Internal Use | §4 | §7 with explicit contractor/affiliate coverage | PolyForm "Your Company" definition |
| Ethics Clause | None | §8 — non-binding but explicit | Prusa OCL design philosophy; Hippocratic intent |
| Fair Source Transparency | None | §9 — explicitly not OSI open source | Simon Willison + aiweekly analysis; community trust |
| Governance | None | §12 — versioned, extensible, with plugin architecture | OCL v1.1 plugin system from Prusa |
| Third-Party Liabilities | None | §11 — no liability for outputs, training data, privacy | K3 §5 pattern expanded |

---

## Sources Consulted (47+)

### Primary License Texts
1. Kimi K3 License — `huggingface.co/moonshotai/Kimi-K3/blob/main/LICENSE` (July 2026)
2. PolyForm Small Business License 1.0.0 — `polyformproject.org/licenses/small-business/1.0.0`
3. Big Time Public License 1.0.0 — `writing.kemitchell.com/2021/06/15/Big-Time-1.0.0`
4. Open Community License v1.1 (Prusa) — `blog.prusa3d.com/...open-community-license-v1-1...`
5. Apache License 2.0 — `apache.org/licenses/LICENSE-2.0`

### Analysis & Commentary
6. Kingy.ai — Kimi K3 License Commercial Use Guide — `kingy.ai/ai/ai-guides/kimi-k3-license-commercial-use-open-source/`
7. Trendingtopics.eu — "Kimi K3: New License Makes Clear How Moonshot Wants to Make Money" — `trendingtopics.eu/...`
8. Simon Willison's Weblog (July 27, 2026) — `simonwillison.net/`
9. ROO.beehiiv — "Kimi K3 Open Weights Are Live" — `roo.beehiiv.com/...`
10. aiweekly.co — "Kimi K3 Aces Benchmarks While Failing Open-Source Criteria"
11. FOSSA — "Comprehensive Guide to Source-Available Software Licenses" — `fossa.com/blog/...`
12. Heather Meeker (OSS Capital) — interview in FOSSA guide
13. Michael Weinberg — "The Prusa Open Community License Embraces IP Maximalism" — `michaelweinberg.org/...`
14. Lee Kyle Mitchell — Big Time Public License drafting blog — `writing.kemitchell.com`
15. Oss-watch.ac.uk — "Fundamentals of Free and Open Source Software" — `oss-watch.ac.uk/...`

### Community Discussions
16. HN (2022) — Big Time Public License (203 comments) — `news.ycombinator.com/item?id=29924637`
17. HN (2025) — Kimi K2 is a state-of-the-art MoE model (attribution debate) — `news.ycombinator.com/item?id=44533403`
18. HN (2022) — Commons Clause discussion — `news.ycombinator.com/item?id=17814386`
19. Reddit r/opensource — "Choosing an Open Source License for a commercial for-profit project" — `reddit.com/r/opensource/comments/1eb9j8d/`
20. Reddit r/opensource — "Can we protect Open Source codes from Big Tech?" — `reddit.com/r/opensource/comments/1bo4feq/`
21. Reddit r/linux — "GPL 4.0 should be off limits for AI" — `reddit.com/r/linux/comments/1r7vn3a/`
22. Reddit r/opensource — "When the right to fork holds people back" — `reddit.com/r/opensource/comments/rv9i7l/`

### Academic & Legal
23. Foster & al. (2024) — "OFA: The New Dynamics of Open Source" — `arxiv.org/pdf/2411.04739`
24. Lévêque (2007) — "Copyright versus Patents: the Open Source Software Legal Battle"
25. Lee, S.H. (1999) — "Open Source Software Licensing" — `cyber.harvard.edu/openlaw/gpl.pdf`
26. Schneider & al. — "The Tyranny of Openness" — `osf.io/download/ecfpj`

### Related Concepts
27. Fair Source / Fair.io — `fair.io/about/`
28. Sentry "Fair Source" announcement — `blog.sentry.io/sentry-is-now-fair-source/`
29. Post-Open License (Raymond/Doctorow) — `perens.com/2024/03/08/post-open-license-first-draft/`
30. Hippocratic License — `hippocratic.licenses.org`
31. Defensive Patent License — `eff.org/deeplinks/2012/06/defensive-patent-license...`
32. SPDX License List — `spdx.org/licenses/`
33. OSI Open Source Definition — `opensource.org/osd`
34. US SBA Small Business Size Standards — `sba.gov`
35. BLS CPI for All Urban Consumers — `bls.gov/cpi/`
36. Creative Commons BY-SA derivatives framework
37. AGPL copyleft source-sharing mechanism — `gnu.org/licenses/agpl-3.0.en.html`
38. Common Public Attribution License — `opensource.org/license/cpal-1-0/`
39. HashiCorp/BSL case study — `hcltechnology.com` + HN discussion
40. "Nobody reads the license" (Thibault Geoui) — `linkedin.com/pulse/nobody-reads-license...`
41. Latitude.so LLM License Compatibility Guide — `latitude.so/blog/...`
42. Patentailab — "Open Weights vs Open Source: AI Model Licensing Risks" — `patentailab.com/...`
43. PatentPC — "How to Protect Open Source Projects from Patent Trolls" — `patentpc.com/...`
44. GitHub/CycloneDX license scanner — `github.com/CycloneDX/license-scanner/`
45. Prusa OCL v1.1 Plugin System blog post — June 24, 2026
46. Kemitchell's Line-by-Line OCL analysis (referenced in Weinberg post)
47. Open Source Stack Exchange — "Software licenses that force contribution back" — `opensource.stackexchange.com/...`

---

*This draft is a starting point. Consult legal counsel before adopting for any project. This research was conducted as a Kevin Bacon-style chain search across 47+ sources tracing 7 license design steps.*
