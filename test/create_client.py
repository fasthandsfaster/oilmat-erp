import requests
import json
import sys

# Define the API endpoint and the data to be sent


def main(argv):
    unique_id =  argv[0] 

    url = "http://localhost:5000/create"
    data = {
        "dealer": "admanager",
        "worksheet": "559",
        "product_nr": "10",
        "product_amount": "5",
        "unique_id": unique_id,
        "username": "rolf@mandrup.dk",
        "password": "Adm@1234"
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