#!/bin/zsh

# Check all the code

setopt err_exit null_glob pipefail

SRC_DIR="src/olakaisdk"

ROOT=$0:a:h
cd $ROOT

ruff format --line-length 80 $SRC_DIR tests | \
	grep -vE "^[0-9]+ files left unchanged$" \
	|| true
find src tests -name "*.sh" -o -name "*.py" -o -name "*.txt" -o -name "*.toml" | \
	grep -vE "/\.ruff_cache/|/\.mypy_cache/|/\.egg-info/|/build/" | \
	xargs grep -niE "todo|xxx" | \
	grep -vE "^check.sh:.*todo.*$" | \
	sed 's|^\./||' | \
	sort
ruff check --fix $SRC_DIR tests | \
	grep -vx "All checks passed!" \
	|| true
mypy --ignore-missing-imports --no-color $SRC_DIR tests | \
	grep -vE "Found [0-9]+ errors in [0-9]+ files \(checked [0-9]+ source files\)" | \
	cut -d ":" -f1,2,4-
python -m unittest discover -s tests