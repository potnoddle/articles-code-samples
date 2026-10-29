using System;
using System.Collections.Generic;
using System.Linq;
using EPiServer.Core;
using EPiServer.DataAbstraction;

namespace MyProject.Services.Hygiene
{
    public interface IContentHygieneAuditService
    {
        IEnumerable<string> FindUnusedContentTypes();
        IEnumerable<SoftLink> FindBrokenSoftLinks(ContentReference contentLink);
    }

    public class ContentHygieneAuditService : IContentHygieneAuditService
    {
        private readonly IContentTypeRepository _contentTypeRepository;
        private readonly IContentModelUsage _contentModelUsage;
        private readonly IContentSoftLinkRepository _contentSoftLinkRepository;

        public ContentHygieneAuditService(
            IContentTypeRepository contentTypeRepository,
            IContentModelUsage contentModelUsage,
            IContentSoftLinkRepository contentSoftLinkRepository)
        {
            _contentTypeRepository = contentTypeRepository;
            _contentModelUsage = contentModelUsage;
            _contentSoftLinkRepository = contentSoftLinkRepository;
        }

        /// <summary>
        /// Identifies content types defined in C# that have zero instances stored in the database.
        /// </summary>
        public IEnumerable<string> FindUnusedContentTypes()
        {
            var unusedTypes = new List<string>();
            var allContentTypes = _contentTypeRepository.List();

            foreach (var contentType in allContentTypes)
            {
                var usages = _contentModelUsage.ListContentOfContentType(contentType);
                if (usages == null || !usages.Any())
                {
                    unusedTypes.Add(contentType.Name);
                }
            }

            return unusedTypes;
        }

        /// <summary>
        /// Finds broken references or soft links within rich text fields on the specified content item.
        /// </summary>
        public IEnumerable<SoftLink> FindBrokenSoftLinks(ContentReference contentLink)
        {
            var links = _contentSoftLinkRepository.Load(contentLink, true);
            return links.Where(link => link.ReferencedContentLink == ContentReference.EmptyReference);
        }
    }
}
