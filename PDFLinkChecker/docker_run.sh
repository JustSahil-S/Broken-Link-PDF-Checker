#!/bin/bash

DEF_INST_UIPORT="8000"
DEF_DATA_DIR="/DATA"
DEF_PM2_OPTIONS="-m -s"

show_usage() {
    cat << EOF

USAGE:
docker run -ti -v <host_dir>:/DATA [-p <UI_port>:2000] [--name="cnt_name"] <docker_image><:tag>

host_dir:  directory for container data. Use an existing directory for state persistency through upgrades
ui_port:   any unused TCP port for UI (optional)
cnt_name:  container name, same as inst_name preferred (optional)
tag:       optional tag

EXAMPLES:
docker run -ti -v ~/my_data:/DATA  broken_link_checker:latest
docker run -ti -v ~/my_data:/DATA  --name "django_app"  broken_link_checker:latest

EOF
}

if [ -z "$INST_UIPORT" ]
then
    export INST_UIPORT=$DEF_INST_UIPORT
fi
if [ -z "$DATA_DIR" ]
then
    export DATA_DIR=$DEF_DATA_DIR

if [ ! -d $DATA_DIR ]
then
    echo $DATA_DIR "not mounted!!!"
    echo "Please re-instantiate docker container by mounting (-v option) a host directory at /DATA"
    show_usage
    exit 1
fi

if [ ! -f $DATA_DIR/db.sqlite3 ]
then
    echo "################################"
    echo "#    Initializing Database     #"
    echo "################################"

    echo "DATA_DIR directory is set to: "$DATA_DIR

    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
fi

:'
if [ -z "$PM2_OPTIONS" ]
then
    PM2_OPTIONS=$DEF_PM2_OPTIONS
fi
if [ -f $DATA_DIR/pm2_$INST_ID.json ]
then
    # enable redis and python server if necessary
    if [ ! -z "$PYTHON_SERVER" ]
    then
        redis-server &
        pm2 start $ERED_DIR/bin/eREDServer.py $PM2_OPTIONS --name ered_py
    fi
    pm2 start $DATA_DIR/pm2_$INST_ID.json $PM2_OPTIONS --name ered
    pm2 logs
else
    echo "pm2_$INST_ID.json" file not found!!!
    echo "exiting"
    exit 1
fi
'
python manage.py runserver 0.0.0.0:$INST_UIPORT