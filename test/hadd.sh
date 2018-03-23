#!/bin/bash

#Original author: Andrea Carlo Marini. 23 Mar 2018.
echo "Example of hadd script. Sequentially add branch."

for file in TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root;
do
tb=$(echo -n "$file" | sed -s 's:.*batch.*tb::g'| sed 's:/.*::g')
echo "->Adding tb $tb to file $file"
python  $CMSSW_BASE/src/ChargedHiggsCombination/python/addToTree.py  -i $file -b tb --value $tb
done


## hadd everything
hadd -f all.root  TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root
