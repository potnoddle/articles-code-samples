# Optimizely CMS Code Smells: Spotting and Fixing Model Debt

## Description
This research document aggregates common architecture, content modelling, editorial security, and technical debt anti-patterns in Optimizely CMS (Episerver) estates. It provides exact code mitigations, programmatic cleanup APIs, and configuration best practices.

  - key insights:
    * Block proliferation creates massive editorial friction and makes headless querying via Optimizely Graph brittle
    * Unrestricted TinyMCE rich-text properties introduce stored XSS vulnerabilities and invalid DOM markup
    * Hardcoded numeric ContentLink IDs break cross-environment synchronization and multi-site tenancy
    * Built-in interfaces like IContentModelUsage and SoftLinkRepository enable automated detection of orphaned content

  - keywords:
    * Optimizely CMS Code Smells
    * Block Proliferation
    * IContentModelUsage
    * TinyMCE Sanitization
    * Content Type Refactoring
---

### Platform Constraints & Variable Adjustments
- **Target Platform**: LinkedIn (Article) (linkedin-article)
- **Constraints**: No native markdown tables in final draft. Transform tabular audits into comparative bullet lists. Enforce UK English spelling and ASCII straight quotes throughout.

### Conflicts & Caveats
Refactoring in-use content types and properties in production Optimizely databases requires careful migration planning. Deleting code-first properties without running database migration jobs leaves orphaned "zombie" metadata in the database schema.

### Target Audience & Keywords
- **Primary Audience**: Optimizely CMS Developers & Technical Leads (cms_developers)
- **Audience Level**: Subject Matter Expert (advanced_sme)
- **SEO Keywords**: Optimizely CMS Code Smells, Episerver Block Proliferation, IContentModelUsage, Clean Content Modelling, TinyMCE XhtmlString Hardening

## Outline
1. **The Hidden Cost of CMS Code Smells** (Target Word Count: ~120 words | Visual: Model duplication vs. componentized architecture diagram)
2. **Block Proliferation: The Clone-and-Tweak Trap** (Target Word Count: ~160 words | Visual: Block inheritance & configuration vs duplicate types)
3. **Rich-Text Abuse & The TinyMCE Dumping Ground** (Target Word Count: ~140 words | Visual: TinyMCE cleanup pipeline & XhtmlString sanitizer)
4. **Magic Numbers & Brittle Environment Coupling** (Target Word Count: ~130 words | Visual: Hardcoded IDs vs strongly-typed settings)
5. **Automated Hygiene: Detection Tools and Cleanup APIs** (Target Word Count: ~150 words | Visual: IContentModelUsage scanner and orphaned property cleanup)

## Research

### 1. The Hidden Cost of CMS Code Smells
Technical debt in CMS architectures rarely starts with complex algorithm failures; it begins with subtle content modeling anti-patterns. When developers treat [Optimizely Content Architecture](https://docs.developers.optimizely.com/content-management-system/v1.0.0-CMS-12/docs/content-types) as a rapid UI generator rather than an enterprise domain schema, the resulting estate degrades editor efficiency, slows API response times, and multiplies maintenance overhead across release cycles.

### 2. Block Proliferation: The Clone-and-Tweak Trap
The most pervasive anti-pattern in Optimizely estates is the proliferation of nearly identical `BlockData` types. When editors request a slight visual variation (e.g., Speaker Block vs. Author Block vs. Team Member Block), developers frequently copy the class definition, duplicating Name, Image, Bio, and SocialLink properties.
- **Systemic Impact**: Bloats the "Create New Block" modal, forces redundant property-level changes during rebranding, and fragments schemas indexed into [Optimizely Graph](https://docs.developers.optimizely.com/platform-optimizely/v1.0.0-graph/docs).
- **Architectural Solution**: Define the domain model once (`PersonBlock`). Vary presentation using `DisplayOptions`, template tags, or a layout selection factory. Use `AvailableInEditMode = false` on core building blocks embedded inside composite page structures.

### 3. Rich-Text Abuse & The TinyMCE Dumping Ground
Allowing unrestricted copy-paste into `XhtmlString` properties introduces severe formatting pollution and security risks. Pasting rich text from Microsoft Word or Teams injects invalid inline styles, unclosed tags, and proprietary XML markup (`mso-` attributes) that degrade Lighthouse Core Web Vitals.
- **Security Vulnerability**: Unrestricted rich-text fields become conduits for stored cross-site scripting (XSS) if editors paste raw scripts or malicious embeds.
- **Mitigation**: Configure strict TinyMCE options in `Startup.cs`:
```csharp
services.Configure<TinyMcePropertySettingsOptions>(options =>
{
    options.PasteFromWordImportType = PasteFromWordImportType.RemoveFormatting;
});
```
Enforce custom `valid_elements`, strip inline style attributes, and require dedicated block components instead of free-form HTML embeds.

### 4. Magic Numbers & Brittle Environment Coupling
Hardcoding numeric content IDs (`ContentReference(124)`) or string-based page type IDs inside controllers, service classes, or `appsettings.json` creates brittle multi-environment dependencies.
- **Why It Fails**: Content IDs differ between local development, DXP Integration, Preproduction, and Production environments following database restores.
- **Remediation**: Use strongly-typed site settings pages inheriting from a singleton `SiteSettingsBlock` or `SiteDefinition.Current.StartPage`. Reference pages via `PageReference` properties rather than numeric integers.

### 5. Automated Hygiene: Detection Tools and Cleanup APIs
Preventing model decay requires proactive, programmatic scanning of CMS schemas:
- **`IContentModelUsage`**: The core Optimizely API for scanning how many instances of a specific content type or block exist across the database.
- **`SoftLinkRepository`**: Programmatically inspects incoming and outgoing references to identify orphaned media assets and unlinked blocks.
- **Admin Schema Verification**: Regularly audit `Admin -> Content Types -> Properties` to identify orphaned "From Code = No" properties left behind after code deletions.

### Other Research
- Running continuous background jobs for version trimming (`TrimVersionsScheduledJob`) prevents `tblContentVersion` database bloat on active high-volume editorial estates.
- Treating `CurrentPage` or `CurrentBlock` as mutable view-models inside controllers causes cross-request cache corruption under high concurrency on Azure App Services.

---

## Companion Code Samples

- [TinyMceConfigExtensions.cs](TinyMceConfigExtensions.cs): Extension method applying `PasteFromWordImportType.RemoveFormatting`, element allow-lists (`valid_elements`), and inline style stripping.
- [SiteSettingsBlock.cs](SiteSettingsBlock.cs): Strongly typed singleton settings model with `PageReference` and `ContentReference` properties replacing magic numbers.
- [ContentHygieneAuditService.cs](ContentHygieneAuditService.cs): Audit service demonstrating `IContentModelUsage` to find unused content types and `IContentSoftLinkRepository` to identify broken/unlinked assets.
