FROM tomcat:9.0-jdk17-temurin

ARG GEONETWORK_WAR=geonetwork.war

ENV CATALINA_OPTS="-Dgeonetwork.dir=/var/lib/geonetwork_data -Xms1g -Xmx2g" \
    GEONETWORK_ES_PROTOCOL=http \
    GEONETWORK_ES_HOST=elasticsearch \
    GEONETWORK_ES_PORT=9200

RUN rm -rf /usr/local/tomcat/webapps/*
RUN sed -i 's#port="8080" protocol="HTTP/1.1"#port="8080" protocol="HTTP/1.1" maxPostSize="-1" maxSwallowSize="-1"#' /usr/local/tomcat/conf/server.xml
COPY ${GEONETWORK_WAR} /tmp/ROOT.war
RUN mkdir -p /usr/local/tomcat/webapps/ROOT \
    && cd /usr/local/tomcat/webapps/ROOT \
    && jar -xf /tmp/ROOT.war \
    && rm /tmp/ROOT.war
COPY deploy-manifest.sha256 /opt/izrk/deploy-manifest.sha256
COPY runtime/webapp/ /usr/local/tomcat/webapps/ROOT/
COPY runtime/schema_plugins/eml-gbif /opt/izrk/schema_plugins/eml-gbif
COPY scripts/docker-entrypoint.sh /usr/local/bin/izrk-entrypoint.sh
COPY scripts/sync-public-url.sh /usr/local/bin/izrk-sync-public-url.sh
RUN chmod +x /usr/local/bin/izrk-entrypoint.sh /usr/local/bin/izrk-sync-public-url.sh

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/izrk-entrypoint.sh"]
