import os,sys,re
from optparse import OptionParser, OptionGroup
usage=''' %prog [options]
    High level script to call combination for BSM Models. 
    Send jobs on batch and calls FeynHiggs where relevant 
    '''
parser=OptionParser()

parser.add_option("-d","--dir" ,dest='dir',type='string',help="Directory where to write the configuration [%default]",default="submit")

parser.add_option("-c","--channel",action="append",help="append a datacard channel [Hptn,Hptb,]:[13TeV]:file",default=[])
parser.add_option("","--feyn",help="FeynHiggs [%default]",default=os.environ['PWD']+'/'+'FeynHiggs-2.14.0'+'/'+'x86_64-Linux'+'/' +'bin' + '/' + 'FeynHiggs')
parser.add_option("","--flags",help="FeynHiggs flags [%default]",default="42423110")
parser.add_option("-m","--model",help="LHCHXSDatacard [%default]",default='/'.join([os.environ['PWD'],'FeynHiggs-2.14.0', 'example','LHCHXSWG','mhmodm-LHCHXSWG.in']))
parser.add_option("","--ncore",type='int',help="num. of core. [%default]",default=4)
parser.add_option("-t","--templates",action='append',help="Template files to be copied in the work directory. Can be specified more than once. [%default]",default=[])
parser.add_option("","--Hpm",dest='Hpm',action='store_true',help="Use twice the cross section of FeynHiggs to account for H+- [%default]",default=True)
parser.add_option("","--Hplusonly",dest='Hpm',action='store_false',help="Use twice the cross section of FeynHiggs to account for H+- [%default]")

scan_options = OptionGroup(parser,"Scan options","")
scan_options.add_option("","--mhp",help="MHp points (1000 or 100,200,500 or 200:1000:100) [%default]",default="1000")
scan_options.add_option("","--tb",help="Tan beta points (27 or 5,7,11 or 10:60:5) [%default]",default="10:60:5")
scan_options.add_option("-q","--queue",help="Batch Queue [%default]",default="1nd")

combine_options = OptionGroup(parser,"Combine Options","")
combine_options.add_option("-C","--combine",action='append',help="Pass this option to combine. Eg. '-M Asymptotics', '-t -1', ...",default=[])

debug_options = OptionGroup(parser,"Debug options","")
debug_options.add_option("","--debug",action='store_true',help="Debug status and printout [%default]",default=False)
debug_options.add_option("","--br1",dest="br1",default=False,action="store_true",help="don't scale for br")
debug_options.add_option("","--dryrun",dest="dryrun",default=False,action="store_true",help="don't call combineTools to submit the job")
# add a verbosity 

parser.add_option_group(scan_options)
parser.add_option_group(combine_options)
parser.add_option_group(debug_options)

opts,args=parser.parse_args()

#################
### functions ###
#################

def drange(start, stop, step):
        ''' Return a floating range list. Start and stop are included in the list if possible.'''
        eps = 0.000001
        r = start
        while r <= stop+eps:
                yield r
                r += step

def listFromStr(s):
    r = []
    for comma in s.split(','):
        if ':' in comma:
            start=float(comma.split(':')[0])
            stop =float(comma.split(':')[1])
            end  =float(comma.split(':')[2])
            r.extend([x for x in drange(start,stop,end)])
        else:
            r.append(float(comma))
    return r


from glob import glob
from subprocess import call, check_output
import threading
import time

# these lists are tried in order. Put the less constraining first
chMap={'Hptn':['CMS_Hptntj_Hp%(mass)d_a','Hptn','HplusTauNu'],   ## possible process name
       'Hptb':['Hptb','HplusTopBottom','CMS_Hptbemu_Hpemu','CMS_Hptbmumu_Hpmumu','CMS_Hptbee_Hpee','CMS_Hptbmt_Hptb'],
    }
###################
## check combine ##
###################

if not os.path.exists(os.path.expandvars('$CMSSW_BASE/bin/$SCRAM_ARCH/combine')):
        sys.exit('ERROR - CombinedLimit package must be installed')
if not os.path.exists(os.path.expandvars('$CMSSW_BASE/bin/$SCRAM_ARCH/text2workspace.py')):
        sys.exit('ERROR - CombinedLimit package must be installed')
if not os.path.exists(os.path.expandvars('$CMSSW_BASE/bin/$SCRAM_ARCH/combineCards.py')):
        sys.exit('ERROR - CombinedLimit package must be installed')
if not os.path.exists(os.path.expandvars('$CMSSW_BASE/bin/$SCRAM_ARCH/combineTool.py')):
        sys.exit('ERROR - CombinedTool package must be installed')

####################
## check work dir ##
####################

st = call("[ -d %s ] && rmdir %s || [ ! -d %s ]"%(opts.dir,opts.dir,opts.dir),shell=True)
if st != 0: raise IOError("ERROR: directory " + opts.dir+ " already exist and not empty")
call("mkdir -p %s"%opts.dir,shell=True)

## copy templates inside
if opts.debug: print "[DEBUG]","Copying template files"
for t in opts.templates:
    st = call("cp -v %s %s"%(t,opts.dir),shell=True)
    if st !=0: raise IOError("unable to copy file %s in %s"%(t,opts.dir))

########################################
## compute lists of mhp and tb to run ##
########################################

mhp=listFromStr(opts.mhp)
tb =listFromStr(opts.tb)

if opts.debug:
    print "[DEBUG]","I will run on MHp",','.join(["%.0f"%x for x in mhp])
    print "[DEBUG]","I will run on tb",','.join(["%.1f"%x for x in tb])

## update chMap if there is a channel with mass in the name
for ch in chMap:
    l=[]
    for procname in chMap[ch]:
        if '%' in procname:
            for m in mhp:
                l.append(procname%{"mass":int(m)})
        else:
            l.append(procname)
    chMap[ch]=l

if opts.debug:
    print "[DEBUG]", "Supported channels are:"
    for ch in chMap:
        print "[DEBUG]","  *)",ch,":",",".join(chMap[ch])
##########################################################
## preparation: parse cards, add scaling and merge them ##
##########################################################

allSqrtS=set([])
allCh=set([])

cmdCombineCards="combineCards.py"
for chIdx,chStr in enumerate(opts.channel):
    ch=chStr.split(':')[0] 
    sqrtS=int(re.sub('[T,t][E,e][v,V]','',chStr.split(':')[1]))
    fname=chStr.split(':')[2]

    allSqrtS |= set([sqrtS])
    allCh |= set([ch])

    print "[INFO]: Considering datacard #%d:"%chIdx, fname
    print "   -) type ",ch
    print "   -) sqrtS ",sqrtS,"TeV"
    datacard=opts.dir +'/ch%d.txt'%chIdx
    cmd=' '.join(['cp','-v',fname,datacard])
    st=call(cmd,shell=True)
    if st != 0 : raise IOError("Unable to run:'"+cmd+"'")
    ok=False
    for procname in chMap[ch]:
        cmd=' '.join(['grep',procname,datacard,"2>&1",">/dev/null"])
        st=call(cmd,shell=True)
        if opts.debug:
            print "[DEBUG]","considered process",procname,"in datacard",datacard,"and results is",st
            print "[DEBUG]","   - command was",cmd
        if st != 0 : continue
        ok=True
        txt = open(datacard,"a")
        print >> txt, ""  ## newline
        print >> txt, "### automatically added by:",sys.argv[0]  ## 
        print >> txt, "xsec_hp_%dTeV"%sqrtS,"rateParam","*",procname,"1.0"
        if not opts.br1: print >> txt, "br_"+ch,"rateParam","*",procname,"1.0"
        #print >> txt, "tb extArg 100" # doesn't work for limits
        print >> txt, "nuisance","edit","freeze","xsec_hp_%dTeV"%sqrtS
        if not opts.br1: print >> txt, "nuisance","edit","freeze","br_"+ch
        txt.close()
        break

    if not ok:
        print "[ERROR]: Unable to identify signal process in datacard"
        print "       : Allow values for",ch,"process are",','.join(chMap[ch])
        raise ValueError("No Signal in datacard")

    cmdCombineCards+=" ch%d="%chIdx+datacard

#xsec_hp rateParam * Hptn 1.0
#br_Hptn rateParam * Hptn 1.0
#nuisance edit freeze xsec_hp
#nuisance edit freeze br_tn

####################
## Combine cards  ##
####################
if opts.debug: print "[DEBUG]","Combined datacards"

combDatacard=opts.dir+"/datacard.txt"
cmdCombineCards+= " >"+combDatacard
st=call(cmdCombineCards,shell=True)
if st != 0 : raise IOError("Unable to run:'"+cmdCombineCards+"'")


def parallel(cmd):
	print "-> Parallel command :'"+cmd+"'"
	if cmd != "/bin/true":
		st = call(cmd,shell=True);
	else: 
		st =0

	if st !=0 :
		print "[ERROR] Unable to execute command","'"+cmd+"'"
		raise RuntimeError('Unable to excute command call')
	return 0 

####################
## text2workspace ##
####################
if opts.debug: print "[DEBUG]","Running text2workspace on all the mass points"
threads=[]
for m in mhp:
    text2ws=' '.join(['text2workspace.py' ,'-m%f'%m,'-o %s/datacard_MHp%.0f.root'%(opts.dir,m),combDatacard])
    while threading.activeCount() >= opts.ncore:
        print "sleep ....",
        time.sleep(1)
        print "wake up"
    t= threading.Thread(target=parallel,args=(text2ws,) )
    t.start()
    threads.append(t)

print "-> waiting all text2workspace jobs to finish"
for t in threads:
    t.join()

########################
## Prepare submission ##
########################
def prepareSubmission(m,t):
    ''' Main submission routine. Function of MHp and TB'''
    if opts.debug: print "[DEBUG]","Starting prepare submission for point (%(mass).0f,%(tb).1f)"%{"mass":m,"tb":t}
    #compute parameters using FeynHiggs
    params=[]
    #params.append("tb=%f"%(t)) # doesn't work
    for idx,sqrtS in enumerate(allSqrtS):
        if opts.debug: print "[DEBUG]","Submission for (%(mass).0f,%(tb).1f) is considering sqrtS=%(sqrtS).0f"%{"mass":m,"tb":t,"sqrtS":sqrtS}
        fcard=opts.dir+"/feyn.MHp%.0f.tb%.1f.sqrtS%dTeV.in"%(m,t,sqrtS)
        cmd=' '.join(['cp','-v',opts.model,fcard])
        #1 copy feyn higgs card
        st=call(cmd,shell=True)
        if st != 0 : raise IOError("Unable to run:'"+cmd+"'")
        #2. Remove MA0, TB lines
        cmd=' '.join(['sed',"-i''","'/TB\|MA0\|MHp\|prodSqrts/d'",fcard])
        st=call(cmd,shell=True)
        fstream=open(fcard,"a")
        fstream.write("MHp        %f\n"%m)
        fstream.write("TB        %f\n"%t)
        fstream.write("prodSqrts        %f\n"%sqrtS)
        fstream.close()
        fout=opts.dir+"/feyn.MHp%.0f.tb%.1f.sqrtS%dTeV.out"%(m,t,sqrtS)
        cmd=' '.join([opts.feyn,fcard,opts.flags,">",fout])
        if opts.debug: print "[DEBUG]","Submission for (%(mass).0f,%(tb).1f,%(sqrtS).0f) is running FEynHiggs"%{"mass":m,"tb":t,"sqrtS":sqrtS}
        st = call(cmd,shell=True)
        if st != 0 : raise IOError("Unable to run:'"+cmd+"'") ## run FeynHiggs

        #cmd = "cat "+ fout + "| grep 'prod:alt-t-Hp' | sed 's/^.*=//'"
        #"xsec_hp_%dTeV"%sqrtS
        #  | prod:alt-t-Hp         =     20.6766     fb
        cmd=' '.join(['cat',fout,"|","grep 'prod:alt-t-Hp'","|","sed 's/^.*=//'","|","tr -d ' '"])
        out=check_output(cmd,shell=True)
        if opts.debug: print "[DEBUG]","Submission for (%(mass).0f,%(tb).1f,%(sqrtS).0f) FeynHiggs xsec=%(out)s fb"%{"mass":m,"tb":t,"sqrtS":sqrtS,"out":out}
        hplus=1.0
        if opts.Hpm: hplus*=2.0
        params.append("xsec_hp_%dTeV=%f"%(sqrtS,hplus*float(out)/1000.)) ## xsec is in fb
        if idx == 0 and not opts.br1:
            for ch in allCh:
                gstr=""
                if ch=="Hptn":gstr="Hp-nu_tau-tau"
                elif ch =="Hptb":gstr="Hp-t-b"
                #   ch gamma br
                #%| Hp-nu_tau-tau        =    0.484940       6.063097E-02
                cmd=' '.join(['cat',fout,"|","grep '"+gstr+"'","|","grep -v CL" ,"|","grep -v CR","|","sed 's/^.*=//'","|","sed 's/^\ *//'","|","tr -s ' '" ,"|","cut -d ' ' -f2"])
                out=check_output(cmd,shell=True)
                if opts.debug: print "[DEBUG]","Submission for (%(mass).0f,%(tb).1f,%(sqrtS).0f) FeynHiggs br for %(ch)s is %(out)s"%{"mass":m,"tb":t,"sqrtS":sqrtS,"out":out,"ch":ch}
                #if opts.debug: print "[DEBUG]","with cmd:",cmd
                params.append("br_%s=%f"%(ch,float(out)))
    ## end computing parameters with feynhiggs
    ## start writing batch commands. Use combine Tool!
    d=opts.dir+"/batch_MHp%.0f_tb%.1f"%(m,t)
    cmd=' '.join(["mkdir","-p",d])
    st=call(cmd,shell=True)
    if st != 0 : raise IOError("Unable to run:'"+cmd+"'")
    
    sh=open("%s/cmd.sh"%d,"w")
    cmd="cd %s"%d + ' && ' 
    datacard=os.environ['PWD']+'/'+opts.dir+'/datacard_MHp%.0f.root'%m
    if opts.dir[0] == '/':
        datacard=opts.dir+'/datacard_MHp%.0f.root'%m
    cmd+= ' '.join(['combineTool.py',datacard,'-m %f'%m,"--job-mode lxbatch","--sub-opts='-q "+opts.queue+"'","--task-name BSM_Scan_MHp%.0f_TB%.1f"%(m,t)])
    combine=[]
    splitPointsDefault="--split-points 30"
    for c in opts.combine:
        if 'setParameters' in c: raise ValueError("to implement merge of setParameters")
        if '-m' in c: 
            print "-> ignoring -m option, since it will be set in the scan"
            continue
        if '-M' in c and (not 'AsymptoticLimits' in c or 'MultiDimFit' in c):splitPointsDefault=""
        if '--split-points' in c: splitPointsDefault=""
        combine .append(c)
    cmd+= ' ' + '--setParameters='+','.join(params)
    #cmd+= ' ' + '--saveSpecifiedNuis=tb' # doesn't work
    cmd+= ' ' + ' '.join(combine)
    cmd+= ' ' + splitPointsDefault
    cmd+= ' ' + '--rMin=0'
    cmd+= ' ' + '--rMax=5' ## I care only around 1
    cmd+= ' ' + '--strictBounds' ## as above

    print>>sh,"## Command issued automatically by",sys.argv[0]
    print>>sh,cmd

    if opts.debug: print "[DEBUG]","going to call combineTools with cmd:",cmd

    if not opts.dryrun:
        st=call(cmd,shell=True)
        if st != 0 : raise IOError("Unable to run:'"+cmd+"'")
    return


if opts.debug: print "[DEBUG]","Preparing for job submission"
threads=[]
for m in mhp:
    for t in tb:
        #prepareSubmission(m,t)
        while threading.activeCount() >= opts.ncore:
            print "sleep ....",
            time.sleep(1)
            print "wake up"
        th= threading.Thread(target=prepareSubmission,args=(m,t,) )
        th.start()
        threads.append(th)
print "-> waiting for batch submission to finish"
for t in threads:
    t.join()

print "-> DONE :D "
if opts.debug: print "[DEBUG]","That's all folks!"
        
# to change
#TB
# to remove
#MA0
# to add
#MHp    605.36256773
#FeynHiggs example/LHCHXSWG/mhmodm-LHCHXSWG.in 42423110
#prodSqrts

#fetch BR
#  Channel                   xsection/fb
#  | prod:t-Hp             =    -999.000    
#  | prod:alt-t-Hp         =     20.6766    
#  | prod:altlo-t-Hp       =     16.7892    
#  | prod:althi-t-Hp       =     24.5372 

#%| Hp-nu_tau-tau        =    0.484940       6.063097E-02
#%| Hp-t-b               =     2.77684       0.347182    


