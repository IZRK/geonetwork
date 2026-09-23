<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:tax="http://geonetwork-opensource.org/izrk/taxonomy"
                version="2.0" exclude-result-prefixes="#all">

  <!-- Frozen display references only. Rendering never calls an external API or
       modifies the record. Recorded nested classifications always take priority. -->
  <xsl:variable name="tax-reference" select="document('taxonomy-reference.xml')/taxonomy-reference"/>

  <xsl:function name="tax:rank-order" as="xs:integer">
    <xsl:param name="rank"/>
    <xsl:sequence select="(index-of(('domain', 'kingdom', 'subkingdom', 'phylum', 'division',
      'subphylum', 'class', 'subclass', 'order', 'suborder', 'superfamily', 'family',
      'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'species', 'subspecies',
      'variety', 'form'), lower-case(normalize-space($rank))), 99)[1]"/>
  </xsl:function>

  <xsl:template name="eml-taxonomy">
    <xsl:param name="coverage"/>
    <xsl:param name="uuid" select="''"/>
    <xsl:for-each select="$coverage">
      <xsl:for-each select="generalTaxonomicCoverage[normalize-space(.) != '']">
        <p><xsl:value-of select="normalize-space(.)"/></p>
      </xsl:for-each>
      <xsl:variable name="expanded">
        <xsl:for-each select="taxonomicClassification[normalize-space(.) != '' or @id]">
          <xsl:variable name="name" select="normalize-space(taxonRankValue)"/>
          <xsl:variable name="rank" select="lower-case(normalize-space(taxonRankName))"/>
          <xsl:variable name="reference" select="$tax-reference/record[@uuid = $uuid]/taxon
            [@name = $name and @rank = $rank][not(current()/taxonomicClassification)
            and not(current()/taxonId) and not(current()/@id)][1]"/>
          <xsl:call-template name="eml-taxon-parents">
            <xsl:with-param name="node" select="."/>
            <xsl:with-param name="parents" select="$reference[@status = 'matched']/parent"/>
            <xsl:with-param name="reference" select="$reference"/>
          </xsl:call-template>
        </xsl:for-each>
      </xsl:variable>
      <xsl:variable name="tree">
        <xsl:call-template name="eml-taxon-merge">
          <xsl:with-param name="nodes" select="$expanded/taxonomicClassification"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$tree/taxon">
        <div class="izrk-taxonomy">
          <xsl:if test="$tree/taxon[not(taxon)] and not($expanded//*[@izrk-gbif])">
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

  <xsl:template name="eml-taxon-parents">
    <xsl:param name="node"/>
    <xsl:param name="parents"/>
    <xsl:param name="reference"/>
    <xsl:choose>
      <xsl:when test="$parents">
        <taxonomicClassification izrk-context="true">
          <taxonRankName><xsl:value-of select="$parents[1]/@rank"/></taxonRankName>
          <taxonRankValue><xsl:value-of select="$parents[1]/@name"/></taxonRankValue>
          <xsl:call-template name="eml-taxon-parents">
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="parents" select="$parents[position() &gt; 1]"/>
            <xsl:with-param name="reference" select="$reference"/>
          </xsl:call-template>
        </taxonomicClassification>
      </xsl:when>
      <xsl:otherwise>
        <taxonomicClassification>
          <xsl:copy-of select="$node/@*"/>
          <xsl:if test="$reference/@status = 'matched'">
            <xsl:attribute name="izrk-gbif" select="$reference/@usageKey"/>
          </xsl:if>
          <xsl:if test="$reference/@reason">
            <xsl:attribute name="izrk-reason" select="$reference/@reason"/>
          </xsl:if>
          <xsl:copy-of select="$node/node()"/>
        </taxonomicClassification>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Merge only siblings: an identically named genus in different families
       remains separate. Distinct explicit identifiers also remain separate. -->
  <xsl:template name="eml-taxon-merge">
    <xsl:param name="nodes"/>
    <xsl:for-each-group select="$nodes[normalize-space(.) != '' or @id]"
      group-by="concat(lower-case(normalize-space(taxonRankName)), '|',
        normalize-space(taxonRankValue), '|', @id, '|', string-join(taxonId, '|'))">
      <xsl:sort select="tax:rank-order(taxonRankName)" data-type="number"/>
      <xsl:sort select="lower-case(normalize-space(taxonRankValue))"/>
      <taxon rank="{normalize-space(taxonRankName)}" name="{normalize-space(taxonRankValue)}">
        <xsl:for-each select="current-group()[not(@izrk-context)]
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
      <xsl:if test="@izrk-gbif"><a class="izrk-taxon-reference" href="https://www.gbif.org/species/{@izrk-gbif}" aria-label="GBIF reference for {normalize-space(taxonRankValue)}" title="GBIF reference">↗</a></xsl:if>
      <xsl:if test="@izrk-reason"><span class="izrk-taxon-unresolved-note"><xsl:value-of select="@izrk-reason"/></span></xsl:if>
    </span>
  </xsl:template>
</xsl:stylesheet>
