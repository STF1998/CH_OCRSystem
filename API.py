import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import time


def get_filing_history(http: requests.Session, company_id):

    returns = []

    try:
        i = 0
        while True:
            params = {"items_per_page": 100, "start_index": i}
            response = http.get(f"https://api.company-information.service.gov.uk/company/{company_id}/filing-history",
            auth=HTTPBasicAuth('afc84b20-eab4-496b-b347-844ba6c893ab',''), timeout = 10, params= params)
            if response.status_code == 200:
                response = response.json()
            else:
                print("unable to retrieve filing history")
                print("reponse code =", response.status_code)
                exit(8)
            if (total_items := response["total_count"]) == 0:
                exit(8)
            i += 100
            returns.append(response)
            if total_items <= i:
                return returns
    except requests.exceptions.RequestException as e:
        exit(8)
    return None

def get_file(http, pathway, link):

    try:
        response = http.get(link,
        auth=HTTPBasicAuth('afc84b20-eab4-496b-b347-844ba6c893ab',''), timeout = 10)
        if response.status_code == 200:
            with open(pathway, "wb") as accounts:
                accounts.write(response.content)
        else:
            print("unable to retrieve accounts")
            print("response code =", response.status_code)
            exit(8)
    except requests.exceptions.RequestException as e:
        exit(8)


def retrieve_document(http, pathway, company_id):
    
    info = get_filing_history(http, company_id)

    year = "2019"

    for page in info:
        for item in page["items"]:
            if "accounts-with-accounts-type-full" in item["description"]:
                if item["date"].split("-")[0] == year:
                    link = f"https://find-and-update.company-information.service.gov.uk/company/{company_id}/filing-history/{item['transaction_id']}/document?format=pdf&download=0"
                    get_file(http, pathway, link)
                    return item["date"]

    print("no document for this year")
    return 0



def api_drive(firm_reg, pathway):

    if (length := len(firm_reg)) != 8:
        zeros = abs(8 - length) * "0"
        firm_reg = zeros + firm_reg


    retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"])

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    if retrieve_document(http, pathway, firm_reg) == 0:
        print("unable to retrieve document")
        exit(8)

