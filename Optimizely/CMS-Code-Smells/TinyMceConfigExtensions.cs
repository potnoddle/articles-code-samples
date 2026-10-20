using EPiServer.Cms.TinyMce.Core;
using Microsoft.Extensions.DependencyInjection;

namespace MyProject.Infrastructure.TinyMce
{
    public static class TinyMceConfigExtensions
    {
        public static IServiceCollection AddCustomTinyMceConfiguration(this IServiceCollection services)
        {
            services.Configure<TinyMceConfiguration>(config =>
            {
                config.Default()
                    // Strip MS Word formatting artifacts on paste
                    .AddSetting("paste_from_word_import", "clean")
                    // Enforce allowed HTML elements and attributes
                    .AddSetting("valid_elements", "p,h2,h3,h4,strong/b,em/i,ul,ol,li,a[href|target|rel],table,tr,td,th")
                    // Strip inline font and style properties
                    .AddSetting("invalid_styles", "color font-size font-family background")
                    .Toolbar("bold italic | bullist numlist | link unlink | table");
            });

            return services;
        }
    }
}
