#!/bin/bash

echo "Example of hadd script"

for file in TauNu_MHp*_tb_10_60_5/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root;
do
tb=$(echo -n "$file" | sed -s 's:.*batch.*tb::g'| sed 's:/.*::g')
echo "->Adding tb $tb to file $file"
python  ../python/addToTree.py  -i $file -b tb --value $tb
done


## hadd everything
hadd -f all.root  TauNu_MHp*_tb_10_60_5/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root
