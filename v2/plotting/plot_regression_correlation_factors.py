import ROOT
from .plotting import Plotting
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

class PlotRegressionCorrelationFactors:
    def __init__(self, config: "Config", output_folder: str, training_id: str):
        self.config = config
        self.output_folder = output_folder
        self.training_id = training_id
        
        # Configuration parameters
        self.rightmargin = 0.19
        self.zaxistitleoffset = 1.1
        self.onlyupperhalf = True
        self.diff = 'divide'  # 'subtract'
        self.ndigits = 2
        self.whitethreshold = 0.8
        
        # Get plotting configuration
        self.variables = config.plotting.correlationVariables
        
        # Fixed sample definitions
        self.samples = [
            {
                "name": "full",
                "suffix": "FullSim",
                "label": "FullSim",
                "color": "ROOT.kGreen+2",
                "fillStyle": 3004,
                "lineWidth": 3,
                "selection": "1&&",
                "legendOption": "lf"
            },
            {
                "name": "fast",
                "suffix": "FastSim",
                "label": "FastSim",
                "color": "ROOT.kRed+1",
                "fillStyle": 0,
                "lineWidth": 3,
                "selection": "1&&",
                "legendOption": "l"
            },
            {
                "name": "refined",
                "suffix": "Refined",
                "label": "FastSim Refined",
                "color": "ROOT.kAzure+2",
                "fillStyle": 0,
                "lineWidth": 3,
                "selection": "isTrainValTest<2&&",
                "legendOption": "l"
            },
            {
                "name": "refinedtest",
                "suffix": "Refined",
                "label": "FastSim Refined (Test)",
                "color": "ROOT.kAzure+1",
                "fillStyle": 0,
                "lineWidth": 3,
                "selection": "isTrainValTest>1&&",
                "legendOption": "lp"
            }
        ]
        
    def create_plots(self, root_file_path: str):
        """Create correlation factor plots from ROOT file"""
        
        fin = ROOT.TFile(root_file_path)
        tree = fin.Get('tJet')
        
        numvars = len(self.variables)
        height = 600
        width = 800
        
        p = Plotting(
            text='',
            extratext='Simulation',
            H_ref=height,
            W_ref=width,
            iPos=0
        )
        
        p.setStyle()
        
        c0 = ROOT.TCanvas('c0', 'c0', 1, 1)
        
        histos = {}
        corrhistos = {}
        
        for s in self.samples:
            print(f"Processing sample: {s['name']}")
            
            histos[s['name']] = ROOT.TH2D('hCorrFactors' + s['name'], '', numvars, 0, numvars, numvars, 0, numvars)
            histos[s['name'] + 'diffFull'] = ROOT.TH2D('hCorrFactorsDiffFull' + s['name'], '', numvars, 0, numvars, numvars, 0, numvars)
            
            histos[s['name'] + 'white'] = ROOT.TH2D('hCorrFactorsWhite' + s['name'], '', numvars, 0, numvars, numvars, 0, numvars)
            histos[s['name'] + 'diffFull' + 'white'] = ROOT.TH2D('hCorrFactorsDiffFullWhite' + s['name'], '', numvars, 0, numvars, numvars, 0, numvars)
            
            for ix, x in enumerate(self.variables):
                histos[s['name']].GetXaxis().SetBinLabel(ix+1, x['name'])
                histos[s['name'] + 'diffFull'].GetXaxis().SetBinLabel(ix+1, x['name'])
                
                for iy, y in enumerate(self.variables):
                    if ix == 0:
                        histos[s['name']].GetYaxis().SetBinLabel(iy+1, y['name'])
                        histos[s['name'] + 'diffFull'].GetYaxis().SetBinLabel(iy+1, y['name'])
                    
                    if self.onlyupperhalf and iy <= ix: continue
                    
                    corrhistos[s['name'] + x['name'] + y['name']] = ROOT.TH2F('h' + s['name'] + x['name'] + y['name'], '', 
                                                                            x['bins'][0], x['bins'][1], x['bins'][2], 
                                                                            y['bins'][0], y['bins'][1], y['bins'][2])
                    
                    # Construct branch names and selections
                    y_branch = y['branch'].replace('CLASS', s['suffix']).replace('RefinedNOTREFINED', 'FastSimNOTREFINED').replace('NOTREFINED', '')
                    x_branch = x['branch'].replace('CLASS', s['suffix']).replace('RefinedNOTREFINED', 'FastSimNOTREFINED').replace('NOTREFINED', '')
                    
                    tree.Draw(y_branch + ':' + x_branch + '>>h' + s['name'] + x['name'] + y['name'], '1', '')
                    
                    corrfactor = corrhistos[s['name'] + x['name'] + y['name']].GetCorrelationFactor()
                    
                    histos[s['name']].SetBinContent(ix+1, iy+1, round(corrfactor, self.ndigits))
                    if abs(corrfactor) > self.whitethreshold:
                        histos[s['name'] + 'white'].SetBinContent(ix+1, iy+1, round(corrfactor, self.ndigits))
                    
                    # Calculate difference with respect to full simulation
                    if s['name'] != 'full':
                        full_corrfactor = corrhistos['full' + x['name'] + y['name']].GetCorrelationFactor()
                        
                        if self.diff == 'subtract':
                            diff_value = abs(round(corrfactor, self.ndigits) - round(full_corrfactor, self.ndigits))
                            histos[s['name'] + 'diffFull'].SetBinContent(ix+1, iy+1, diff_value)
                            if abs(diff_value) > self.whitethreshold:
                                histos[s['name'] + 'diffFull' + 'white'].SetBinContent(ix+1, iy+1, diff_value)
                        elif self.diff == 'divide':
                            if not round(full_corrfactor, self.ndigits) == 0:
                                diff_value = 1 - round(corrfactor, self.ndigits) / round(full_corrfactor, self.ndigits)
                                histos[s['name'] + 'diffFull'].SetBinContent(ix+1, iy+1, diff_value)
                                if abs(diff_value) > self.whitethreshold:
                                    histos[s['name'] + 'diffFull' + 'white'].SetBinContent(ix+1, iy+1, diff_value)
                            else:
                                if round(corrfactor, self.ndigits) == 0:
                                    histos[s['name'] + 'diffFull'].SetBinContent(ix+1, iy+1, 0.)
                                else:
                                    histos[s['name'] + 'diffFull'].SetBinContent(ix+1, iy+1, 1.)
                                    histos[s['name'] + 'diffFull' + 'white'].SetBinContent(ix+1, iy+1, 1.)
        
        # Create main canvas
        canvas = ROOT.TCanvas('c', 'c', 3*width, 2*height)
        canvas.Divide(len(self.samples), 2)
        
        # Plot correlation factors
        for ipad, s in enumerate(self.samples):
            canvas.cd(ipad+1)
            
            p_local = Plotting(
                text='(13 TeV)',
                extratext='  Simulation',
                H_ref=height,
                W_ref=width,
                iPos=0
            )
            
            p_local.setStyle()
            
            ROOT.gStyle.SetPalette(ROOT.kGreenPink)
            ROOT.gStyle.SetNumberContours(101)
            ROOT.gStyle.SetPaintTextFormat('4.' + str(self.ndigits) + 'f')
            
            p_local.preparePad()
            
            ROOT.gPad.SetRightMargin(self.rightmargin)
            histos[s['name']].GetZaxis().SetTitle('r_{xy}(' + s['label'] + ')')
            histos[s['name']].GetZaxis().SetTitleOffset(self.zaxistitleoffset)
            histos[s['name']].GetZaxis().SetLabelSize(histos[s['name']].GetXaxis().GetLabelSize())
            histos[s['name']].GetZaxis().SetRangeUser(-1., 1.)
            histos[s['name']].SetMarkerSize(2.)
            
            histos[s['name']].Draw('colz')
            
            histos[s['name'] + 'white'].SetMarkerSize(2.)
            histos[s['name'] + 'white'].SetMarkerColor(ROOT.kWhite)
            histos[s['name'] + 'white'].Draw('text same')
            
            p_local.postparePad()
        
        # Create smaller canvas for individual plots
        lilcanv = ROOT.TCanvas('clil', 'clil', width, height)
        lilcanv.Divide(1,1)
        
        # Plot difference plots
        for ipad, s in enumerate(self.samples):
            canvas.cd(ipad+1+len(self.samples))
            
            p_local = Plotting(
                text='(13 TeV)',
                extratext='  Simulation',
                H_ref=height,
                W_ref=width,
                iPos=0
            )
            
            p_local.setStyle()
            
            ROOT.gStyle.SetPalette(ROOT.kGreenPink)
            ROOT.gStyle.SetNumberContours(101)
            ROOT.gStyle.SetPaintTextFormat('4.' + str(self.ndigits) + 'f')
            
            p_local.preparePad()
            
            ROOT.gPad.SetRightMargin(self.rightmargin)
            if self.diff == 'divide':
                histos[s['name'] + 'diffFull'].GetZaxis().SetTitle('1 - r_{xy}(' + s['label'] + ') / r_{xy}(FullSim)')
            elif self.diff == 'subtract':
                histos[s['name'] + 'diffFull'].GetZaxis().SetTitle('|r_{xy}(' + s['label'] + ') - r_{xy}(FullSim)|')
            histos[s['name'] + 'diffFull'].GetZaxis().SetTitleOffset(self.zaxistitleoffset)
            histos[s['name'] + 'diffFull'].GetZaxis().SetLabelSize(histos[s['name']].GetXaxis().GetLabelSize())
            histos[s['name'] + 'diffFull'].GetZaxis().SetRangeUser(-1., 1.)
            histos[s['name'] + 'diffFull'].SetMarkerSize(2.)
            
            histos[s['name'] + 'diffFull'].Draw('text colz')
            histos[s['name'] + 'diffFull' + 'white'].SetMarkerSize(2.)
            histos[s['name'] + 'diffFull' + 'white'].SetMarkerColor(ROOT.kWhite)
            histos[s['name'] + 'diffFull' + 'white'].Draw('text same')
            p_local.postparePad()
            
            # Save individual plots for fast and refined samples
            if ipad in [1,2]:
                lilcanv.cd()
                
                p_local = Plotting(
                    text='(13 TeV)',
                    extratext='  Simulation',
                    H_ref=height,
                    W_ref=width,
                    iPos=0
                )
                p_local.setStyle()
                
                ROOT.gStyle.SetPalette(ROOT.kGreenPink)
                ROOT.gStyle.SetNumberContours(101)
                ROOT.gStyle.SetPaintTextFormat('4.' + str(self.ndigits) + 'f')
                
                p_local.preparePad()
                
                ROOT.gPad.SetRightMargin(self.rightmargin)        
                histos[s['name'] + 'diffFull'].Draw('text colz')
                histos[s['name'] + 'diffFull' + 'white'].SetMarkerSize(2.)
                histos[s['name'] + 'diffFull' + 'white'].SetMarkerColor(ROOT.kWhite)
                histos[s['name'] + 'diffFull' + 'white'].Draw('text same') 
                lilcanv.Update()
                
                if ipad==1: 
                    output_filename = os.path.join(self.output_folder, 'zfastPearsonRes.png')
                    lilcanv.Print(output_filename)
                    print(f"Saved plot: {output_filename}")
                if ipad==2: 
                    output_filename = os.path.join(self.output_folder, 'zrefinedFastPearsonRes.png')
                    lilcanv.Print(output_filename)
                    print(f"Saved plot: {output_filename}")
                p_local.postparePad()
        
        # Save main canvas
        main_output_filename = os.path.join(self.output_folder, 'regcfs.png')
        canvas.Print(main_output_filename)
        print(f"Saved main correlation plot: {main_output_filename}")
        
        fin.Close() 