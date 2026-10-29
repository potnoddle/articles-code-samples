# Technical Research Document: Refactoring Content Types & Properties in Optimizely CMS

---

> **Summary:** Refactoring C# class names or property names in Optimizely CMS (formerly EPiServer) requires strict alignment between code-first models, the database schema, and model GUIDs. Using Optimizely’s built-in `MigrationStep` mechanism ensures smooth database updates without losing content.

---

## 1. Overview & Context

When refactoring Optimizely CMS solutions, developers frequently need to:

1. **Rename Content Types:** Page or Block models (e.g., `OldArticlePage` → `NewArticlePage`).
2. **Rename Internal Properties:** Properties within a Content Type (e.g., `IntroText` → `MainBody`).

If a C# class or property is renamed in code without explicit database migration instructions, Optimizely treats the new names as entirely new schema elements. This leads to **content loss** for existing pages/blocks in the database or orphaned properties.

---

## 2. Core Architectural Principles

### The Model GUID Rule

Optimizely uses the **`[ContentType]` GUID** as the primary unique identifier for content types in the database.

* **Class Renaming:** When renaming a C# class, **never change the GUID** inside `[ContentType(GUID = "...")]`. Preserving the original GUID enables the framework to correlate the renamed C# class with its existing record in the database.
* **Database Identity:** The GUID anchors the identity, while `MigrationStep` updates the system name mapping.

### Migration Step Mechanics

The `EPiServer.DataAbstraction.Migration.MigrationStep` class provides a fluid API (`AddChanges()`) to explicitly instruct Optimizely how to map historical database identities to new C# names during application startup.

---

## 3. Implementation Blueprint

### Step 1: Define the `MigrationStep`

Combine content type and property renaming inside the `AddChanges()` method.

> **Important Rule:** Always reference the **new** Content Type name when chaining property-level migrations.

```csharp
using EPiServer.DataAbstraction.Migration;

namespace YourNamespace.Migrations
{
    public class RenameContentAndPropertyMigration : MigrationStep
    {
        public override void AddChanges()
        {
            // 1. Map old Content Type name to new Content Type name
            ContentType("NewArticlePage")            // New type name
                .UsedToBeNamed("OldArticlePage");    // Old type name

            // 2. Map old property name to new property name on the NEW Content Type
            ContentType("NewArticlePage")
                .Property("MainBody")                // New property name
                .UsedToBeNamed("IntroText");         // Old property name
        }
    }
}
```

### Step 2: Update the C# Content Model

Update your page or block model to match the new names, keeping the original GUID intact.

```csharp
using EPiServer.Core;
using EPiServer.DataAnnotations;

namespace YourNamespace.Models.Pages
{
    [ContentType(
        DisplayName = "New Article Page", 
        GUID = "9F8E7D6C-5B4A-3210-FEDC-BA9876543210", // MUST keep original GUID
        Description = "Updated article page type"
    )]
    public class NewArticlePage : PageData
    {
        public virtual XhtmlString MainBody { get; set; } // Refactored property
    }
}
```

---

## 4. Execution Sequence & Order of Operations

When the application boots up, Optimizely processes model synchronization in a specific order:

| Phase | Action | Description |
| --- | --- | --- |
| **1. Startup Scan** | GUID Resolution | Optimizely scans assemblies for models marked with `[ContentType]`. It uses the GUID to locate the existing database record. |
| **2. Migration Execution** | `MigrationStep` | The system executes pending `MigrationStep` classes. Old type/property names are mapped to the new schema targets in the database. |
| **3. Database Sync** | Schema Commit | Database entries, property data tables, and content instances are updated to reflect the new system names without data loss. |

---

## 5. Key Risks & Best Practices

* **Do not modify GUIDs during refactoring:** Changing the GUID causes Optimizely to treat the renamed class as a brand-new content type, leaving existing database content orphaned.
* **Database Backups:** Always run migration code in a non-production environment first and take a database backup prior to deploying to Production.
* **Deployment Cleanup:** Once a `MigrationStep` has executed successfully across all environments (Dev, Test, Prod), it can be retained in source control for historical tracking or cleaned up according to team policy.

---

## 6. Companion Code Samples

- [promo-block-migration.cs](promo-block-migration.cs): Full implementation of `RefactorPromoBlockMigration`, the updated `PromoBlock` with preserved GUID, and the Razor view.
- [MigrationStepVerificationTests.cs](MigrationStepVerificationTests.cs): Automated xUnit test fixture verifying `MigrationStep` declarations and GUID attribute retention.

