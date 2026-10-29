// Companion code for "Refactoring Optimizely CMS Content Types Without Data Loss"
// Scenario: TeaserBlock -> PromoBlock, LeadText -> Summary, original GUID preserved.

// ---------------------------------------------------------------
// Infrastructure/Migrations/RefactorPromoBlockMigration.cs
// ---------------------------------------------------------------
using EPiServer.DataAbstraction.Migration;

namespace MyProject.Infrastructure.Migrations
{
    // Discovered automatically at startup; no registration required.
    public class RefactorPromoBlockMigration : MigrationStep
    {
        public override void AddChanges()
        {
            ContentType("PromoBlock")
                .UsedToBeNamed("TeaserBlock");

            // Property mappings chain from the NEW content type name.
            ContentType("PromoBlock")
                .Property("Summary")
                .UsedToBeNamed("LeadText");
        }
    }
}

// ---------------------------------------------------------------
// Models/Blocks/PromoBlock.cs
// ---------------------------------------------------------------
using System.ComponentModel.DataAnnotations;
using EPiServer.Core;
using EPiServer.DataAnnotations;

namespace MyProject.Models.Blocks
{
    [ContentType(
        DisplayName = "Promotional Block",
        GUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890", // unchanged from TeaserBlock
        Description = "Promotional callout block used across marketing landing pages."
    )]
    public class PromoBlock : BlockData
    {
        [Display(
            Name = "Summary Text",
            Description = "Main promotional body text.",
            Order = 100
        )]
        public virtual XhtmlString Summary { get; set; } // was LeadText
    }
}

// ---------------------------------------------------------------
// Views/Shared/Blocks/PromoBlock.cshtml
// ---------------------------------------------------------------
// @model MyProject.Models.Blocks.PromoBlock
//
// <div class="promo-block">
//     @Html.PropertyFor(x => x.Summary)
// </div>
