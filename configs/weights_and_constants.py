import numpy as np

class weights_and_constants:
    """
    This class contains the weights and constants used in the analysis.
    """

    def __init__(self):
        self.weights_0p6ttWcb_and_0p05ttLF = {
            "ttLF": 0.537, "ttcc": 0.09, "tt2c": 0.09, "ttcj": 0.116,
            "ttbb": 0.071, "tt2b": 0.071, "ttbj": 0.156
        }
        self.weights_0p6ttWcb_and_0p1ttLF = {
            "ttLF": 0.63, "ttcc": 0.09, "tt2c": 0.09, "ttcj": 0.12,
            "ttbb": 0.04, "tt2b": 0.071, "ttbj": 0.10
        }
        self.weights_ttLFm0p1 = {
            "ttLF": 0.5483, "ttcc": 0.0656, "tt2c": 0.0850, "ttcj": 0.1145,
            "ttbb": 0.0589, "tt2b": 0.0399, "ttbj": 0.0877
        }
        self.weights_ttLFm0p1_and_ttWcbm0p8 = {
            "ttLF": 0.5351, "ttcc": 0.0676, "tt2c": 0.0868, "ttcj": 0.1154,
            "ttbb": 0.0709, "tt2b": 0.0378, "ttbj": 0.0863
        }

        # Define event classification selection and binning
        evtClassification_weights = self.weights_ttLFm0p1_and_ttWcbm0p8

        eventClassificationBaseSelection = "score_ttLF < 0.1"
        #eventClassificationBaseSelection = "score_ttLF <= 1"
        SR_selection = "score_tt_Wcb > 0.8"
        #CR_selection = "score_tt_Wcb > 0.2 && score_tt_Wcb < 0.8"
        CR_selection = "score_tt_Wcb < 0.8"

        #SR_selection = "score_tt_Wcb > 0.7 && score_tt_Wcb < 0.8"
        #CR_selection = "score_tt_Wcb < 0.7"
        
        
        # SR selection
        self.adhoc_selection = {
            "score_tt_Wcb": f"{eventClassificationBaseSelection} && {SR_selection}"
        }

        # ttbar categories used to define CR scores
        categories = ["ttbb", "tt2b", "ttbj", "ttcc", "tt2c", "ttcj", "ttLF"]
        
        # CR selection
        for cat in categories:
            # Condition: this category must have weighted score greater than all others
            conditions = " && ".join([
                f"{evtClassification_weights[cat]} * score_{cat} > {evtClassification_weights[other]} * score_{other}"
                for other in categories if other != cat
            ])
            self.adhoc_selection[f"fscore_{cat}"] = f"{eventClassificationBaseSelection} && {CR_selection} && {conditions}"
        
        # Binning adhoc
        self.adhoc_binning = {
            "score_tt_Wcb": np.array([0.0, 0.82, 0.84, 0.88, 0.92, 1.0]),
            "fscore_ttbb": np.array([0.0, 0.27, 0.31, 0.35, 0.39, 0.43, 0.47, 0.51, 0.57, 0.65, 0.75, 0.87, 1.0]),
            "fscore_tt2b": np.array([0.0, 0.50, 0.56, 0.60, 0.64, 0.68, 0.72, 0.78, 1.0]),
            #"fscore_tt2b": np.array([0.0, 0.50, 0.56, 0.60, 0.64, 0.68, 0.72, 1.0]),
            "fscore_ttbj": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 0.50, 0.60, 1.0]),
            #"fscore_ttbj": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 0.50, 1.0]),
            "fscore_ttcc": np.array([0.0, 0.31, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.59, 0.65, 0.73, 0.87, 1.0]),
            #"fscore_ttcc": np.array([0.0, 0.31, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.59, 0.65, 1.0]),
            "fscore_tt2c": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 0.50, 1.0]),
            #"fscore_tt2c": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 1.0]),
            "fscore_ttcj": np.array([0.0, 0.23, 0.26, 0.30, 0.34, 0.38, 0.42, 0.48, 1.0]),
            #"fscore_ttcj": np.array([0.0, 0.23, 0.26, 0.30, 0.34, 0.38, 0.42, 1.0]),
            "fscore_ttLF": np.array([0.0, 0.07, 0.09, 0.10, 0.11, 1.0])
        }

_wc_instance = weights_and_constants()
adhoc_selection = _wc_instance.adhoc_selection
adhoc_binning = _wc_instance.adhoc_binning