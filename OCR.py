import pytesseract
import os, re
import pandas
from PIL import Image
from io import StringIO
import pre_processing as proc
from financial_statement.Balance_sheet import Balance_sheet
from financial_statement.PandL import PandL
import numpy
from pythonds.basic import Stack
import jellyfish
import GCV.gcv_client as gcv_client
import GCV.gcv_line_processor as gcv_process
import math

def make_measurments(df):

    df["bottom"] = df["top"] + df["height"]
    df["right"] = df["left"] + df["width"]
    return df



def get_labels_and_values(page_dataframe):
    return gcv_process.gcv_line_processor(page_dataframe)




def get_table_dataframe(page_dataframe, page_lines):

    def is_match(line):

        reg = {
            "intercept": -0.7914866811,
            "beta": 2.018169921
        }

        words = ['shareholder','loss','profit','results','income','earnings','retained','equity', 'deficit', 
                'funds', 'year']
        table_end = r'^.*[0-9-()]+$'

        def similar(a, b):
            return jellyfish.levenshtein_distance(a, b)

        if re.match(table_end, line):
            if len(label := re.findall(r'([^\d]+)', line)) != 0:
                label = label[0]
                for possibility in words:
                    lev_dist = round(reg["intercept"] + reg["beta"]*math.log(len(possibility), 10))
                    stop_at = (len(label) - len(possibility)) + 1
                    if stop_at > 0:
                        for i in range(stop_at):
                            test_word = line[i:len(possibility) + i]
                            if similar(test_word, possibility) <= lev_dist:
                                return True
                    else:
                        if similar(label, possibility) <= lev_dist:
                            return True
        
        return False

            
            
    if len(page_dataframe) == 0:
        return None

    unit_regex = r'^(.*([£$ ]+m|[£$(US$) ]+k|[£$ ]+000|[£$]|[£$ ]+million|[£$ ]+thousand)+.*)*$'
    backup_regex = r'^(note[s]?){1}[0-9]*'

    start = -1
    backup = -1
    finish = -1
    for i in range(len(page_lines) - 1):
        line = page_lines[i]
        text = line[0].lower()
        if re.match(unit_regex, text) and start == -1:
            start = line[1]
        if re.match(backup_regex, text) and backup == -1:
            backup = line[1]
        if is_match(text):
           finish = line[2]
           if re.match(r'^[()0-9]{2,}$', page_lines[i + 1][0].lower()):
               finish = page_lines[i + 1][2]

    if start == -1 and backup != -1:
        start = backup

    if finish != -1 and start != -1:
        upper = page_dataframe["top"] >= start
        lower = page_dataframe["bottom"] <= finish
        upper[0] = True
        lower[0] = True
        return page_dataframe[upper & lower].reset_index(drop = True)

    return None











def get_lines(dataframe, space):

    lines = []

    get_numpy_of_concern = lambda row: numpy.array([row["pdf_page"], row["block_num"], row["par_num"], row["line_num"]])

    row_iterator = dataframe.iterrows()
    not_used, row_of_concern = row_iterator.__next__()
    array_of_concern = get_numpy_of_concern(row_of_concern)
    string = " "
    top = float("inf")
    bottom = 0

    for index, current_row in row_iterator:
        test_array = get_numpy_of_concern(current_row)
        if numpy.array_equiv(array_of_concern, test_array) and current_row['text'] != None:
            if bool(re.match(r'^[ \t]+$', current_row['text'])) == False and current_row['text'] != "":
                string = string + space + current_row['text'].strip()
                if current_row["top"] < top:
                    top = current_row["top"]
                if current_row["bottom"] > bottom:
                    bottom = current_row["bottom"]
        else:
            if (string := string.strip()) != "":
                four_cell = [string, row_of_concern["pdf_page"], top, bottom]
                lines.append(four_cell)
            top = float("inf")
            bottom = 0
            row_of_concern = current_row
            array_of_concern = get_numpy_of_concern(row_of_concern)
            string = " "
        
    return lines








def analyse_pages(acc_type, dataframe, page_lines):

    # This should work for all CAPS now
    def sort_line_continuations(dataframe: pandas.DataFrame):

        def join(continued_line, value_list, i):

            text = continued_line[0] + value_list[i][0]
            return [text, value_list[i][1], value_list[i][2]]
        
        def append_returning_data(returning_data, continued_line):
            continued_line[0] = continued_line[0].lower()
            returning_data.append(continued_line)


        value_list =[list(dataframe.iloc[i]) for i in range(len(dataframe.index))]
        returning_data = []
        returning_data.append([value_list[0][0], value_list[0][1], value_list[0][2]])
        continued_line = value_list[1]

        for i in range(2, len(value_list)):

            value_list[i][0] = re.sub(r'[0-9]', '', value_list[i][0])
            joining = False

            if value_list[i][0] != "" and continued_line[0] != "":
                if continued_line[0][-1].isupper() == value_list[i][0][0].isupper():
                    if value_list[i][0][0].isupper() == value_list[i][0][1].isupper():
                        if continued_line[1] == "" and continued_line[2] == "":
                            continued_line = join(continued_line, value_list, i)
                            joining = True
    
            if joining == False:
                append_returning_data(returning_data, continued_line)
                continued_line = value_list[i]
            
            if i == len(value_list) - 1:
                continued_line[0] = continued_line[0].lower()
                returning_data.append(continued_line)

        return pandas.DataFrame(data = returning_data, columns = ["label", "t", "t-1"])

        
    def sort_units(ordered_df):

        units = [ordered_df.iloc[0]["t"], ordered_df.iloc[0]["t-1"]]
        if re.match(r'[£\',US$€\s]', units[0]) == None:
            units[0] = '£'
            units[1] = '£'
            ordered_df.iloc[0]["t"] = units[0]
            ordered_df.iloc[0]["t-1"] = units[1]

        multiplier = re.sub(r'[£\',US$€\s]', "", str(units[0]))
        if multiplier == "":
            multiplier = "1"
        multiplier = re.sub(r"(000|k|thousand)", "1000", multiplier)
        multiplier = re.sub(r"(m|million)", "1000000", multiplier)

        multiplier = int(multiplier)

        for i in range(1, len(ordered_df.index)):
            if ordered_df.iloc[i]["t"] != None:
                ordered_df.iloc[i]["t"] = ordered_df.iloc[i]["t"] * multiplier
            if ordered_df.iloc[i]["t-1"] != None:
                ordered_df.iloc[i]["t-1"] = ordered_df.iloc[i]["t-1"] * multiplier

        value = re.findall(r"[£$]", ordered_df.iloc[0]["t"])
        if len(value) != 0:
            ordered_df.iloc[0]["t"] = value[0]
        value = re.findall(r"[£$]", ordered_df.iloc[0]["t-1"])
        if len(value) != 0:
            ordered_df.iloc[0]["t-1"] = value[0]
        
        return ordered_df


    def integer_conversion(ordered_df):

        def convertible(continued_line):

            if continued_line == None:
                return False

            continued_line = continued_line.strip()

            if continued_line == "":
                return False

            if re.match(r'[-.,]', continued_line):
                return False
                
            return True

        def clean_numbers(continued_line):

            sub = r'[^0-9(]'

            if continued_line["label"].lower() == "total":
                continued_line["label"] = ""

            # handling OCR inaccuracies due to noise
            if continued_line["t"].strip() == "-" and continued_line["t-1"].strip() == "":
                continued_line["t"] = ""
            if continued_line["t-1"].strip() == "-" and continued_line["t"].strip() == "":
                continued_line["t-1"] = ""

            if continued_line["t"].strip() == "" and continued_line["t-1"].strip() != "":
                continued_line["t"] = "0"
            if continued_line["t-1"].strip() == "" and continued_line["t"].strip() != "":
                continued_line["t-1"] = "0"

            if continued_line["t"].strip() == "-":
                continued_line["t"] = "0"
            if continued_line["t-1"].strip() == "-":
                continued_line["t-1"] = "0"

            continued_line["t"] = re.sub(sub, '', continued_line["t"])
            continued_line["t-1"] = re.sub(sub, '', continued_line["t-1"])

            return continued_line
        
        to_int = lambda continued_line: int(continued_line.replace("(", "-"))

        for i in range(len(ordered_df.index)):
            if i != 0:
                ordered_df.iloc[i] = clean_numbers(ordered_df.iloc[i])
                if convertible(ordered_df.iloc[i]["t"]) == True:
                    ordered_df.iloc[i]["t"] = to_int(ordered_df.iloc[i]["t"])
                else:
                    ordered_df.iloc[i]["t"] = None
                if convertible(ordered_df.iloc[i]["t-1"]) == True:
                    ordered_df.iloc[i]["t-1"] = to_int(ordered_df.iloc[i]["t-1"])
                else:
                    ordered_df.iloc[i]["t-1"] = None
        
        return ordered_df

        
    table_dataframe = get_table_dataframe(dataframe, page_lines)
    if type(table_dataframe) != type(None):
        ordered_df = get_labels_and_values(table_dataframe)
        ordered_df = sort_line_continuations(ordered_df)
        ordered_df = integer_conversion(ordered_df)
        ordered_df = sort_units(ordered_df)
        ordered_df = acc_type.sort_headings_totals(ordered_df)
        return ordered_df

    print("Couldn't extract info - probably because I couldn't find the table")
    exit(4)



def investigate_accounts(type, firm_reg, all_lines):

    if len(page := type.find_pages(all_lines)) == 0:
        print(f"Can't find {type.get_type()} pages")
        exit(5)

    page_dataframe = gcv_client.detect_text(f'images_{firm_reg}/companies_house_document-{page[0]}.png')
    page_lines = gcv_process.gcv_get_lines(page_dataframe)

    return analyse_pages(type, page_dataframe, page_lines)







def run_OCR(png_file):

    print(f"analysing {png_file} with OCR")

    image = Image.open(png_file)

    configuration = """--psm 6 --oem 1 -c tessedit_char_blacklist=.°_=*~`;“”:,|\/}{[]^%@!?><±§+‘’\\"\\'"""

    # --psm 6 is important as the get_lines function treats the whole page as a single block
    image_to_data = StringIO(pytesseract.image_to_data(image, config= configuration, lang="eng"))
    data = pandas.read_csv(image_to_data, sep=' |\t', error_bad_lines=False, engine='python')

    return data





 
def OCR_pdf(firm_reg):

    filepath = f"images_{firm_reg}/companies_house_document.pdf"

    # Convert the pdf to png, pre-process and remove the pdfs
    print("converting PDFs to PNGs")
    proc.pdf_to_png(filepath)
    png_filepaths = proc.pre_process(filepath.replace(".pdf", ""))

    
    # If there are not any images then return an empty array
    if len(png_filepaths) == 0:
        print("No images to OCR")
        exit(6)

    # Run OCR on each page
    df = pandas.DataFrame()
    page_number = 1
    for png_file in png_filepaths:
        data = run_OCR(png_file)
        data["pdf_page"] = page_number
        page_number += 1
        df = df.append(data)
    df = make_measurments(df)

    """with open("OCR_Output.csv", "w") as ocr:
        df.to_csv(ocr)
    exit()"""

    # Get all of the lines in the document
    all_lines = []
    for page in range(1,df["pdf_page"].max() + 1):
        page_lines = get_lines(df[df['pdf_page'] == page], "")
        all_lines = all_lines + page_lines
    
    # find the balance sheet pages
    print("Balance Sheet search")
    Balance_information = investigate_accounts(Balance_sheet(), firm_reg, all_lines)
    print("PandL search")
    PandL_information = investigate_accounts(PandL(), firm_reg, all_lines)

    return PandL_information, Balance_information



def practise_OCR(firm_reg):

    with open("OCR_Output.csv", "r") as input:
        df = pandas.read_csv(input, index_col=[0])

    # Get all of the lines in the document
    all_lines = []
    for page in range(1,df["pdf_page"].max() + 1):
        page_lines = get_lines(df[df['pdf_page'] == page], "")
        all_lines = all_lines + page_lines
    
    # find the balance sheet pages
    print("Balance Sheet search")
    Balance_information = investigate_accounts(Balance_sheet(), firm_reg, all_lines)
    print("PandL search")
    PandL_information = investigate_accounts(PandL(), firm_reg, all_lines)

    return PandL_information, Balance_information

    # Join the extracted info for P&L and Balance sheet together
    return pandas.concat([Balance_information, PandL_information.iloc[1:]], ignore_index=True, sort=False)

        