#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

# export the SQLite to CSV
sqlite3 -header -csv $DIR/website.db "select * from website;" > $DIR/temp.csv
mv $DIR/temp.csv $DIR/../website.csv
