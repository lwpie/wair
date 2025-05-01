#!/bin/zsh

rm -f file_stats.txt duck.txt

for file in $(ls tpch/0/lineitem/*.parquet | sort -V); do
    result_set_size=$(duckdb :memory: "SET enable_profiling TO 'json'; SELECT l_receiptdate FROM '$file' WHERE l_shipdate <= DATE '1992-12-01';" >/dev/null 2> >(grep result_set_size) | tail -n 1 | grep -oP '\d+')
    echo $file l_receiptdate $result_set_size >>duck.txt
    result_set_size=$(echo ".mode csv\nSELECT SUM(bit_length(l_shipmode)) FROM '$file' WHERE l_shipdate <= DATE '1992-12-01';" | duckdb | grep -oP '\d+')
    echo $file l_shipmode $result_set_size >>duck.txt
done

~/duckdb/build/release/duckdb :memory: "SET enable_profiling TO 'json'; SET profiling_output TO 'stats.json'; SET threads TO 32; SELECT l_receiptdate, l_shipmode FROM 'tpch/0/lineitem/*.parquet' WHERE l_shipdate <= DATE '1992-12-01';" >/dev/null

python3 diff/diff.py file_stats.txt duck.txt
