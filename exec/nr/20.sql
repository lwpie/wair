SELECT
    s_name,
    s_address
FROM
    'pool/supplier/*.parquet',
    'pool/nation.parquet'
WHERE
    s_suppkey IN (
        SELECT
            ps_suppkey
        FROM
            'pool/partsupp/*.parquet'
        WHERE
            ps_partkey IN (
                SELECT
                    p_partkey
                FROM
                    'pool/part/*.parquet'
                WHERE
                    p_name LIKE '$COLOR%')
                AND ps_availqty > (
                    SELECT
                        0.5 * sum(l_quantity)
                    FROM
                        read_parquet([$PRUNED])
                    WHERE
                        l_partkey = ps_partkey
                        AND l_suppkey = ps_suppkey
                        AND l_shipdate >= DATE '1992-01-01' + INTERVAL $DELTA MONTH
                        AND l_shipdate < DATE '1993-01-01' + INTERVAL $DELTA MONTH
                )
            )
            AND s_nationkey = n_nationkey
            AND n_name = '$NATION'
        ORDER BY
            s_name;
