using System.ComponentModel.DataAnnotations;
using EPiServer.Core;
using EPiServer.DataAnnotations;

namespace MyProject.Models.Blocks
{
    [ContentType(
        DisplayName = "Site Settings",
        GUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        Description = "Global site settings eliminating hardcoded content IDs.",
        AvailableInEditMode = false
    )]
    public class SiteSettingsBlock : BlockData
    {
        [Display(
            Name = "Search Results Page",
            Description = "Reference to the global search results page.",
            GroupName = "Navigation",
            Order = 100
        )]
        public virtual PageReference SearchPage { get; set; }

        [Display(
            Name = "Contact Us Page",
            Description = "Reference to the global contact page.",
            GroupName = "Navigation",
            Order = 110
        )]
        public virtual PageReference ContactPage { get; set; }

        [Display(
            Name = "Default Fallback Image",
            Description = "Used when an editorial article lacks a featured banner.",
            GroupName = "Media",
            Order = 200
        )]
        public virtual ContentReference DefaultFallbackImage { get; set; }
    }
}
