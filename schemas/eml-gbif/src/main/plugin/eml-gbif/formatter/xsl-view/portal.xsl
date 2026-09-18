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
      <div class="row gn-card gn-card-dataset gn-margin-top gn-margin-bottom gn-padding-top gn-padding-bottom">
        <div class="col-md-8 gn-record">
          <h1 class="gn-break"><i class="fa gn-icon-dataset" aria-hidden="true"></i><xsl:text> </xsl:text><xsl:value-of select="$metadata/dataset/title"/></h1>
          <xsl:apply-templates mode="getMetadataHeader" select="$metadata"/>
        </div>
        <aside class="col-md-4 gn-md-side">
          <xsl:apply-templates mode="getOverviews" select="$metadata"/>
          <xsl:call-template name="eml-keywords"/>
        </aside>
      </div>

      <xsl:if test="$metadata/dataset/coverage/geographicCoverage[normalize-space(.) != '']">
        <section class="row gn-section gn-section-dataset gn-padding-top">
          <div class="col-md-8 gn-record">
            <h2>Spatial extent</h2>
            <xsl:call-template name="eml-geographic-coverage"/>
          </div>
          <div class="col-md-4 gn-md-side"><xsl:call-template name="eml-temporal-coverage"/></div>
        </section>
      </xsl:if>

      <section class="row gn-section gn-section-dataset">
        <div class="col-md-8 gn-record">
          <xsl:call-template name="eml-distribution"/>
          <xsl:if test="normalize-space($metadata/dataset/intellectualRights) != ''">
            <h2>Use constraints</h2>
            <xsl:call-template name="render-paragraph-html"><xsl:with-param name="node" select="$metadata/dataset/intellectualRights"/></xsl:call-template>
          </xsl:if>
        </div>
      </section>

      <section class="row gn-section gn-section-dataset">
        <div class="col-md-12 gn-record">
          <h2>Technical information</h2>
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

      <xsl:call-template name="eml-portal-parties">
        <xsl:with-param name="label" select="'Dataset creators'"/>
        <xsl:with-param name="nodes" select="$metadata/dataset/creator"/>
      </xsl:call-template>
      <xsl:call-template name="eml-portal-parties">
        <xsl:with-param name="label" select="'Contact for the resource'"/>
        <xsl:with-param name="nodes" select="$metadata/dataset/contact"/>
      </xsl:call-template>

      <section class="row gn-section gn-section-dataset">
        <div class="col-md-8 gn-record">
          <h2>Metadata information</h2>
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Metadata identifier'"/>
            <xsl:with-param name="value" select="$metadataUuid"/>
          </xsl:call-template>
          <xsl:call-template name="eml-field">
            <xsl:with-param name="label" select="'Package identifier'"/>
            <xsl:with-param name="value" select="$metadata/@packageId"/>
          </xsl:call-template>
          <h3>Cite dataset</h3>
          <p><xsl:value-of select="$metadata/dataset/title"/>.
            <xsl:if test="normalize-space($metadata/dataset/pubDate) != ''"><xsl:value-of select="$metadata/dataset/pubDate"/>.</xsl:if>
            <br/><a href="{$nodeUrl}api/records/{$metadataUuid}"><xsl:value-of select="concat($nodeUrl, 'api/records/', $metadataUuid)"/></a>
          </p>
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

  <xsl:template name="eml-portal-parties">
    <xsl:param name="label"/>
    <xsl:param name="nodes"/>
    <xsl:if test="$nodes[normalize-space(.) != '']">
      <section class="row gn-section gn-section-dataset">
        <div class="col-md-12 gn-record">
          <h2><xsl:value-of select="$label"/></h2>
          <div class="izrk-eml-contacts">
            <xsl:for-each select="$nodes[normalize-space(.) != '']">
              <div class="flex-row">
                <span class="badge badge-rounded"><i class="fa fa-fw fa-user" aria-hidden="true"></i></span>
                <div>
                  <h3><xsl:call-template name="eml-party-name"/></h3>
                  <p><xsl:value-of select="organizationName"/></p>
                  <xsl:if test="normalize-space(role) != ''"><p><xsl:value-of select="role"/></p></xsl:if>
                  <xsl:if test="normalize-space(positionName) != ''"><p><xsl:value-of select="positionName"/></p></xsl:if>
                  <xsl:for-each select="electronicMailAddress[normalize-space(.) != '']">
                    <p><a href="mailto:{normalize-space(.)}"><xsl:value-of select="normalize-space(.)"/></a></p>
                  </xsl:for-each>
                  <xsl:for-each select="userId[normalize-space(.) != '']">
                    <p><xsl:choose>
                      <xsl:when test="matches(@directory, '^https?://')">
                        <a href="{concat(@directory, if (ends-with(@directory, '/')) then '' else '/', normalize-space(.))}"><xsl:value-of select="normalize-space(.)"/></a>
                      </xsl:when>
                      <xsl:otherwise><xsl:value-of select="normalize-space(.)"/></xsl:otherwise>
                    </xsl:choose></p>
                  </xsl:for-each>
                </div>
              </div>
            </xsl:for-each>
          </div>
        </div>
      </section>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
