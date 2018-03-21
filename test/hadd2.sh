#!/bin/bash

echo "Example of hadd script"
echo " python python/bsmCombination.py -C '-M AsymptoticLimits -t -1' --mhp=200 --tb=10:60:5 -c Hptn:13TeV:combine_datacard_hplushadronic_m200.txt -d test/TauNu_MHp200_tb_10_60_5 -q 1nd -t combine_histograms_hplushadronic_m200.root --debug "


### 
N=8
TMPDIR=/tmp/${USER}

open_sem(){
    mkfifo ${TMPDIR}/pipe-$$
    exec 3<>${TMPDIR}/pipe-$$
    rm ${TMPDIR}/pipe-$$
    local i=$1
    for((;i>0;i--)); do
        printf %s 000 >&3
    done
}

run_with_lock(){
    local x
    read -u 3 -n 3 x && ((0==x)) || exit $x
    (
    "$@" 
    printf '%.3d' $? >&3
    )&
}

open_sem $N
for file in TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root;
do
    tb=$(echo -n "$file" | sed -s 's:.*batch.*tb::g'| sed 's:/.*::g')
    echo "->Adding tb $tb to file $file"
    run_with_lock python  ../python/addToTree.py  -i $file -b tb --value $tb
done

echo "-> waiting before hadding"
wait
## hadd everything
hadd -f all.root  TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root
