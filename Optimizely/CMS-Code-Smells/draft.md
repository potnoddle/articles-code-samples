# Optimizely CMS Code Smells: Spotting and Fixing Model Debt

**Treating a CMS schema as a visual layout engine creates massive technical debt. By eliminating duplicate block definitions, locking down rich-text sanitisation, and purging hardcoded content IDs, we cut editorial friction and stabilised headless API performance across enterprise Optimizely estates.**

---

## Introduction

Technical debt in an Optimizely estate rarely begins with catastrophic infrastructure failures; it accumulates silently in the content model. When inspecting legacy implementations, I repeatedly encounter codebases where rapid feature delivery took priority over domain discipline, turning the editorial interface into a fragile maze of duplicate blocks and unmaintainable rich-text fields.

A clean Optimizely CMS architecture treats content types as structured data contracts rather than disposable UI containers. When we enforce strict boundary hygiene between presentation and storage, both developer velocity and editor satisfaction improve.

*[Visual: Model Duplication vs. Componentised Architecture Diagram]*

### The block proliferation trap

The most frequent architectural smell in Optimizely development is cloning existing `BlockData` classes to satisfy minor visual tweaks. When a project ends up with separate `AuthorBlock`, `SpeakerBlock`, `TeamMemberBlock`, and `ContactCardBlock` types that all share identical fields (Name, Bio, Photo, SocialLink), technical debt multiplies.

Every new property, validation rule, or indexing convention must be manually duplicated across four distinct classes. The fragmentation also pollutes the editorial "Create New Block" modal and degrades GraphQL querying efficiency in [Optimizely Graph](https://www.linkedin.com/pulse/optimizely-graph-migrating-from-search-navigation-paul-graham-fnome).

The fix is straightforward: model the domain data once in a single `PersonBlock`. Handle visual variance using `DisplayOptions`, template descriptors, or a simple layout selection factory.

### Rich-text abuse and TinyMCE sanitisation

Allowing unrestricted rich-text editing in `XhtmlString` properties is a direct invitation for markup corruption. When editors copy and paste campaign copy directly from Word or email, proprietary XML formatting, broken tags, and hardcoded inline styles bypass your design system and damage Lighthouse performance scores.

Unrestricted rich-text fields also introduce severe security vulnerabilities, including stored cross-site scripting (XSS) if raw embed codes are pasted into unescaped fields.

We lock down the editorial environment by enforcing strict TinyMCE sanitisation in the application startup configuration:

```csharp
services.Configure<TinyMcePropertySettingsOptions>(options =>
{
    options.PasteFromWordImportType = PasteFromWordImportType.RemoveFormatting;
});
```

Pairing this with an explicit element allow-list ensures that complex visual layouts are constructed using dedicated, structured blocks rather than free-form HTML dumps (see [TinyMceConfigExtensions.cs](TinyMceConfigExtensions.cs) for the full configuration).

*[Visual: TinyMCE Cleanup Pipeline and XhtmlString Sanitisation Flow]*

### Eliminating hardcoded IDs and magic numbers

Hardcoding numeric content references like `new ContentReference(124)` inside controllers or configuration files is an operational anti-pattern. Content IDs change between local environments, staging slots, and DXP production instances following database restores.

Relying on magic numbers introduces silent runtime bugs and breaks multi-site tenancy. Instead, technical leads should implement strongly-typed settings models.

By defining a singleton settings model ([SiteSettingsBlock.cs](SiteSettingsBlock.cs)) referenced on the start page, developers can expose typed `PageReference` properties directly to editors. This guarantees compile-time safety and reliable deployment across cloud environments.

### Programmatic hygiene with core Optimizely APIs

Sustaining a clean CMS estate requires continuous automated auditing rather than periodic manual cleanups. Optimizely provides built-in diagnostic APIs to identify dead code and orphaned content (implemented in [ContentHygieneAuditService.cs](ContentHygieneAuditService.cs)):

- **Content Model Usage Inspection**: Calls `IContentModelUsage` to scan the database and report exactly how many instances of a given content type or block exist across the entire tree.
- **Reference Graph Tracing**: Uses `IContentSoftLinkRepository` to programmatically trace dependencies between pages, blocks, and media, identifying unlinked assets ready for archival.
- **Admin Schema Verification**: Audits property definitions in admin mode to highlight orphaned database columns where the corresponding C# model property has been removed.

*[Visual: Automated Content Model Usage Scanner Terminal Output]*

## Conclusion

A resilient Optimizely architecture relies on deliberate content modelling, strict rich-text governance, and the complete elimination of hardcoded environment dependencies. By adopting programmatic cleanup routines and enforcing reusable component design, engineering teams can safeguard long-term platform health.

---

💬 Which smell do you find most often when you inherit an Optimizely estate: cloned blocks, rich-text dumping grounds, or hardcoded IDs?

#Optimizely #OptimizelyCMS #DotNetCore #WebArchitecture #SoftwareEngineering
