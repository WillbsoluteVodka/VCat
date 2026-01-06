import json

def get_current_pet():
    """
    Load the JSON file and return the current pet kind and color.
    """
    try:
        with open("src/current_pet.json", "r") as file:
            data = json.load(file)

        pet_kind = data.get("Current_Pet_Kind", None)
        pet_color = data.get("Current_Pet_Color", None)

        if pet_kind and pet_color:
            return pet_kind, pet_color
        else:
            print("Error: Current_Pet_Kind or Current_Pet_Color is missing in the JSON file.")
            return None, None
    except FileNotFoundError:
        print("Error: current_pet.json file not found.")
        return None, None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None, None

def load_pet_data(pet_kind, pet_color, action):
    """
    Load the JSON file and retrieve the path for the given pet kind, color, and action.
    """
    try:
        with open("src/pets_info.json", 'r') as file:
            data = json.load(file)

        # Navigate through the JSON structure
        if pet_kind in data:
            kind_data = data[pet_kind]
            if pet_color in kind_data:
                color_data = kind_data[pet_color]
                if action in color_data:
                    # print("src/"+color_data[action])
                    return "src/"+color_data[action]
                else:
                    print(f"Action '{action}' not found for pet '{pet_kind}' of color '{pet_color}'.")
                    return None
            else:
                print(f"Color '{pet_color}' not found under pet kind '{pet_kind}'.")
                return None
        else:
            print(f"Pet kind '{pet_kind}' not found in the configuration.")
            return None
    except FileNotFoundError:
        print(f"File not found: pets_info.json")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def get_all_pet_kinds_and_colors():
    """
    Retrieve all pairs of pet kinds, their corresponding colors, and lock_flag values.
    Returns a dictionary of the structure:
    {
        pet_kind: {
            color: lock_flag_value,
            ...
        },
        ...
    }
    """
    try:
        with open("src/pets_info.json", "r") as file:
            data = json.load(file)

        all_pet_kinds_and_colors = {}
        for pet_kind, colors in data.items():
            all_pet_kinds_and_colors[pet_kind] = {
                color: color_data.get("lock_flag", None)  # Get lock_flag value or None if missing
                for color, color_data in colors.items()
            }

        return all_pet_kinds_and_colors
    except FileNotFoundError:
        print("Error: pets_info.json file not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}



