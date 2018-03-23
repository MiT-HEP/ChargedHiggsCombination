# ChargedHiggsCombination
Combination scripts and utils for ChargedHiggs Analysis

## Setup
* Install combine: [link](https://cms-hcomb.gitbooks.io/combine/content/part1/#for-end-users-that-dont-need-to-commit-or-do-any-development)
* Install combine-tools: [link](https://cms-hcomb.gitbooks.io/combine/content/part1/#combine-tool)

~~~bash
bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-ssh.sh)
~~~

* Install FeynHiggs: 
    The version and url of FeynHiggs is controlled by the file download/feynhiggs.txt

~~~bash
make 
~~~

## Usage

There are the following scripts:

* python/bsmCombination.py

    Run the combination jobs to collect all the informations.

* python/addToTree.py

    Add to a ROOT TTree a branch with a specific value. Use to add a tb branch to the combine output

* test/hadd[2].sh

    Hadd [parallelizing the addToTree] all the combine files into a single results file. 

* python/makeLimitPlot.py

    Collect the results in the limit plot.



