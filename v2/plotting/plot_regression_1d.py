import ROOT
from .plotting import Plotting
from array import array
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

class PlotRegression1D:
    def __init__(self, config: "Config", output_folder: str, training_id: str):
        self.config = config
        self.output_folder = output_folder
        self.training_id = training_id
        self.normalize = True
        
        # Get plotting configuration
        self.variables = config.plotting.variables
        
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
        """Create 1D regression plots from ROOT file"""
        
        fin = ROOT.TFile(root_file_path)
        tree = fin.Get('tJet')
        
        height = 800
        width = 800
        
        p = Plotting(
            text='(13.6 TeV)',
            extratext='Simulation',
            H_ref=height,
            W_ref=width,
            iPos=0
        )
        
        p.setStyle()
        
        c0 = ROOT.TCanvas('c0', 'c0', 1, 1)
        
        histos = {}
        ratios = {}
        canvas = {}
        subpads = {}
        lines = {}
        leg = {}
        
        for v in self.variables:
            print(f"Processing variable: {v['name']}")
            
            c0.cd()
            
            # Create histograms for each sample
            for s in self.samples:
                hstub = v['name'] + s['name']
                
                if isinstance(v['bins'], list) and len(v['bins']) > 3:
                    histos[hstub] = ROOT.TH1F('h' + hstub, '', len(v['bins'])-1, array('d', v['bins']))
                else:
                    histos[hstub] = ROOT.TH1F('h' + hstub, '', v['bins'][0], v['bins'][1], v['bins'][2])
                
                # Fill histogram
                branch_name = v['branch'].replace('CLASS', s['suffix'])
                selection = s['selection'] + v['selection'].replace('CLASS', s['suffix'])
                tree.Draw(branch_name + '>>h' + hstub, selection, '')
                
                if self.normalize: 
                    histos[hstub].Scale(1. / histos[hstub].Integral())
                
                # Set histogram style
                color = eval(s['color']) if isinstance(s['color'], str) and 'ROOT' in s['color'] else s['color']
                histos[hstub].SetFillStyle(s['fillStyle'])
                histos[hstub].SetFillColor(color)
                histos[hstub].SetLineWidth(s['lineWidth'])
                if 'test' not in s['name'] and 'val' not in s['name']: 
                    histos[hstub].SetMarkerSize(0)
                histos[hstub].SetLineColor(color)
                histos[hstub].SetMarkerColor(color)
            
            # Create ratio histograms
            for s in self.samples:
                if s['name'] == 'full': continue
                hstub = v['name'] + s['name']
                if not histos[hstub].GetSumw2N(): histos[hstub].Sumw2()
                ratios[hstub] = histos[hstub].Clone('hr' + hstub)
                ratios[hstub].UseCurrentStyle()
                ratios[hstub].SetStats(0)
                ratios[hstub].Divide(histos[v['name'] + 'full'])
                
                color = eval(s['color']) if isinstance(s['color'], str) and 'ROOT' in s['color'] else s['color']
                ratios[hstub].SetFillStyle(s['fillStyle'])
                ratios[hstub].SetFillColor(color)
                ratios[hstub].SetLineWidth(s['lineWidth'])
                ratios[hstub].SetMarkerSize(0)
                ratios[hstub].SetLineColor(color)
                ratios[hstub].SetMarkerColor(color)
            
            # Create legend
            leg[v['name']] = ROOT.TLegend(0.5, 0.6, 0.95, 0.9)
            
            # Create canvas with subpads
            canvas[v['name']] = ROOT.TCanvas('c' + v['name'], 'c' + v['name'], 2*width, height)
            canvas[v['name']].Divide(2, 1)
            
            subpads[v['name']] = p.addLowerPads(canvas[v['name']])
            
            # Plot linear scale
            subpads[v['name']]['1_1'].cd()
            
            for s in self.samples:
                hstub = v['name'] + s['name']
                if 'test' in s['name'] or 'val' in s['name']: 
                    histos[hstub].Draw('e0 x0 same')
                else: 
                    histos[hstub].Draw('hist same')
                leg[v['name']].AddEntry(histos[hstub], s['label'], s['legendOption'])
            
            histos[v['name'] + self.samples[0]['name']].SetMaximum(1.6*max([histos[key].GetMaximum() for key in histos if v['name'] == key[:len(v['name'])] and key[len(v['name']):] in [s['name'] for s in self.samples]]))
            histos[v['name'] + self.samples[0]['name']].GetXaxis().SetTitle(v['title'])
            histos[v['name'] + self.samples[0]['name']].GetXaxis().SetLabelSize(0)
            if self.normalize: 
                histos[v['name'] + self.samples[0]['name']].GetYaxis().SetTitle('Fraction of Jets')
            else: 
                histos[v['name'] + self.samples[0]['name']].GetYaxis().SetTitle('Jets')
            
            leg[v['name']].Draw('same')
            p.postparePad()
            
            # Plot log scale
            subpads[v['name']]['2_1'].cd()
            
            histos[v['name'] + 'emptyloghist'] = histos[v['name'] + self.samples[0]['name']].Clone('emptyloghist')
            histos[v['name'] + 'emptyloghist'].Reset()
            histos[v['name'] + 'emptyloghist'].Draw('AXIS')
            
            for s in self.samples:
                hstub = v['name'] + s['name']
                if 'test' in s['name'] or 'val' in s['name']: 
                    histos[hstub].Draw('e0 x0 same')
                else: 
                    histos[hstub].Draw('hist same')
            
            globalmin = histos[v['name'] + self.samples[0]['name']].GetMinimum(0)
            globalmax = histos[v['name'] + self.samples[0]['name']].GetMaximum()
            
            logrange = ROOT.TMath.Log10(globalmax) - ROOT.TMath.Log10(globalmin)
            
            histos[v['name'] + 'emptyloghist'].SetMinimum(0.5 * globalmin)
            histos[v['name'] + 'emptyloghist'].SetMaximum(globalmax * 10 ** max(1, logrange))
            histos[v['name'] + 'emptyloghist'].GetXaxis().SetTitle(v['title'])
            if self.normalize: 
                histos[v['name'] + 'emptyloghist'].GetYaxis().SetTitle('Fraction of Jets')
            else: 
                histos[v['name'] + 'emptyloghist'].GetYaxis().SetTitle('Jets')
            
            leg[v['name']].Draw('SAME')
            ROOT.gPad.SetLogy()
            p.postparePad()
            
            # Plot ratio plots
            for padname in ['1_2', '2_2']:
                subpads[v['name']][padname].cd()
                
                firstname = None
                for s in self.samples:
                    hstub = v['name'] + s['name']
                    if s['name'] == 'full': continue
                    if firstname is None: firstname = s['name']
                    if 'test' in s['name'] or 'val' in s['name']:
                        ratios[hstub].Draw('e0 x0 same')
                        ratios[hstub].Draw('hist same')
                    else:
                        ratios[hstub].Draw('e0 x0 same')
                        ratios[hstub].Draw('hist same')
                
                p.adjustLowerHisto(ratios[v['name'] + firstname])
                ratios[v['name'] + firstname].SetMinimum(1. - v['ratioRange'] + 0.0001)
                ratios[v['name'] + firstname].SetMaximum(1. + v['ratioRange'] - 0.0001)
                ratios[v['name'] + firstname].GetXaxis().SetTitle(v['title'])
                ratios[v['name'] + firstname].GetYaxis().SetTitle('#scale[0.9]{#frac{FastSim}{FullSim}}')
                
                if isinstance(v['bins'], list) and len(v['bins']) > 3:
                    lines[v['name'] + padname] = ROOT.TLine(v['bins'][0], 1., v['bins'][-1], 1.)
                else:
                    lines[v['name'] + padname] = ROOT.TLine(v['bins'][1], 1., v['bins'][2], 1.)
                lines[v['name'] + padname].SetLineWidth(1)
                lines[v['name'] + padname].SetLineColor(ROOT.kBlack)
                lines[v['name'] + padname].Draw('same')
            
            canvas[v['name']].Update()
            canvas[v['name']].Draw()
            
            # Save plot
            output_filename = os.path.join(self.output_folder, f'reg1D_{v["name"]}.png')
            canvas[v['name']].Print(output_filename)
            print(f"Saved plot: {output_filename}")
        
        fin.Close() 