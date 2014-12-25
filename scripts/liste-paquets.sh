#!/bin/sh

cd "$(dirname $(pwd)/$0)/.."
grep -h import archeo-lex marcheolex/*.py | grep -v '#import' | grep -v marcheolex | sort | uniq | sed 's/^import //' | sed 's/from \([^ ]*\) import .*/\1/' | sed 's/\..*//' | sort | uniq
