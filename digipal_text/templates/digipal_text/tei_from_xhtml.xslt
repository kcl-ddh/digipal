<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:template match="/root">
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>"Faith is a fine invention"</title>
                        <author>by Emily Dickinson</author>
                        <respStmt>
                            <name>John Davis</name>
                            <resp>Editing</resp>
                        </respStmt>
                        <respStmt>
                            <name>Geoffroy Noel</name>
                            <resp>Text encoding</resp>
                        </respStmt>
                    </titleStmt>
                    <publicationStmt>
                        <availability>
                            <p>This text is available only for demonstration purposes. It was
                                created as part of a research project to experiment with ways of
                                displaying multiple witnesses of a TEI-encoded poem using XML,
                                XSLT and JavaScript.</p>
                        </availability>
                    </publicationStmt>
                    <sourceDesc>
                        <listWit>
                            <witness xml:id="A660" n="va660" facs="images/p1891.jpg">
                                A 660, verse embedded in letter to Samuel Bowles.
                            </witness>
                        </listWit>
                    </sourceDesc>
                </fileDesc>
                <encodingDesc>
                    <projectDesc>
                        <p>Test document for versioning machine project. Marked-up
                            collation of three manuscript witnesses: A 660, H 201, and H 72,
                            and four early print witnesses: Poems (1891)--XXX, Letters
                            (1894)--p. 191, Complete Poems (1924)--LVI, and Life and Letters
                            (1926)--p. 227. </p>
                    </projectDesc>
                    <variantEncoding location="internal" method="parallel-segmentation" />
                </encodingDesc>
            </teiHeader>
            <text>
                <body>
                    <xsl:apply-templates />
                </body>
            </text>
        </TEI>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="span[@data-dpt='location'][@data-dpt-loctype='locus']">
        <xsl:element name="pb">
            <xsl:attribute name="n">
                <xsl:value-of select="text()" />
            </xsl:attribute>
        </xsl:element>
    </xsl:template>

    <xsl:template match="span[@data-dpt='lb']">
        <lb/>
    </xsl:template>

    <xsl:template match="span[@data-dpt='ex']">
        <ex><xsl:apply-templates/></ex>
    </xsl:template>

    <xsl:template match="span[@data-dpt='clause']">
        <xsl:element name="div">
            <xsl:attribute name="type">diplomatic</xsl:attribute>
            <xsl:attribute name="subtype">
                <xsl:value-of select="@data-dpt-type" />
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

</xsl:stylesheet>
