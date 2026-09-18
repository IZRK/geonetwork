package org.fao.geonet.schema.emlgbif;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import org.fao.geonet.kernel.schema.SchemaPlugin;
import org.jdom.Namespace;

import java.util.Map;

public class EmlGbifSchemaPlugin extends SchemaPlugin {
    public static final String IDENTIFIER = "eml-gbif";

    public static final Namespace EML =
        Namespace.getNamespace("eml", "https://eml.ecoinformatics.org/eml-2.2.0");

    private static final ImmutableSet<Namespace> NAMESPACES = ImmutableSet.<Namespace>builder()
        .add(EML)
        .add(Namespace.getNamespace("stmml", "http://www.xml-cml.org/schema/stmml-1.2"))
        .add(Namespace.getNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance"))
        .build();

    private static final Map<String, Namespace> CSW_TYPE_NAMES = ImmutableMap.<String, Namespace>builder()
        .put("eml:eml", EML)
        .build();

    public EmlGbifSchemaPlugin() {
        super(IDENTIFIER, NAMESPACES);
    }

    @Override
    public Map<String, Namespace> getCswTypeNames() {
        return CSW_TYPE_NAMES;
    }
}
