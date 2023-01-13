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
sqlite3 $DIR/website.db -cmd '.mode csv' -cmd ".import $DIR/../website.csv website" .quit
