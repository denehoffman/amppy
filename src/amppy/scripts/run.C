void run(TString treeName, TString dselector) {
    gROOT->ProcessLine(".x $ROOT_ANALYSIS_HOME/scripts/Load_DSelector.C");
    gROOT->ProcessLine(treeName.Append("->Process(\"").Append(dselector).Append("\");").Data());
}
