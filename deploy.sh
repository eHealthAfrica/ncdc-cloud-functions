#!/bin/bash

set -ex

export GOOGLE_APPLICATION_CREDENTIALS="gcp-key-dev.json"
export GOOGLE_CLOUD_PROJECT="development-223016"

for runtime in */; do
  for function in $runtime/*; do
    if [ -d $function ]; then
      runtime=${runtime%/} #ignore slash
      func_name=${function##*/} #split and take last
      gcloud functions deploy $func_name --source $function --region europe-west1 --trigger-http --runtime $runtime --allow-unauthenticated
    fi
  done
done
