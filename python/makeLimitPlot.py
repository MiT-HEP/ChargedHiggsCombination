#!/usr/bin/env python
import os,sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-f","--file",dest="file",default="",type="string",help="Input file")
parser.add_option("-l","--label",dest="label",default="",type="string",help="Label to add to the plot")
parser.add_option("-o","--outname",dest="outname",help="Name of output pdf/png/C [%default]",default="")
parser.add_option("-b","--batch",dest="batch",default=False,action="store_true")
parser.add_option("-u","--unblind",dest="unblind",default=False,action="store_true",help="Draw observation")
parser.add_option(""  ,"--yaxis",help="Y axis range Y1,Y2 [%default]",default="")
parser.add_option(""  ,"--xaxis",help="X axis range X1,X2 [%default]",default="")
parser.add_option("","--paper",dest="paper",default=False,action="store_true",help="don't display preliminary")
parser.add_option("","--supplementary",dest="supplementary",default=False,action="store_true")
parser.add_option(""  ,"--debug",type='int',help="More verbose output [%default]",default=0)
parser.add_option("","--MH125",dest="MH125",default="",help="Draw MH !=125. I will look for feyn out files specified. Example: dir/*/feyn*out files (feynHiggs) ")

opts,args=parser.parse_args()

def interpolate(x1,y1,x2,y2,x):
	''' linear interpolation between the points (x1,y1) (x2,y2) evaluated at x'''
	#y = mx +q
	if x1==x2 and y1==y2 and x==x1 : return y1

	m= (y2-y1)/(x2-x1)
	q= y2 - m*x2
	return m*x+q

sys.argv=[]
import ROOT
if opts.batch: ROOT.gROOT.SetBatch()

f=ROOT.TFile.Open(opts.file)
t=f.Get("limit")

def GetLimit(t, quantile=0.5):
    if opts.debug: print "[DEBUG]:[1]","considering quantile",quantile
    maxTB=60
    minTB=0
    r={}
    for ientry in range(0,t.GetEntries()):
        t.GetEntry(ientry)
        mh = t.mh
        l  = t.limit
        q  = t.quantileExpected
        tb  = t.tb
        if opts.debug>1: print "[DEBUG]:[2]","processing entry",ientry,[mh,l,q,tb]
        if abs(q-quantile) >1e-3 : continue
        if "%.1f"%mh not in r: r["%.1f"%mh]=[]
        r["%.1f"%mh].append( (tb,l) )
    # search for crossing in tb
    g0=ROOT.TGraph()
    g0.SetName("limit1_q%.1f"%quantile)
    g1=ROOT.TGraph()
    g1.SetName("limit2_q%.1f"%quantile)
    masses=[ float(x) for x in r]
    masses.sort()
    keys=[ "%.1f"%y  for y in masses ]
    for mhstr in keys : ## keys are sorted
        if opts.debug>2: print "[DEBUG]:[3]","Considering mh=",mhstr
        mh=float(mhstr)
        r[mhstr].sort()
        if opts.debug>2: print "[DEBUG]:[3]","    -->",r[mhstr]
        count=0
        for i in range(0, len(r[mhstr])-1):
            n = r[mhstr][i+1]
            c = r[mhstr][i]
            if opts.debug>2: print "[DEBUG]:[3]","Considering limits at between tb",c[0],n[0]," that corresponds to", c[1],n[1]
            if (c[1] < 1. and n[1] >=1.) or (c[1] >= 1. and n[1] <1.): 
                tb=interpolate(c[1],c[0],n[1],n[0],1.)
                if count==0:
                    if opts.debug: print "[DEBUG]:[1]: Adding point limit",mh,tb,"for quantile",quantile 
                    g0.SetPoint(g0.GetN(),mh,tb)
                if count >1: 
                    print "[WARNING]","Found second crossing at:",mh,tb
                    g1.SetPoint(g1.GetN(),mh,tb)
                count+=1

        if count==0:
            if opts.debug>0: print "[WARNING]:[1]","Unable to find crossing for",mh,"at quantile",quantile,r[mhstr]
            else: print "[WARNING]:[1]","Unable to find crossing for",mh,"at quantile",quantile

            if n[1] >1:
                g0.SetPoint(g0.GetN(),mh,maxTB)
            else:
                g0.SetPoint(g0.GetN(),mh,minTB)
        else:
            if opts.debug>1: print "[DEBUG]:[2]","HURRAH!: Able to find crossing for",mh,"at quantile",quantile,r[mhstr]
            elif opts.debug>0: print "[DEBUG]:[1]","HURRAH!: Able to find crossing for",mh,"at quantile",quantile

    return g0,g1


if opts.unblind:obs=GetLimit(t,-1)[0]
else: obs = ROOT.TGraph()

exp=GetLimit(t, 0.5)[0]
oneDn=GetLimit(t,0.16)[0]
oneUp=GetLimit(t,0.84)[0]
twoDn=GetLimit(t,0.025)[0]
twoUp=GetLimit(t,0.975)[0]

### re-arranging the tgraphs
two=ROOT.TGraphAsymmErrors()
two.SetName("twoSigma")

one=ROOT.TGraphAsymmErrors()
one.SetName("oneSigma")

for idx in range(0,oneUp.GetN()):
    xref=exp.GetX()[idx]
    yref=exp.GetY()[idx]

    x0=oneUp.GetX()[idx]
    y0=oneUp.GetY()[idx]
    x1=oneDn.GetX()[idx]
    y1=oneDn.GetY()[idx]

    if abs(x0-x1)>1.e-3:
        print "---- TWO UP ---"
        oneUp.Print("V")
        print "---- TWO DN ---"
        oneDn.Print("V")
        print "---------------"
    if abs(x0-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,x1))
    if abs(x0-xref)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,xref))
    if abs(xref-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(xref,x1))

    n=one.GetN()
    one.SetPoint(n,x0,yref)
    yup=max(y0,y1) - yref
    ydn=yref -min(y1,y0) 
    one.SetPointError(n,0,0,ydn,yup)

    if opts.debug>0: print "[DEBUG]:[1]","Results: ->",x0," median is",yref,"two",ydn,yup
    one_yup,one_ydn=yup,ydn

    x0=twoUp.GetX()[idx]
    y0=twoUp.GetY()[idx]
    x1=twoDn.GetX()[idx]
    y1=twoDn.GetY()[idx]

    if abs(x0-x1)>1.e-3:
        print "---- TWO UP ---"
        twoUp.Print("V")
        print "---- TWO DN ---"
        twoDn.Print("V")
        print "---------------"
    if abs(x0-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,x1))
    if abs(x0-xref)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,xref))
    if abs(xref-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(xref,x1))

    n=two.GetN()
    two.SetPoint(n,x0,yref)
    yup=max(y1,y0) - yref
    ydn=yref -min(y1,y0) 
    two.SetPointError(n,0,0,ydn,yup)

    print "[INFO]","Results: ->",x0," median is",yref," +/- (1s)",one_ydn,one_yup,"+/- (2s)",ydn,yup

obs.SetMarkerStyle(21)
obs.SetMarkerSize(0.5)
obs.SetLineColor(1)
obs.SetLineWidth(2)
obs.SetFillStyle(0)
obs.SetMarkerColor(ROOT.kBlack)
obs.SetLineColor(ROOT.kBlack)

exp.SetLineColor(1)
exp.SetLineStyle(2)
exp.SetFillStyle(0)

one.SetLineStyle(2)
two.SetLineStyle(2)

one.SetFillColor(ROOT.kGreen+1)
two.SetFillColor(ROOT.kYellow)

###################
## Start Drawing ##
###################

c=ROOT.TCanvas()
c.SetCanvasSize(800,800)
c.SetBottomMargin(0.15)
c.SetLeftMargin(0.15)
c.SetTopMargin(0.05)
c.SetRightMargin(0.05)

ROOT.gStyle.SetOptTitle(0)
ROOT.gStyle.SetOptStat(0)

if opts.xaxis != "":
    dummy = ROOT.TH1D("dummy","dummy",100, float(opts.xaxis.split(',')[0]), float(opts.xaxis.split(',')[1]))
else:
    dummy = ROOT.TH1D("dummy","dummy",1000, 0, 3000)
    dummy.GetXaxis().SetRangeUser(200,3000)

dummy.GetYaxis().SetRangeUser(0,60.)

dummy.GetXaxis().SetTitle("m_{H^{+}} [GeV]")
dummy.GetYaxis().SetTitle("tan#beta")
dummy.GetXaxis().SetTitleSize(0.05)
dummy.GetYaxis().SetTitleSize(0.05)
dummy.GetXaxis().SetTitleOffset(1.2)
dummy.GetYaxis().SetTitleOffset(1.2)
dummy.GetXaxis().SetLabelSize(0.045)
dummy.GetYaxis().SetLabelSize(0.045)

dummy.Draw("AXIS")
dummy.Draw("AXIG SAME") ## draw grid

two.Draw("PE3 SAME")
one.Draw("PE3 SAME")
exp.Draw("L SAME")

if opts.unblind: obs.Draw("PL SAME")

g125=ROOT.TGraph()
if opts.MH125 != "":
    from glob import glob
    from subprocess import check_output
    #parser.add_option("","--MH125",dest="MH125",default=False,action="store_true",help="Draw Mh != 125")
    if opts.debug:print "[DEBUG]","Constructing 125 Exclusion region"
    files=glob(opts.MH125)
    excluded={} ## mHP -> TB excluded
    if opts.debug: print "[DEBUG]","Processing",len(files),"files"
    for idx,fout in enumerate(files):
        if opts.debug and idx %1000==0: 
		    print "\r Doing entry:",idx,"/",len(files), ":", "%.1f %%"%(float(idx)*100./len(files)),
		    sys.stdout.flush()
        #fetch tb,mhp and mh
        cmd=' '.join(['cat',fout,"|","grep '^| TB'","|","sed 's/^.*=//'","|","tr -d ' '"])
        out=check_output(cmd,shell=True)
        tb=float(out)
        cmd=' '.join(['cat',fout,"|","grep '^| MHp'","|","head -n 1","|","sed 's/^.*=//'","|","tr -d ' '"])
        out=check_output(cmd,shell=True)
        mhp=float(out)
        cmd=' '.join(['cat',fout,"|","grep '^| Mh0'","|","sed 's/^.*=//'","|","tr -d ' '"])
        out=check_output(cmd,shell=True)
        mh0=float(out)
        #if abs(tb-10)<0.1: print "[DEBUG]","MHp=",mhp,"TB=",tb,"mh0=",mh0

        if abs(mh0-125)>3:
            if "%.1f"%mhp not in excluded: excluded["%.1f"%mhp] = []
            excluded["%.1f"%mhp] .append(tb)

    masses=[ float(x) for x in excluded]
    masses.sort()
    keys=[ "%.1f"%y  for y in masses ]
    for mhpstr in keys: ## keys are sorted
        g125.SetPoint(g125.GetN(),float(mhpstr), max(excluded[mhpstr]))
    # uncomment for having a compact region
    #for mhpstr in reversed(keys): 
    #    g125.SetPoint(g125.GetN(),float(mhpstr), min(excluded[mhpstr]))
    #if len(keys) >0:
    #    g125.SetPoint(g125.GetN(),float(keys[0]), max(excluded[keys[0]]))
    g125.SetLineColor(ROOT.kRed)
    g125.SetLineWidth(-503) ## 5 -> exclusion, 3 -> lineWidt
    g125.SetFillStyle(3004)
    g125.SetFillColor(ROOT.kRed)
    g125.Draw("C SAME")
        

ltx=ROOT.TLatex()
if opts.label != "":
   ltx.SetNDC() 
   ltx.SetTextSize(0.04)
   ltx.SetTextFont(42)
   ltx.SetTextAlign(13)
   #ltx.DrawLatex(0.18,0.88,opts.label)
   ltx.SetTextAlign(33)
   ltx.DrawLatex(0.93,.22,opts.label)

obj=[]
if True:
    print "-> Adding NEW Legend"
    obj.append(ltx)
    ltx . SetNDC()
    ltx . SetTextSize(0.05)
    ltx . SetTextFont(42)
    ltx . SetTextAlign(12)
    xmin = 0.6
    ymax = .5
    textSep = 0.05
    delta = 0.045
    entryDelta = 0.07

    dataPoint =  ROOT.TMarker(xmin,ymax,20)
    dataPoint.SetMarkerColor(ROOT.kBlack)
    dataPoint.SetMarkerStyle(obs.GetMarkerStyle())
    dataPoint.SetMarkerSize(obs.GetMarkerSize())
    dataPoint.SetNDC()
    dataLine =  ROOT.TLine(xmin-delta/2., ymax ,xmin + delta/2, ymax)
    dataLine.SetNDC()
    dataLine.SetLineColor(ROOT.kBlack)
    dataLine.SetLineWidth(1)
    obj += [dataPoint,dataLine]
    ## Draw data
    dataPoint.Draw("SAME")
    dataLine.Draw("SAME")
    ltx.DrawLatex(xmin+ textSep,ymax,"Observed")
    
    ## draw median and error
    y_exp = ymax - entryDelta
    vertical=False
    if vertical:
        l_exp = ROOT.TLine(xmin,y_exp -delta/2., xmin,y_exp+delta/2.)
        l_exp.SetNDC()
        l_exp.SetLineColor(ROOT.kBlack)
        l_exp.SetLineWidth(2)
        l_exp.SetLineColor(1)
        l_exp.SetLineStyle(7)
        oneSigma = ROOT.TPave(xmin-delta/3.,y_exp-delta/2.,xmin+delta/3.,y_exp+delta/2.,0,"NDC")
        twoSigma = ROOT.TPave(xmin-delta*2/3.,y_exp-delta/2.,xmin+delta*2/3.,y_exp+delta/2.,0,"NDC")
        obj . extend([l_exp,oneSigma,twoSigma])
    else:
        l_exp = ROOT.TLine(xmin-delta/2.,y_exp, xmin + delta/2.,y_exp)
        l_exp.SetNDC()
        l_exp.SetLineColor(ROOT.kBlack)
        l_exp.SetLineWidth(3)
        l_exp.SetLineColor(1)
        l_exp.SetLineStyle(2)
        oneSigma = ROOT.TPave(xmin-delta/2.,y_exp-delta/3.,xmin+delta/2.,y_exp+delta/3.,0,"NDC")
        twoSigma = ROOT.TPave(xmin-delta/2.,y_exp-delta*2/3.,xmin+delta/2.,y_exp+delta*2/3.,0,"NDC")
        obj . extend([l_exp,oneSigma,twoSigma])
    oneSigma.SetFillColor(ROOT.kGreen+1)
    twoSigma.SetFillColor(ROOT.kYellow)
    twoSigma.Draw("SAME")
    oneSigma.Draw("SAME")
    l_exp.Draw("SAME")
    #ltx.DrawLatex(xmin +textSep,y_exp,"Expected (#scale[0.7]{background, 68% CL, 95% CL})")
    ltx.DrawLatex(xmin +textSep,y_exp,"Expected")

    if opts.MH125:
        y_excl125 = ymax - 2*entryDelta
        l_excl125 = ROOT.TLine(xmin-delta/2.,y_excl125 , xmin+delta/2.,y_excl125)
        l_excl125.SetNDC()
        l_excl125.SetLineColor(ROOT.kRed)
        l_excl125.SetLineStyle(2)
        l_excl125.SetLineWidth(3)

        f_excl125 = ROOT.TPave(xmin-delta/2.,y_excl125-delta*2/3.,xmin+delta/2.,y_excl125+delta*2/3.,0,"NDC")
        f_excl125.Draw("SAME")
        f_excl125.SetFillStyle(3004)
        f_excl125.SetFillColor(ROOT.kRed)
        l_excl125.Draw("SAME")
        ltx.DrawLatex(xmin +textSep,y_excl125,"m_{h}^{#scale[0.8]{MSSM} } #neq 125\pm3")

dummy.Draw("AXIS SAME")
dummy.Draw("AXIS X+ Y+ SAME")

c.Modified()
c.Update()

raw_input("Looks ok?")

if opts.outname!="":
    c.SaveAs(opts.outname + ".pdf")
    c.SaveAs(opts.outname + ".png")
    c.SaveAs(opts.outname + ".root")
