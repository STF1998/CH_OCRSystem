import pandas
import re
from google.cloud import vision
import io

no_need = r"[.°_=*~`;“”:,\|/}{\[\]^%@!?><±§+‘’\"\']"


def detect_text(path):

    
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(
        image=image,
        image_context={"language_hints": ["en"]},
        )
    document = response.full_text_annotation

    data = []
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        symbol_info = []
                        if re.match(no_need, symbol.text) == None:
                            symbol_info.append(symbol.text)
                            symbol_info.append(symbol.bounding_box.vertices[0].y)
                            symbol_info.append(symbol.bounding_box.vertices[2].y)
                            symbol_info.append(symbol.bounding_box.vertices[0].x)
                            symbol_info.append(symbol.bounding_box.vertices[2].x)
                            data.append(symbol_info)

    df = pandas.DataFrame(data = data, columns = ['text', 'top', 'bottom', 'left', 'right'])
    
    # Bounding boxes for rows can sometime overlap. Giving a (padding * 2) pixel space helps to correct this issue 
    padding = 2
    df["top"] = df["top"] + padding
    df["bottom"] = df["bottom"] - padding

    """with open("GCVOutput.csv", "w") as out:
        df.to_csv(out)
    
    exit()"""
    return df