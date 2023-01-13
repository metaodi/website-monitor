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

# update db from params
$DIR/increase_error_count.py -d $DIR/website.db --hash $1

# export the SQLite to CSV
sqlite3 -header -csv $DIR/website.db "select * from website;" > $DIR/temp.csv
mv $DIR/temp.csv $DIR/../website.csv
