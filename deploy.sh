#!/bin/bash

set -ex

gcloud auth activate-service-account --key-file "${PWD}/gcp-key-dev.json" || die "unable to authenticate service account for gcloud"
gcloud --quiet config set project "development-223016"

for runtime in */; do
  for function in $runtime/*; do
    if [ -d $function ]; then
      runtime=${runtime%/} #ignore slash
      func_name=${function##*/} #split and take last
      gcloud functions deploy $func_name --source $function --region europe-west1 --trigger-http --runtime $runtime --allow-unauthenticated
    fi
  done
done
