#!/usr/bin/env bash
#
# Download data w/o S3
#
##

# We want our paths to be relative to *this* script
# NOTE: Funky syntax to behave when *sourced* by ZSH (not that we do that here...)
SCRIPT_NAME="${BASH_SOURCE[0]-${(%):-%x}}"
SCRIPT_DIR="$(readlink -f "${SCRIPT_NAME%/*}")"
PROJECT_DIR="$(realpath "${SCRIPT_DIR}/..")"

BASE_URL="https://tal-m1-fouille.s3.gra.io.cloud.ovh.net"

DATA_LIST=(
	"processed/frwikisource-dev-micro.csv"
	# Also available: the *full* final corpus (2.2GB)
	# "processed/frwikisource-full.parquet"
)

s3_http_download() {
	wget "${BASE_URL}/${1}" -O "${PROJECT_DIR}/${1}"
}

for file in "${DATA_LIST[@]}" ; do
	s3_http_download "data/${file}"
done
