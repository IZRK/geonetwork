package org.fao.geonet.api.records;

import org.fao.geonet.api.records.model.related.RelatedItemType;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class MetadataUtilsTest {
    private static final String CURRENT_UUID = "c7710542-10ea-43e8-b4d7-9bdd3d559905";
    private static final String OTHER_UUID = "842f9143-fd7d-452c-96b4-425ca1281642";

    @Test
    public void reverseRelationsExcludeTheCurrentRecord() {
        assertTrue(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.hasfeaturecats, CURRENT_UUID, CURRENT_UUID));
        assertTrue(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.associated, CURRENT_UUID, CURRENT_UUID));
        assertTrue(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.children, CURRENT_UUID, CURRENT_UUID));
        assertTrue(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.services, CURRENT_UUID, CURRENT_UUID));
        assertTrue(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.hassources, CURRENT_UUID, CURRENT_UUID));
        assertFalse(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.hasfeaturecats, CURRENT_UUID, OTHER_UUID));
    }

    @Test
    public void directRelationsAndVersionsAreUnchanged() {
        assertFalse(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.fcats, CURRENT_UUID, CURRENT_UUID));
        assertFalse(MetadataUtils.isSelfReverseRelation(
            RelatedItemType.versions, CURRENT_UUID, CURRENT_UUID));
    }
}
