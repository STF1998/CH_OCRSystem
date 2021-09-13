from .Financial_document import Fin_Doc
import re
import pandas
import jellyfish
import math

class PandL(Fin_Doc):

    def __init__(self):
        self.info_type = "P and L"

    def find_pages(self, lines):

    
        required = ["profitandlossaccount", "statementofincome", "pandlreport", "incomestatement"]
        req_reserve = ["statementofcomprehensiveincome", "comprehensiveincome"]
        group = ["group", "consolidated"]
        not_required = ["balancesheet", "officersand", "directorsreport", "directorssreport",
                        "auditorsreport", "statementofchangesinequity", "statementofchanges",
                        "notestothefinancialstatement", "notestotheaccounts", "statementofaccountingpolicies",
                        "cashflow", "messagefromtheceo", "statementofdirectorsresponsibilit", 
                        "statementofdirectorssresponsibilit", "statementoffinancialposition",
                        "accountingpolicies", "statementoftotalrecognisedgainsandlosses", "continued"]

        include, exclude, comp, grp = [],[],[],[]

        df = pandas.DataFrame({'text': [line[0] for line in lines], 'page': [line[1] for line in lines]})
        df = df.groupby('page').head(7).reset_index(drop=True)
        
        for index, row in df.iterrows():
            text = row['text'].lower()
            if any(item in text for item in required):
                include.append(row['page'])
            if any(item in text for item in not_required):
                exclude.append(row['page'])
            if any(item in text for item in req_reserve):
                comp.append(row['page'])
            if any(item in text for item in group):
                grp.append(row['page'])
        

        answer = [number for number in include if number not in exclude]

        if len(answer) == 0:
            answer = [number for number in comp if number not in exclude]
        
        if len(answer) > 1:
            answer = [number for number in answer if number not in grp]
            if len(answer) > 1:
                print("Place of PandL is ambiguous")
                exit(7)

        return answer

        
    def sort_headings_totals(self, ordered_df):

        for index, row in ordered_df.iterrows():
            if ordered_df.iloc[index]["label"] != "":
                if ordered_df.iloc[index]["t"] == None:
                    ordered_df.iloc[index]["t"] = 0
                if ordered_df.iloc[index]["t-1"] == None:
                    ordered_df.iloc[index]["t-1"] = 0
        
        return ordered_df
            