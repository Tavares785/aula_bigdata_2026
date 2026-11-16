#!/usr/bin/env bash
set -Eeuo pipefail
export AWS_PAGER='' AWS_DEFAULT_REGION=us-east-1
DB=$1; BUCKET=$2
TABLES=$(aws glue get-tables --database-name "$DB" --query 'TableList[].Name' --output text)
[[ -n "$TABLES" && "$TABLES" != None ]]
count=0
for table in $TABLES; do
  [[ "$table" =~ ^[a-zA-Z0-9_]+$ ]] || exit 1
  echo "===== ATHENA: $table ====="
  ID=$(aws athena start-query-execution --query-string "SELECT * FROM \"$table\" LIMIT 10" --query-execution-context "Database=$DB" --result-configuration "OutputLocation=s3://$BUCKET/athena/" --query QueryExecutionId --output text)
  echo "QueryExecutionId=$ID"
  state=QUEUED
  for ((i=0;i<120;i++)); do
    state=$(aws athena get-query-execution --query-execution-id "$ID" --query QueryExecution.Status.State --output text)
    case "$state" in SUCCEEDED) break;; FAILED|CANCELLED) aws athena get-query-execution --query-execution-id "$ID" --query QueryExecution.Status; exit 1;; esac
    sleep 5
  done
  [[ "$state" == SUCCEEDED ]]
  aws athena get-query-results --query-execution-id "$ID" --output table
  count=$((count+1))
done
[[ $count -ge 2 ]] || { echo 'Menos de duas tabelas catalogadas'; exit 1; }
