<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                version="2.0" exclude-result-prefixes="#all">
  <xsl:include href="base.xsl"/>
  <xsl:include href="../../../iso19115-3.2018/formatter/citation/common.xsl"/>
  <xsl:output omit-xml-declaration="yes" method="xml" indent="yes" encoding="UTF-8"/>
  <xsl:variable name="schemaStrings" select="/root/schemas/eml-gbif/strings"/>

  <xsl:template match="/">
    <xsl:variable name="citationInfo">
      <xsl:call-template name="get-eml-citation">
        <xsl:with-param name="metadata" select="/root/eml:eml"/>
        <xsl:with-param name="uuid" select="/root/info/record/uuid"/>
        <xsl:with-param name="nodeUrl" select="/root/gui/nodeUrl"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:apply-templates mode="citation" select="$citationInfo"/>
  </xsl:template>
</xsl:stylesheet>
