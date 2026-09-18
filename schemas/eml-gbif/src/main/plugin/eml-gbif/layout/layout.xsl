<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                xmlns:gn="http://www.fao.org/geonetwork"
                xmlns:gn-fn-metadata="http://geonetwork-opensource.org/xsl/functions/metadata"
                exclude-result-prefixes="#all">

  <xsl:template name="get-eml-gbif-is-service">
    <xsl:value-of select="false()"/>
  </xsl:template>

  <xsl:template name="get-eml-gbif-title">
    <xsl:value-of select="($metadata/eml:eml/dataset/title[1], $metadata/dataset/title[1])[1]"/>
  </xsl:template>

  <xsl:template name="get-eml-gbif-language">
    <xsl:value-of select="(($metadata/eml:eml/dataset/language[1], $metadata/dataset/language[1])[1], 'eng')[1]"/>
  </xsl:template>

  <xsl:template name="get-eml-gbif-other-languages"/>

  <xsl:template name="get-eml-gbif-other-languages-as-json">
    <xsl:text>[]</xsl:text>
  </xsl:template>

  <xsl:template name="get-eml-gbif-online-source-config"/>

  <xsl:template name="get-eml-gbif-extents-as-json">
    <xsl:text>[]</xsl:text>
  </xsl:template>

  <xsl:template mode="get-formats-as-json" match="eml:eml|*[local-name() = 'eml']"/>

  <xsl:template mode="mode-eml-gbif" match="gn:*|@*"/>

  <xsl:template mode="mode-eml-gbif" match="eml:eml|*[local-name() = 'eml']" priority="200">
    <xsl:call-template name="render-boxed-element">
      <xsl:with-param name="label" select="gn-fn-metadata:getLabel($schema, name(.), $labels)/label"/>
      <xsl:with-param name="cls" select="'eml-gbif-root'"/>
      <xsl:with-param name="xpath" select="gn-fn-metadata:getXPath(.)"/>
      <xsl:with-param name="subTreeSnippet">
        <xsl:apply-templates mode="mode-eml-gbif" select="*"/>
      </xsl:with-param>
      <xsl:with-param name="editInfo" select="gn:element"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="mode-eml-gbif" match="*[not(self::gn:*)][gn:child]" priority="150">
    <xsl:variable name="xpath" select="gn-fn-metadata:getXPath(.)"/>
    <xsl:call-template name="render-boxed-element">
      <xsl:with-param name="label" select="gn-fn-metadata:getLabel($schema, name(.), $labels, name(..), '', $xpath)/label"/>
      <xsl:with-param name="cls" select="local-name()"/>
      <xsl:with-param name="xpath" select="$xpath"/>
      <xsl:with-param name="subTreeSnippet">
        <xsl:apply-templates mode="mode-eml-gbif" select="*"/>
      </xsl:with-param>
      <xsl:with-param name="editInfo" select="gn:element"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="mode-eml-gbif"
                match="*[not(self::gn:*)][not(*) or not(*[not(self::gn:*)])]"
                priority="100">
    <xsl:variable name="xpath" select="gn-fn-metadata:getXPath(.)"/>
    <xsl:variable name="labelConfig" select="gn-fn-metadata:getLabel($schema, name(.), $labels, name(..), '', $xpath)"/>

    <xsl:call-template name="render-element">
      <xsl:with-param name="label" select="$labelConfig"/>
      <xsl:with-param name="value" select="."/>
      <xsl:with-param name="cls" select="local-name()"/>
      <xsl:with-param name="xpath" select="$xpath"/>
      <xsl:with-param name="type" select="gn-fn-metadata:getFieldType($editorConfig, name(), '', $xpath)"/>
      <xsl:with-param name="name" select="if ($isEditing) then string(gn:element/@ref) else ''"/>
      <xsl:with-param name="editInfo" select="gn:element"/>
      <xsl:with-param name="parentEditInfo" select="../gn:element"/>
      <xsl:with-param name="listOfValues" select="gn-fn-metadata:getHelper($labelConfig/helper, .)"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="mode-eml-gbif" match="*[not(self::gn:*)]" priority="50">
    <xsl:variable name="xpath" select="gn-fn-metadata:getXPath(.)"/>
    <xsl:call-template name="render-boxed-element">
      <xsl:with-param name="label" select="gn-fn-metadata:getLabel($schema, name(.), $labels, name(..), '', $xpath)/label"/>
      <xsl:with-param name="cls" select="local-name()"/>
      <xsl:with-param name="xpath" select="$xpath"/>
      <xsl:with-param name="subTreeSnippet">
        <xsl:apply-templates mode="mode-eml-gbif" select="*"/>
      </xsl:with-param>
      <xsl:with-param name="editInfo" select="gn:element"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="mode-eml-gbif" match="gn:child" priority="2000">
    <xsl:if test="$isEditing and not($isFlatMode)">
      <xsl:call-template name="render-element-to-add">
        <xsl:with-param name="childEditInfo" select="."/>
        <xsl:with-param name="parentEditInfo" select="../gn:element"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
