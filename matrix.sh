#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

# import the CSV to SQLite
rm -rf $DIR/website.db
sqlite3 $DIR/website.db -cmd '.mode csv' -cmd '.import website.csv website' .quit

# run script to check each website
$DIR/build_matrix.py -d $DIR/website.db | jq -cnR
