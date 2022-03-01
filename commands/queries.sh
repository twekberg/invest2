#!/usr/bin/env bash
#
# Run queries and generate CSV files.

for sql_file in sql/*.sql; do
    csv_file="$(echo $sql_file | sed 's/.sql$//').csv"
    tmp_file="$(echo $sql_file | sed 's/.sql$//').tmp"
    cols_file="$(echo $sql_file | sed 's/.sql$//').cols"
    echo $csv_file
    (echo ".mode csv"; echo ".once $tmp_file"; cat $sql_file; echo ".q") | sqlite3.exe investments.db
    cat $cols_file $tmp_file > $csv_file
    rm $tmp_file
done
