#!/bin/zsh

output_file="pydt.zip"

rm -f $output_file
zip -r $output_file . -x "*.git*" -x "*.sh" -x "*.md" -x "*.gitignore" -x "*.gitattributes" -x "*.gitmodules"