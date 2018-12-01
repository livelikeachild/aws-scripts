#!/bin/bash
read -r -a array <<<"$1"

for index in "${!array[@]}"
do
    echo "$index ${array[index]}"
done
