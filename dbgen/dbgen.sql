CALL dbgen(sf=$SF, children=$I, step=$i);

--- O_ORDERDATE uniformly distributed between STARTDATE and (ENDDATE - 151 days).

UPDATE orders SET o_orderdate = ('1992-01-01'::DATE + INTERVAL $i MONTH)::DATE + floor(random() * (('1992-01-01'::DATE + INTERVAL 
($i + 1) MONTH)::DATE - ('1992-01-01'::DATE + INTERVAL $i MONTH)::DATE))::INT;

--- L_SHIPDATE = O_ORDERDATE + random value [1 .. 121].

-- UPDATE lineitem SET l_shipdate = (SELECT o_orderdate FROM orders WHERE l_orderkey = o_orderkey) + floor(random() * 121 + 1)::INT;
UPDATE lineitem SET l_shipdate = (SELECT o_orderdate FROM orders WHERE l_orderkey = o_orderkey) + floor(random() * (('1992-01-01'::DATE + INTERVAL ($i + $J) MONTH)::DATE - ('1992-01-01'::DATE + INTERVAL $i MONTH)::DATE))::INT;

--- L_COMMITDATE = O_ORDERDATE + random value [30 .. 90].

UPDATE lineitem SET l_commitdate = (SELECT o_orderdate FROM orders WHERE l_orderkey = o_orderkey) + floor(random() * 61 + 30)::INT;

-- L_LINESTATUS set the following value:
-- "O" if L_SHIPDATE > CURRENTDATE
-- "F" otherwise.

UPDATE lineitem SET l_linestatus = CASE WHEN l_shipdate > '1995-06-17'::DATE THEN 'O' ELSE 'F' END;

-- L_RECEIPTDATE = L_SHIPDATE + random value [1 .. 30].

UPDATE lineitem SET l_receiptdate = l_shipdate + floor(random() * 30 + 1)::INT;

-- L_RETURNFLAG set to a value selected as follows:
-- If L_RECEIPTDATE <= CURRENTDATE
--     then either "R" or "A" is selected at random
--     else "N" is selected.

UPDATE lineitem SET l_returnflag = CASE WHEN l_receiptdate <= '1995-06-17'::DATE THEN CASE WHEN random() < 0.5 THEN 'R' ELSE 'A' END ELSE 'N' END;

-- O_ORDERSTATUS set to the following value:
-- "F" if all lineitems of this order have L_LINESTATUS set to "F".
-- "O" if all lineitems of this order have L_LINESTATUS set to "O".
-- "P" otherwise.

UPDATE orders SET o_orderstatus = CASE WHEN (SELECT COUNT(*) FROM lineitem WHERE l_orderkey = o_orderkey AND l_linestatus = 'F') = (SELECT COUNT(*) FROM lineitem WHERE l_orderkey = o_orderkey) THEN 'F' WHEN (SELECT COUNT(*) FROM lineitem WHERE l_orderkey = o_orderkey AND l_linestatus = 'O') = (SELECT COUNT(*) FROM lineitem WHERE l_orderkey = o_orderkey) THEN 'O' ELSE 'P' END;

EXPORT DATABASE 'tpch/$i' (FORMAT 'parquet');
