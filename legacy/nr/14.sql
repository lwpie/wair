SELECT
    100.00 * sum(CASE
            WHEN p_type LIKE 'PROMO%' 
            THEN l_extendedprice * (1 - l_discount)
            ELSE 0
    END) / sum(l_extendedprice * (1 - l_discount)) AS promo_revenue
FROM
    read_parquet([$PRUNED]),
    'pool/part/*.parquet'
WHERE
    l_partkey = p_partkey
    AND l_shipdate >= DATE '1992-01-01' + INTERVAL $DELTA MONTH
    AND l_shipdate < DATE '1992-02-01' + INTERVAL $DELTA MONTH;
