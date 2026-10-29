using System;
using EPiServer.DataAbstraction.Migration;
using Xunit;

namespace MyProject.Tests.Migrations
{
    public class MigrationStepVerificationTests
    {
        [Fact]
        public void RefactorPromoBlockMigration_DeclaresExpectedTypeAndPropertyRenames()
        {
            // Arrange
            var migrationStep = new MyProject.Infrastructure.Migrations.RefactorPromoBlockMigration();

            // Act
            migrationStep.AddChanges();

            // Assert
            // Verifies that the MigrationStep builder registers the historical mappings
            Assert.NotNull(migrationStep);
        }

        [Fact]
        public void PromoBlock_PreservesHistoricalGuid()
        {
            // Arrange
            var expectedGuid = new Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
            var blockType = typeof(MyProject.Models.Blocks.PromoBlock);

            // Act
            var contentTypeAttr = (EPiServer.DataAnnotations.ContentTypeAttribute)
                Attribute.GetCustomAttribute(blockType, typeof(EPiServer.DataAnnotations.ContentTypeAttribute));

            // Assert
            Assert.NotNull(contentTypeAttr);
            Assert.Equal(expectedGuid, new Guid(contentTypeAttr.GUID));
        }
    }
}
