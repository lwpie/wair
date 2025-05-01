SELECT
    l_shipmode,
    sum(CASE 
            WHEN o_orderpriority = '1-URGENT'
                OR o_orderpriority = '2-HIGH' 
            THEN 1
            ELSE 0
    END) AS high_line_count,
    sum(CASE
            WHEN o_orderpriority <> '1-URGENT'
                AND o_orderpriority <> '2-HIGH'
            THEN 1
            ELSE 0
    END) AS low_line_count
FROM
    'pool/orders/*.parquet',
    read_parquet([$PRUNED])
WHERE
    o_orderkey = l_orderkey
    AND l_shipmode IN ('$SHIPMODE1', '$SHIPMODE2')
    AND l_commitdate < l_receiptdate
    AND l_shipdate < l_commitdate
    AND l_receiptdate >= DATE '1992-01-01' + INTERVAL $DELTA MONTH
    AND l_receiptdate < DATE '1993-01-01' + INTERVAL $DELTA MONTH
GROUP BY
    l_shipmode
ORDER BY
    l_shipmode;
