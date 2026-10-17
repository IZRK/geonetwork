<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:tax="http://geonetwork-opensource.org/izrk/taxonomy"
                version="2.0" exclude-result-prefixes="#all">

  <xsl:function name="tax:rank-order" as="xs:integer">
    <xsl:param name="rank"/>
    <xsl:sequence select="(index-of(('domain', 'kingdom', 'subkingdom', 'phylum', 'division',
      'subphylum', 'class', 'subclass', 'order', 'suborder', 'superfamily', 'family',
      'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'species', 'subspecies',
      'variety', 'form'), lower-case(normalize-space($rank))), 99)[1]"/>
  </xsl:function>

  <xsl:template name="eml-taxonomy">
    <xsl:param name="coverage"/>
    <xsl:for-each select="$coverage">
      <xsl:for-each select="generalTaxonomicCoverage[normalize-space(.) != '']">
        <p><xsl:value-of select="normalize-space(.)"/></p>
      </xsl:for-each>
      <xsl:variable name="tree">
        <xsl:call-template name="eml-taxon-merge">
          <xsl:with-param name="nodes" select="taxonomicClassification"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$tree/taxon">
        <div class="izrk-taxonomy">
          <xsl:if test="$tree/taxon[not(taxon)]">
            <p class="izrk-taxonomy-note">Parent relationships are not supplied for unlinked names; their ranks are shown from broadest to most specific.</p>
          </xsl:if>
          <details class="izrk-taxonomy-browser" open="open">
            <summary>Browse taxonomy <span class="izrk-taxon-count"><xsl:value-of select="count($tree//entry)"/> recorded entries</span></summary>
            <p class="izrk-taxonomy-help">Expand a group to explore its classification.</p>
            <div class="izrk-taxonomy-scroll" tabindex="0" role="region" aria-label="Taxonomic classification">
              <xsl:call-template name="eml-taxon-tree">
                <xsl:with-param name="nodes" select="$tree/taxon[taxon]"/>
              </xsl:call-template>
              <xsl:if test="$tree/taxon[not(taxon)]">
                <div class="izrk-taxon-unlinked">
                  <h4>Unlinked names</h4>
                  <xsl:call-template name="eml-taxon-tree">
                    <xsl:with-param name="nodes" select="$tree/taxon[not(taxon)]"/>
                  </xsl:call-template>
                </div>
              </xsl:if>
            </div>
          </details>
        </div>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <!-- Merge only siblings: an identically named genus in different families
       remains separate. Distinct explicit identifiers also remain separate. -->
  <xsl:template name="eml-taxon-merge">
    <xsl:param name="nodes"/>
    <xsl:for-each-group select="$nodes[normalize-space(.) != '' or @id]"
      group-by="concat(lower-case(normalize-space(taxonRankName)), '|',
        lower-case(normalize-space(taxonRankValue)), '|', @id, '|', string-join(taxonId, '|'))">
      <xsl:sort select="tax:rank-order(taxonRankName)" data-type="number"/>
      <xsl:sort select="lower-case(normalize-space(taxonRankValue))"/>
      <taxon rank="{normalize-space(taxonRankName)}" name="{normalize-space(taxonRankValue)}">
        <xsl:for-each select="current-group()
          [normalize-space(taxonRankName) != '' or normalize-space(taxonRankValue) != ''
           or commonName or taxonId or @id]">
          <entry><xsl:copy-of select="@* | *[not(self::taxonomicClassification)]"/></entry>
        </xsl:for-each>
        <xsl:call-template name="eml-taxon-merge">
          <xsl:with-param name="nodes" select="current-group()/taxonomicClassification"/>
        </xsl:call-template>
      </taxon>
    </xsl:for-each-group>
  </xsl:template>

  <xsl:template name="eml-taxon-tree">
    <xsl:param name="nodes"/>
    <xsl:param name="depth" select="0"/>
    <xsl:for-each select="$nodes[taxon]">
      <details class="izrk-taxon-branch" data-rank="{lower-case(@rank)}" data-name="{@name}">
        <xsl:if test="$depth &gt; 0 or position() = 1">
          <xsl:attribute name="open">open</xsl:attribute>
        </xsl:if>
        <summary>
          <span class="izrk-taxon-rank-label"><xsl:value-of select="if (@rank != '') then @rank else 'Unspecified rank'"/></span>
          <xsl:choose>
            <xsl:when test="entry">
              <xsl:for-each select="entry[1]"><xsl:call-template name="eml-taxon-entry"/></xsl:for-each>
            </xsl:when>
            <xsl:otherwise><span class="izrk-taxon-context-name"><xsl:value-of select="if (@name != '') then @name else 'Unspecified taxon'"/></span></xsl:otherwise>
          </xsl:choose>
          <small class="izrk-taxon-count"><xsl:value-of select="count(.//entry)"/><xsl:value-of select="if (count(.//entry) = 1) then ' entry' else ' entries'"/></small>
        </summary>
        <div class="izrk-taxon-children">
          <xsl:for-each select="entry[position() &gt; 1]">
            <div class="izrk-taxon-repeat"><xsl:call-template name="eml-taxon-entry"/></div>
          </xsl:for-each>
          <xsl:call-template name="eml-taxon-tree">
            <xsl:with-param name="nodes" select="taxon"/>
            <xsl:with-param name="depth" select="$depth + 1"/>
          </xsl:call-template>
        </div>
      </details>
    </xsl:for-each>
    <xsl:for-each-group select="$nodes[not(taxon)]" group-by="lower-case(@rank)">
      <xsl:sort select="tax:rank-order(@rank)" data-type="number"/>
      <div class="izrk-taxon-leaves" data-rank="{current-grouping-key()}">
        <h5 class="izrk-taxon-rank-label"><xsl:value-of select="if (@rank != '') then @rank else 'Unspecified rank'"/></h5>
        <ul class="izrk-taxon-list">
          <xsl:for-each select="current-group()/entry">
            <li><xsl:call-template name="eml-taxon-entry"/></li>
          </xsl:for-each>
        </ul>
      </div>
    </xsl:for-each-group>
  </xsl:template>

  <xsl:template name="eml-taxon-entry">
    <span class="izrk-taxon-entry">
      <xsl:variable name="name" select="normalize-space(taxonRankValue)"/>
      <xsl:choose>
        <xsl:when test="lower-case(normalize-space(taxonRankName)) = 'species'">
          <a class="izrk-taxon-search" href="https://www.gbif.org/taxon/search?q={replace(encode-for-uri($name), '%20', '+')}"
             aria-label="Search GBIF for {$name}" title="Search GBIF for {$name}">
            <xsl:value-of select="$name"/>
          </a>
        </xsl:when>
        <xsl:otherwise>
          <span class="izrk-taxon-name"><xsl:value-of select="$name"/></span>
        </xsl:otherwise>
      </xsl:choose>
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
    </span>
  </xsl:template>
</xsl:stylesheet>
