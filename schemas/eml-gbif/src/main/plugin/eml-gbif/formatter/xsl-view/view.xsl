<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:tr="java:org.fao.geonet.api.records.formatters.SchemaLocalizations"
                xmlns:gn-fn-render="http://geonetwork-opensource.org/xsl/functions/render"
                version="2.0"
                exclude-result-prefixes="#all">

  <xsl:variable name="configuration"
                select="document('../../layout/config-editor.xml')"/>

  <xsl:include href="../../layout/evaluate.xsl"/>
  <xsl:include href="../../layout/utility-tpl.xsl"/>
  <xsl:include href="sharedFormatterDir/xslt/render-layout.xsl"/>
  <xsl:include href="../taxonomy.xsl"/>
  <xsl:include href="portal.xsl"/>

  <xsl:variable name="metadata"
                select="/root/eml:eml"/>

  <xsl:template name="get-eml-gbif-other-languages">
    <lang id="eng" code="eng" default=""/>
  </xsl:template>

  <xsl:template mode="render-view" match="@xpath[. = '/eml:eml']">
    <xsl:apply-templates mode="render-field" select="$metadata"/>
  </xsl:template>

  <xsl:template mode="render-view" match="tab[@id = 'default']">
    <div id="gn-tab-default">
      <h1 class="hidden">
        <xsl:value-of select="$schemaStrings/default"/>
      </h1>
      <div id="gn-view-eml-gbif-default" class="gn-tab-content">
        <xsl:call-template name="eml-default-summary"/>
      </div>
    </div>
  </xsl:template>

  <xsl:template mode="getMetadataTitle" match="eml:eml">
    <xsl:value-of select="dataset/title"/>
  </xsl:template>

  <xsl:template mode="getMetadataHierarchyLevel" match="eml:eml">
    <xsl:text>dataset</xsl:text>
  </xsl:template>

  <xsl:template mode="getMetadataAbstract" match="eml:eml">
    <xsl:call-template name="render-paragraph-text">
      <xsl:with-param name="node" select="dataset/abstract"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="getMetadataHeader" match="eml:eml">
    <xsl:if test="normalize-space(dataset/abstract) != ''">
      <div class="gn-abstract">
        <xsl:call-template name="render-paragraph-html">
          <xsl:with-param name="node" select="dataset/abstract"/>
        </xsl:call-template>
      </div>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="getMetadataThumbnail" match="eml:eml">
    <xsl:value-of select="additionalMetadata/metadata/gbif/resourceLogoUrl[1]"/>
  </xsl:template>

  <xsl:template mode="getOverviews" match="eml:eml">
    <xsl:variable name="logo"
                  select="normalize-space(additionalMetadata/metadata/gbif/resourceLogoUrl[1])"/>
    <xsl:if test="$logo != ''">
      <section class="gn-md-side-overview">
        <h2>
          <i class="fa fa-fw fa-image"></i>
          <span>
            <xsl:value-of select="$schemaStrings/overviews"/>
          </span>
        </h2>
        <img data-gn-img-modal="md"
             class="gn-img-thumbnail"
             alt="{$schemaStrings/overview}"
             src="{$logo}"
             onerror="this.onerror=null; this.parentNode.style.display='none';"/>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="getTags" match="eml:eml">
    <xsl:param name="byThesaurus" select="false()"/>

    <xsl:variable name="tags">
      <xsl:for-each select="dataset/keywordSet/keyword[normalize-space(.) != '']">
        <tag thesaurus="{normalize-space(../keywordThesaurus)}">
          <xsl:value-of select="normalize-space(.)"/>
        </tag>
      </xsl:for-each>
    </xsl:variable>

    <xsl:if test="count($tags/tag) > 0">
      <section class="gn-md-side-social">
        <h2>
          <i class="fa fa-fw fa-tag"></i>
          <span>
            <xsl:value-of select="$schemaStrings/noThesaurusName"/>
          </span>
        </h2>
        <xsl:choose>
          <xsl:when test="$byThesaurus">
            <xsl:for-each-group select="$tags/tag" group-by="@thesaurus">
              <xsl:sort select="@thesaurus"/>
              <xsl:if test="current-grouping-key() != ''">
                <xsl:value-of select="current-grouping-key()"/>
                <br/>
              </xsl:if>
              <xsl:for-each select="current-group()">
                <xsl:sort select="."/>
                <a class="btn btn-default btn-xs"
                   href='#/search?query_string=%7B"tag.\\*":%7B"{.}":true%7D%7D'>
                  <xsl:value-of select="."/>
                </a>
              </xsl:for-each>
              <xsl:if test="position() != last()">
                <hr/>
              </xsl:if>
            </xsl:for-each-group>
          </xsl:when>
          <xsl:otherwise>
            <xsl:for-each select="$tags/tag">
              <xsl:sort select="."/>
              <a class="btn btn-default btn-xs"
                 href='#/search?query_string=%7B"tag.\\*":%7B"{.}":true%7D%7D'>
                <xsl:value-of select="."/>
              </a>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="getExtent" match="eml:eml">
    <xsl:if test="dataset/coverage/geographicCoverage/boundingCoordinates">
      <section class="gn-md-side-extent">
        <h2>
          <i class="fa fa-fw fa-map-marker"></i>
          <span>
            <xsl:value-of select="$schemaStrings/spatialExtent"/>
          </span>
        </h2>
        <xsl:for-each select="dataset/coverage/geographicCoverage/boundingCoordinates[
                              westBoundingCoordinate castable as xs:double
                              and southBoundingCoordinate castable as xs:double
                              and eastBoundingCoordinate castable as xs:double
                              and northBoundingCoordinate castable as xs:double]">
          <xsl:copy-of select="gn-fn-render:bbox(
            xs:double(westBoundingCoordinate),
            xs:double(southBoundingCoordinate),
            xs:double(eastBoundingCoordinate),
            xs:double(northBoundingCoordinate))"/>
        </xsl:for-each>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-default-summary">
    <xsl:call-template name="eml-default-metadata"/>
    <xsl:call-template name="eml-party-table">
      <xsl:with-param name="label" select="'Dataset Creators'"/>
      <xsl:with-param name="nodes" select="$metadata/dataset/creator"/>
    </xsl:call-template>
    <xsl:call-template name="eml-party-table">
      <xsl:with-param name="label" select="'Contacts'"/>
      <xsl:with-param name="nodes" select="$metadata/dataset/contact"/>
    </xsl:call-template>
    <xsl:call-template name="eml-keywords"/>
    <xsl:call-template name="eml-geographic-coverage"/>
    <xsl:call-template name="eml-temporal-coverage"/>
    <xsl:call-template name="eml-taxonomic-coverage"/>
    <xsl:call-template name="eml-distribution"/>
    <xsl:call-template name="eml-methods"/>
  </xsl:template>

  <xsl:template name="eml-default-metadata">
    <div id="gn-section-eml-metadata" class="gn-tab-content">
      <h2>Metadata</h2>
      <xsl:call-template name="eml-field">
        <xsl:with-param name="label" select="'Metadata Identifier'"/>
        <xsl:with-param name="value" select="$metadata/dataset/alternateIdentifier[1]"/>
      </xsl:call-template>
      <xsl:call-template name="eml-field">
        <xsl:with-param name="label" select="'Publication Date'"/>
        <xsl:with-param name="value" select="$metadata/dataset/pubDate"/>
        <xsl:with-param name="date" select="true()"/>
      </xsl:call-template>
      <xsl:call-template name="eml-field">
        <xsl:with-param name="label" select="'Language'"/>
        <xsl:with-param name="value" select="$metadata/dataset/language"/>
      </xsl:call-template>
      <xsl:call-template name="eml-field">
        <xsl:with-param name="label" select="'Package identifier'"/>
        <xsl:with-param name="value" select="$metadata/@packageId"/>
      </xsl:call-template>
    </div>
  </xsl:template>

  <xsl:template name="eml-party-table">
    <xsl:param name="label"/>
    <xsl:param name="nodes" as="node()*"/>
    <xsl:if test="$nodes">
      <dl class="gn-table">
        <dt>
          <xsl:value-of select="$label"/>
        </dt>
        <dd>
          <table class="table">
            <thead>
              <tr>
                <th>Organisation name</th>
                <th>Individual name</th>
                <th>Electronic mail address</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="$nodes">
                <tr>
                  <td>
                    <xsl:value-of select="normalize-space(organizationName)"/>
                  </td>
                  <td>
                    <xsl:call-template name="eml-party-name"/>
                  </td>
                  <td>
                    <xsl:choose>
                      <xsl:when test="normalize-space(electronicMailAddress) != ''">
                        <a href="mailto:{normalize-space(electronicMailAddress)}">
                          <xsl:value-of select="normalize-space(electronicMailAddress)"/>
                        </a>
                      </xsl:when>
                      <xsl:otherwise>
                        <xsl:text> </xsl:text>
                      </xsl:otherwise>
                    </xsl:choose>
                  </td>
                  <td>
                    <xsl:value-of select="normalize-space(role)"/>
                  </td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-party-name">
    <xsl:variable name="nameParts"
                  select="(individualName/givenName|individualName/surName|individualName/surname)[normalize-space(.) != '']"/>
    <xsl:value-of select="string-join(for $p in $nameParts return normalize-space($p), ' ')"/>
  </xsl:template>

  <xsl:template name="eml-keywords">
    <xsl:if test="$metadata/dataset/keywordSet/keyword[normalize-space(.) != '']">
      <dl class="gn-keyword">
        <dt>Keywords</dt>
        <dd>
          <div>
            <xsl:for-each select="$metadata/dataset/keywordSet">
              <xsl:if test="normalize-space(keywordThesaurus) != ''">
                <p class="text-muted">
                  <xsl:value-of select="normalize-space(keywordThesaurus)"/>
                </p>
              </xsl:if>
              <ul>
                <xsl:for-each select="keyword[normalize-space(.) != '']">
                  <li>
                    <span>
                      <xsl:value-of select="normalize-space(.)"/>
                    </span>
                  </li>
                </xsl:for-each>
              </ul>
            </xsl:for-each>
          </div>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-geographic-coverage">
    <xsl:for-each select="$metadata/dataset/coverage/geographicCoverage">
      <xsl:call-template name="eml-field">
        <xsl:with-param name="label" select="'Description'"/>
        <xsl:with-param name="value" select="geographicDescription"/>
      </xsl:call-template>
      <xsl:for-each select="boundingCoordinates[
                            westBoundingCoordinate castable as xs:double
                            and southBoundingCoordinate castable as xs:double
                            and eastBoundingCoordinate castable as xs:double
                            and northBoundingCoordinate castable as xs:double]">
        <xsl:copy-of select="gn-fn-render:bbox(
          xs:double(westBoundingCoordinate),
          xs:double(southBoundingCoordinate),
          xs:double(eastBoundingCoordinate),
          xs:double(northBoundingCoordinate))"/>
        <br/>
        <br/>
      </xsl:for-each>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="eml-temporal-coverage">
    <xsl:if test="$metadata/dataset/coverage/temporalCoverage">
      <div id="gn-section-eml-temporal" class="gn-tab-content">
        <h2>Temporal extent</h2>
        <xsl:for-each select="$metadata/dataset/coverage/temporalCoverage">
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Date'"/>
            <xsl:with-param name="value" select="singleDateTime/calendarDate"/>
            <xsl:with-param name="date" select="true()"/>
          </xsl:call-template>
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Begin'"/>
            <xsl:with-param name="value" select="rangeOfDates/beginDate/calendarDate"/>
            <xsl:with-param name="date" select="true()"/>
          </xsl:call-template>
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'End'"/>
            <xsl:with-param name="value" select="rangeOfDates/endDate/calendarDate"/>
            <xsl:with-param name="date" select="true()"/>
          </xsl:call-template>
        </xsl:for-each>
      </div>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-taxonomic-coverage">
    <xsl:variable name="coverage" select="$metadata/dataset/coverage/taxonomicCoverage[normalize-space(.) != '']"/>
    <xsl:if test="$coverage">
      <dl class="gn-table">
        <dt>Taxonomic coverage</dt>
        <dd>
          <xsl:call-template name="eml-taxonomy">
            <xsl:with-param name="coverage" select="$coverage"/>
          </xsl:call-template>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="taxonomicCoverage" priority="2">
    <xsl:if test="normalize-space(.) != ''">
      <section class="gn-md-section">
        <h2>Taxonomic coverage</h2>
        <xsl:call-template name="eml-taxonomy">
          <xsl:with-param name="coverage" select="."/>
        </xsl:call-template>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-distribution">
    <xsl:variable name="links"
                  select="$metadata/dataset/distribution/online/url[normalize-space(.) != '']"/>
    <xsl:if test="$links">
      <div id="gn-section-eml-distribution" class="gn-tab-content">
        <h2>Distribution</h2>
        <ul>
          <xsl:for-each select="$links">
            <li>
              <a href="{normalize-space(.)}">
                <xsl:value-of select="normalize-space(.)"/>
              </a>
            </li>
          </xsl:for-each>
        </ul>
      </div>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-methods">
    <xsl:if test="$metadata/dataset/methods/methodStep/description[normalize-space(.) != '']">
      <div id="gn-section-eml-methods" class="gn-tab-content">
        <h2>Methods</h2>
        <xsl:for-each select="$metadata/dataset/methods/methodStep/description">
          <xsl:call-template name="render-paragraph-html">
            <xsl:with-param name="node" select="."/>
          </xsl:call-template>
        </xsl:for-each>
      </div>
    </xsl:if>
  </xsl:template>

  <xsl:template name="eml-field">
    <xsl:param name="label"/>
    <xsl:param name="value"/>
    <xsl:param name="date" select="false()"/>
    <xsl:if test="normalize-space($value) != ''">
      <dl>
        <dt>
          <xsl:value-of select="$label"/>
        </dt>
        <dd>
          <xsl:choose>
            <xsl:when test="$date">
              <span data-gn-humanize-time="{normalize-space($value)}">
                <xsl:value-of select="normalize-space($value)"/>
              </span>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="normalize-space($value)"/>
            </xsl:otherwise>
          </xsl:choose>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="eml:eml">
    <xsl:apply-templates mode="render-field"
                         select="dataset|additionalMetadata"/>
  </xsl:template>

  <xsl:template mode="render-field"
                match="dataset|additionalMetadata|metadata|gbif|creator|metadataProvider|associatedParty|contact|keywordSet|coverage|geographicCoverage|temporalCoverage|taxonomicCoverage|taxonomicClassification|methods|methodStep|project|personnel|distribution|physical|online|collection|attributeList|attribute|measurementScale|nominal|ratio|unit|customUnit|qualityControl|sampling|studyExtent">
    <xsl:if test="normalize-space(.) != '' or @*">
      <section class="gn-md-section">
        <h2>
          <xsl:call-template name="node-label"/>
        </h2>
        <div>
          <xsl:apply-templates mode="render-field" select="@*|*"/>
        </div>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="alternateIdentifier[position() > 1]"/>

  <xsl:template mode="render-field"
                match="abstract|additionalInfo|intellectualRights|purpose|description|samplingDescription|funding">
    <xsl:if test="normalize-space(.) != ''">
      <dl>
        <dt>
          <xsl:call-template name="node-label"/>
        </dt>
        <dd>
          <xsl:call-template name="render-paragraph-html">
            <xsl:with-param name="node" select="."/>
          </xsl:call-template>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="url|online/url">
    <xsl:if test="normalize-space(.) != ''">
      <dl>
        <dt>
          <xsl:call-template name="node-label"/>
        </dt>
        <dd>
          <a href="{normalize-space(.)}">
            <xsl:value-of select="normalize-space(.)"/>
          </a>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="@*">
    <xsl:if test="normalize-space(.) != ''">
      <dl>
        <dt>
          <xsl:value-of select="name(.)"/>
        </dt>
        <dd>
          <xsl:value-of select="normalize-space(.)"/>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-field" match="*">
    <xsl:if test="normalize-space(.) != ''">
      <dl>
        <dt>
          <xsl:call-template name="node-label"/>
        </dt>
        <dd>
          <xsl:apply-templates mode="render-value" select="."/>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-value" match="*">
    <xsl:choose>
      <xsl:when test="*">
        <xsl:apply-templates mode="render-field" select="@*|*"/>
      </xsl:when>
      <xsl:when test="matches(normalize-space(.), '^https?://')">
        <a href="{normalize-space(.)}">
          <xsl:value-of select="normalize-space(.)"/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space(.)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="node-label">
    <xsl:value-of select="tr:nodeLabel(tr:create($schema), name(), local-name(..))"/>
  </xsl:template>

  <xsl:template name="render-paragraph-text">
    <xsl:param name="node"/>
    <xsl:choose>
      <xsl:when test="$node/para">
        <xsl:value-of select="string-join(for $p in $node/para return normalize-space($p), ' ')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="render-paragraph-html">
    <xsl:param name="node"/>
    <xsl:choose>
      <xsl:when test="$node/para">
        <xsl:for-each select="$node/para">
          <p>
            <xsl:call-template name="addLineBreaksAndHyperlinks">
              <xsl:with-param name="txt" select="normalize-space(.)"/>
            </xsl:call-template>
          </p>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="addLineBreaksAndHyperlinks">
          <xsl:with-param name="txt" select="normalize-space($node)"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
