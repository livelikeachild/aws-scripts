#!/bin/bash
read -r -a array <<<"$1"

for index in "${!array[@]}"
do
    echo "$index ${array[index]}"
    aws s3 cp ~/results/illinois-temporal/${array[index]}/${array[index]}.stats s3://cogcomp-public-data/results/illinois-temporal-postprocessing/${array[index]}.stats
done
