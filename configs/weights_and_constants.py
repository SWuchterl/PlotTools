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
        self.weights_ttLFm0p1_and_ttWcbm0p8_centralVcb = {
            "ttLF": 0.5351, "ttcc": 0.0676, "tt2c": 0.0868, "ttcj": 0.1154,
            "ttbb": 0.0709, "tt2b": 0.0378, "ttbj": 0.0863
        }

        # Define event classification selection and binning
        evtClassification_weights = self.weights_ttLFm0p1_and_ttWcbm0p8_centralVcb

        eventClassificationBaseSelection = "score_ttLF < 0.1"
        #eventClassificationBaseSelection = "score_ttLF <= 1"
        SR_selection = "score_tt_Wcb > 0.8"
        #CR_selection = "score_tt_Wcb > 0.25 && score_tt_Wcb < 0.8"
        CR_selection = "score_tt_Wcb < 0.8"
        #SR_selection = "score_tt_Wcb > 0.7 && score_tt_Wcb < 0.8"
        #CR_selection = "score_tt_Wcb < 0.7"
        
        # ttbar categories used to define CR scores
        categories = ["ttbb", "tt2b", "ttbj", "ttcc", "tt2c", "ttcj", "ttLF"]
        
        # SR selection
        self.adhoc_selection = {
            "score_tt_Wcb": f"{eventClassificationBaseSelection} && {SR_selection}"
        }

        # CR selection
        for cat in categories:
            # Condition: this category must have weighted score greater than all others
            conditions = " && ".join([
                f"{evtClassification_weights[cat]} * score_{cat} > {evtClassification_weights[other]} * score_{other}"
                for other in categories if other != cat
            ])
            self.adhoc_selection[f"fscore_{cat}"] = f"{eventClassificationBaseSelection} && {CR_selection} && {conditions}"
        
        # Binning adhoc
        #bins_list = []
        #for i in np.arange(0, 1.01, 0.01):
        #    bins_list.append(i)
        #bins_array = np.array(bins_list)
        #self.adhoc_binning = {
        #    "score_tt_Wcb": bins_array,
        #    "fscore_ttbb": bins_array,
        #    "fscore_tt2b": bins_array,
        #    "fscore_ttbj": bins_array,
        #    "fscore_ttcc": bins_array,
        #    "fscore_tt2c": bins_array,
        #    "fscore_ttcj": bins_array,
        #    "fscore_ttLF": bins_array
        #}
        #self.adhoc_binning = {
        #    "score_tt_Wcb": np.array([0.0, 0.82, 0.84, 0.86, 0.88, 0.9, 0.92, 0.94, 0.96, 1.0]),
        #    #"score_tt_Wcb": np.array([0.0, 1.0]),
        #    "fscore_ttbb": np.array([0.0, 0.25, 0.27, 0.29, 0.31, 0.33, 0.35, 0.37, 0.39, 0.41, 0.43, 0.45, 0.47, 0.49, 0.51, 0.53, 0.55, 0.57, 0.59, 0.61, 0.63, 0.65, 0.67, 0.69, 0.71, 0.73, 0.75, 0.77, 0.79, 0.81, 0.83, 0.85,0.87, 0.89, 0.91, 0.93, 0.95, 0.97, 0.99, 1.0]),
        #    "fscore_tt2b": np.array([0.0, 0.46, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 1.0]),
        #    "fscore_ttbj": np.array([0.0, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38,0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.67, 1.0]),
        #    "fscore_ttcc": np.array([0.0, 0.27, 0.29, 0.31, 0.33, 0.35, 0.37, 0.39, 0.41, 0.43, 0.45, 0.47, 0.49, 0.51, 0.53, 0.55, 0.57, 0.59, 0.61, 0.63, 0.65, 0.67, 0.69, 0.71, 0.73, 0.75, 0.77, 0.79, 0.81,0.83, 0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 1.0]),
        #    "fscore_tt2c": np.array([0.0, 0.20, 0.22, 0.24, 0.26, 0.28, 0.3, 0.32, 0.34, 0.36, 0.38, 0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.54, 0.56, 0.58, 0.61, 1.0]),
        #    "fscore_ttcj": np.array([0.0, 0.21, 0.23, 0.26, 0.28, 0.3, 0.32, 0.34, 0.36, 0.38, 0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.52, 0.55, 1.0]),
        #    "fscore_ttLF": np.array([0.0, 0.07, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.21, 0.23, 0.25, 0.27, 1.0])
        #}
        self.adhoc_binning = {
            "score_tt_Wcb": np.array([0.0, 0.82, 0.84, 0.88, 0.92, 1.0]),
            "fscore_ttbb": np.array([0.0, 0.27, 0.31, 0.35, 0.39, 0.43, 0.47, 0.51, 0.57, 0.65, 0.75, 0.87, 1.0]),
            "fscore_tt2b": np.array([0.0, 0.50, 0.56, 0.60, 0.64, 0.68, 0.72, 0.78, 1.0]),
            "fscore_ttbj": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 0.50, 0.60, 1.0]),
            "fscore_ttcc": np.array([0.0, 0.31, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.59, 0.65, 0.73, 0.87, 1.0]),
            "fscore_tt2c": np.array([0.0, 0.24, 0.28, 0.32, 0.36, 0.40, 0.44, 0.50, 1.0]),
            "fscore_ttcj": np.array([0.0, 0.23, 0.26, 0.30, 0.34, 0.38, 0.42, 0.48, 1.0]),
            "fscore_ttLF": np.array([0.0, 0.07, 0.09, 0.10, 0.11, 1.0])
        }

_wc_instance = weights_and_constants()
adhoc_selection = _wc_instance.adhoc_selection
adhoc_binning = _wc_instance.adhoc_binning