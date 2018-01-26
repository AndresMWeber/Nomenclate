#!/usr/bin/env bash
echo "Updating project to $version"

sed -i "/^__version__/c\__version__ = '$version'" ./nomenclate/version.py
echo "Updated version.py"

git add -A
git commit -m "versioned up to $version"
echo "Committed."

git tag $version
echo "Tagged."

git push --tags
echo "Pushed!"