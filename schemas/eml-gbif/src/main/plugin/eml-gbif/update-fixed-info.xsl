<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
								xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
								xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
								exclude-result-prefixes="eml">	

	<!-- ================================================================= -->

	<xsl:template match="/root">
		<xsl:apply-templates select="eml:eml"/>
	</xsl:template>

	<!-- ================================================================= -->

	<xsl:template match="eml:eml">
		<xsl:copy>
			<xsl:copy-of select="@*[name(.)!='xsi:schemaLocation']"/>
			<xsl:attribute name="xsi:schemaLocation">https://eml.ecoinformatics.org/eml-2.2.0 http://rs.gbif.org/schema/eml-gbif-profile/dev/eml.xsd</xsl:attribute>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->

	<xsl:template match="dataset">
		<xsl:copy>
			<xsl:copy-of select="@*"/>
			<alternateIdentifier>
				<xsl:value-of select="/root/env/uuid"/>
			</alternateIdentifier>
			<xsl:apply-templates select="node()[local-name(.) != 'alternateIdentifier']"/>
		</xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->
	<!-- GeoNetwork manages the metadata UUID in alternateIdentifier. Drop
	     existing values before writing the current UUID to avoid duplicates. -->

	<xsl:template match="*[local-name(.) = 'alternateIdentifier']"/>

	<!-- ================================================================= -->
	<!-- copy everything else as is -->
	
	<xsl:template match="@*|node()">
	    <xsl:copy>
	        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
	</xsl:template>

</xsl:stylesheet>
