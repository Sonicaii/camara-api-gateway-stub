#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
  CREATE ROLE keycloak_owner WITH LOGIN PASSWORD '${KEYCLOAK_OWNER_PASSWORD}';
  CREATE DATABASE keycloak;
  GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak_owner;
  \connect keycloak
  CREATE SCHEMA keycloak AUTHORIZATION keycloak_owner;
EOSQL