#!/bin/bash

cd $(dirname ${0})/..
version="$(cat VERSION)"

if `git tag --list | grep -q ${version}`; then
  echo "A tag for this version (${version}) already exists. Aborting."
  exit 1
fi
exit 0

git checkout master
git merge --no-ff develop

git tag -a ${version} -m "${version} release"
git push
git push --tags

python setup.py sdist upload
