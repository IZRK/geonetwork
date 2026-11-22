package de.fzi.dbs.xml.transform;

import org.junit.Test;

import javax.xml.transform.Transformer;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertTrue;

public class CachingTransformerFactoryTest {
    @Test(timeout = 15000)
    public void cacheAccessAcrossFactoriesDoesNotHang() throws Exception {
        ExecutorService workers = Executors.newFixedThreadPool(12, task -> {
            Thread thread = new Thread(task);
            thread.setDaemon(true);
            return thread;
        });
        CountDownLatch start = new CountDownLatch(1);
        List<Future<?>> results = new ArrayList<>();
        try {
            for (int worker = 0; worker < 12; worker++) {
                results.add(workers.submit(() -> {
                    CachingTransformerFactory factory = new CachingTransformerFactory();
                    start.await();
                    for (int iteration = 0; iteration < 10000; iteration++) {
                        factory.read("uncached-stylesheet");
                        factory.clearCache();
                    }
                    return null;
                }));
            }
            start.countDown();
            for (Future<?> result : results) {
                result.get(10, TimeUnit.SECONDS);
            }
        } finally {
            workers.shutdownNow();
        }
    }

    @Test
    public void cachedStylesheetRefreshesAcrossFactories() throws Exception {
        Path stylesheet = Files.createTempFile("cached-transformer-", ".xsl");
        CachingTransformerFactory first = new CachingTransformerFactory();
        CachingTransformerFactory second = new CachingTransformerFactory();
        try {
            writeStylesheet(stylesheet, "before");
            assertTrue(transform(first, stylesheet).contains("before"));
            assertTrue(transform(second, stylesheet).contains("before"));
            long modified = Files.getLastModifiedTime(stylesheet).toMillis();
            writeStylesheet(stylesheet, "after");
            Files.setLastModifiedTime(stylesheet, FileTime.fromMillis(modified + 2000));
            assertTrue(transform(second, stylesheet).contains("after"));
            first.clearCache();
            assertTrue(transform(first, stylesheet).contains("after"));
        } finally {
            first.clearCache();
            Files.deleteIfExists(stylesheet);
        }
    }

    private static void writeStylesheet(Path path, String value) throws Exception {
        Files.write(path, ("<xsl:stylesheet version=\"1.0\" "
            + "xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">"
            + "<xsl:template match=\"/\"><result>" + value
            + "</result></xsl:template></xsl:stylesheet>").getBytes(StandardCharsets.UTF_8));
    }

    private static String transform(CachingTransformerFactory factory, Path stylesheet) throws Exception {
        Transformer transformer = factory.newTransformer(new StreamSource(stylesheet.toFile()));
        StringWriter output = new StringWriter();
        transformer.transform(new StreamSource(new StringReader("<record/>")), new StreamResult(output));
        return output.toString();
    }
}
