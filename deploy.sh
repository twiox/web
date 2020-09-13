#!/bin/bash

die () {
  echo "ERROR: $*. Aborting." >&2
  exit 1
}

#BOF PROGRAM =================================================================================================================================================================================================
NOW=$(date +"%s")
COMPOSE_FILE='docker-compose-server.yml'
# process arguments
STAGING='1'
PROD_FLAG=''
ENV='stage'
TAG='latest'
REBUILD=true
DOMAIN='stage.twio-x.com'
NETWORK_IP=127.0.0.50
ONEOF=0
while getopts "spt:" flag; do
  case ${flag} in
    s) ((ONEOF++));;
    p) ((ONEOF++)); ENV='prod'; PROD_FLAG=' -p'; STAGING='0'; DOMAIN='twio-x.com'; NETWORK_IP=127.0.0.51;;
    t) TAG="${OPTARG}";REBUILD=false;;
  esac
done

if [ "$ONEOF" -gt "1" ]; then
  die "You can't deploy multiple environments at once"
fi

echo "********************************************************"
echo "* ==================================================== *"
echo -e "* \E[37;44m\033[1m     TWIO X  DEPLOYMENT  AND  MAINTENANCE  TOOL     \033[0m *"
echo "* ==================================================== *"
echo "********************************************************"
echo ""

if [ "$ONEOF" = "0" ]; then
  echo ""
  echo "Help:"
  echo "This script builds and starts docker containers to run Twio X website."
  echo ""
  echo "  Options:"
  echo "    -s      - Build or update stage environment"
  echo "    -p      - Build or update production environment"
  echo ""
  exit
fi

if [ "${STAGING}" = "0" ]; then
  echo ""
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo -e  "!! \e[01;31mYou selected the PRODUCTION environment.\e[00m !!"
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo ""
fi

git pull

# check if volumes and network exist, otherwise create
#FILE_VOLUME_IS_NEW=false
#if [ $( docker volume ls | grep twio-$ENV-file | wc -l) == "0" ]; then
#  FILE_VOLUMES_IS_NEW=true
#  echo ""
#  echo "File volume does not exist. Creating it now."
#  docker volume create --name=twio-$ENV-file > /dev/null
#  echo "Created docker volume twio-$ENV-file"
#  echo ""
#fi;

DB_VOLUME_IS_NEW=false
if [ $( docker volume ls | grep twio-$ENV-db | wc -l) == "0" ]; then
  DB_VOLUME_IS_NEW=true
  echo ""
  echo "Database volume does not exist. Creating it now."
  docker volume create --name=twio-$ENV-db > /dev/null
  echo "Created docker volume twio-$ENV-db"
  echo ""
fi;


if [ $( docker network ls | grep twio-$ENV | wc -l) == "0" ]; then
  echo ""
  echo "Docker network does not exist. Creating it now."
  docker network create -o "com.docker.network.bridge.host_binding_ipv4"="$NETWORK_IP" twio-$ENV > /dev/null
  echo "Created docker network twio-$ENV"
  echo ""
fi;

# 1. If container is found running, we rebuild and restart
# 2. If container is found  stopped, just start
# 3. if container is not found at all, build and start

if [ $( docker ps | grep twio-$ENV-python | wc -l) == "1" ]; then
  if [ "$REBUILD" = true ]; then
    echo ""
    echo "Environment '$ENV' is running. Rebuilding container."
    echo ""

    # build:
    ENV=$ENV DOMAIN=$DOMAIN TAG=latest docker-compose -p twio-$ENV -f $COMPOSE_FILE build twio-python

    # now get currently used image tag, in case we want to roll back
    OLDIMGID=$(docker ps | grep twio-$ENV-python | awk '{print $2}' )
    OLDTAG=$(docker images | grep twio-python-server | grep $OLDIMGID | awk '{print $2}' )

    # replace container
    ENV=$ENV DOMAIN=$DOMAIN TAG=latest docker-compose -p twio-$ENV -f $COMPOSE_FILE up -d twio-python

    docker tag twio-python-server:latest twio-python-server:$NOW

    echo ""
    echo "New container is up & running. To switch back to the previous version, run './deploy.sh$PROD_FLAG -t $OLDTAG'"
    echo ""
  else
    # TODO: Check if tag exists, return error and exit if not
    echo ""
    echo "TAG $TAG given. Won't rebuild, just restart image."
    echo ""
    ENV=$ENV DOMAIN=$DOMAIN TAG=$TAG docker-compose -p twio-$ENV -f $COMPOSE_FILE up -d twio-python
  fi
else
  echo ""
  echo "Environment '$ENV' is not running. Starting docker-compose up."
  echo ""
  ENV=$ENV DOMAIN=$DOMAIN TAG=latest docker-compose -p twio-$ENV -f $COMPOSE_FILE up -d
  echo ""
fi

exit
