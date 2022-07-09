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

# update db from artifacts
for artifact in $DIR/hashes/*.txt
do
    old_hash=$(basename $artifact .txt)
    new_hash=$(cat $artifact)
    $DIR/update_hash.py -d $DIR/website.db -o $old_hash -n $new_hash
done

# export the SQLite to CSV
sqlite3 -header -csv $DIR/website.db "select * from website;" > $DIR/temp.csv
mv $DIR/temp.csv $DIR/website.csv
