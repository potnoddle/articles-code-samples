# Refactoring Optimizely CMS Content Types Without Data Loss

**Renaming C# content types and properties in a code-first CMS can silently orphan database records and drop production content. By combining explicit [ContentType] GUID preservation with the built-in MigrationStep API, engineering teams can rename models and properties while keeping existing content attached.**

---

## Introduction

Code-first content modelling is one of the greatest strengths of Optimizely CMS. Engineers define C# classes representing pages, blocks, and media, while the CMS automatically synchronises those definitions with the database schema during application startup. Over long-term enterprise maintenance cycles, however, this convenience introduces a serious trap.

When evolving a codebase (whether cleaning up legacy naming conventions, restructuring content models, or aligning domain models with new architecture), renaming a C# class or property without explicit migration instructions breaks the link between compiled code and database tables. The CMS treats renamed models as brand-new entities, leaving existing content stranded in orphaned database rows.

*[Visual: Code Refactoring to Database Schema Mapping Diagram]*

```
[ Code Refactoring ]              [ Database Schema ]
C# Class: OldArticlePage  ───►  tblContentType (ID: 42, Name: "OldArticlePage")
       │                                  │
       ▼ (Renamed in C#)                  ▼ (Unlinked Data)
C# Class: ArticlePage     ───►  tblContentType (ID: 99, Name: "ArticlePage")
                                 * Existing page instances remain tied to ID 42 *
```

### The hidden pitfall of code-first model refactoring

In standard C# application development, renaming a class via IDE refactoring tools is a routine task. In a code-first CMS like Optimizely, however, C# code is the active schema definition for live database tables.

During a major CMS 12 migration for an enterprise client, an uncoordinated property rename on a core hero block went live to staging. Because the property definition changed from `Heading` to `Title` without a migration step, hundreds of landing pages suddenly rendered blank banners while the database quietly held the legacy values in orphaned property rows.

When the application boots, the CMS scans assemblies for classes decorated with the `[ContentType]` attribute and compares them against registered records in `tblContentType` and `tblPropertyDefinition`. If an engineer alters a C# class or property name without migration metadata:

- **Class Renaming without GUID Stability**: The framework fails to correlate the renamed class with its existing database record, generating a duplicate content type entry while leaving published pages bound to the missing type.
- **Property Renaming without Migration Steps**: The framework registers the renamed property as a new column definition. Existing content instances retain their data under the historical property ID, but editors and frontend templates see empty values because the new property name holds no records.

### The golden rule: preserve the model GUID

Optimizely uses globally unique identifiers (GUIDs) to anchor content type definitions in the database. When defining any content type in C#, the `[ContentType]` attribute accepts an explicit GUID argument:

```csharp
[ContentType(
    DisplayName = "Article Page",
    GUID = "9F8E7D6C-5B4A-3210-FEDC-BA9876543210",
    Description = "Standard article page model."
)]
public class ArticlePage : PageData
{
}
```

Preserving this GUID provides three essential architectural guarantees:

- **Immutable Identity Anchor**: The GUID string is the permanent primary link between your C# class and the `tblContentType` database row.
- **Refactoring Resilience**: If you rename a C# class (such as `LegacyArticlePage` to `ArticlePage`) while keeping the original GUID, Optimizely recognises that both names represent the identical database entity.
- **Automatic System Name Synchronisation**: Retaining the GUID allows the system to update the display name and type mapping safely without creating duplicate database records.

Never generate a fresh `Guid.NewGuid()` when renaming an existing `PageData` or `BlockData` class; doing so breaks identity tracking and forces the CMS to treat the refactored class as a separate entity.

*[Visual: GUID Identity Resolution Flowchart]*

### Deep dive: the MigrationStep mechanism

While preserving the GUID maintains class identity, renaming internal properties (or renaming types where historical tracking requires explicit system-name mapping) demands the `EPiServer.DataAbstraction.Migration.MigrationStep` API.

The `MigrationStep` class allows developers to register explicit mapping rules that execute automatically during startup synchronisation:

```csharp
using EPiServer.DataAbstraction.Migration;

namespace MyProject.Infrastructure.Migrations
{
    public class RefactorArticlePageMigration : MigrationStep
    {
        public override void AddChanges()
        {
            // 1. Map historical content type system name
            ContentType("ArticlePage")
                .UsedToBeNamed("OldArticlePage");

            // 2. Map historical property name on the NEW content type
            ContentType("ArticlePage")
                .Property("MainBody")
                .UsedToBeNamed("IntroText");
        }
    }
}
```

When implementing migration steps, remember three critical API rules:

- **Target the New Model Name**: When declaring property mappings, chain the call from the new content type name (`ContentType("ArticlePage")`), not the historical name.
- **Batch Multiple Modifications**: Multiple content types and properties can be refactored within a single `MigrationStep` class or organised into modular migration files.
- **Automatic Reflection Discovery**: During startup, Optimizely uses reflection to discover all concrete classes inheriting from `MigrationStep` without requiring manual dependency injection registrations.

*[Visual: MigrationStep Schema Transformation Sequence]*

### Worked example: TeaserBlock to PromoBlock

A common clean-up is consolidating an old `TeaserBlock` into a standardised `PromoBlock` and renaming its `LeadText` property to `Summary`. Three changes ship together in one deployment:

- **Migration Step**: Map `TeaserBlock` to `PromoBlock` and `LeadText` to `Summary` with `UsedToBeNamed`.
- **Model Class**: Rename the class and property, keeping the original `GUID` value untouched.
- **Views and Services**: Update Razor views and any code that reads the old property name.

The full migration class, block model and Razor view are in the companion file [promo-block-migration.cs](promo-block-migration.cs). The only lines that carry the migration are these:

```csharp
ContentType("PromoBlock").UsedToBeNamed("TeaserBlock");
ContentType("PromoBlock").Property("Summary").UsedToBeNamed("LeadText");
```

Before raising a pull request for schema refactoring, I always restore a sanitised production snapshot to my local SQL LocalDB instance, boot the site, and verify that the content renders in the refactored view before checking git status.

### What happens at startup

Optimizely discovers `MigrationStep` classes automatically when the site starts and applies their renames as part of content type synchronisation. The existing property definition is renamed in place rather than recreated, so values already stored against `LeadText` surface under `Summary` with no data copy.

Two limits are worth knowing before you rely on it:

- **Renames Only**: `UsedToBeNamed` handles name changes. Changing a property's type (for example `string` to `XhtmlString`) still needs a new property and a data migration through `IContentRepository`.
- **No Commerce Catalog Support**: The mechanism covers CMS content types; it is not supported for Commerce catalog content.

*[Visual: Rename-in-place vs Recreate Property Comparison]*

### Production deployment and risk mitigation best practices

Executing schema migrations across deployment pipelines requires strict operational verification:

- **GUID Verification**: Audit all modified C# model classes to verify that `[ContentType(GUID = "...")]` attributes match historical production values.
- **Migration Syntax Validation**: Confirm that all property-level migration rules chain from the new content type system name.
- **Automated Test Verification**: Execute automated unit tests ([MigrationStepVerificationTests.cs](MigrationStepVerificationTests.cs)) to confirm GUID preservation and migration registrations before merge.
- **Staging Database Sanity Run**: Restore a production database backup into staging and execute the build to verify complete content preservation before touching live servers.
- **Immutable Database Snapshot**: Always capture a full database backup immediately prior to deploying schema migration code to production.

### Should migration steps stay in the codebase?

Once a step has run in every environment, including production, it is safe to delete. Keeping it for a release or two is cheap insurance: any database restored from a backup taken before the rename still needs the mapping.

## Conclusion

Code-first content modelling in Optimizely CMS makes development fast, but long-term refactoring requires deliberate architecture. By preserving `[ContentType]` GUIDs and applying the `MigrationStep` API, engineering teams can rename models and properties without orphaning the content already stored against them.

---

💬 Have you ever found a renamed property that emptied content in production, and how long did it take to notice?

#Optimizely #OptimizelyCMS #DotNetCore #WebDevelopment #SoftwareEngineering
