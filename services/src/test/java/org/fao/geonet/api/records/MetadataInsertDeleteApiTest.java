/*
 * Copyright (C) 2001-2026 Food and Agriculture Organization of the
 * United Nations (FAO-UN), United Nations World Food Programme (WFP)
 * and United Nations Environment Programme (UNEP)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 */

package org.fao.geonet.api.records;

import org.junit.Test;

import java.util.Locale;

public class MetadataInsertDeleteApiTest {

    @Test
    public void checkGroupIsWorkspaceAllowsMissingOptionalGroup() throws Exception {
        MetadataInsertDeleteApi api = new MetadataInsertDeleteApi();

        api.checkGroupIsWorkspace(null, Locale.ROOT);
        api.checkGroupIsWorkspace("", Locale.ROOT);
        api.checkGroupIsWorkspace("   ", Locale.ROOT);
    }
}
