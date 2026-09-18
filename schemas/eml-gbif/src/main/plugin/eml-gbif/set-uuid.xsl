<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet   xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
								xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
								exclude-result-prefixes="eml">	

	<!-- ================================================================= -->
	
	<xsl:template match="/root">
		 <xsl:apply-templates select="eml:eml"/>
	</xsl:template>

	<!-- ================================================================= -->

	<xsl:template match="eml:eml">
		<xsl:copy>
			<xsl:copy-of select="@*[name(.) != 'packageId']"/>
			<xsl:attribute name="packageId">
				<xsl:value-of select="/root/env/uuid"/>
			</xsl:attribute>
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
	
	<xsl:template match="*[local-name(.) = 'alternateIdentifier']"/>
	
	<!-- ================================================================= -->
	
	<xsl:template match="@*|node()">
		 <xsl:copy>
			  <xsl:apply-templates select="@*|node()"/>
		 </xsl:copy>
	</xsl:template>

	<!-- ================================================================= -->

</xsl:stylesheet>
