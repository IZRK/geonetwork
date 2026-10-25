<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
                xmlns:eml-fn="http://geonetwork-opensource.org/xsl/functions/eml"
                version="2.0"
                exclude-result-prefixes="#all">

  <xsl:function name="eml-fn:party-key" as="xs:string">
    <xsl:param name="party" as="element()"/>
    <xsl:variable name="name" select="eml-fn:party-name($party)"/>
    <xsl:variable name="organization" select="normalize-space($party/organizationName)"/>
    <xsl:sequence select="if ($name != '') then concat('person|', lower-case($name), '|', lower-case($organization))
      else if ($organization != '') then concat('organization|', lower-case($organization))
      else concat('party|', generate-id($party))"/>
  </xsl:function>

  <xsl:function name="eml-fn:party-name" as="xs:string">
    <xsl:param name="party" as="element()"/>
    <xsl:sequence select="string-join(for $name in ($party/individualName/givenName,
      $party/individualName/surName, $party/individualName/surname)
      return normalize-space($name[normalize-space(.) != '']), ' ')"/>
  </xsl:function>

  <xsl:function name="eml-fn:party-roles" as="xs:string">
    <xsl:param name="party" as="element()"/>
    <xsl:param name="schemaStrings" as="node()*"/>
    <xsl:variable name="implicitRole" select="
      if ($party/role[normalize-space(.) != '']) then ()
      else if (local-name($party) = 'creator') then 'Creator'
      else if (local-name($party) = 'contact') then 'Contact'
      else if (local-name($party) = 'metadataProvider') then 'Metadata provider'
      else ()"/>
    <xsl:sequence select="string-join(distinct-values(($implicitRole,
      for $role in $party/role return normalize-space($role[normalize-space(.) != '']))), ' · ')"/>
  </xsl:function>

  <xsl:function name="eml-fn:field-key" as="xs:string">
    <xsl:param name="field" as="node()"/>
    <xsl:sequence select="concat(if ($field instance of attribute()) then 'attribute|' else 'element|',
      namespace-uri($field), '|', local-name($field))"/>
  </xsl:function>

  <xsl:template name="get-eml-citation">
    <xsl:param name="metadata" as="node()"/>
    <xsl:param name="uuid" as="xs:string"/>
    <xsl:param name="nodeUrl" as="xs:string"/>
    <xsl:variable name="authors">
      <xsl:for-each select="$metadata/dataset/creator">
        <author>
          <xsl:value-of select="if (normalize-space(eml-fn:party-name(.)) != '')
            then eml-fn:party-name(.) else normalize-space(organizationName)"/>
        </author>
      </xsl:for-each>
    </xsl:variable>
    <xsl:variable name="publishers">
      <xsl:for-each select="$metadata/dataset/publisher">
        <author>
          <xsl:value-of select="if (normalize-space(eml-fn:party-name(.)) != '')
            then eml-fn:party-name(.) else normalize-space(organizationName)"/>
        </author>
      </xsl:for-each>
    </xsl:variable>
    <citation>
      <uuid><xsl:value-of select="$uuid"/></uuid>
      <authorsNameAndOrgList><xsl:copy-of select="$authors/author[normalize-space(.) != '']"/></authorsNameAndOrgList>
      <lastPublicationDate><xsl:value-of select="$metadata/dataset/pubDate"/></lastPublicationDate>
      <translatedTitle><xsl:value-of select="$metadata/dataset/title"/></translatedTitle>
      <publishersNameAndOrgList><xsl:copy-of select="$publishers/author[normalize-space(.) != '']"/></publishersNameAndOrgList>
      <landingPageUrl><xsl:value-of select="concat($nodeUrl, 'api/records/', $uuid)"/></landingPageUrl>
      <doi/>
      <doiUrl/>
      <xsl:for-each select="$metadata/dataset/keywordSet/keyword[normalize-space(.) != '']">
        <keyword><xsl:value-of select="normalize-space(.)"/></keyword>
      </xsl:for-each>
      <additionalCitation><xsl:value-of select="$metadata/dataset/additionalInfo"/></additionalCitation>
    </citation>
  </xsl:template>
</xsl:stylesheet>
