#!/usr/bin/bash

curl https://static.snyk.io/cli/latest/snyk-linux -o snyk
chmod +x ./snyk
mv ./snyk /usr/local/bin/ 

SNYK_TOKEN=$SNYK_API_TOKEN

snyk test --all-projects --org=78b2f53f-b8ed-4a42-940f-60f8f8f18274