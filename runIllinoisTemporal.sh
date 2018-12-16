#!/bin/bash
source ~/.customrc
read -r -a array <<<"$1"
if [ $# -lt 2 ]; then
	forceUpdate=false
else
	forceUpdate=$2
fi
if [ $# -lt 3 ]; then
	MAX_NUM_EVENT=300
else
	MAX_NUM_EVENT=$3
fi
echo "forceUpdate="$forceUpdate
echo "MAX_NUM_EVENT="$MAX_NUM_EVENT
for index in "${!array[@]}"
do
	partition=${array[index]}
    echo partition=$partition
    cpfroms3.sh results/illinois-temporal/$partition.ser.tgz data/nyt-annotated-jsons/$partition.ser.tgz && echo $partition.ser.tgz copied
	tar xzf data/nyt-annotated-jsons/$partition.ser.tgz -C data/nyt-annotated-jsons
	cd ~/code/illinois-temporal
	java -jar ~/code/illinois-temporal/illinois-temporal-1.0.0.jar ~/data/nyt-annotated-jsons/$partition ~/results/illinois-temporal/$partition ~/log/illinois-temporal $partition.log

	cd ~/results/illinois-temporal
	tar czf $partition.temprel.tgz $partition/*.temprel
	cptos3.sh $partition.temprel.tgz results/illinois-temporal-postprocessing/$partition.temprel.tgz
	cptos3.sh $partition/$partition.stats results/illinois-temporal-postprocessing/$partition.stats
	cd ~
	cptos3.sh ~/log/illinois-temporal/$partition.log logs/illinois-temporal-postprocessing/$partition.log
done