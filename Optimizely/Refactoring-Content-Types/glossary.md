# Architectural Glossary: Optimizely CMS Content Type Refactoring

This glossary disambiguates code-first schema evolution, database mapping tables, and startup synchronization mechanics across Optimizely CMS, preventing confusion between identity anchoring (GUIDs), system names, and runtime property descriptors.

---

### Section 1: Schema Mapping & Identity Architecture

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **Model GUID** | Identity Layer | An immutable 128-bit integer declared in the `[ContentType(GUID = "...")]` attribute that serves as the permanent primary link to the `tblContentType` database record. | **NOT** a generated surrogate key; it must never be regenerated during a rename or refactoring operation. |
| **MigrationStep** | Startup Engine | A fluent API class inheriting from `EPiServer.DataAbstraction.Migration.MigrationStep` executed automatically during application boot to map historical names via `UsedToBeNamed`. | **NOT** an EF Core migration or raw SQL script; it operates within Optimizely's internal content repository metadata engine. |
| **System Name** | Schema Layer | The technical identifier used by Optimizely to locate content types and property definitions (`ContentType.Name`), distinct from the editor-facing `DisplayName`. | **NOT** the C# class name, although by default it matches the class name unless overridden. |
| **Property Definition ID** | Database Layer | The internal numeric identity in `tblPropertyDefinition` linking stored content rows in `tblContentProperty` to a specific model field. | **NOT** tied directly to C# property names; it survives property renaming when mapped via `MigrationStep`. |

---

### Section 2: Synchronisation Lifecycle & Execution Mechanics

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **Type Scanning** | Runtime Initialisation | Assembly reflection phase where Optimizely discovers classes inheriting from `ContentData` and decorated with `[ContentType]`. | **NOT** dynamic runtime compilation; scanning occurs once per application startup. |
| **Schema Commit** | Database Layer | Phase where discovered model changes and migration mappings are committed to database schema tables. | **NOT** a destructive schema reset; it preserves untouched existing rows. |
| **Content Copy Migration** | Data Transformation | Explicit programmatic iteration over content instances using `IContentRepository` to transform values when changing data types (e.g., `string` to `XhtmlString`). | **NOT** handled automatically by `MigrationStep`, which only supports renaming existing structures. |

---

### Section 3: Governance, Forensics & Failure Modes

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **Orphaned Content Type** | Database Decay | A database record in `tblContentType` that has no matching C# class in the active compiled assemblies, leaving existing pages inaccessible. | **NOT** an automatically deleted record; Optimizely preserves orphaned rows to prevent accidental data loss. |
| **Property Desync** | Editorial Fault | A state where a C# property is renamed without `UsedToBeNamed`, causing Optimizely to instantiate a new empty property while original values remain trapped under the historical property ID. | **NOT** data deletion; data persists in the database but cannot be addressed by templates. |
