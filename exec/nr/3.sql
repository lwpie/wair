SELECT
    l_orderkey,
    sum(l_extendedprice * (1 - l_discount)) AS revenue,
    o_orderdate,
    o_shippriority
FROM
    'pool/customer/*.parquet',
    'pool/orders/*.parquet',
    read_parquet([$PRUNED])
WHERE
    c_mktsegment = '$SEGMENT'
    AND c_custkey = o_custkey
    AND l_orderkey = o_orderkey
    AND o_orderdate < DATE '1995-03-01' + INTERVAL $DELTA DAY
    AND l_shipdate > DATE '1995-03-01' + INTERVAL $DELTA DAY
GROUP BY
    l_orderkey,
    o_orderdate,
    o_shippriority
ORDER BY
    revenue DESC,
    o_orderdate
LIMIT 10;
