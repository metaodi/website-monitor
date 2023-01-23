#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

CSV_FILE=$1

# export the SQLite to CSV
sqlite3 -header -csv $DIR/website.db "SELECT * FROM website ORDER BY label COLLATE NOCASE ASC;" > $DIR/temp.csv
mv $DIR/temp.csv $DIR/../$CSV_FILE
