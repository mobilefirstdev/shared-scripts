#!/usr/bin/env bash
# Downloads the JSON Swagger document
cd "$(dirname "$0")"
set -e
if [ $# -ne 2 ]; then
    >&2 echo "Must provide the stage and service name as arguments 1 and 2."
    exit 1
fi
stage=$1
serviceName=$2
region=us-west-2
apiId=$(aws apigateway get-rest-apis --profile=m1dev --output=json --region=$region | /usr/bin/env node ./extract-rest-api-id.js "$stage" "$serviceName")
fileType=json
outputFileName=$stage-$serviceName-docs.$fileType
s3BucketPath=s3://budboard-api-docs/$stage/docs/
printf "Downloading Swagger definition to ../../docs/api-docs/%s
  API ID: %s
   Stage: %s
  Accept: %s\n\n" "$outputFileName" "$apiId" "$stage" "$fileType"

aws apigateway get-export \
  --rest-api-id="$apiId" \
  --stage-name="$stage" \
  --export-type=swagger \
  --accept=application/$fileType \
  --region=$region \
  --profile=m1dev \
  ../../docs/api-docs/"$outputFileName"

printf "$(tput setaf 2)Done, your swagger document is: ../../docs/api-docs/%s \n\n $(tput sgr0)" "$outputFileName"

aws --profile=m1dev \
  --region=$region \
  s3 cp ../../docs/api-docs/"$outputFileName" "$s3BucketPath"

printf "$(tput setaf 2)Done, api docs uploaded to: ./%s \n\n $(tput sgr0)" "$s3BucketPath"