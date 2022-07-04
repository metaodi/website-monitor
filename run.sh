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
$DIR/update_hashes.py -d $DIR/website.db

# export the SQLite to CSV
sqlite3 -header -csv $DIR/website.db "select * from website;" > $DIR/temp.csv
mv $DIR/temp.csv $DIR/website.csv
