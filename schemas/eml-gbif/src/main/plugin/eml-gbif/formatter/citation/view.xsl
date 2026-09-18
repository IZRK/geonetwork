<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                version="2.0"
                exclude-result-prefixes="#all">

  <xsl:include href="../taxonomy.xsl"/>

  <xsl:output omit-xml-declaration="yes"
              method="xhtml"
              doctype-system="html"
              indent="yes"
              encoding="UTF-8"/>

  <xsl:variable name="metadata" select="/root/eml:eml"/>
  <xsl:variable name="uuid" select="/root/info/record/uuid"/>

  <xsl:template match="/">
    <div class="container-fluid gn-metadata-view gn-schema-eml-gbif">
      <article id="{$uuid}" class="gn-md-view gn-metadata-display">
        <header>
          <h1>
            <i class="fa fa-fw gn-icon-dataset"></i>
            <xsl:value-of select="$metadata/dataset/title"/>
          </h1>
          <xsl:if test="normalize-space($metadata/dataset/abstract) != ''">
            <div class="gn-abstract">
              <xsl:call-template name="paragraphs">
                <xsl:with-param name="node" select="$metadata/dataset/abstract"/>
              </xsl:call-template>
            </div>
          </xsl:if>
        </header>

        <section class="gn-md-section">
          <h2>Metadata</h2>
          <xsl:call-template name="field">
            <xsl:with-param name="label" select="'Metadata Identifier'"/>
            <xsl:with-param name="value" select="$metadata/dataset/alternateIdentifier[1]"/>
          </xsl:call-template>
          <xsl:call-template name="field">
            <xsl:with-param name="label" select="'Publication Date'"/>
            <xsl:with-param name="value" select="$metadata/dataset/pubDate"/>
          </xsl:call-template>
          <xsl:call-template name="field">
            <xsl:with-param name="label" select="'Resource Language'"/>
            <xsl:with-param name="value" select="$metadata/dataset/language"/>
          </xsl:call-template>
        </section>

        <xsl:if test="$metadata/dataset/creator">
          <section class="gn-md-section">
            <h2>Dataset Creators</h2>
            <xsl:for-each select="$metadata/dataset/creator">
              <div class="gn-md-section">
                <xsl:call-template name="agent"/>
              </div>
            </xsl:for-each>
          </section>
        </xsl:if>

        <xsl:if test="$metadata/dataset/contact">
          <section class="gn-md-section">
            <h2>Dataset Contacts</h2>
            <xsl:for-each select="$metadata/dataset/contact">
              <div class="gn-md-section">
                <xsl:call-template name="agent"/>
              </div>
            </xsl:for-each>
          </section>
        </xsl:if>

        <xsl:if test="$metadata/dataset/keywordSet/keyword">
          <section class="gn-md-section">
            <h2>Keywords</h2>
            <xsl:for-each select="$metadata/dataset/keywordSet">
              <dl>
                <dt>
                  <xsl:value-of select="normalize-space(keywordThesaurus)"/>
                </dt>
                <dd>
                  <xsl:for-each select="keyword[normalize-space(.) != '']">
                    <xsl:if test="position() &gt; 1">, </xsl:if>
                    <xsl:value-of select="normalize-space(.)"/>
                  </xsl:for-each>
                </dd>
              </dl>
            </xsl:for-each>
          </section>
        </xsl:if>

        <xsl:if test="$metadata/dataset/coverage/geographicCoverage">
          <section class="gn-md-section">
            <h2>Geographic Coverage</h2>
            <xsl:for-each select="$metadata/dataset/coverage/geographicCoverage">
              <xsl:call-template name="field">
                <xsl:with-param name="label" select="'Geographic Description'"/>
                <xsl:with-param name="value" select="geographicDescription"/>
              </xsl:call-template>
              <xsl:for-each select="boundingCoordinates">
                <xsl:call-template name="field">
                  <xsl:with-param name="label" select="'West Bounding Coordinate'"/>
                  <xsl:with-param name="value" select="westBoundingCoordinate"/>
                </xsl:call-template>
                <xsl:call-template name="field">
                  <xsl:with-param name="label" select="'East Bounding Coordinate'"/>
                  <xsl:with-param name="value" select="eastBoundingCoordinate"/>
                </xsl:call-template>
                <xsl:call-template name="field">
                  <xsl:with-param name="label" select="'North Bounding Coordinate'"/>
                  <xsl:with-param name="value" select="northBoundingCoordinate"/>
                </xsl:call-template>
                <xsl:call-template name="field">
                  <xsl:with-param name="label" select="'South Bounding Coordinate'"/>
                  <xsl:with-param name="value" select="southBoundingCoordinate"/>
                </xsl:call-template>
              </xsl:for-each>
            </xsl:for-each>
          </section>
        </xsl:if>

        <xsl:if test="$metadata/dataset/coverage/taxonomicCoverage">
          <section class="gn-md-section">
            <h2>Taxonomic Coverage</h2>
            <xsl:call-template name="eml-taxonomy">
              <xsl:with-param name="coverage" select="$metadata/dataset/coverage/taxonomicCoverage"/>
            </xsl:call-template>
          </section>
        </xsl:if>
      </article>
    </div>
  </xsl:template>

  <xsl:template name="agent">
    <xsl:call-template name="field">
      <xsl:with-param name="label" select="'Individual Name'"/>
      <xsl:with-param name="value" select="individualName"/>
    </xsl:call-template>
    <xsl:call-template name="field">
      <xsl:with-param name="label" select="'Organization Name'"/>
      <xsl:with-param name="value" select="organizationName"/>
    </xsl:call-template>
    <xsl:call-template name="field">
      <xsl:with-param name="label" select="'Email'"/>
      <xsl:with-param name="value" select="electronicMailAddress"/>
    </xsl:call-template>
    <xsl:call-template name="field">
      <xsl:with-param name="label" select="'Role'"/>
      <xsl:with-param name="value" select="role"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="field">
    <xsl:param name="label"/>
    <xsl:param name="value"/>
    <xsl:if test="normalize-space($value) != ''">
      <dl>
        <dt>
          <xsl:value-of select="$label"/>
        </dt>
        <dd>
          <xsl:value-of select="normalize-space($value)"/>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template name="paragraphs">
    <xsl:param name="node"/>
    <xsl:choose>
      <xsl:when test="$node/para">
        <xsl:for-each select="$node/para">
          <p>
            <xsl:value-of select="normalize-space(.)"/>
          </p>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise>
        <p>
          <xsl:value-of select="normalize-space($node)"/>
        </p>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
