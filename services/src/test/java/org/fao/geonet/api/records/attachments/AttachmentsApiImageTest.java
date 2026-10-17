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

package org.fao.geonet.api.records.attachments;

import org.junit.Test;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class AttachmentsApiImageTest {
    @Test
    public void undecodableImageReturnsUnsupportedMediaType() {
        byte[] invalidImage = "not an image".getBytes(StandardCharsets.UTF_8);
        MockHttpServletResponse response = resize(invalidImage, "invalid.jpg", 100);

        assertEquals(415, response.getStatus());
        assertEquals("Attachment cannot be decoded as an image", response.getErrorMessage());
        assertEquals(0, response.getContentAsByteArray().length);
    }

    @Test
    public void truncatedPngReturnsUnsupportedMediaType() {
        byte[] truncatedPng = {(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10};
        MockHttpServletResponse response = resize(truncatedPng, "truncated.png", 100);

        assertEquals(415, response.getStatus());
        assertEquals(0, response.getContentAsByteArray().length);
    }

    @Test
    public void validImageStillProducesResizedPng() throws Exception {
        ByteArrayOutputStream input = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(8, 4, BufferedImage.TYPE_INT_RGB), "png", input);

        MockHttpServletResponse response = resize(input.toByteArray(), "valid.png", 4);

        assertEquals(200, response.getStatus());
        assertEquals("image/png", response.getContentType());
        BufferedImage image = ImageIO.read(new ByteArrayInputStream(response.getContentAsByteArray()));
        assertNotNull(image);
        assertEquals(4, image.getWidth());
        assertEquals(2, image.getHeight());
    }

    private MockHttpServletResponse resize(byte[] image, String filename, int size) {
        MockHttpServletResponse response = new MockHttpServletResponse();
        ReflectionTestUtils.invokeMethod(new AttachmentsApi(), "serveResizedImage",
            new ByteArrayResource(image), "record-uuid", filename, "original-etag", size, response);
        return response;
    }
}
