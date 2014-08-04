#!/bin/sh

cd "$(dirname $(pwd)/$0)/.."
grep -h import archéo-lex legifrance/*.py | grep -v '#import' | grep -v legifrance | sort | uniq | sed 's/^import //' | sed 's/from \([^ ]*\) import .*/\1/' | sed 's/\..*//' | sort | uniq
