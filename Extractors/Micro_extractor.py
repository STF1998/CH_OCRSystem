from .Parent_extractor import Parent

class Micro_extractor(Parent):
    def __init__(self, information):
        self.company_information = information
        self.results = {
        "Current Liabilities": "",
        "Current Assets": "",
        "Working Capital": "",
        "Provisions": "",
        "Total Assets": "",
        "Total Liabilities": "", 
        "Capital Employed": "",
        "Shareholders' Funds": ""}

    def get_variables(self):


        CL_list = ["creditors", "amounts falling due within one year", "within one year", "within one", "within"]
        WC_list = ["net current liabilities", "net current assets"]
        Prov_list = ["provision"]
        CE_list = ["total assets less current liabilities"]
        SF_list = ["shareholders' funds", "capital and reserves", "shareholders'", "reserves"]
        CA_list = ["current assets"]

        for key, value in self.company_information.items():
            if any(item in key for item in CL_list):
                if self.results["Current Liabilities"] == "":
                    self.results["Current Liabilities"] = int(value)
            if any(item in key for item in WC_list):
                if self.results["Working Capital"] == "":
                    self.results["Working Capital"] = int(value)
            if any(item in key for item in Prov_list):
                if self.results["Provisions"] == "":
                    self.results["Provisions"] = int(value)
            if any(item in key for item in CE_list):
                if self.results["Capital Employed"] == "":
                    self.results["Capital Employed"] = int(value)
            if any(item in key for item in SF_list):
                if self.results["Shareholders' Funds"] == "":
                    self.results["Shareholders' Funds"] = int(value)
            if any(item in key for item in CA_list):
                if self.results["Current Assets"] == "":
                    self.results["Current Assets"] = int(value)
            
            
    


    def calculate_extra_variables(self):

        if self.results["Current Liabilities"] < 0:
            self.results["Current Liabilities"] = - self.results["Current Liabilities"]

        if self.results["Working Capital"] != "" and self.results["Current Liabilities"] != "":
            WC = self.results["Working Capital"]
            CL = self.results["Current Liabilities"]
            self.results["Current Assets"] = WC + CL

        if self.results["Capital Employed"] != "" and self.results["Current Liabilities"] != "":
            CE = self.results["Capital Employed"]
            CL = self.results["Current Liabilities"]
            self.results["Total Assets"] = CE + CL
        
        if self.results["Shareholders' Funds"] != "" and self.results["Total Assets"] != "":
            SF = self.results["Shareholders' Funds"]
            TA = self.results["Total Assets"]
            self.results["Total Liabilities"] = SF + TA
        
    
    def is_missing_items(self):

        for key, value in self.results.items():
            if self.results[key] == "":
                return True

        return False
    
        
    
    def calculate_ratios(self):
        self.results ["Current Ratio"] = self.results["Current Assets"] / self.results["Current Liabilities"]
        self.results ["Current Ratio"] = round(self.results ["Current Ratio"], 4)
        self.results ["Debt Ratio"] = self.results["Current Assets"] / self.results["Current Liabilities"]
        self.results ["Debt Ratio"] = round(self.results ["Debt Ratio"], 4)
        self.results ["Equity-Asset Ratio"] = self.results["Total Assets"] / self.results["Total Liabilities"]
        self.results ["Equity-Asset Ratio"] = round(self.results ["Equity-Asset Ratio"], 4)
        self.results ["Current Liabilities-to-Debt Ratio"] =  self.results["Current Liabilities"] / self.results["Total Liabilities"]
        self.results ["Current Liabilities-to-Debt Ratio"] = round(self.results ["Current Liabilities-to-Debt Ratio"], 4)


    def get_results(self):
        return self.results