<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                exclude-result-prefixes="#all">

  <xsl:include href="evaluate.xsl"/>
  <xsl:include href="layout.xsl"/>

  <xsl:template name="get-eml-gbif-configuration">
    <xsl:copy-of select="document('config-editor.xml')"/>
  </xsl:template>

  <xsl:template name="dispatch-eml-gbif">
    <xsl:param name="base" as="node()"/>
    <xsl:param name="overrideLabel" as="xs:string?" required="no" select="''"/>
    <xsl:param name="refToDelete" as="node()?" required="no"/>
    <xsl:param name="config" as="node()?" required="no"/>

    <xsl:apply-templates mode="mode-eml-gbif" select="$base">
      <xsl:with-param name="overrideLabel" select="$overrideLabel"/>
      <xsl:with-param name="refToDelete" select="$refToDelete"/>
      <xsl:with-param name="config" select="$config"/>
    </xsl:apply-templates>
  </xsl:template>
</xsl:stylesheet>
