#!/bin/bash

declare -a services
services[0]="ApproveOrReject:8001"
services[1]="checkMail:8002"
services[2]="ckan_requestor:8003"
services[3]="getApprovers:8004"
services[4]="sendMail:8005"
services[5]="get_reviewers:8006"

for service in ${services[@]}; do
    IFS=":" read -r -a arr <<< "${service}"
    kill -9 $(lsof -t -i:${arr[1]} -sTCP:LISTEN)
done