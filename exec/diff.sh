#!/bin/zsh

alias duck=~/duckdb/build/release/duckdb
ulimit -s unlimited

export BUCKET=tpch$RANDOM--apne1-az1--x-s3
export S3_BUCKET=s3://$BUCKET
aws s3api create-bucket \
    --bucket $BUCKET \
    --create-bucket-configuration 'Location={Type=AvailabilityZone,Name=apne1-az1},Bucket={DataRedundancy=SingleAvailabilityZone,Type=Directory}' \
    --output text --no-cli-pager

redis-cli flushall
rm -rf pool stats
mkdir pool stats

cp {nation,region}.parquet pool
for i in {0..24}; do
    echo $i
    duck :memory: "SET enable_profiling TO 'json'; SELECT * FROM 'tpch/$i/lineitem/*.parquet';" >/dev/null 2>&1
    python3 meta.py ingest tpch/$i/lineitem
    cp -aL tpch/$i/* pool
    aws s3 cp tpch/$i/lineitem $S3_BUCKET --recursive --only-show-errors

    rm -f file_stats.txt
done

let i++
for file in $(ls nr/*.sql | sort -V); do
    echo $file
    n=$(basename $file .sql)
    eval $(python3 query.py $n $i)

    export PRUNED=\'lineitem.parquet\'
    cat nr/h <(echo "EXPLAIN (FORMAT JSON)") nr/$n.sql | envsubst | duck | tail -n +7 >explain.json
    python3 meta.py prune
    python3 diff/prune.py

    cat nr/h $file | python3 envsubst.py | envsubst | duck | wc
    mv httpfs_stats.txt stats/$n.txt
    mv file_stats.txt stats/$n.bin
    mv stats.json stats/$n.json

    rm -f explain.json pruned.txt file_stats.txt httpfs_stats.txt stats.json
done

ret=$(python3 wair.py 2>metrics.txt)
if [[ -n $ret ]]; then
    echo $ret
    python3 diff/dynamic.py

    cat nr/h r.sql | duck
    mv httpfs_stats.txt stats/r.txt
    mv file_stats.txt stats/r.bin
    mv stats.json stats/r.json

    aws s3 cp $S3_BUCKET/r.parquet . --only-show-errors
    aws s3 rm $S3_BUCKET/r.parquet --only-show-errors
    ./split r.parquet
    python3 fix.py

    duck :memory: "SET enable_profiling TO 'json'; SELECT * FROM 'r/*.parquet';" >/dev/null 2>&1
    python3 meta.py ingest r
    cat files.txt | parallel -j 10 aws s3 cp r/{} $S3_BUCKET --only-show-errors
    cat trashes.txt | parallel -j 10 aws s3 rm $S3_BUCKET/{} --only-show-errors

    rm -rf metrics.txt files.txt trashes.txt r.parquet r.sql r
fi

aws s3 rm --recursive $S3_BUCKET --only-show-errors
aws s3 rb $S3_BUCKET
