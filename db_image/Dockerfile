FROM postgres:latest
ARG DB_REPL_USER
ARG DB_REPL_PASSWORD

COPY init.sql /docker-entrypoint-initdb.d/

WORKDIR /app

RUN sed -i "s/123USERNAME/${DB_REPL_USER}/" /docker-entrypoint-initdb.d/init.sql
RUN sed -i "s/123PASSWORD/${DB_REPL_PASSWORD}/" /docker-entrypoint-initdb.d/init.sql

RUN mkdir -p /oracle/pg_data/archive \
    && chown postgres:postgres /oracle/pg_data/archive

