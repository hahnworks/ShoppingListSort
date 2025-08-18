"""
    This file is part of ShoppingListSort

    Copyright (C) 2025 Alexander Hahn

    This program is free software: you can redistribute it and/or modify
    it under the terms of the European Union Public License (EUPL), version 1.2.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    European Union Public License for more details.

    You should have received a copy of the European Union Public License
    along with this program. If not, see <https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12>.
"""

import requests
import re
from openai import OpenAI
import json
from pydantic import BaseModel
from time import sleep

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
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_shopping_list(self):
        url = self.api_url + "shopping_list"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def add_to_shopping_list(self, names):
        responses = []

        if not isinstance(names, list):
            names = [names]

        for i in names:
            url = self.api_url + "services/shopping_list/add_item"
            data = {
                "name": i
            }
            response = requests.post(url, headers=self.headers, json=data)
            responses.append(response.json())
        return responses

    def drop_from_shopping_list(self, names):
        responses = []

        if not isinstance(names, list):
            names = [names]

        for i in names:
            url = self.api_url + "services/shopping_list/remove_item"
            data = {
                "name": i
            }
            response = requests.post(url, headers=self.headers, json=data)
            responses.append(response.json())
        return responses

    def drop_shopping_list(self, drop_complete=False):
        shopping_list = self.get_shopping_list()
        self.drop_from_shopping_list([i["name"] for i in shopping_list if not i["complete"] or drop_complete])

class OpenAIInterface:
    def __init__(self, api_key, system_message = "You are a helpful assistant.", model="gpt-4.1"):
        self.client = OpenAI(api_key=api_key)
        self.system_message = system_message
        self.model = model

    def call(self, message, format=Item):
        # https://platform.openai.com/docs/guides/structured-outputs

        input = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": message}
            ]

        response = self.client.responses.parse(
            model=self.model,
            input=input,
            text_format=format
        )

        return response.output_parsed

class ShoppingListSorter:
    def __init__(self, config):
        self.config = config

        domain = re.match(r"https?://([^/]+)", config["api"]["homeassistant"]["url"]).group(1)
        self.config["api"]["homeassistant"]["url"] = f"https://{domain}/api/"

        self.ha_interface = HomeAssistantInterface(
            api_url=config['api']['homeassistant']['url'],
            api_key=config['api']['homeassistant']['key']
        )
        self.oai_interface = OpenAIInterface(
            api_key=config['api']['openai']['key'],
            model = config['api']['openai']['model'],
            system_message=generate_system_message(config["api"]["openai"]["system_message"], config["stores"])
        )
    def _item_major2location_major(self, item_major_list, stores):
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

    def _shopping_list_from_json(self, json_data):
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


    def get_categorized_item_list_from_llm(self, item_list):
            response = self.oai_interface.call(json.dumps(item_list), format=Items)
            json_data = json.loads(response.model_dump_json())
            item_major_list = json_data["items"]

            # “transpose” to store aisles major format
            location_major_list = self._item_major2location_major(item_major_list, self.config["stores"])
            new_shopping_list = self._shopping_list_from_json(location_major_list)

            return new_shopping_list

    def sort(self):
        current_shopping_list = self.ha_interface.get_shopping_list()

        clean_item_list = [i['name'] for i in current_shopping_list if not i['complete'] and (i['name'][0] not in ["+", "-", "=", "!"])]

        tries = 0
        success = False
        categorized_item_list = []

        while tries < self.config['api']['openai']['retries_on_item_drop']:

            categorized_item_list = self.get_categorized_item_list_from_llm(clean_item_list)

            # prepare clean shopping list, to check whether the LLM has dropped any items
            clean_new_item_list = [s for s in categorized_item_list if s[0] not in ["+", "-", "=", "!"]]

            if sorted(clean_item_list) != sorted(clean_new_item_list):
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

        self.ha_interface.drop_shopping_list(drop_complete=False)
        self.ha_interface.add_to_shopping_list(categorized_item_list)
        self.ha_interface.add_to_shopping_list("--- END ---")

    def listen(self):
        print("Listening...")
        while True:
            current_shopping_list = self.ha_interface.get_shopping_list()
            clean_item_list = [i['name'] for i in current_shopping_list if not i['complete'] and (i['name'][0] not in ["+", "-", "="])]

            if "!sort" in clean_item_list:
                self.sort()
            sleep(self.config['api']['homeassistant']['fetch_interval'])

def generate_system_message(system_message, stores):
    system_prompt = system_message
    system_prompt += json.dumps(stores, indent=4)

    return system_prompt

def main():
    # Read configuration from JSON file
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    sorter = ShoppingListSorter(config)
    sorter.listen()


if __name__ == "__main__":
    main()
