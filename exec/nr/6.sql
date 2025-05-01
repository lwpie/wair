SELECT
    sum(l_extendedprice * l_discount) AS revenue
FROM
    read_parquet([$PRUNED])
WHERE
    l_shipdate >= DATE '1992-01-01' + INTERVAL $DELTA MONTH
    AND l_shipdate < DATE '1993-01-01' + INTERVAL $DELTA MONTH
    AND l_discount BETWEEN 0.0$DISCOUNT - 0.01 AND 0.0$DISCOUNT + 0.01
    AND l_quantity < $QUANTITY;
