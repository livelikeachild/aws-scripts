#!/bin/bash
source ~/.customrc
./scripts/cpfroms3.sh scripts/runIllinoisTemporal.sh scripts/runIllinoisTemporal.sh && chmod 774 ~/scripts/runIllinoisTemporal.sh &
./scripts/cpfroms3.sh packages/illinois-temporal/illinois-temporal-1.0.0.jar ~/code/illinois-temporal/illinois-temporal-1.0.0.jar
mkdir -p data/nyt-annotated-jsons
mkdir -p log/illinois-temporal
mkdir -p results/illinois-temporal