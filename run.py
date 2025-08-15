import requests
from openai import OpenAI
import json
from pydantic import BaseModel

# Using an item based approach allows the LLM to pick the store and not the items.

class Item(BaseModel):
    item_name: str
    item_store: str
    item_aisle: str

class Items(BaseModel):
    items : list[Item]

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

    def call(self, message, format=Item):
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

def generate_system_message(system_message, stores):
    system_prompt = system_message
    system_prompt += json.dumps(stores, indent=4)

    return system_prompt

def item_major2location_major(item_major_list, stores):
    location_major_list = []
    for store in stores:
        tmp_sl_for_store = []
        for aisle in store["aisles"]:
            tmp_sl_for_aisle = []
            for item in item_major_list:
                if item["item_store"] == store["name"] and item["item_aisle"] == aisle["name"]:
                    tmp_sl_for_aisle.append(item["item_name"])
            if tmp_sl_for_aisle:
                tmp_sl_for_store.append({
                    "aisle_name": aisle["name"],
                    "items_in_aisle": tmp_sl_for_aisle
                })
        if tmp_sl_for_store:
            location_major_list.append({
                "store_name": store["name"],
                "store_aisles": tmp_sl_for_store
            })
    return location_major_list

def shopping_list_from_json(json_data):
    new_shopping_list = []
    for store in json_data:
        if store['store_aisles'] not in [None, [], {}]:
            new_shopping_list.append("+++ " + store['store_name'] + " +++")
            for aisle in store['store_aisles']:
                if aisle['items_in_aisle'] not in [None, [], {}]:
                    #new_shopping_list.append("--- " + aisle['aisle_name'] + " ---")
                    for item in aisle['items_in_aisle']:
                        new_shopping_list.append(item)
    return new_shopping_list

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
        system_message=generate_system_message(config["api"]["openai"]["system_message"], config["stores"])
    )

    current_shopping_list = ha_interface.get_shopping_list()

    clean_shopping_list = [i['name'] for i in current_shopping_list if not i['complete'] and (i['name'][0] not in ["+", "-", "="])]

    tries = 0
    item_major_list = []
    success = False

    while tries < config['api']['openai']['retries_on_item_drop']:
        response = oai_interface.call(json.dumps(clean_shopping_list), format=Items)
        json_data = json.loads(response.model_dump_json())
        item_major_list = json_data["items"]
        #print(json.dumps(item_major_list, indent=4))

        # “transpose” to store aisles major format
        location_major_list = item_major2location_major(item_major_list, config["stores"])
        new_shopping_list = shopping_list_from_json(location_major_list)

        # prepare clean shopping list, to check whether the LLM has dropped any items
        clean_new_shopping_list = [s for s in new_shopping_list if s[0] not in ["+", "-", "="]]

        if sorted(clean_shopping_list) != sorted(clean_new_shopping_list):
            print("Warning: Items have been dropped by the model!")
            tries += 1
            print("Retrying...")
        else:
            success = True
            break
    if not success:
        print("Error: Item sorting failed after multiple attempts.")
        print("Consider using a more complex model.")
        return


    for s in new_shopping_list:
        print(s)

if __name__ == "__main__":
    main()
