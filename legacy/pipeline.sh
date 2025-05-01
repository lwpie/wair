#!/bin/bash

ulimit -s unlimited

# export S3_BUCKET=s3://tpch--apne1-az1--x-s3

export BUCKET=tpch$RANDOM--apne1-az1--x-s3
export S3_BUCKET=s3://$BUCKET
aws s3api create-bucket \
    --bucket $BUCKET \
    --create-bucket-configuration 'Location={Type=AvailabilityZone,Name=apne1-az1},Bucket={DataRedundancy=SingleAvailabilityZone,Type=Directory}' \
    --output text --no-cli-pager

# aws s3 rm $S3_BUCKET --recursive --only-show-errors

rm -rf pool stats
# cp -aL tpch pool
mkdir pool stats
cp {nation,region}.parquet pool
# aws s3 cp pool/lineitem $S3_BUCKET --recursive --only-show-errors

for i in $(ls tpch | sort -V); do
    echo $i

    if [[ $i -ge 25 ]]; then
        touch ingest.txt
        rm -rf files.txt trashes.txt r.sql explain.json

        for file in $(ls nr/*.sql | sort -V); do
            echo $file
            n=$(basename $file .sql)
            eval $(python3 query.py $n $i)

            export PRUNED=\'pool/lineitem/*.parquet\'
            cat nr/h <(echo "EXPLAIN (FORMAT JSON)") nr/$n.sql | envsubst | ~/duckdb/build/release/duckdb | tail -n +7 >explain.json
            python3 prune.py
            # export PRUNED=$(cat pruned.txt | envsubst)

            # export PRUNED=\'$S3_BUCKET/*.parquet\'

            # cat nr/h $file | envsubst | ~/duckdb/build/release/duckdb
            cat nr/h $file | python3 envsubst.py | envsubst | ~/duckdb/build/release/duckdb | wc
            mv httpfs_stats.txt stats/$n.txt
            mv stats.json stats/$n.json
        done

        if [[ $i -ge 0 ]]; then
            ret=$(python3 dynamic.py)
            if [[ -n $ret ]]; then
                echo $ret
                cat nr/h r.sql | ~/duckdb/build/release/duckdb
                mv httpfs_stats.txt stats/r.txt
                mv stats.json stats/r.json
                aws s3 rm $S3_BUCKET/tmp --only-show-errors
                cat files.txt | parallel -j 10 aws s3 cp pool/lineitem/{} $S3_BUCKET --only-show-errors
                cat trashes.txt | parallel -j 10 aws s3 rm $S3_BUCKET/{} --only-show-errors

                python3 analyze.py
            fi
        fi

        mkdir stats/$i
        mv stats/*.{txt,json} stats/$i
    fi

    cp -aL tpch/$i/* pool
    ls tpch/$i/lineitem >ingest.txt
    aws s3 cp tpch/$i/lineitem $S3_BUCKET --recursive --only-show-errors
done

let i++
echo $i

touch ingest.txt
rm -rf files.txt trashes.txt r.sql explain.json
for file in $(ls nr/*.sql | sort -V); do
    echo $file
    n=$(basename $file .sql)
    eval $(python3 query.py $n $i)

    export PRUNED=\'pool/lineitem/*.parquet\'
    cat nr/h <(echo "EXPLAIN (FORMAT JSON)") nr/$n.sql | envsubst | ~/duckdb/build/release/duckdb | tail -n +7 >explain.json
    python3 prune.py
    # export PRUNED=$(cat pruned.txt | envsubst)

    # export PRUNED=\'$S3_BUCKET/*.parquet\'

    cat nr/h $file | python3 envsubst.py | envsubst | ~/duckdb/build/release/duckdb | wc
    mv httpfs_stats.txt stats/$n.txt
    mv stats.json stats/$n.json
done

mkdir stats/$i
mv stats/*.{txt,json} stats/$i

aws s3 rm --recursive $S3_BUCKET --only-show-errors
aws s3api delete-bucket --bucket $BUCKET
