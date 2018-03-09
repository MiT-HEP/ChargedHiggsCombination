import os,sys
import ROOT
from array import array
from optparse import OptionParser, OptionGroup

usage = '''usage: %prog [options]
        This script is adding a branch with a fixed value to a tree
'''
parser=OptionParser(usage=usage)
parser.add_option("-i","--input" ,dest='input',type='string',help="Input File [%default]",default="")
parser.add_option("-t","--tree" ,dest='tree',type='string',help="Tree [%default]",default="limit")
parser.add_option("-b","--branch" ,dest='branch',type='string',help="BranchName [%default]",default="")
parser.add_option("-v","--value" ,type='float',dest='value',help="Value [%default]",default=-99)
(opts,args)=parser.parse_args()

f=ROOT.TFile.Open(opts.input,"UPDATE")
t=f.Get(opts.tree)

if t.GetBranch(opts.branch) != None:
    print "-> Branch",opts.branch,"already exist"
    sys.exit(0)

v=array('f',[opts.value])
b=t.Branch(opts.branch,v,opts.branch+"/F")

for ientry in range(0,t.GetEntries()): b.Fill()

t.Write("",ROOT.TObject.kOverwrite);

print "-> DONE"
