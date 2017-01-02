#!/bin/bash

DOCKER="docker -H=tcp://127.0.0.1:4243"

${DOCKER} rm $(${DOCKER}  ps -a -q)
${DOCKER} rmi $(${DOCKER} images | grep "^<none>" | awk '{ print $3 }')
