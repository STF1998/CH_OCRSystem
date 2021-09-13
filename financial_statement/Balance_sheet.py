from .Financial_document import Fin_Doc
import re
from pythonds.basic import Stack
import pandas
import jellyfish
import math

class Balance_sheet(Fin_Doc):

    def __init__(self):
        self.info_type = "Balance Sheet"
    


    def find_pages(self, lines):

        required = ["balancesheet", "statementoffinancialposition"]
        group = ["groupbalancesheet", "consolidatedbalancesheet"]
        not_required = ["statementofincome", "pandlreport", "p&lreport", "incomeandexpensesstatement",
                        "incomestatement", "statementofoperation", "statementoffinancialresults",
                        "officersand", "directorsreport", "directorssreport", "auditorsreport",
                        "notestothefinancialstatement", "notestotheaccounts",
                        "statementofaccountingpolicies", "cashflow", "messagefromtheceo", 
                        "statementofdirectorsresponsibilit", "statementofdirectorssresponsibilit",
                        "statementofchangesinequity", "statementofchanges", "accountingpolicies",
                        "continued"]

        include, exclude, grp = [],[], []

        df = pandas.DataFrame({'text': [line[0] for line in lines], 'page': [line[1] for line in lines]})
        df = df.groupby('page').head(8).reset_index(drop=True)

        for index, row in df.iterrows():
            text = row['text'].lower()
            if any(item in text for item in required):
                include.append(row['page'])
            if any(item in text for item in not_required):
                exclude.append(row['page'])
            if any(item in text for item in group):
                grp.append(row['page'])



        answer = [number for number in include if number not in exclude]

        if len(answer) > 1:
            answer = [number for number in answer if number not in grp]
            if len(answer) > 1:
                print("Place of Balance Sheet is ambiguous")
                exit(7)

        return answer
    
    def sort_headings_totals(self, ordered_df):

        def is_match(little, big):

            def similar(a, b):
                return jellyfish.levenshtein_distance(a, b)

            reg = {
                "intercept": -0.106148668,
                "beta": 2.018169921
            }

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

        stack = Stack()
        iterator = ordered_df.iterrows()
        iterator.__next__()
        check_list = ["creditor", "shareholdersfunds", "capitalandreserve", "totalequity",
        "shareholders", "reserves", "shareholdersfunds", "shareholders", "fixedassets",
        "currentassets"]

        t = 0
        tMinOne = 0

        new_data = []
        new_data.append([ordered_df.iloc[0]['label'], ordered_df.iloc[0]['t'], ordered_df.iloc[0]['t-1']])

        for index, row in iterator:

            # if the headers stack is not empty
            if stack.isEmpty() == False:
                if row['t'] != None:
                    t += row["t"]
                if row['t-1'] != None:
                    tMinOne += row['t-1']
                if row['t'] == None and row['t-1'] == None and row['label'] == "":
                    if t != 0 or tMinOne != 0:
                        label = stack.pop()
                        new_data.append([label,t,tMinOne])
                        t, tMinOne = 0, 0

            if row["t"] == None and row["t-1"] == None and row['label'] != "":
                if any(is_match(item, row['label']) for item in check_list):
                    stack.push(row['label'])
                else:
                    new_data.append([row["label"], 0, 0])

            if row["label"] == "" and (row["t"] != None or row["t-1"] != None):
                if stack.isEmpty() == False:
                    new_data.append([stack.pop(), row["t"], row["t-1"]])

            if row['label'] != "" and (row["t"] != None or row["t-1"] != None):
                new_data.append([row['label'], row["t"], row["t-1"]])

        return pandas.DataFrame(data = new_data, columns = ["label", "t", "t-1"])