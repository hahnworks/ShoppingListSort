# ✏️📋🛒 Shopping List Sort

Sort your Home Assistant list by store and aisle using OpenAIs GPT models!


## Motivation

While the Shopping List integration in Home Assistant is very convenient when sharing a shopping list and communicating efficiently which groceries or supplies have to be bought, it lacks any ordering.
Creating multiple shopping list is cumbersome, and walking through the aisles forth and back to find the items takes time.

Thanks to recent hype in Large Language Models (commonly called AI, although I dislike this term...) we can let the sorting be performed by a language model and still have the freedom of free text input for our shopping lists!

You have to define a list of stores and aisles. See the [Configuration Section](#configuration) for help.

## Usage

As this application currently is not a Home Assistant integration, but merely uses its REST API, you have to call it manually from any device which is able to access your Home Assistant server.

Setting up the [Configuraiton](#configuration) and calling `python shoppinglistsort.py suffices.`


## Configuration

If you rather read examples instead of explanation, take a look at `config_example.json`.

You have to configure the [API access](#api) and the [Stores](#stores) you are usually doing your shopping.
After editing save it as `config.json`.


### API and models

You have to provide this application with your Home Assistant instance and an API key.
Additionally, you have to provide it with a valid OpenAI api key and the model you want to use.
As for the models, `gpt-4.1-nano` regularly drops items and is unusuable, while `gpt-4.1-mini` seems to work consistently well.
Should you ever encounter issues, you can try `gpt-4.1`, which never had any issues, even with less descriptive system prompts.

Note, that you should pick a model which supports [Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) as this application relies on them to ensure an accurate response.


### Stores and Aisles

This application groups items by store and aisle.
The idea is, that you visit the store and typically walk around a typical path.
**ShoppingListSort** aims to sort all items in such way, that you are not required to make any detours, as every item should be placed in your path.

For this, you need to provide the aisles and their order to this application.
The LLM is only used to assign every a item a store and an aisle, while the sorting is done according to the provided configuration.

Here is a shortened version of the `stores` section in `config_example.json` for reference:

```json
"stores": [
    {
        "name": "EDEKA",
        "description": "A generic german supermarket.",
        "aisles": [
            {
                "name": "Fruits and Vegetables",
                "description": "Contains fruits and vegetables. Additionally has a fridge for vegan products"
            },
            {
                "name": "Eggs and Dairy",
                "description": "Contains eggs and dairy products. Additionally includes doughs"
            },
            {
                "name": "Freezer",
                "description": "Contains frozen food items."
            }
        ]
    },
    {
        "name": "IKEA",
        "description": "Furniture store, which sells household items and some electronics as well"
        "aisles": [
            {
                "name": "Kitchen accessories",
                "description": "Contains various kitchen utensils and appliances."
            },
            {
                "name": "Storage and organization",
                "description": "Contains various storage solutions and organizational systems."
            },
            {
                "name": "Electronics",
                "description": "Lighting, batteries and more."
            },
            {
                "name": "Furniture",
                "description": "Contains various pieces of furniture."
            }
        ]
    },
]
```

## TODO

- [ ] HACS
- [ ] Support for Ollama and more LLM providers
- [ ] Error handling