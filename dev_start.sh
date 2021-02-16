#!/bin/bash

HOME=$PWD

start () {
    declare -a services
    services[0]="ApproveOrReject:8001"
    services[1]="checkMail:8002"
    services[2]="ckan_requestor:8003"
    services[3]="getApprovers:8004"
    services[4]="sendMail:8005"
    services[5]="get_reviewers:8006"
    services[6]="ckan_utils:8007"

    for service in ${services[@]}; do
        IFS=":" read -r -a arr <<< "${service}"
        kill -9 $(lsof -t -i:${arr[1]} -sTCP:LISTEN)
        cd ${HOME}/python37/${arr[0]}
        functions-framework --target ${arr[0]} --port ${arr[1]} --debug &
    done
}

start
