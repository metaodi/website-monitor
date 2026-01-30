#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

# import the CSV to SQLite
$DIR/populate_database.sh $1

# run script to check each website
uv run $DIR/build_matrix.py -d $DIR/website.db
