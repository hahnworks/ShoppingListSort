import configparser
import requests
from openai import OpenAI
import json
from pydantic import BaseModel

class Item(BaseModel):
    item_name: str

class Aisle(BaseModel):
    aisle_name: str
    items_in_aisle: list[Item]

class Store(BaseModel):
    store_name: str
    store_aisles: list[Aisle]

class Stores(BaseModel):
    store_list: list[Store]


"""
The response will look something like this:

{
    "stores": {
        "EDEKA": {
            "aisles": {
                "Obst und Gemüse": {
                    "items": [
                        {"name": "Äpfel"},
                        {"name": "Bananen"}
                    ]
                }
            }
        }
    }
}
"""


class HomeAssistantInterface:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def get_shopping_list(self):
        url = self.api_url + "shopping_list"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response.json()

class OpenAIInterface:
    def __init__(self, api_key, system_message = "You are a helpful assistant.", model="gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.system_message = system_message
        self.model = model

    def call(self, message, format=Stores):
        # https://platform.openai.com/docs/guides/structured-outputs

        response = self.client.responses.parse(
            model=self.model,
            input = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": message}
            ],
            text_format=format
        )

        return response.output_parsed

def generate_system_message(config):
    system_message = """
    Your task is to sort a grocery item list based on the provided stores and their layout.
    Assign every item a store and (if applicable) a specific aisle.

    Use only the aisles specified in the following JSON.
    DO NOT INVENT ANY NEW AISLES.
    If unsure, use "Miscellaneous" as the aisle.
    """

    system_message += json.dumps(config['stores'], indent=4)

    return system_message

def main():
    # Read configuration from JSON file
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    ha_interface = HomeAssistantInterface(
        api_url=config['api']['homeassistant']['url'],
        api_key=config['api']['homeassistant']['key']
    )
    oai_interface = OpenAIInterface(
        api_key=config['api']['openai']['key'],
        model = config['api']['openai']['model'],
        system_message=generate_system_message(config)
    )

    current_shopping_list = ha_interface.get_shopping_list()

    #clean_shopping_list = [i for i in current_shopping_list if not i['complete'] and (i['name'][0] not in ["+", "-", "="])]
    clean_shopping_list = [i for i in current_shopping_list if (i['name'][0] not in ["+", "-", "="])]

    # since cheap gpt models tend to "forget" some items, check the length.
    clean_shopping_list_length = len(clean_shopping_list)

    response = oai_interface.call(json.dumps(clean_shopping_list), format=Stores)
    json_data = json.loads(response.model_dump_json())

    #print(json.dumps(json_data["store_list"]))

    new_shopping_list = []
    for store in json_data['store_list']:
        if store['store_aisles'] not in [None, [], {}]:
            new_shopping_list.append("+++ " + store['store_name'] + " +++")
            for aisle in store['store_aisles']:
                if aisle['items_in_aisle'] not in [None, [], {}]:
                    #new_shopping_list.append("--- " + aisle['aisle_name'] + " ---")
                    for item in aisle['items_in_aisle']:
                        new_shopping_list.append(item['item_name'])

    clean_new_shopping_list = [i for i in new_shopping_list if (i[0] not in ["+", "-", "="])]
    clean_new_shopping_list_length = len(clean_new_shopping_list)
    if clean_new_shopping_list_length != clean_shopping_list_length:
        print("Warning: Some items may have been forgotten.")
        print("Old: ", clean_shopping_list_length)
        print("New: ", clean_new_shopping_list_length)

    for s in new_shopping_list:
        print(s)

if __name__ == "__main__":
    main()
