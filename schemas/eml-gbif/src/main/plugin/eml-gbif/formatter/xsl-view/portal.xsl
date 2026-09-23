<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="2.0" exclude-result-prefixes="#all">

  <!-- The portal uses the same card and section structure as its native dataset
       view. Standalone HTML and the full metadata view retain the shared layout. -->
  <xsl:template match="/" priority="2">
    <xsl:choose>
      <xsl:when test="$root = 'div' and $view = 'portal'">
        <xsl:call-template name="eml-portal-record"/>
      </xsl:when>
      <xsl:otherwise><xsl:next-match/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="eml-portal-record">
    <article class="izrk-eml-portal" id="{$metadataUuid}">
      <div class="row izrk-record-header gn-card gn-card-dataset">
        <div class="col-md-8 gn-record">
          <div class="izrk-resource-type"><i class="fa gn-icon-dataset" aria-hidden="true"></i> Dataset</div>
          <h1 class="gn-break"><xsl:value-of select="$metadata/dataset/title"/></h1>
          <xsl:apply-templates mode="getMetadataHeader" select="$metadata"/>
        </div>
        <aside class="col-md-4 gn-md-side">
          <xsl:apply-templates mode="getOverviews" select="$metadata"/>
          <xsl:call-template name="eml-keywords"/>
        </aside>
      </div>

      <xsl:if test="$metadata/dataset/coverage/geographicCoverage[normalize-space(.) != '']">
        <section class="row izrk-record-section gn-section gn-section-dataset">
          <div class="col-md-12 gn-record">
            <h2><i class="fa fa-map-marker" aria-hidden="true"></i> Spatial extent</h2>
            <xsl:call-template name="eml-geographic-coverage"/>
          </div>
          <xsl:if test="$metadata/dataset/coverage/temporalCoverage">
            <div class="col-md-12 gn-md-side"><xsl:call-template name="eml-temporal-coverage"/></div>
          </xsl:if>
        </section>
      </xsl:if>

      <xsl:if test="$metadata/dataset/distribution/online/url[normalize-space(.) != ''] or normalize-space($metadata/dataset/intellectualRights) != ''">
      <section class="row izrk-record-section gn-section gn-section-dataset">
        <div class="col-md-12 gn-record">
          <xsl:call-template name="eml-distribution"/>
          <xsl:if test="normalize-space($metadata/dataset/intellectualRights) != ''">
            <h2><i class="fa fa-shield" aria-hidden="true"></i> Use constraints</h2>
            <xsl:call-template name="render-paragraph-html"><xsl:with-param name="node" select="$metadata/dataset/intellectualRights"/></xsl:call-template>
          </xsl:if>
        </div>
      </section>
      </xsl:if>

      <section class="row izrk-record-section gn-section gn-section-dataset">
        <div class="col-md-12 gn-record">
          <h2><i class="fa fa-sliders" aria-hidden="true"></i> Technical information</h2>
          <div class="izrk-eml-facts">
            <xsl:call-template name="eml-portal-fact">
              <xsl:with-param name="label" select="'Publication date'"/>
              <xsl:with-param name="icon" select="'calendar'"/>
              <xsl:with-param name="value" select="$metadata/dataset/pubDate"/>
            </xsl:call-template>
            <xsl:call-template name="eml-portal-fact">
              <xsl:with-param name="label" select="'Language'"/>
              <xsl:with-param name="icon" select="'language'"/>
              <xsl:with-param name="value" select="$metadata/dataset/language"/>
            </xsl:call-template>
            <xsl:call-template name="eml-portal-fact">
              <xsl:with-param name="label" select="'Metadata standard'"/>
              <xsl:with-param name="icon" select="'certificate'"/>
              <xsl:with-param name="value" select="'EML / GBIF'"/>
            </xsl:call-template>
          </div>
          <xsl:if test="not($metadata/dataset/coverage/geographicCoverage[normalize-space(.) != ''])"><xsl:call-template name="eml-temporal-coverage"/></xsl:if>
          <xsl:call-template name="eml-taxonomic-coverage"/>
          <xsl:call-template name="eml-methods"/>
        </div>
      </section>

      <section class="row izrk-record-section gn-section gn-section-dataset">
        <div class="col-md-12 gn-record">
          <xsl:call-template name="eml-party-table">
            <xsl:with-param name="label" select="'Contacts'"/>
            <xsl:with-param name="nodes" select="$metadata//*[self::creator or self::contact or self::associatedParty or self::metadataProvider or self::personnel]"/>
          </xsl:call-template>
        </div>
      </section>

      <section class="row izrk-record-section gn-section gn-section-dataset">
        <h2 class="col-md-12"><i class="fa fa-file-text-o" aria-hidden="true"></i> Metadata information</h2>
        <div class="col-md-8 gn-record">
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Metadata identifier'"/>
            <xsl:with-param name="value" select="$metadataUuid"/>
          </xsl:call-template>
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Package identifier'"/>
            <xsl:with-param name="value" select="$metadata/@packageId"/>
          </xsl:call-template>
        </div>
        <aside class="col-md-4 gn-md-side">
          <h3>Provided by</h3>
          <img class="gn-source-logo" alt="Catalogue provider" src="{$nodeUrl}api/sources/{$source}/logo"/>
        </aside>
      </section>
    </article>
  </xsl:template>

  <xsl:template name="eml-portal-fact">
    <xsl:param name="label"/>
    <xsl:param name="icon"/>
    <xsl:param name="value"/>
    <xsl:if test="normalize-space($value) != ''">
      <div class="flex-row">
        <span class="badge badge-rounded"><i class="fa fa-fw fa-{$icon}" aria-hidden="true"></i></span>
        <div><h3><xsl:value-of select="$label"/></h3><p><xsl:value-of select="$value"/></p></div>
      </div>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
