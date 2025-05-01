#!/bin/zsh

export J=33
export I=$((84 - 1 - $J))
export SF=$(($I * 10))

rm -rf tpch
mkdir tpch

head=0
for i in {0..$((I - 1))}; do
    echo $i
    export i
    cat dbgen.sql | envsubst | duckdb

    ./split tpch/$i/lineitem.parquet
    for src in $(ls tpch/$i/lineitem/*.parquet | sort -V); do
        dst=$(dirname $src)/$((head++)).parquet
        if [ $src != $dst ]; then
            mv $src $dst
        fi
    done

    rm tpch/$i/{lineitem.parquet,{load,schema}.sql}
    mv tpch/$i/{nation,region}.parquet .
    for file in tpch/$i/*.parquet; do
        _path=${file%.parquet}
        mkdir $_path
        mv $file $_path/$i.parquet
    done
done

echo $head

# head=$(ls tpch/*/lineitem/*.parquet | wc -l)

# head=
# for i in $(ls tpch/ | sort -V); do
#     echo $i $head
#     for src in $(ls tpch/$i/lineitem/*.parquet | sort -V); do
#         dst=$(dirname $src)/$((head++)).parquet
#         if [ $src != $dst ]; then
#             mv $src $dst
#         fi
#     done
# done
# echo $head
