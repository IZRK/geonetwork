<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="2.0" exclude-result-prefixes="#all">

  <!-- Keep every classification, including nested taxa, without repeating the
       rank for every name. Group by lineage as well so hierarchy is not lost. -->
  <xsl:template name="eml-taxonomy">
    <xsl:param name="coverage"/>
    <xsl:for-each select="$coverage">
      <xsl:for-each select="generalTaxonomicCoverage[normalize-space(.) != '']">
        <p><xsl:value-of select="normalize-space(.)"/></p>
      </xsl:for-each>
      <div class="izrk-taxonomy">
        <xsl:for-each-group select=".//taxonomicClassification[normalize-space(taxonRankValue) != ''
                                    or normalize-space(taxonRankName) != '' or commonName or taxonId]"
                            group-by="lower-case(normalize-space(taxonRankName))">
          <div class="izrk-taxon-rank">
            <h3>
              <xsl:value-of select="if (current-grouping-key() != '')
                                    then normalize-space(taxonRankName) else 'Unspecified rank'"/>
              <small> (<xsl:value-of select="count(current-group())"/>)</small>
            </h3>
            <xsl:for-each-group select="current-group()"
                                group-by="string-join(for $p in ancestor::taxonomicClassification
                                          return concat(normalize-space($p/taxonRankName), ': ',
                                                        normalize-space($p/taxonRankValue)), ' / ')">
              <xsl:if test="current-grouping-key() != ''">
                <p class="izrk-taxon-lineage"><xsl:value-of select="current-grouping-key()"/></p>
              </xsl:if>
              <ul class="izrk-taxon-list">
                <xsl:for-each select="current-group()">
                  <li>
                    <span class="izrk-taxon-name"><xsl:value-of select="normalize-space(taxonRankValue)"/></span>
                    <xsl:for-each select="commonName[normalize-space(.) != '']">
                      <span class="izrk-taxon-detail"> (<xsl:value-of select="normalize-space(.)"/>)</span>
                    </xsl:for-each>
                    <xsl:for-each select="taxonId[normalize-space(.) != '']">
                      <span class="izrk-taxon-detail"> [<xsl:choose>
                        <xsl:when test="matches(normalize-space(.), '^https?://')">
                          <a href="{normalize-space(.)}"><xsl:value-of select="normalize-space(.)"/></a>
                        </xsl:when>
                        <xsl:otherwise><xsl:value-of select="normalize-space(.)"/></xsl:otherwise>
                      </xsl:choose><xsl:if test="@provider">; <xsl:value-of select="@provider"/></xsl:if>]</span>
                    </xsl:for-each>
                    <xsl:if test="@id"><span class="izrk-taxon-detail"> [ID: <xsl:value-of select="@id"/>]</span></xsl:if>
                    <xsl:if test="position() != last()"><xsl:text>; </xsl:text></xsl:if>
                  </li>
                </xsl:for-each>
              </ul>
            </xsl:for-each-group>
          </div>
        </xsl:for-each-group>
      </div>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
