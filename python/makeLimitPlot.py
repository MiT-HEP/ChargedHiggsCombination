#!/usr/bin/env python
import os,sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-f","--file",dest="file",default="",type="string",help="Input file")
parser.add_option("-l","--label",dest="label",default="",type="string",help="Label to add to the plot")
parser.add_option("-o","--outname",dest="outname",help="Name of output pdf/png/C")
parser.add_option("-b","--batch",dest="batch",default=False,action="store_true")
parser.add_option("-u","--unblind",dest="unblind",default=False,action="store_true",help="Draw observation")
parser.add_option(""  ,"--yaxis",help="Y axis range Y1,Y2 [%default]",default="")
parser.add_option(""  ,"--xaxis",help="X axis range X1,X2 [%default]",default="")
parser.add_option("","--paper",dest="paper",default=False,action="store_true",help="don't display preliminary")
parser.add_option("","--supplementary",dest="supplementary",default=False,action="store_true")

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
    print "DEBUG","considering quantile",quantile
    maxTB=60
    minTB=0
    r={}
    for ientry in range(0,t.GetEntries()):
        t.GetEntry(ientry)
        mh = t.mh
        l  = t.limit
        q  = t.quantileExpected
        tb  = t.tb
        #print "DEBUG","processing entry",ientry,[mh,l,q,tb]
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
        mh=float(mhstr)
        r[mhstr].sort()
        count=0
        for i in range(0, len(r[mhstr])-1):
            n = r[mhstr][i+1]
            c = r[mhstr][i]
            print "Considering limits at between tb",c[0],n[0]," that corresponds to", c[1],n[1]
            if (c[1] < 1. and n[1] >=1.) or (c[1] >= 1. and n[1] <1.): 
                tb=interpolate(c[1],c[0],n[1],n[0],1.)
                if count==0:
                    print "DEBUG: Adding point limit",mh,tb,"for quantile",quantile 
                    g0.SetPoint(g0.GetN(),mh,tb)
                if count >1: 
                    print "WARNING: found second crossing at:",mh,tb
                    g1.SetPoint(g1.GetN(),mh,tb)
                count+=1

        if count==0:
            print "WARNING: unable to find crossing for",mh,"at quantile",quantile,r[mhstr]
            if n[1] >1:
                g0.SetPoint(g0.GetN(),mh,maxTB)
            else:
                g0.SetPoint(g0.GetN(),mh,minTB)
        else:
            print "HURRAH!: Able to find crossing for",mh,"at quantile",quantile,r[mhstr]

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

    if abs(x0-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,x1))
    if abs(x0-xref)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,xref))
    if abs(xref-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(xref,x1))

    n=one.GetN()
    one.SetPoint(n,x0,yref)
    yup=max(y0,y1) - yref
    ydn=yref -min(y1,y0) 
    one.SetPointError(n,0,0,ydn,yup)

    print "->",x0," median is",yref,"one",ydn,yup

    x0=twoUp.GetX()[idx]
    y0=twoUp.GetY()[idx]
    x1=twoDn.GetX()[idx]
    y1=twoDn.GetY()[idx]

    if abs(x0-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,x1))
    if abs(x0-xref)>1.e-3: raise ValueError("Assuming %f==%f"%(x0,xref))
    if abs(xref-x1)>1.e-3: raise ValueError("Assuming %f==%f"%(xref,x1))

    n=two.GetN()
    two.SetPoint(n,x0,yref)
    yup=max(y1,y0) - yref
    ydn=yref -min(y1,y0) 
    two.SetPointError(n,0,0,ydn,yup)

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
two.SetFillColor(ROOT.kOrange)

###################
## Start Drawing ##
###################

c=ROOT.TCanvas()
c.SetCanvasSize(700,500)
c.SetBottomMargin(0.15)
c.SetLeftMargin(0.15)
c.SetTopMargin(0.10)
c.SetRightMargin(0.05)

ROOT.gStyle.SetOptTitle(0)
ROOT.gStyle.SetOptStat(0)

if opts.xaxis != "":
    dummy = ROOT.TH1D("dummy","dummy",100, float(opts.xaxis.split(',')[0]), float(opts.xaxis.split(',')[1]))
    dummy.GetXaxis().SetRangeUser(200,3000)
else:
    dummy = ROOT.TH1D("dummy","dummy",1000, 0, 3000)

dummy.GetYaxis().SetRangeUser(0,60.)

dummy.GetXaxis().SetTitle("m_{H^{+}} [GeV]")
dummy.GetYaxis().SetTitle("tan#beta")
dummy.GetXaxis().SetTitleSize(0.05)
dummy.GetYaxis().SetTitleSize(0.05)
dummy.GetXaxis().SetLabelSize(0.045)
dummy.GetYaxis().SetLabelSize(0.045)

dummy.Draw("AXIS")
dummy.Draw("AXIG SAME") ## draw grid

two.Draw("PE3 SAME")
one.Draw("PE3 SAME")
exp.Draw("L SAME")

if opts.unblind: obs.Draw("PL SAME")


dummy.Draw("AXIS SAME")
dummy.Draw("AXIS X+ Y+ SAME")

c.Modified()
c.Update()

raw_input("Looks ok?")

c.SaveAs(opts.outname + ".pdf")
c.SaveAs(opts.outname + ".png")
c.SaveAs(opts.outname + ".root")
