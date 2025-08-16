# ✏️📋🛒 Shopping List Sort

Sort your Shopping List in HomeAssistant using OpenAIs GPT models


## Motivation

While the Shopping List integration in Home Assistant is very convenient when sharing a shopping list and communicating efficiently which groceries or supplies have to be bought, it lacks any ordering.
Creating multiple shopping list for multiple stores is cumbersome, and walking through the aisles forth and back to find the items takes time.
There are other apps able to perform sorting and different stores, but I do not want to configure them myself.


This application attempts to solve this: Thanks to recent hype in Large Language Models (commonly called AI, although I dislike this term...) we can let the sorting be performed by a language model and still have the freedom of free text input for our shopping lists!

You have to define a list of stores and aisles. See the [Configuration Section](#configuration) for help.

## Usage

## Configuration

Take a look at `config_example.json`.
You have to configure the [API access](#api) and the [Stores](#stores) you are usually doing your shopping.
After editing save it as `config.json`.


### API

You have to provide this application with your Home Assistant instance and an API key.
Additionally, you have to provide it with a valid OpenAI api key and the model you want to use.
As for the models, `gpt-4.1-nano` regularly drops items and is unusuable, while `gpt-4.1-mini` seems to work consistently well.
Should you ever encounter issues, you can try `gpt-4.1`, which never had any issues, even with less descriptive system prompts.

Note, that you should pick a model which supports [Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) as this application heavily relies on them to ensure an accurate response.


### Stores and Aisles

TODO

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
    }
]
```




## TODO

In the long run, this is intended as an integration for Home Assistant using HACS. 
I just do not have the time yet to implement this application properly as an integration, but this is the goal.