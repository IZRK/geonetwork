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

import org.fao.geonet.api.tools.i18n.LanguageUtils;
import org.fao.geonet.domain.Group;
import org.fao.geonet.repository.GroupRepository;
import org.junit.Before;
import org.junit.Test;
import org.springframework.test.util.ReflectionTestUtils;

import javax.servlet.http.HttpServletRequest;
import java.util.Collections;
import java.util.Locale;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class MetadataInsertDeleteApiTest {
    private MetadataInsertDeleteApi api;
    private GroupRepository groups;

    @Before
    public void setUp() {
        api = new MetadataInsertDeleteApi();
        groups = mock(GroupRepository.class);
        ReflectionTestUtils.setField(api, "groupRepository", groups);
    }

    @Test
    public void optionalBlankGroupHasNoWorkspace() throws Exception {
        assertNull(api.validateAndNormalizeGroup(null, Locale.ROOT, false));
        assertNull(api.validateAndNormalizeGroup("", Locale.ROOT, false));
        assertNull(api.validateAndNormalizeGroup("   ", Locale.ROOT, false));
    }

    @Test
    public void requiredBlankGroupIsRejected() {
        assertThrows(IllegalArgumentException.class,
            () -> api.validateAndNormalizeGroup(" \t ", Locale.ROOT, true));
    }

    @Test
    public void workspaceGroupIsCanonicalized() throws Exception {
        Group workspace = mock(Group.class);
        when(workspace.isWorkspace()).thenReturn(true);
        when(groups.findById(42)).thenReturn(java.util.Optional.of(workspace));

        assertEquals("42", api.validateAndNormalizeGroup(" 0042 ", Locale.ROOT, true));
        assertEquals("42", api.validateAndNormalizeGroup("\t42\n", Locale.ROOT, false));
    }

    @Test
    public void malformedGroupIsRejectedBeforeImport() {
        HttpServletRequest request = mockRequest();

        assertThrows(NumberFormatException.class, () -> api.insert(
            null, null, null, null, false, false, false, null, "invalid", null,
            false, null, null, false, null, request));
        assertThrows(NumberFormatException.class, () -> api.insertFile(
            null, null, null, "invalid", null, false, false, false,
            null, null, null, false, request));
        assertThrows(NumberFormatException.class, () -> api.insertOgcMapContextFile(
            null, null, null, null, null, null, null, null, null, false,
            null, "invalid", null, request));
    }

    @Test
    public void duplicateRequiresGroupBeforeLookingUpSourceRecord() {
        HttpServletRequest request = mockRequest();
        assertThrows(IllegalArgumentException.class, () -> api.create(
            null, null, null, "   ", false, null, false, false, false,
            null, request));
    }

    @Test
    public void mapImportTreatsWhitespaceAsMissingOptionalGroup() {
        HttpServletRequest request = mockRequest();
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
            () -> api.insertOgcMapContextFile(null, null, null, null, null,
                null, null, null, null, false, null, "   ", null, request));
        assertEquals("A context as XML or a remote URL MUST be provided.", error.getMessage());
    }

    private HttpServletRequest mockRequest() {
        HttpServletRequest request = mock(HttpServletRequest.class);
        when(request.getLocales()).thenReturn(Collections.enumeration(
            Collections.singletonList(Locale.ROOT)));
        LanguageUtils languages = mock(LanguageUtils.class);
        when(languages.parseAcceptLanguage(any(java.util.Enumeration.class)))
            .thenReturn(Locale.ROOT);
        ReflectionTestUtils.setField(api, "languageUtils", languages);
        return request;
    }
}
