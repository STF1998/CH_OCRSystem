from .Parent_extractor import Parent
import pandas
import jellyfish
import math

class Full_extractor(Parent):

    def __init__(self, PandL: pandas.DataFrame, BaSh: pandas.DataFrame()):

        self.PandL = PandL
        self.BaSh = BaSh


        self.results = {
        "Fixed Assets (t)": "",
        "Cash (t)": "",
        "Debtors (t)": "",
        "Current Liabilities (t)": "", 
        "Working Capital (t)": "",
        "Current Assets (t)": "",
        "Capital Employed (t)": "",
        "Shareholders's Funds (t)": "",
        "Turnover (t)": "",
        "Cost of Sales (t)": "",
        "Gross profit (t)": "", 
        "Administrative Expenses (t)": "",
        "Operating profit (t)": "",
        "Interest payable (t)": "",
        "Profit before tax (t)": "",
        "Tax (t)": "",
        "Profit after tax (t)": "",
        "Fixed Assets (t-1)": "",
        "Cash (t-1)": "",
        "Debtors (t-1)": "",
        "Current Liabilities (t-1)": "", 
        "Working Capital (t-1)": "",
        "Current Assets (t-1)": "",
        "Capital Employed (t-1)": "",
        "Shareholders's Funds (t-1)": "",
        "Turnover (t-1)": "",
        "Cost of Sales (t-1)": "",
        "Gross profit (t-1)": "", 
        "Administrative Expenses (t-1)": "",
        "Operating profit (t-1)": "",
        "Interest payable (t-1)": "",
        "Profit before tax (t-1)": "",
        "Tax (t-1)": "",
        "Profit after tax (t-1)": ""
        }

    def is_match(self, little, big):

        def similar(a, b):
            return jellyfish.levenshtein_distance(a, b)

        reg = {
            "intercept": -0.7914866811,
            "beta": 2.018169921
        }

        if little == "":
            return False

        lev_dist = round(reg["intercept"] + reg["beta"]*math.log(len(little), 10))
        stop_at = (len(big) - len(little)) + 1
        if stop_at > 0:
            for i in range(stop_at):
                test_word = big[i:len(little) + i]
                if similar(test_word, little) <= lev_dist:
                    return True
        if similar(big, little) <= lev_dist:
            return True
        return False

    def register_result(self, row, required, not_required, label):

        for item in required:
            if self.is_match(item, row['label']) and self.is_match(not_required[0], row['label']) == False:
                if self.results[label + " (t)"] == "":
                    self.results[label + " (t)"] = row["t"]
                if self.results[label + " (t-1)"] == "":
                    self.results[label + " (t-1)"] = row["t-1"]
                return



    def get_PandL_variables(self):

        check_list = {
            "Turnover": [["turnover","revenue"],[""]],
            "Cost of Sales": [["costofsales"],[""]],
            "Gross profit": [["grossprofit","grossloss","gross"],[""]],
            "Administrative Expenses": [["administrativeexpenses", "administrativecosts", "administrative"],[""]],
            "Operating profit": [["operatingprofit", "operatingloss", "operating(loss)", "operating"],["other"]],
            "Interest payable": [["interestpayable", "netinterest", "interestexpense"],["recievable"]],
            "Profit before tax": [["lossonordinaryactivitiesbeforetax", "profitonordinaryactivitiesbeforetax",
                                "beforetax", "beforeincometax"],[""]],
            "Tax":[["taxonprofit", "taxonloss", "taxon(loss)", "incometaxcredit"],[""]],
            "Profit after tax":[["lossforthefinancialperiod", "profitforthefinancialperiod", "aftertax",
                                 "lossfortheyear", "profitforthefinancialyear", "(loss)/profitforthefinancialyear",
                                 "lossforthefinancialyear"],[""]]
        }


        for index, row in self.PandL.iterrows():
            if index != 0:
                for key, list in check_list.items():
                    self.register_result(row, list[0], list[1], key)
        
        if self.results["Profit after tax (t-1)"] == "":
            self.results["Profit after tax (t-1)"] = self.PandL.iloc[-1]["t-1"]
        if self.results["Profit after tax (t)"] == "":
            self.results["Profit after tax (t)"] = self.PandL.iloc[-1]["t"]

        if self.results["Interest payable (t-1)"] == "":
            self.results["Interest payable (t-1)"] = 0
        if self.results["Interest payable (t)"] == "":
            self.results["Interest payable (t)"] = 0

            
    def get_BaSh_variables(self):

        check_list = {
            "Current Liabilities": [["creditorsamountsfallingduewithinoneyear", "creditors"],[""]],
            "Working Capital": [["netcurrentliabilit", "netcurrentasset", "workingcapital"],[""]],
            "Capital Employed": [["totalassetslesscurrentliabilities", "assetslesscurrent"],[""]],
            "Shareholders's Funds": [["shareholdersdeficit", "totalequity", "shareholdersfunds",
                                    "shareholders"],[""]],
            "Current Assets": [["currentassets", "current"],[""]],
            "Cash": [["cashatbankandinhand", "cashatbank", "cash"],[""]],
            "Debtors": [["debtors"],["after"]],
            "Fixed Assets": [["fixedassets", "fixed"],[""]]
        }

        for index, row in self.BaSh.iterrows():
            if index != 0:
                for key, list in check_list.items():
                    self.register_result(row, list[0], list[1], key)

        if self.results["Shareholders's Funds (t-1)"] == "":
            self.results["Shareholders's Funds (t-1)"] = self.BaSh.iloc[-1]["t-1"]
        if self.results["Shareholders's Funds (t)"] == "":
            self.results["Shareholders's Funds (t)"] = self.BaSh.iloc[-1]["t"]

        if self.results["Debtors (t)"] == "":
            self.results["Debtors (t)"] = 0
        if self.results["Debtors (t-1)"] == "":
            self.results["Debtors (t-1)"] = 0
        if self.results["Cash (t)"] == "":
            self.results["Cash (t)"] = 0
        if self.results["Cash (t-1)"] == "":
            self.results["Cash (t-1)"] = 0
        if self.results["Fixed Assets (t)"] == "":
            self.results["Fixed Assets (t)"] = 0
        if self.results["Fixed Assets (t-1)"] == "":
            self.results["Fixed Assets (t-1)"] = 0


    def get_variables(self):
        self.get_PandL_variables()
        self.get_BaSh_variables()
                   

    def fill_obvious_gaps(self):

        if self.results["Current Liabilities (t)"] != "":
            if self.results["Current Liabilities (t)"] > 0:
                self.results["Current Liabilities (t)"] = -self.results["Current Liabilities (t)"]
        if self.results["Current Liabilities (t-1)"] != "":
            if self.results["Current Liabilities (t-1)"] > 0:
                self.results["Current Liabilities (t-1)"] = -self.results["Current Liabilities (t-1)"]

        if self.results["Cost of Sales (t)"] != "":
            if self.results["Cost of Sales (t)"] > 0:
                self.results["Cost of Sales (t)"] = -self.results["Cost of Sales (t)"]
        if self.results["Cost of Sales (t-1)"] != "":
            if self.results["Cost of Sales (t-1)"] > 0:
                self.results["Cost of Sales (t-1)"] = -self.results["Cost of Sales (t-1)"]

        if self.results["Administrative Expenses (t)"] != "":
            if self.results["Administrative Expenses (t)"] > 0:
                self.results["Administrative Expenses (t)"] = -self.results["Administrative Expenses (t)"]
        if self.results["Administrative Expenses (t-1)"] != "":
            if self.results["Administrative Expenses (t-1)"] > 0:
                self.results["Administrative Expenses (t-1)"] = -self.results["Administrative Expenses (t-1)"]

        if self.results["Interest payable (t)"] != "":
            if self.results["Interest payable (t)"] > 0:
                self.results["Interest payable (t)"] = -self.results["Interest payable (t)"]
        if self.results["Interest payable (t-1)"] != "":
            if self.results["Interest payable (t-1)"] > 0:
                self.results["Interest payable (t-1)"] = -self.results["Interest payable (t-1)"]

        if self.results['Tax (t)'] == "":
            if self.results['Profit before tax (t)'] != "" and self.results['Profit after tax (t)'] != "":
                self.results['Tax (t)'] = self.results['Profit after tax (t)'] - self.results['Profit before tax (t)']
        if self.results['Tax (t-1)'] == "":
            if self.results['Profit after tax (t-1)'] != "" and self.results['Profit before tax (t-1)'] != "":
                self.results['Tax (t-1)'] = self.results['Profit after tax (t-1)'] - self.results['Profit before tax (t-1)']

        if self.results['Working Capital (t)'] == "":
            if self.results['Current Assets (t)'] != "" and self.results['Current Liabilities (t)'] != "":
                self.results['Working Capital (t)'] = self.results['Current Assets (t)'] + self.results['Current Liabilities (t)']
        if self.results['Working Capital (t-1)'] == "":
            if self.results['Current Assets (t-1)'] != "" and self.results['Current Liabilities (t-1)'] != "":
                self.results['Working Capital (t-1)'] = self.results['Current Assets (t-1)'] + self.results['Current Liabilities (t-1)']
        

    def fill_missing_variables(self, time):

        if self.results["Fixed Assets " + time] == "" and self.results["Total Assets " + time] != "" and self.results["Current Assets"] != "":
            self.results["Fixed Assets " + time] = self.results["Total Assets " + time] - self.results["Current Assets " + time]
        
        if self.results["Current Assets " + time] == "" and self.results["Fixed Assets " + time] != "" and self.results["Total Assets " + time] != "":
            self.results["Current Assets " + time] = self.results["Total Assets " + time] - self.results["Fixed Assets " + time]

    def is_missing_items(self):

        count = 0

        for key, value in self.results.items():
            if value == "":
                count += 1

        self.count = count
        
        if count > 0:
            return True

        return False

    def get_number_missing(self):

        return self.count


    def are_results_valid(self, time):

        
        # if current assets + fixed assets minus total liabilities != shareholder funds
        if (self.results["Current Assets " + time] + self.results["Fixed Assets " + time]) + self.results["Total Liabilities " + time] != self.results["Shareholders's Funds " + time]:
            print("Test 1 failed")
            return False
        
        # Check that gross profit = turnover - cost of sales
        if self.results["Turnover " + time] + self.results["Cost of Sales " + time] != self.results["Gross profit " + time]:
            print("Test 2 failed")
            return False
        
        # Check that Earnings after tax is equal to earnings before tax + tax on profit/loss
        if self.results["Profit before tax " + time] + self.results["Tax " + time] != self.results["Profit after tax " + time]:
            print("Test 3 failed")
            return False

        # Check that earning before tax + interest payable == operating profit
        if self.results["Profit before tax " + time] + self.results["Interest payable " + time] != self.results["Operating profit " + time]:
            print("Test 4 failed")
            return False
        
        print("Data validity checks passed - no need for manual checks")
        return True


    def get_results(self):
        return self.results
