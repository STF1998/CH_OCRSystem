from abc import ABC, abstractmethod
import re
import numpy

class Fin_Doc(ABC):

    @abstractmethod
    def find_pages(self, lines):
        pass


    def get_type(self):
        return self.info_type


    def prep_lines_for_page_search(self, dataframe):

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
                    string = string + current_row['text'].strip()
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


        
    def get_table_lines(self, text):

        if len(text) == 0:
            return None

        unit_regex = r'^(.*([£$ ]+m|[£$ ]+k|[£$ ]+000|[£$]|[£$ ]+million|[£$ ]+thousand)+\s*)*$'
        # start - word {0+} - space {0,1} then a number - space - number - end
        final_line_regex = r'(.*)(\(?\-?[\,0-9-]+\)?)(\(?\-?[\,0-9-]+\)?)$'

        start = -1
        finish = -1
        for i in range(0, len(text)):
            line = text[i][0]
            if re.match(unit_regex, line) and start == -1:
                start = i
            if re.match(final_line_regex, line):
                finish = i
        
        if finish != -1 and start != -1:
            array = []
            for i in range(start, finish + 1):
                array.append(text[i][0])
            return array
    
        print("No table identified")
        return None

    
    def get_units(self, text):

        regex = r'^(.*([£$ ]+m|[£$ ]+k|[£$]|[£$ ]+million|[£$ ]+thousand)+\s*)*$'
        if match := re.match(regex, text[0]):
            return match.group()

        return None