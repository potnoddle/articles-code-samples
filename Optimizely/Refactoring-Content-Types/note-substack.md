**Renaming a C# property in Optimizely CMS without a migration step will silently drop content across production pages.**

Code-first modelling is Optimizely's greatest convenience, but IDE refactoring tools treat compiled classes as isolated code rather than active database schema contracts.

**1. GUID preservation is non-negotiable.**
The GUID inside `[ContentType]` is the permanent anchor connecting your C# class to the database. If you rename a class but regenerate its GUID, Optimizely treats it as a brand-new entity, stranding existing content in orphaned database records.

**2. Property renames require MigrationStep.**
The CMS cannot guess that your new `Summary` property replaces the legacy `LeadText` field. Without declaring `UsedToBeNamed` in a `MigrationStep` class, the framework creates a blank database definition, leaving editors staring at empty fields.

**3. Startup execution handles the migration in place.**
Because `MigrationStep` execution runs before schema validation commits during boot, database rows update in place without dropping columns or copying tables.

Full breakdown and zero-downtime refactoring playbook coming soon — covering GUID stability, migration testing harnesses, and database sync sequences.

Have you ever discovered an orphaned property that emptied production content after a release? 💬 Share with your Optimizely and .NET teams. ♻️
