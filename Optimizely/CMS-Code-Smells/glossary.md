# Architectural Glossary: Optimizely CMS Code Smells & Content Debt

This glossary disambiguates content modelling anti-patterns, editorial security constraints, and programmatic cleanup APIs across Optimizely CMS, preventing confusion between domain models, presentation blocks, and environment coupling.

---

### Section 1: Content Modelling & Block Topology

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **Block Proliferation** | Anti-Pattern | Cloning existing `BlockData` classes to achieve minor visual styling differences, duplicating identical data fields across multiple schemas. | **NOT** modular component design; true components reuse the same data model and vary presentation via display options. |
| **Domain Model Block** | Architecture Layer | A unified `BlockData` definition (e.g. `PersonBlock`) representing an authoritative entity regardless of layout context. | **NOT** a page-specific container or single-use editorial wrapper. |
| **Display Option** | Presentation Layer | Built-in Optimizely rendering mechanism allowing editors to apply pre-configured CSS wrappers or layout templates to a single block type. | **NOT** a schema change; it alters the wrapper tag or template descriptor without creating database fields. |
| **Singleton Settings Block** | Configuration Layer | A dedicated `BlockData` instance linked to the site start page exposing strongly-typed `PageReference` and `ContentReference` properties. | **NOT** hardcoded configuration in `appsettings.json` or raw database IDs. |

---

### Section 2: Editorial Security & Markup Governance

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **XhtmlString Sanitisation** | Editorial Security | Enforcing rules in `TinyMceConfiguration` to strip proprietary formatting (`mso-` attributes, invalid styles) and enforce element allow-lists. | **NOT** output-encoding in Razor; sanitisation cleans content at input time before database commit. |
| **PasteFromWord Clean** | Ingestion Layer | TinyMCE configuration setting (`paste_from_word_import: "clean"`) that intercepts clipboard content from Word or Teams, removing inline presentation markup. | **NOT** a plain-text-only paste; it preserves structural HTML tags like headings and lists while stripping styling. |
| **Stored XSS** | Vulnerability | Malicious scripts injected into unescaped rich-text fields by compromised accounts or pasted embeds, executing in the browser of downstream visitors. | **NOT** reflected XSS; stored XSS persists in `tblContentProperty` rows until cleansed. |

---

### Section 3: Diagnostic Telemetry & Cleanup Forensics

| Term | Scope / Level | Mechanism / Definition | Disambiguation / What It Is NOT |
| :--- | :--- | :--- | :--- |
| **IContentModelUsage** | Diagnostic API | Optimizely service that scans the database and reports every instance and location where a specific content type is referenced. | **NOT** a content deletion tool; it only reports usage metrics for dependency analysis. |
| **IContentSoftLinkRepository** | Link Forensics | Optimizely service that inspects soft links and uncompiled references within content fields, identifying broken links or orphaned media. | **NOT** hard foreign-key constraint checking; it parses string references and URL fragments. |
| **Orphaned Property Definition** | Schema Debt | A column in `tblPropertyDefinition` marked as "From Code = No", lingering in the database after its C# property has been deleted from compiled assemblies. | **NOT** automatically purged by the CMS; it requires manual admin removal or programmatic cleanup. |
