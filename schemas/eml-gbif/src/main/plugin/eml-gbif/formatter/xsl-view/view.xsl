<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:eml-fn="http://geonetwork-opensource.org/xsl/functions/eml"
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
  <xsl:include href="../citation/base.xsl"/>
  <xsl:include href="../../../iso19115-3.2018/formatter/citation/common.xsl"/>
  <xsl:include href="portal.xsl"/>

  <xsl:variable name="metadata"
                select="/root/eml:eml"/>

  <xsl:template name="get-eml-gbif-other-languages">
    <lang id="eng" code="eng" default=""/>
  </xsl:template>

  <xsl:template mode="render-view" match="@xpath" priority="2">
    <xsl:variable name="nodes">
      <xsl:call-template name="evaluate-eml-gbif">
        <xsl:with-param name="base" select="$metadata"/>
        <xsl:with-param name="in" select="concat('/../', .)"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:apply-templates mode="render-field" select="$nodes/*"/>
  </xsl:template>

  <xsl:template mode="render-view" match="view[@name = 'advanced']/tab" priority="2">
    <xsl:variable name="content"><xsl:apply-templates mode="render-view" select="section"/></xsl:variable>
    <xsl:if test="normalize-space($content) != ''">
      <div id="gn-tab-{@id}" class="tab-pane">
        <h2 class="{if ($tabs = 'true') then 'hidden' else 'view-header'}">
          <xsl:value-of select="gn-fn-render:get-schema-strings($schemaStrings, @id)"/>
        </h2>
        <xsl:copy-of select="$content"/>
      </div>
    </xsl:if>
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

  <xsl:template mode="getExtent" match="eml:eml"/>

  <xsl:template name="eml-default-summary">
    <xsl:call-template name="eml-default-metadata"/>
    <xsl:call-template name="eml-party-table">
      <xsl:with-param name="label" select="$schemaStrings/emlContacts"/>
      <xsl:with-param name="nodes" select="$metadata//*[self::creator or self::contact or self::metadataProvider or self::associatedParty or self::personnel]"/>
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

  <!-- Render each person once and retain every distinct role and contact detail. -->
  <xsl:template name="eml-party-table">
    <xsl:param name="label"/>
    <xsl:param name="nodes" as="node()*"/>
    <xsl:if test="$nodes">
      <section class="gn-md-section izrk-eml-contact-section">
        <h2><xsl:value-of select="$label"/></h2>
        <div class="izrk-contact-organisations">
        <xsl:for-each-group select="$nodes" group-by="lower-case(normalize-space(organizationName))">
          <details class="izrk-eml-contact-organisation" open="open">
            <summary>
              <span class="izrk-organisation-name"><xsl:value-of select="if (current-grouping-key() != '') then normalize-space(organizationName) else $label"/></span>
              <span class="izrk-contact-count"><xsl:value-of select="count(distinct-values(for $party in current-group() return eml-fn:party-key($party)))"/></span>
            </summary>
            <div class="izrk-eml-contacts">
          <xsl:for-each-group select="current-group()" group-by="eml-fn:party-key(.)">
            <xsl:variable name="parties" select="current-group()"/>
            <div class="izrk-eml-contact">
              <span class="badge badge-rounded izrk-contact-icon" aria-hidden="true">
                <i class="fa fa-fw fa-user"/>
              </span>
              <div class="izrk-contact-details">
                <xsl:if test="individualName">
                  <h4><xsl:value-of select="eml-fn:party-name(.)"/></h4>
                </xsl:if>
                <p class="text-muted izrk-contact-roles">
                  <xsl:value-of select="string-join(distinct-values(for $party in $parties return eml-fn:party-roles($party, $schemaStrings)), ' · ')"/>
                </p>
                <xsl:for-each-group select="$parties/(@* | *[not(self::individualName or self::organizationName or self::role)])"
                                    group-by="eml-fn:field-key(.)">
                  <xsl:apply-templates mode="render-field" select="."/>
                </xsl:for-each-group>
              </div>
            </div>
          </xsl:for-each-group>
            </div>
          </details>
        </xsl:for-each-group>
        </div>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="render-view" match="section[@name = 'emlContacts']" priority="2">
    <xsl:call-template name="eml-party-table">
      <xsl:with-param name="label" select="$schemaStrings/emlContacts"/>
      <xsl:with-param name="nodes" select="$metadata//*[self::creator or self::contact or self::metadataProvider or self::associatedParty or self::personnel]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="render-view" match="section[@name = 'emlMetadata']" priority="2">
    <xsl:apply-templates mode="render-field" select="$metadata/@* | $metadata/dataset/@* | $metadata/*[not(self::dataset)]"/>
  </xsl:template>

  <!-- Empty sections should not leave dead tabs in sparse EML records. -->
  <xsl:template mode="render-toc" match="view[@name = 'advanced']" priority="2">
    <xsl:if test="$tabs = 'true'">
      <ul class="view-outline nav nav-tabs nav-tabs-advanced">
        <xsl:for-each select="tab">
          <xsl:variable name="content"><xsl:apply-templates mode="render-view" select="."/></xsl:variable>
          <xsl:if test="normalize-space($content) != ''">
            <li><a href="#gn-tab-{@id}"><xsl:value-of select="gn-fn-render:get-schema-strings($schemaStrings, @id)"/></a></li>
          </xsl:if>
        </xsl:for-each>
      </ul>
    </xsl:if>
  </xsl:template>

  <!-- People are presented together in the Contacts tab, including project roles. -->
  <xsl:template mode="render-field" match="creator|contact|metadataProvider|associatedParty|personnel" priority="2"/>

  <xsl:template mode="render-field" match="electronicMailAddress|userId" priority="2">
    <xsl:if test="normalize-space(.) != ''">
      <dl>
        <dt><xsl:call-template name="node-label"/></dt>
        <dd>
          <xsl:variable name="url" select="if (self::electronicMailAddress) then concat('mailto:', normalize-space(.))
            else if (matches(normalize-space(.), '^https?://')) then normalize-space(.)
            else if (matches(@directory, '^https?://')) then concat(replace(@directory, '/$', ''), '/', normalize-space(.))
            else ''"/>
          <xsl:choose>
            <xsl:when test="$url != ''"><a href="{$url}"><xsl:value-of select="normalize-space(.)"/></a></xsl:when>
            <xsl:otherwise><xsl:value-of select="normalize-space(.)"/></xsl:otherwise>
          </xsl:choose>
          <xsl:apply-templates mode="render-field" select="@*[not(local-name() = 'directory') or not(matches(., '^https?://'))]"/>
        </dd>
      </dl>
    </xsl:if>
  </xsl:template>

  <xsl:template mode="getMetadataCitation" match="eml:eml">
    <xsl:if test="$root != 'div'">
    <section class="gn-md-section izrk-citation">
      <h2><xsl:value-of select="$schemaStrings/citationProposal"/></h2>
      <xsl:variable name="citationInfo">
        <xsl:call-template name="get-eml-citation">
          <xsl:with-param name="metadata" select="."/>
          <xsl:with-param name="uuid" select="$metadataUuid"/>
          <xsl:with-param name="nodeUrl" select="$nodeUrl"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:apply-templates mode="citation" select="$citationInfo"/>
    </section>
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
    <xsl:variable name="boundingCoordinates"
      select="$metadata/dataset/coverage/geographicCoverage/boundingCoordinates[
        westBoundingCoordinate castable as xs:double
        and southBoundingCoordinate castable as xs:double
        and eastBoundingCoordinate castable as xs:double
        and northBoundingCoordinate castable as xs:double]"/>
    <div class="izrk-geographic-coverage">
      <xsl:for-each select="$metadata/dataset/coverage/geographicCoverage">
        <xsl:call-template name="eml-field">
          <xsl:with-param name="label" select="'Description'"/>
          <xsl:with-param name="value" select="geographicDescription"/>
        </xsl:call-template>
      </xsl:for-each>
      <xsl:if test="$boundingCoordinates">
        <xsl:variable name="geometries">
          <xsl:for-each select="$boundingCoordinates">
            <xsl:variable name="west" select="format-number(xs:double(westBoundingCoordinate), '0.############')"/>
            <xsl:variable name="south" select="format-number(xs:double(southBoundingCoordinate), '0.############')"/>
            <xsl:variable name="east" select="format-number(xs:double(eastBoundingCoordinate), '0.############')"/>
            <xsl:variable name="north" select="format-number(xs:double(northBoundingCoordinate), '0.############')"/>
            <xsl:if test="position() gt 1"><xsl:text>,</xsl:text></xsl:if>
            <xsl:text>'</xsl:text>
            <xsl:choose>
              <xsl:when test="$west = $east and $south = $north">
                <xsl:text>{"type":"Point","coordinates":[</xsl:text>
                <xsl:value-of select="$west"/><xsl:text>,</xsl:text><xsl:value-of select="$south"/>
                <xsl:text>]}</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>{"type":"Polygon","coordinates":[[[</xsl:text>
                <xsl:value-of select="$west"/><xsl:text>,</xsl:text><xsl:value-of select="$south"/><xsl:text>],[</xsl:text>
                <xsl:value-of select="$east"/><xsl:text>,</xsl:text><xsl:value-of select="$south"/><xsl:text>],[</xsl:text>
                <xsl:value-of select="$east"/><xsl:text>,</xsl:text><xsl:value-of select="$north"/><xsl:text>],[</xsl:text>
                <xsl:value-of select="$west"/><xsl:text>,</xsl:text><xsl:value-of select="$north"/><xsl:text>],[</xsl:text>
                <xsl:value-of select="$west"/><xsl:text>,</xsl:text><xsl:value-of select="$south"/>
                <xsl:text>]]]}</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
            <xsl:text>'</xsl:text>
          </xsl:for-each>
        </xsl:variable>
        <div class="izrk-eml-spatial-preview">
          <div>
            <xsl:attribute name="data-ng-init">
              <xsl:text>mdView.current.record.geom = [</xsl:text>
              <xsl:value-of select="normalize-space(string($geometries))"/>
              <xsl:text>]</xsl:text>
            </xsl:attribute>
            <div data-gn-data-preview="mdView.current.record"></div>
          </div>
        </div>
      </xsl:if>
    </div>
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
            <xsl:with-param name="uuid" select="$metadataUuid"/>
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
          <xsl:with-param name="uuid" select="$metadataUuid"/>
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
          <xsl:if test="not(*)"><xsl:apply-templates mode="render-field" select="@*"/></xsl:if>
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
