#!/bin/bash

for file in *.tgz; do
        echo "Dealing with $file :"
        echo `tar -xf $file`
        echo "Unpacked. Now processing..."
        basis=`basename $file .tgz`
        echo `python entity_lemmas.py $basis`
        echo "Pythonism done for $basis."
        echo `rm -r $basis`
        echo "Directory removed"
done
