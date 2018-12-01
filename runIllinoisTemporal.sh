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
    cpfroms3.sh processed/nyt-annotated-zipped-jsons/$partition.zip data/nyt-annotated-jsons/$partition.zip && echo $partition.zip copied
	unzip data/nyt-annotated-jsons/$partition.zip -d data/nyt-annotated-jsons
	cd ~/code/illinois-temporal
	java -jar ~/code/illinois-temporal/illinois-temporal-1.0.0.jar ~/data/nyt-annotated-jsons/$partition ~/results/illinois-temporal/$partition ~/log/illinois-temporal $partition.log $forceUpdate $MAX_NUM_EVENT

	cd ~/results/illinois-temporal
	tar czf $partition.ser.tgz $partition/*.ser
	tar czf $partition.timeline.tgz $partition/*.timeline
	cptos3.sh $partition.ser.tgz results/illinois-temporal/$partition.ser.tgz
	cptos3.sh $partition.timeline.tgz results/illinois-temporal/$partition.timeline.tgz
	cd ~
	cptos3.sh ~/log/illinois-temporal/$partition.log logs/illinois-temporal/$partition.log
done