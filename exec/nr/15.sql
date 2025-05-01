WITH revenue AS (
    SELECT
        l_suppkey AS supplier_no,
        sum(l_extendedprice * (1 - l_discount)) AS total_revenue
    FROM
        read_parquet([$PRUNED])
    WHERE
        l_shipdate >= DATE '1992-01-01' + INTERVAL $DELTA MONTH
        AND l_shipdate < DATE '1992-01-01' + INTERVAL $DELTA MONTH + INTERVAL 3 MONTH
    GROUP BY
        supplier_no
)
SELECT
    s_suppkey,
    s_name,
    s_address,
    s_phone,
    total_revenue
FROM
    'pool/supplier/*.parquet',
    revenue
WHERE
    s_suppkey = supplier_no
    AND total_revenue = (
        SELECT
            max(total_revenue)
        FROM
            revenue
    )
ORDER BY
    s_suppkey;
