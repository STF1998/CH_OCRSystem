import pandas
import re

def retrieve_column_pixels(df, page_width):


    buffer = 20
    occupied_pixels = []
    columns = []
    for i in range(page_width + 2):
        result = (( df['right'] >= i ) & ( df['left'] <= i )).sum() > 0
        if result:
            occupied_pixels.append(i)
        else:
            if len(occupied_pixels) != 0:
                columns.append([min(occupied_pixels), max(occupied_pixels)])
                occupied_pixels = []


    error_adjusted = []
    main_column = columns[0]

    for i in range(1, len(columns)):
        if main_column[1] >= columns[i][0] - buffer:
            main_column[1] = columns[i][1]
        else:
            error_adjusted.append(main_column)
            main_column = columns[i]
        if i == len(columns) - 1:
            error_adjusted.append(main_column)
            
            
    return error_adjusted
        

def retrieve_row_pixels(df, page_height):

    occupied_pixels = []
    rows = []
    for i in range(page_height + 2):
        result = (( df['bottom'] >= i ) & ( df['top'] <= i )).sum() > 0
        if result:
            occupied_pixels.append(i)
        else:
            if len(occupied_pixels) != 0:
                rows.append([min(occupied_pixels), max(occupied_pixels)])
                occupied_pixels = []
    return rows

def condense_columns(full_data: list):

    new_cols = []
    column_count = len(full_data)

    if column_count == 8:
        return [full_data[0], full_data[1], full_data[4], full_data[7]]

    if column_count % 2 == 0:
        stop_at = 1
    else:
        stop_at = 0

    # iterate backwards from n to 2nd column
    for i in range(len(full_data) - 1, stop_at, -2):
        final_columns = []
        # iterate 0 to column length
        for j in range(min(len(full_data[i]),len(full_data[i - 1]))):
            if j != 0:
                if full_data[i][j].strip() == '' or full_data[i-1][j].strip() == '':
                    final_columns.append((full_data[i][j] + full_data[i-1][j]).strip())
                else:
                    print("trying to join non-null columns")
                    exit(10)
            else:
                final_columns.append(full_data[i][j])
        new_cols.append(final_columns)

    final_columns = full_data[:2]
    for j in range(len(new_cols) - 1, -1, -1):
        final_columns.append(new_cols[j])
            
            
    return final_columns

def add_blank_rows(full_data, blank_rows):

    column_length = len(full_data[0])

    index = len(blank_rows) - 1 
    for i in range(column_length - 1, -1, -1):
        if i == blank_rows[index]:
            for j in range(len(full_data)):
                full_data[j].insert(i, '')
            index -= 1
    
    return full_data


def run_corrections(full_data):


    def remove_rows(removals, full_data):

        for j in range(len(removals) - 1, -1, -1):
            index = removals[j]
            for i in range(len(full_data)):
                del full_data[i][index]

        return full_data

    def find_excess_rows_before_table(full_data):

        removals = []
        # iterate through rows
        for i in range(len(full_data[0])):
            numb_cols = len(full_data)
            #iterate through columns
            for j in range(numb_cols):
                cell = full_data[j][i].lower()
                if 'note' in cell or re.match(r'[£$€]', cell):
                    return remove_rows(removals, full_data)
            removals.append(i)

        return full_data

    full_data = find_excess_rows_before_table(full_data)

    #remove columns with very few items
    for i in range(len(full_data) - 1, -1, -1):
        count = 0
        is_note_column = False
        for item in full_data[i]:
            if item == '':
                count += 1
            if "note" in item.lower().strip():
                is_note_column = True
        if (count / len(full_data[i])) > 0.85 and is_note_column == False:
            del full_data[i]


    # join working columns
    if len(full_data) > 4:
        full_data = condense_columns(full_data)

    # there should now be an even number of columns or exactly 3 columns
    if len(full_data)%2 != 0 and len(full_data) != 3:
        print("odd number of columns (>3)")
        exit(2)

    if len(full_data) != 4 and len(full_data) != 3:
        print("column condensation failure")
        exit(3)

    return full_data



def gcv_get_lines(page_dataframe):

    page_dataframe = page_dataframe[page_dataframe['text'].isnull() == False]

    rows = retrieve_row_pixels(page_dataframe, page_dataframe['bottom'].max())

    full_data = []
    for row in rows:
        data = []
        horizontal = (page_dataframe['bottom'] <= row[1]) & (page_dataframe['top'] >= row[0])
        joint = page_dataframe[horizontal].sort_values(by=['right'])
        data.append("".join([str(word) for word in joint['text']]))
        data.append(row[0])
        data.append(row[1])
        full_data.append(data)

    return full_data


def gcv_line_processor(page_dataframe):

    page_dataframe = page_dataframe[page_dataframe['text'].isnull() == False]

    columns = retrieve_column_pixels(page_dataframe, page_dataframe['right'].max())
    rows = retrieve_row_pixels(page_dataframe, page_dataframe['bottom'].max())

    blank_rows = []
    for i in range(1, len(rows)):
        delta = rows[i][0] - rows[i - 1][1] 
        if delta > 50 and delta < 110:
            blank_rows.append(i)

    full_data = []
    
    for i in range(len(columns)):
        column_data = []
        for row in rows:
            horizontal = (page_dataframe['bottom'] <= row[1]) & (page_dataframe['top'] >= row[0])
            vertical = (page_dataframe['right'] <= columns[i][1]) & (page_dataframe['left'] >= columns[i][0])
            selection = horizontal & vertical
            joint = page_dataframe[selection].sort_values(by=['right'])
            column_data.append("".join([str(word) for word in joint['text']]))
        full_data.append(column_data)

    if len(blank_rows) != 0:
        full_data = add_blank_rows(full_data, blank_rows)

    full_data = run_corrections(full_data)

    if len(full_data) == 4:
        data = {
            "label":full_data[0],
            "t": full_data[2],
            "t-1": full_data[3]
        }
    else:
        data = {
            "label":full_data[0],
            "t": full_data[1],
            "t-1": full_data[2]
        }

        
    return pandas.DataFrame(data)

