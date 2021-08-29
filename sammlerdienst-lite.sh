#!/bin/bash

# parse command line arguments
while getopts u:d: flag
do
    case "${flag}" in
        u) SERVER_URL=${OPTARG};;
        d) DIR=${OPTARG};;
        ?)
          echo "Invalid option: -${OPTARG}."
          echo
          usage
          ;;
    esac
done

# show usage
if [ -z "$SERVER_URL" ] || [ -z "$DIR" ]; then
  echo "Usage: $(basename $0) -u https://server_url/xzufi -d ./data/downlaod_dir"
  echo "   -u=URL   the url where 'index.txt' can be found."
  echo "   -d=DIR   save files to DIR/"
  exit 1
fi

# download index.txt
wget --directory-prefix=$DIR "$SERVER_URL/index.txt"

# download files listed in index.txt
while read filename; do
  url=$(echo "$SERVER_URL/$filename" | tr -d '\r')
  wget --directory-prefix=$DIR "$url"
done < $DIR/index.txt
