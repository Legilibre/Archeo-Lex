#!/bin/bash
if [ -n "$1" ]
then
    cat "$1" | grep "<option" | grep title | sed 's/.*<option value="//' | sed 's/" title="/ /' | sed 's/".*//' | sort | uniq | sed 's/&#39;/’/g' > "$(dirname $(pwd)/$0)/../cache/divers/codes.txt"
else
    wget --output-document=- "http://legifrance.gouv.fr/initRechCodeArticle.do" | grep "<option" | grep title | sed 's/.*<option value="//' | sed 's/" title="/ /' | sed 's/".*//' | sort | uniq | sed 's/&#39;/’/g' > "$(dirname $(pwd)/$0)/../cache/divers/codes.txt"
fi
