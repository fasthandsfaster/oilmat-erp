import requests
import json
import sys

# Define the API endpoint and the data to be sent


def main(argv):

    port = argv[0]
    case_nr = argv[1]
    product_nr = argv[2]
    product_amount = argv[3]
    unique_id =  argv[4] 
    username = argv[5]
    password = argv[6]

    url = "http://localhost:"+ port +"/create"
    data = {
        "dealer": "Gygag",
        "case_nr": case_nr,
        "product_nr": product_nr,
        "product_amount": product_amount,
        "unique_id": unique_id,
        "username": username,
        "password": password
    }

    json_data = json.dumps(data)

    # Send the PUT request with the data
    response = requests.post(url, json=json_data) # verify='path/to/cert.pem')

    # Print the response
    if response.status_code == 200:
        print("Success:", response)
    else:
        print("Error:", response)

if __name__ == "__main__":
   main(sys.argv[1:])