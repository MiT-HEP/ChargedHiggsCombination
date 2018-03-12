#!/bin/bash

echo "Example of hadd script"
echo " python python/bsmCombination.py -C '-M AsymptoticLimits -t -1' --mhp=200 --tb=10:60:5 -c Hptn:13TeV:combine_datacard_hplushadronic_m200.txt -d test/TauNu_MHp200_tb_10_60_5 -q 1nd -t combine_histograms_hplushadronic_m200.root --debug "

for file in TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root;
do
tb=$(echo -n "$file" | sed -s 's:.*batch.*tb::g'| sed 's:/.*::g')
echo "->Adding tb $tb to file $file"
python  ../python/addToTree.py  -i $file -b tb --value $tb
done


## hadd everything
hadd -f all.root  TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root
