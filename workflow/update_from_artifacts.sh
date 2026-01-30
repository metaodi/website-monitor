#!/bin/bash

set -e
set -o pipefail

function cleanup {
      exit $?
  }
trap "cleanup" EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"

# update hashes in db from artifacts
for artifact in $DIR/../output/hashes/*.txt
do
    old_hash=$(basename $artifact .txt)
    new_hash=$(cat $artifact)
    uv run $DIR/update_hash.py -d $DIR/website.db -o $old_hash -n $new_hash
done

# update error_counts in db from artifacts
for artifact in $DIR/../output/error_counts/*.txt
do
    error_hash=$(basename $artifact .txt)
    uv run $DIR/increase_error_count.py -d $DIR/website.db --hash="${error_hash}"
done
