from Extractors.Full_extractor import Full_extractor
from csv import writer
import API as api
import OCR as ocr
import os, time
from pebble import ProcessPool
from concurrent.futures import TimeoutError
import pandas
import functools

data_columns = ["Fixed Assets (t)",
        "Cash (t)",
        "Debtors (t)",
        "Current Liabilities (t)", 
        "Working Capital (t)",
        "Current Assets (t)",
        "Capital Employed (t)",
        "Shareholders's Funds (t)",
        "Turnover (t)",
        "Cost of Sales (t)",
        "Gross profit (t)", 
        "Administrative Expenses (t)",
        "Operating profit (t)",
        "Interest payable (t)",
        "Profit before tax (t)",
        "Tax (t)",
        "Profit after tax (t)",
        "Fixed Assets (t-1)",
        "Cash (t-1)",
        "Debtors (t-1)",
        "Current Liabilities (t-1)", 
        "Working Capital (t-1)",
        "Current Assets (t-1)",
        "Capital Employed (t-1)",
        "Shareholders's Funds (t-1)",
        "Turnover (t-1)",
        "Cost of Sales (t-1)",
        "Gross profit (t-1)", 
        "Administrative Expenses (t-1)",
        "Operating profit (t-1)",
        "Interest payable (t-1)",
        "Profit before tax (t-1)",
        "Tax (t-1)",
        "Profit after tax (t-1)", 
        "Firm Reg"]
    
exit_codes={1: 0, # Too many missing values
            2: 0, # Odd number of columns detected
            3: 0, # Too many columns detected
            4: 0, # No table found
            5: 0, # Couldn't find pages
            6: 0, # PDF conversion error
            7: 0, # Ambiguous detection of pages
            8: 0} # API failure 


def write_results(results):

    values = []
    for key, value in results.items():
        values.append(value)

    with open("Data/results2.csv", "a+") as file:
        csv_writer = writer(file)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(values)


def task_done(future, firm_reg):
    
    try:
        future.result() # blocks until results are ready
    except TimeoutError as error:
        print("Function took longer than %d seconds" % error.args[1])
    except Exception as error:
        print(error)
    
    # clean up
    folder = f"images_{firm_reg}"
    os.system(f"rm -r {folder}")


def driver(firm_reg):

    folder = f"images_{firm_reg}"
    os.mkdir(folder)
    pathway = f"{folder}/companies_house_document.pdf"

    # call CH api to retrieve and save the pdf for company accounts
    api.api_drive(firm_reg, pathway)

    # extract all balance sheet data relating to the company accounts
    PandL, BaSh = ocr.OCR_pdf(firm_reg)
    #PandL, BaSh = ocr.practise_OCR(firm_reg)

    full = Full_extractor(PandL, BaSh)
    full.get_variables()
    check_required = False

    results = results = full.get_results()
    full.fill_obvious_gaps()
    results["Firm Registration"] = firm_reg

    """for key, value in results.items():
        print(key, value)
    
    exit()"""

    if full.is_missing_items() == True:
        if full.get_number_missing():
            check_required = True

    write_results(results)

    if os.path.isfile("Data/manual_checks_list.csv") and check_required == True:
        with open("Data/manual_checks_list.csv", "a") as checker:
            checker.write(firm_reg + " -missing items" + "\n")



if __name__ == '__main__':

    with open("Data/manual_checks_list.csv", "w") as checker:
        checker.write("Firm Registration\n")

    with open("Data/results2.csv", "w") as results:
        pandas.DataFrame(columns = data_columns).to_csv(results) 

    
    firm_list = ["NI020454"]

    with ProcessPool(max_workers=os.cpu_count()) as pool:
        for firm_reg in firm_list:
            future = pool.schedule(driver, args=[firm_reg], timeout= 600)
            future.add_done_callback(functools.partial(task_done, firm_reg = firm_reg))
