<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

{% block tei %}

    <xsl:template match="/root">
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            {% block header %}
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        {% block title %}
                            <title>{{ meta.title }}</title>
                        {% endblock %}
                        {% block author %}
                            {% for author in meta.authors %}
                                <author>{{ author }}</author>
                            {% endfor %}
                        {% endblock %}
                        {% block work_resps %}
                            {% for resp in meta.work_resps %}
                                <respStmt>
                                    <name>{{ resp.person }}</name>
                                    <resp>{{ resp.label }}</resp>
                                </respStmt>
                            {% endfor %}
                        {% endblock %}
                    </titleStmt>
                    <editionStmt>
                        {% block edition %}
                            <edition>{{ meta.project }} edition, <date>{{ meta.edition.date }}</date></edition>
                        {% endblock %}
                        {% block edition_resps %}
                            {% for resp in meta.edition_resps %}
                                <respStmt>
                                    <name>{{ resp.person }}</name>
                                    <resp>{{ resp.label }}</resp>
                                </respStmt>
                            {% endfor %}
                        {% endblock %}
                    </editionStmt>
                    <publicationStmt>
                        {# Publication of what? derived digital edition or original MS??? #}
                        {% if meta.authority %}
                            <authority>{{ meta.authority }}</authority>
                        {% endif %}
                        {% if meta.availability %}
                            <availability>{{ meta.availability }}</availability>
                        {% endif %}
                    </publicationStmt>
                    <sourceDesc>
                        {% if meta.ms %}
                            <msDesc>
                                <msIdentifier>
                                    <settlement>{{ meta.ms.place }}</settlement>
                                    <repository>{{ meta.ms.repository }}</repository>
                                    <idno>{{ meta.ms.shelfmark }}</idno>
                                </msIdentifier>
                            </msDesc>
                        {% endif %}
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
            {% endblock %}
            {% block text %}
            <text>
                <body>
                    <div>
                        <xsl:apply-templates />
                    </div>
                </body>
            </text>
            {% endblock %}
        </TEI>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    {% block location_locus %}
    <xsl:template match="span[@data-dpt='location'][@data-dpt-loctype='locus']">
        <xsl:element name="pb">
            <xsl:attribute name="n">
                <xsl:value-of select="text()" />
            </xsl:attribute>
        </xsl:element>
    </xsl:template>
    {% endblock %}

    {% block line_break %}
    <xsl:template match="span[@data-dpt='lb']">
        <lb/>
    </xsl:template>
    {% endblock %}

    {% block expansion %}
    <xsl:template match="span[@data-dpt='ex']">
        <ex><xsl:apply-templates/></ex>
    </xsl:template>
    {% endblock %}

    {% block em %}
    {# NOTE: what is the difference with ex??? #}
    <xsl:template match="em">
        <ex><xsl:apply-templates/></ex>
    </xsl:template>
    {% endblock %}

    {% block supplied %}
    <xsl:template match="span[@data-dpt='supplied']">
        <supplied><xsl:apply-templates/></supplied>
    </xsl:template>
    {% endblock %}

    {% block clause %}
    <xsl:template match="span[@data-dpt='clause']">
        <xsl:element name="seg">
            <xsl:attribute name="type">diplomatic</xsl:attribute>
            <xsl:attribute name="subtype">
                <xsl:value-of select="@data-dpt-type" />
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    {% endblock %}

    {% block person_name %}
    <xsl:template match="span[@data-dpt='person'][@data-dpt-type='name']">
        <persName><xsl:apply-templates/></persName>
    </xsl:template>
    {% endblock %}

    {% block person_title %}
    {# TODO: join contiguous name and role under the same persName element #}
    {# NOTE: no info about the type of role #}
    <xsl:template match="span[@data-dpt='person'][@data-dpt-type='title']">
        <persName><roleName><xsl:apply-templates/></roleName></persName>
    </xsl:template>
    {% endblock %}

{% endblock %}

</xsl:stylesheet>
