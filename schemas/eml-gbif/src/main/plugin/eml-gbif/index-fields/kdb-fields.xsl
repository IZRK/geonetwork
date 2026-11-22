<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:kdb="http://geonetwork-opensource.org/xsl/functions/kdb-eml"
                exclude-result-prefixes="xs kdb">

  <xsl:function name="kdb:json-string" as="xs:string">
    <xsl:param name="value" as="xs:string?"/>
    <xsl:variable name="hex" as="xs:string" select="'0123456789ABCDEF'"/>
    <xsl:sequence select="string-join(for $codepoint in string-to-codepoints(string($value))
      return if ($codepoint = 34) then '\&quot;'
      else if ($codepoint = 92) then '\\'
      else if ($codepoint = 8) then '\b'
      else if ($codepoint = 9) then '\t'
      else if ($codepoint = 10) then '\n'
      else if ($codepoint = 12) then '\f'
      else if ($codepoint = 13) then '\r'
      else if ($codepoint lt 32) then concat('\u00', substring($hex, ($codepoint idiv 16) + 1, 1), substring($hex, ($codepoint mod 16) + 1, 1))
      else codepoints-to-string($codepoint), '')"/>
  </xsl:function>

  <xsl:function name="kdb:party-json" as="xs:string">
    <xsl:param name="party" as="element()"/>
    <xsl:variable name="kind" select="local-name($party)"/>
    <xsl:variable name="given" select="normalize-space(string($party/*[local-name() = 'individualName']/*[local-name() = 'givenName'][1]))"/>
    <xsl:variable name="surname" select="normalize-space(string($party/*[local-name() = 'individualName']/*[local-name() = 'surName'][1]))"/>
    <xsl:variable name="name" select="normalize-space(string-join(($given, $surname)[. != ''], ' '))"/>
    <xsl:variable name="organisation" select="normalize-space(string($party/*[local-name() = 'organizationName'][1]))"/>
    <xsl:variable name="role" as="xs:string" select="if ($kind = 'creator') then 'author'
      else if ($kind = 'contact') then 'pointOfContact'
      else if ($kind = 'publisher') then 'publisher'
      else normalize-space(string($party/*[local-name() = 'role'][1]))"/>
    <xsl:variable name="email" select="normalize-space(string($party/*[local-name() = 'electronicMailAddress'][1]))"/>
    <xsl:sequence select="if ($name = '' and $organisation = '') then '' else concat(
      '{&quot;name&quot;:&quot;', kdb:json-string($name),
      '&quot;,&quot;organisation&quot;:&quot;', kdb:json-string($organisation),
      '&quot;,&quot;role&quot;:&quot;', kdb:json-string($role),
      '&quot;,&quot;email&quot;:&quot;', kdb:json-string($email),
      '&quot;,&quot;website&quot;:&quot;&quot;}')"/>
  </xsl:function>

  <xsl:function name="kdb:unique-in-order" as="xs:string*">
    <xsl:param name="values" as="xs:string*"/>
    <xsl:variable name="nonempty" as="xs:string*" select="$values[. != '']"/>
    <xsl:for-each select="$nonempty">
      <xsl:if test="not(lower-case(.) = lower-case(subsequence($nonempty, 1, position() - 1)))">
        <xsl:sequence select="."/>
      </xsl:if>
    </xsl:for-each>
  </xsl:function>

  <xsl:function name="kdb:unique-exact-in-order" as="xs:string*">
    <xsl:param name="values" as="xs:string*"/>
    <xsl:variable name="nonempty" as="xs:string*" select="$values[. != '']"/>
    <xsl:for-each select="$nonempty">
      <xsl:if test="not(. = subsequence($nonempty, 1, position() - 1))">
        <xsl:sequence select="."/>
      </xsl:if>
    </xsl:for-each>
  </xsl:function>

  <xsl:function name="kdb:valid-box" as="xs:boolean">
    <xsl:param name="box" as="element()"/>
    <xsl:variable name="west" select="normalize-space(string($box/*[local-name() = 'westBoundingCoordinate'][1]))"/>
    <xsl:variable name="south" select="normalize-space(string($box/*[local-name() = 'southBoundingCoordinate'][1]))"/>
    <xsl:variable name="east" select="normalize-space(string($box/*[local-name() = 'eastBoundingCoordinate'][1]))"/>
    <xsl:variable name="north" select="normalize-space(string($box/*[local-name() = 'northBoundingCoordinate'][1]))"/>
    <xsl:choose>
      <xsl:when test="$west castable as xs:decimal and $south castable as xs:decimal and $east castable as xs:decimal and $north castable as xs:decimal">
        <xsl:sequence select="xs:decimal($west) ge -180 and xs:decimal($west) le 180
          and xs:decimal($east) ge -180 and xs:decimal($east) le 180
          and xs:decimal($south) ge -90 and xs:decimal($south) le 90
          and xs:decimal($north) ge -90 and xs:decimal($north) le 90
          and xs:decimal($west) le xs:decimal($east)
          and xs:decimal($south) le xs:decimal($north)"/>
      </xsl:when>
      <xsl:otherwise><xsl:sequence select="false()"/></xsl:otherwise>
    </xsl:choose>
  </xsl:function>

  <xsl:function name="kdb:text-format" as="xs:string">
    <xsl:param name="text-format" as="element()"/>
    <xsl:variable name="object-name" select="normalize-space(string($text-format/../../*[local-name() = 'objectName'][1]))"/>
    <xsl:variable name="extension" select="lower-case(tokenize($object-name, '\.')[last()])"/>
    <xsl:sequence select="if ($extension = ('csv', 'tsv', 'txt')) then $extension else 'txt'"/>
  </xsl:function>

  <xsl:template name="kdb:index-fields">
    <xsl:param name="eml" as="element()"/>
    <xsl:param name="dataset" as="element()?"/>

    <Field name="kdbMetadataSchema" string="eml-gbif" store="true" index="true"/>
    <kdbMetadataSchema>eml-gbif</kdbMetadataSchema>
    <Field name="kdbIndexVersion" string="1" store="true" index="true"/>
    <kdbIndexVersion>1</kdbIndexVersion>

    <xsl:variable name="party-nodes" as="element()*" select="(
      $dataset/*[local-name() = 'creator'],
      $dataset/*[local-name() = 'contact'],
      $dataset/*[local-name() = 'associatedParty'],
      $dataset/*[local-name() = 'publisher'])"/>
    <xsl:variable name="party-values" as="xs:string*" select="for $party in $party-nodes return kdb:party-json($party)"/>
    <xsl:variable name="parties" as="xs:string*" select="kdb:unique-exact-in-order($party-values)"/>
    <Field name="kdbParties" type="object" string="[{string-join($parties, ',')}]" store="true" index="true"/>
    <kdbParties type="object"><xsl:value-of select="concat('[', string-join($parties, ','), ']')"/></kdbParties>

    <xsl:variable name="identifiers" as="xs:string*" select="for $identifier in $dataset/*[local-name() = 'alternateIdentifier'][normalize-space(.) != '']
      return normalize-space(string($identifier))"/>
    <Field name="kdbIdentifiers" type="object" string="[{string-join(for $value in $identifiers return concat('&quot;', kdb:json-string($value), '&quot;'), ',')}]" store="true" index="true"/>
    <kdbIdentifiers type="object"><xsl:value-of select="concat('[', string-join(for $value in $identifiers return concat('&quot;', kdb:json-string($value), '&quot;'), ','), ']')"/></kdbIdentifiers>

    <xsl:variable name="online" as="element()*" select="$dataset/*[local-name() = 'distribution']/*[local-name() = 'online']"/>
    <xsl:variable name="link-json" as="xs:string*">
      <xsl:for-each select="$online">
        <xsl:variable name="url" select="normalize-space(string(*[local-name() = 'url'][1]))"/>
        <xsl:if test="matches($url, '^https?://', 'i')">
          <xsl:sequence select="concat('{&quot;url&quot;:&quot;', kdb:json-string($url),
            '&quot;,&quot;name&quot;:&quot;', kdb:json-string(normalize-space(string(*[local-name() = 'onlineDescription'][1]))),
            '&quot;,&quot;description&quot;:&quot;&quot;,&quot;protocol&quot;:&quot;&quot;,&quot;function&quot;:&quot;',
            kdb:json-string(string(*[local-name() = 'url'][1]/@function)), '&quot;}')"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <Field name="kdbLinks" type="object" string="[{string-join($link-json, ',')}]" store="true" index="true"/>
    <kdbLinks type="object"><xsl:value-of select="concat('[', string-join($link-json, ','), ']')"/></kdbLinks>

    <xsl:variable name="boxes" as="element()*" select="$dataset/*[local-name() = 'coverage']/*[local-name() = 'geographicCoverage']/*[local-name() = 'boundingCoordinates'][kdb:valid-box(.)]"/>
    <xsl:variable name="box-json" as="xs:string*">
      <xsl:for-each select="$boxes">
        <xsl:sequence select="concat('[', string-join((
          normalize-space(string(*[local-name() = 'westBoundingCoordinate'][1])),
          normalize-space(string(*[local-name() = 'southBoundingCoordinate'][1])),
          normalize-space(string(*[local-name() = 'eastBoundingCoordinate'][1])),
          normalize-space(string(*[local-name() = 'northBoundingCoordinate'][1]))), ','), ']')"/>
      </xsl:for-each>
    </xsl:variable>
    <Field name="kdbBboxes" type="object" string="[{string-join($box-json, ',')}]" store="true" index="true"/>
    <kdbBboxes type="object"><xsl:value-of select="concat('[', string-join($box-json, ','), ']')"/></kdbBboxes>

    <xsl:variable name="type" select="normalize-space(string($eml/*[local-name() = 'additionalMetadata']/*[local-name() = 'metadata']/*[local-name() = 'gbif']/*[local-name() = 'hierarchyLevel'][normalize-space(.) != ''][1]))"/>
    <Field name="type" string="{if ($type != '') then $type else 'dataset'}" store="true" index="true"/>
    <type><xsl:value-of select="if ($type != '') then $type else 'dataset'"/></type>

    <xsl:variable name="format-values" as="xs:string*" select="(
      for $format in $eml/*[local-name() = 'additionalMetadata']/*[local-name() = 'metadata']/*[local-name() = 'gbif']/*[local-name() = 'physical']/*[local-name() = 'dataFormat']/*[local-name() = 'externallyDefinedFormat']/*[local-name() = 'formatName'][normalize-space(.) != '']
      return normalize-space(string($format)),
      for $format in $dataset/*[local-name() = 'dataTable']/*[local-name() = 'physical']/*[local-name() = 'dataFormat']/*[local-name() = 'externallyDefinedFormat']/*[local-name() = 'formatName'][normalize-space(.) != '']
      return normalize-space(string($format)),
      for $text in $dataset/*[local-name() = 'dataTable']/*[local-name() = 'physical']/*[local-name() = 'dataFormat']/*[local-name() = 'textFormat']
      return kdb:text-format($text))"/>
    <xsl:for-each select="kdb:unique-in-order($format-values)">
      <Field name="format" string="{.}" store="true" index="true"/>
      <format><xsl:value-of select="."/></format>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
