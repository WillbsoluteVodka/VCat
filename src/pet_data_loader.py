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
                    print("src/"+color_data[action])
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

def update_current_pet_json(self, pet_kind, pet_color):
    """Update the JSON file with the current pet kind and color."""
    current_pet_data = {
        "Current_Pet_Kind": pet_kind,
        "Current_Pet_Color": pet_color
    }
    try:
        with open("current_pet.json", "w") as file:
            json.dump(current_pet_data, file, indent=2)
        # print("Current pet JSON file updated successfully.")
    except Exception as e:
        print(f"Error updating current_pet.json: {e}")



def update_lock_flag(pet_kind, color,flag):
    """
    Update the lock_flag to true for a specific pet kind and color in 'current_pet.json'.

    :param pet_kind: The pet kind to update (e.g., "DEV_CAT")
    :param color: The color of the pet to update (e.g., "Black")
    """
    file_path = "pets_info.json"  # Hard-coded JSON file path

    try:
        # Load JSON data from the file
        with open(file_path, "r") as file:
            data = json.load(file)
        print(data)
        # Update lock_flag for the specified pet kind and color
        if pet_kind in data and color in data[pet_kind]:
            if "lock_flag" in data[pet_kind][color]:
                data[pet_kind][color]["lock_flag"] = flag
                print(f"Updated lock_flag to true for {pet_kind} {color}.")
            else:
                print(f"lock_flag not found for {pet_kind} {color}.")
        else:
            print(f"Pet kind '{pet_kind}' or color '{color}' not found in the file.")

        # Save the updated JSON data back to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
            print(f"Updated data saved to {file_path}.")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
def is_lock_flag_equal(pet_kind, color, flag):
    """
    Check if the lock_flag for a specific pet kind and color matches the given flag.

    :param pet_kind: The pet kind to check (e.g., "DEV_CAT")
    :param color: The color of the pet to check (e.g., "Black")
    :param flag: The flag value to compare against (True/False)
    :return: True if lock_flag matches the given flag, False otherwise
    """
    file_path = "pets_info.json"  # Hard-coded JSON file path

    try:
        # Load JSON data from the file
        with open(file_path, "r") as file:
            data = json.load(file)

        # Check if the lock_flag matches the given flag
        if pet_kind in data and color in data[pet_kind]:
            if "lock_flag" in data[pet_kind][color]:
                return data[pet_kind][color]["lock_flag"] == flag
            else:
                print(f"lock_flag not found for {pet_kind} {color}.")
                return False
        else:
            print(f"Pet kind '{pet_kind}' or color '{color}' not found in the file.")
            return False

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False



