import re
import pandas

def make_calculations(results, data):

    if results["Working Capital"] != "" and results["Current Liabilities"] != "":
        results["Current Assets"] = int(results["Working Capital"]) + int(results["Current Liabilities"])

    if "total assets less current liabilities" in data and results["Current Liabilities"] != "":
        results["Total Assets"] = int(results["Total Assets Less Current Liabilities"]) + int(results["Current Liabilities"])
    
    return results

    

def extract_information(data):


    unit = data["units"]

    results = {
        "Firm Registration": "",
        "Current Liabilities": "",
        "Current Assets": "",
        "Working Capital": "",
        "Provisions": "",
        "Total Assets": "",
        "Total Assets Less Current Liabilities": ""
    }


    if (unit := re.sub(r'[£$]', '', unit).strip()) != "":
        numbers = {"million" : 1000000, "thousand" : 1000, "m": 1000000, "k": 1000}
        unit = int(numbers[unit])
        data = {key: int(value)*unit for key, value in data}
    
    for key, value in data.items():
        if bool(re.match("creditors", key)):
            results["Current Liabilities"] = value
        if bool(re.match("amounts falling due within one year", key)) and results["Current Liabilities"] == "" :
                results["Current Liabilities"] = value
        if bool(re.match("within one year", key)) and results["Current Liabilities"] == "" :
            results["Current Liabilities"] = value
        if bool(re.match("within one", key)) and results["Current Liabilities"] == "" :
            results["Current Liabilities"] = value
        if bool(re.match("within", key)) and results["Current Liabilities"] == "" :
            results["Current Liabilities"] = value
    
    
        if bool(re.match("net current liabilities", key)):
            results["Working Capital"] = value
        if bool(re.match("net current assets", key)) and results["Working Capital"] == "":
            results["Working Capital"] = value

        if bool(re.match("provision", key)):
            results["Provisions"] = value

        if bool(re.match("total assets less current liabilities", key)):
            results["Total Assets Less Current Liabilities"] = value

    results = make_calculations(results, data)

    return results
    

