# Target Metadata
- **Target Platform**: LinkedIn (Article) (linkedin-article)
- **Target GEO Bracket**: Tier 1: High-Authority Growth (Score 9-10) (tier_1_high_authority_growth)
- **Primary Audience**: Optimizely CMS Developers & Technical Leads (cms_developers)
- **Secondary Audience**: R&D Directors (rd_directors)
- **Audience Level**: Subject Matter Expert (advanced_sme)
- **Article Type**: Technical Deep Dive & Code Fixes (technical_deep_dive)
- **Image Style**: Optimizely 2025 (optimizely_2025)
- **Image Theme**: Hypermedia Architecture (hypermedia_architecture)
- **Colour Scheme**: Optimizely Identity 2025 (optimizely_identity_2025)

### SEO Keywords
1. Optimizely CMS Code Smells
2. Episerver Block Proliferation
3. IContentModelUsage Cleanup
4. Clean Content Modelling
5. TinyMCE XhtmlString Hardening

### Article Outline & Visual Matrix
1. **Introduction** (Word Count: ~120 | Visual: Model Duplication vs. Componentised Architecture Diagram)
2. **The Block Proliferation Trap** (Word Count: ~160 | Visual: Reusable domain model vs duplicated block types)
3. **Rich-Text Abuse and TinyMCE Sanitisation** (Word Count: ~140 | Visual: TinyMCE Cleanup Pipeline and XhtmlString Sanitisation Flow)
4. **Eliminating Hardcoded IDs and Magic Numbers** (Word Count: ~130 | Visual: Hardcoded IDs vs strongly-typed settings)
5. **Programmatic Hygiene with Core Optimizely APIs** (Word Count: ~150 | Visual: Automated Content Model Usage Scanner Terminal Output)
6. **Conclusion** (Word Count: ~60 | Visual: None)

### Follow-up Articles
1. **Automating Optimizely Content Type Audits in CI/CD**: Building automated build gates that flag duplicate property structures and missing GUIDs before merge.
2. **Refactoring Legacy Episerver DB Schemas Without Content Loss**: Step-by-step database migration scripts for consolidating fragmented block types in production.
3. **Auditing Softlinks and Media Hygiene in Large Optimizely Estates**: Using `IContentSoftLinkRepository` to identify and prune orphaned digital assets safely.
