#!/usr/bin/env bash
# 테스트용 Postgres 데이터베이스를 새로 만들고, 실제 ../supabase_schema.sql 을 그대로 적용합니다.
# 접속 정보는 환경변수(PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE)로 바꿀 수 있습니다.
set -e
cd "$(dirname "$0")"
export PGHOST="${PGHOST:-127.0.0.1}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-postgres}" PGPASSWORD="${PGPASSWORD:-pw}"
DB="${PGDATABASE:-relmap_test2}"
psql -q -d postgres -c "drop database if exists $DB" -c "create database $DB"
psql -q -d "$DB" -f sql/env.sql 2>&1 | grep -v "WARNING\|HINT" || true
psql -q -d "$DB" -f ../supabase_schema.sql 2>&1 | grep -v NOTICE || true
psql -q -d "$DB" -f sql/notify_trigger.sql
echo "db ready ($DB)"
