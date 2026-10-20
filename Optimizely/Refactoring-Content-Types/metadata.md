# Target Metadata — Refactoring Content Types & Properties in Optimizely CMS

- **Title**: Refactoring Content Types & Properties in Optimizely CMS Without Content Loss
- **Target Platform**: LinkedIn (Article) (linkedin-article)
- **Target GEO Bracket**: Tier 1: High-Authority Growth (Score 9-10) (tier_1_high_authority_growth)
- **Primary Audience**: Optimizely CMS Developers & Technical Leads (cms_developers)
- **Secondary Audience**: Technical Architects (TA) (technical_architects)
- **Audience Level**: Advanced (advanced)
- **Article Type**: How-To (how_to)
- **Estimated Reading Time**: 6–8 minutes
- **Target Word Count**: ~1,200 words
- **Tone**: Auteur-Engineer (auteur_engineer)
- **Colour Scheme**: Optimizely Identity 2025 (optimizely_identity_2025)
- **Image Style**: Optimizely 2025 (optimizely_2025)
- **Image Theme**: Schema Evolution & Migration Mechanics (schema_evolution_migration_mechanics)

### SEO Keywords

1. Optimizely CMS content type refactoring
2. MigrationStep EPiServer database migration
3. Rename Optimizely property without content loss
4. ContentType GUID preservation EPiServer
5. Optimizely C# model refactoring best practices
6. EPiServer.DataAbstraction.Migration MigrationStep
7. Optimizely database content sync order of operations

### Article Outline & Visual Matrix

1. **Introduction** (Word Count: ~150 | Visual: Code Refactoring to Database Schema Mapping Diagram)
2. **The Hidden Pitfall of Code-First Model Refactoring** (Word Count: ~160 | Visual: Class & property sync failure breakdown)
3. **The Golden Rule: Preserve the Model GUID** (Word Count: ~160 | Visual: GUID Identity Resolution Flowchart)
4. **Deep Dive: The `MigrationStep` Mechanism** (Word Count: ~200 | Visual: MigrationStep Schema Transformation Sequence)
5. **Worked Example: TeaserBlock to PromoBlock** (Word Count: ~150 | Visual: Companion code reference & key mapping lines)
6. **What Happens at Startup** (Word Count: ~140 | Visual: Rename-in-place vs Recreate Property Comparison)
7. **Production Deployment and Risk Mitigation Best Practices** (Word Count: ~150 | Visual: Deployment safety checklist)
8. **Should Migration Steps Stay in the Codebase?** (Word Count: ~90 | Visual: Lifespan policy flowchart)
9. **Conclusion** (Word Count: ~60 | Visual: None)

### Follow-up Articles

1. **Automating Optimizely Content Type Audits in CI/CD**: Building automated build gates that flag duplicate property structures and missing GUIDs before merge.
2. **Refactoring Legacy Episerver DB Schemas Without Content Loss**: Step-by-step database migration scripts for consolidating fragmented block types in production.
3. **Property Type Conversions in Optimizely CMS**: Migrating from raw strings to structured blocks or rich text without dropping historical editorial data.
