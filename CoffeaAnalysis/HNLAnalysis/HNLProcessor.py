import numpy as np
import awkward as ak

from CoffeaAnalysis.HNLAnalysis.helpers import apply_golden_run, apply_reweight, apply_MET_Filter
from CoffeaAnalysis.HNLAnalysis.correction_helpers import compute_tau_e_corr

class HNLProcessor():
    def __init__(self, stitched_list, tag, xsecs, periods):
        #define global variables
        if stitched_list is None or len(stitched_list) == 0:
            raise 'Missing stitched_list in samples_{era}.yaml'
        self.stitched_list = stitched_list

        if tag is None or len(tag) == 0:
            raise 'Missing tag'
        self.tag = tag

        self.xsecs = xsecs

        self.period = periods

        if self.period == '2018':
            self.DeepTauVersion = 'DeepTau2018v2p5'
        else:
            self.DeepTauVersion = 'DeepTau2017v2p1'
    
    # Init process
    def init_process(self, out, events):

        ds = events.metadata["dataset"] # dataset name
        print('Processing: ' + ds)

        if self.dataHLT in ds:
            events['genWeight'] = events.run > 0 #setup genWeight for data (1.)

        # Save initial SumGenWeights 
        out['sumw_init'][ds] += ak.sum(events.genWeight)
        out['n_ev_init'][ds] += len(events)

        # defining the mode
        mode ='MCbackground' # default mode

        if self.dataHLT in ds:
            mode ='Data'
            # only keep the "golden" runs
            events = apply_golden_run(ds, events, self.period)
            #A,B,C and D together
            ds = ds[0:-1]

        if 'HNL' in ds:
            mode ='signal'
        
        #make ds and mode global var
        self.ds = ds
        self.mode = mode
        print(f'Analysis in mode {self.mode}')

        if self.mode != 'Data':
            #check if Xsec is missing
            if self.xsecs is None:
                raise 'Missing xsecs'
            #reweights events with lumi x xsec / n_events (with PU correction) + applying stitching weights for DY and WJets samples 
            events = apply_reweight(self.ds, events, self.stitched_list, self.dataHLT, self.xsecs, self.period)

        # sumw after reweighting (for MC) and "golden" runs selection (for data)
        out['sumw_reweight'][self.ds] += ak.sum(events.genWeight)
        out['n_ev_reweight'][self.ds] += len(events)

        # MET filters
        events = apply_MET_Filter(events)

        # sumw after application of MET filters
        out['sumw_MET_Filter'][self.ds] += ak.sum(events.genWeight)
        out['n_ev_MET_Filter'][self.ds] += len(events)

        # Reco event selection: common minimal requirement for leptons
        #tau 
        self.cut_tau_pt = 20. # Tau_pt > cut_tau_pt (general recommendations)
        self.cut_tau_eta = 2.5 #abs(Tau_eta) < cut_tau_eta (general recommendations for DeepTau2p5: 2.3 for DeepTau2p1)
        self.cut_tau_dz = 0.2 #abs(Tau_dz) < cut_tau_dz
        self.cut_tau_idVSmu = 4 # idDeepTauVSmu >= Tight
        self.cut_tau_idVSe = 2 # idDeepTauVSe >= VVLoose
        self.cut_tau_idVSjet = 2 # idDeepTauVSjet >= VVLoose

        #muons
        self.cut_mu_pt = 10. # Muon_pt > cut_mu_pt
        self.cut_mu_eta = 2.4 # abs(Muon_eta) < cut_mu_eta
        self.cut_mu_dz = 0.2 #abs(Muon_dz) < cut_mu_dz
        self.cut_mu_dxy = 0.045 # abs(Muon_dxy) < cut_mu_dxy
        self.cut_mu_iso = 0.4 # Muon_pfRelIso03_all < cut_mu_iso

        #electrons
        self.cut_e_pt = 10. # Electron_pt > cut_e_pt
        self.cut_e_eta = 2.5 # abs(Electron_eta) < cut_e_eta
        self.cut_e_dz = 0.2 #abs(Electron_dz) < cut_e_dz
        self.cut_e_dxy = 0.045 # abs(Electron_dxy) < cut_e_dxy
        self.cut_e_iso = 0.4 # Electron_pfRelIso03_all < cut_e_iso

        return events, out

    def Lepton_selection(self, events, Treename = None):
        #tau
        # cuts in HNLProcessor + remove decay mode 5 and 6 as suggested here: https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendationForRun2
        if self.DeepTauVersion == 'DeepTau2018v2p5':
            events['SelTau'] = events.Tau[(np.abs(events.Tau.eta) < self.cut_tau_eta) & (np.abs(events.Tau.dz) < self.cut_tau_dz) & (events.Tau.idDeepTau2018v2p5VSmu >= self.cut_tau_idVSmu) & (events.Tau.idDeepTau2018v2p5VSe >= self.cut_tau_idVSe) & (events.Tau.idDeepTau2018v2p5VSjet >= self.cut_tau_idVSjet) & (events.Tau.decayMode != 5) & (events.Tau.decayMode != 6)]
        if self.DeepTauVersion == 'DeepTau2017v2p1':
            events['SelTau'] = events.Tau[(np.abs(events.Tau.eta) < self.cut_tau_eta) & (np.abs(events.Tau.dz) < self.cut_tau_dz) & (events.Tau.idDeepTau2017v2p1VSmu >= self.cut_tau_idVSmu) & (events.Tau.idDeepTau2017v2p1VSe >= self.cut_tau_idVSe) & (events.Tau.idDeepTau2017v2p1VSjet >= self.cut_tau_idVSjet) & (events.Tau.decayMode != 5) & (events.Tau.decayMode != 6)]

        #muons
        # cuts in HNLProcessor + Muon_mediumId
        events['SelMuon'] = events.Muon[(events.Muon.pt > self.cut_mu_pt) & (np.abs(events.Muon.eta) < self.cut_mu_eta) & (np.abs(events.Muon.dz) < self.cut_mu_dz) & (np.abs(events.Muon.dxy) < self.cut_mu_dxy) & (events.Muon.mediumId > 0) & (events.Muon.pfRelIso03_all < self.cut_mu_iso)]

        #electrons
        # cuts in HNLProcessor + mvaNoIso_WP90 > 0 (i.e True)
        events['SelElectron'] = events.Electron[(events.Electron.pt > self.cut_e_pt) & (np.abs(events.Electron.eta) < self.cut_e_eta) & (np.abs(events.Electron.dz) < self.cut_e_dz) & (np.abs(events.Electron.dxy) < self.cut_e_dxy) & (events.Electron.mvaNoIso_WP90 > 0) & (events.Electron.pfRelIso03_all < self.cut_e_iso)]

        #apply energy correction for Tau:
        if self.mode != 'Data':
            tau_es, tau_es_up, tau_es_down = compute_tau_e_corr(events.SelTau, self.period)
            if Treename == None:
                events["SelTau","pt"] = events.SelTau.pt*tau_es
                events["SelTau","mass"] = events.SelTau.mass*tau_es
            else:
                lst = Treename.split('_')
                if lst[1] == 'GenuineTauES':
                    mask_genPartFlav = (events.SelTau.genPartFlav == 5)
                    if lst[2] == 'DM0':
                        mask = (events.SelTau.decayMode == 0) & mask_genPartFlav
                    if lst[2] == 'DM1':
                        mask = (events.SelTau.decayMode == 1) & mask_genPartFlav
                    if lst[2] == '3prong':
                        mask = ((events.SelTau.decayMode == 10) | (events.SelTau.decayMode == 11)) & mask_genPartFlav
                if lst[1] == 'GenuineElectronES':
                    mask_genPartFlav = (events.SelTau.genPartFlav == 1) | (events.SelTau.genPartFlav == 3)
                    if lst[2] == 'DM0':
                        mask = (events.SelTau.decayMode == 0) & mask_genPartFlav
                    if lst[2] == 'DM1':
                        mask = (events.SelTau.decayMode == 1) & mask_genPartFlav
                    if lst[2] == '3prong':
                        mask = ((events.SelTau.decayMode == 10) | (events.SelTau.decayMode == 11)) & mask_genPartFlav
                if lst[1] == 'GenuineMuonES':
                    mask = (events.SelTau.genPartFlav == 2) | (events.SelTau.genPartFlav == 4)

                if lst[-1] == 'up':
                    sf = ak.where(mask,tau_es_up, tau_es)
                if lst[-1] == 'down':
                    sf = ak.where(mask,tau_es_down, tau_es)
                Delta_met = events.SelTau.pt*sf - events.SelTau.pt*tau_es
                Delta_met = ak.sum(Delta_met, axis=1)
                events["SelTau","pt"] = events.SelTau.pt*sf
                events["SelTau","mass"] = events.SelTau.mass*sf
                events["MET","pt"] = events.MET.pt - Delta_met
        #apply cut on Tau pt using corrected energy
        events['SelTau'] = events.SelTau[events.SelTau.pt > self.cut_tau_pt]
        
        return events
    
