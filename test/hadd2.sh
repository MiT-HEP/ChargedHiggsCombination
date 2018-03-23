#!/bin/bash


### 
N=8
TMPDIR=/tmp/${USER}

#Original author: Andrea Carlo Marini. 23 Mar 2018.
#Limited Parallelization based on https://unix.stackexchange.com/a/216475

echo "Example of hadd script. Parallel add branch with $N processes. Will use $TMPDIR for process book-keeping"

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
    run_with_lock python  $CMSSW_BASE/src/ChargedHiggsCombination/python/addToTree.py  -i $file -b tb --value $tb
done

echo "-> waiting before hadding"
wait
## hadd everything
hadd -f all.root  TauNu_MHp*_tb_10_60_*/batch_MHp*_tb*/higgsCombine.Test.AsymptoticLimits*root
