import os
import json

def extract_animations_from_spine_json(spine_json_path):
    """
    Reads the given spine json file and extracts the animation names from it.
    """
    try:
        with open(spine_json_path, 'r') as spine_json_file:
            spine_data = json.load(spine_json_file)
            animations = list(spine_data.get("animations", {}).keys())
            return animations
    except FileNotFoundError:
        print(f"Error: {spine_json_path} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {spine_json_path}.")
        return []

def find_spinescene_files():
    # Get the current directory from where the script is run
    current_directory = os.getcwd()

    # Initialize a list to store the relative file paths
    spinescene_files = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(current_directory):
        for file in files:
            if file.endswith(".spinescene"):
                # Create the relative path
                relative_path = os.path.relpath(os.path.join(root, file), current_directory)
                relative_path_with_slash = "/" + relative_path.replace("\\", "/")

                # Check if the file path includes the ignored paths
                if (
                    "assets/template/template.spinescene" not in relative_path_with_slash and
                    "editor/resources/templates/template.spinescene" not in relative_path_with_slash
                ):
                    spinescene_files.append(relative_path_with_slash)

    # Print the search results
    if spinescene_files:
        print("Search for spine scenes:")
        for file in spinescene_files:
            print(file)

    # Path to the output file for generated embedded components
    go_output_file_path = os.path.join(current_directory, "spine_tester", "generated", "go.go")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(go_output_file_path), exist_ok=True)

    # Dictionary to store component URLs and their animations
    component_animations = {}
    # Dictionary to track file name counts
    file_name_count = {}

    # Write the generated embedded_component text to the go.go file
    with open(go_output_file_path, "w") as go_file:
        print("\nGenerate Components:")
        if spinescene_files:
            for spinescene_file in spinescene_files:
                file_name = os.path.basename(spinescene_file).replace(".spinescene", "")

                # If the file name already exists, append an index to the file name
                if file_name in file_name_count:
                    file_name_count[file_name] += 1
                    file_name = f"{file_name}_{file_name_count[file_name]}"
                else:
                    file_name_count[file_name] = 0

                component_url = f"/go#{file_name}"

                # Read the spinescene file to find the spine_json path
                spinescene_file_path = os.path.join(current_directory, spinescene_file.lstrip("/"))
                try:
                    with open(spinescene_file_path, "r") as spinescene:
                        for line in spinescene:
                            if "spine_json:" in line:
                                spine_json_path = line.split('"')[1]  # Extract the path inside the quotes
                                spine_json_full_path = os.path.join(current_directory, spine_json_path.lstrip("/"))

                                # Extract animations from the spine_json file
                                animations = extract_animations_from_spine_json(spine_json_full_path)

                                # Add to the Lua table dictionary
                                component_animations[component_url] = animations

                                # Use the first animation as the default
                                default_animation = animations[0] if animations else ""

                                # Write the embedded component
                                go_file.write('embedded_components {\n')
                                go_file.write(f'  id: "{file_name}"\n')
                                go_file.write('  type: "spinemodel"\n')
                                go_file.write(f'  data: "spine_scene: \\"{spinescene_file}\\"\\n"\n')
                                go_file.write(f'  "default_animation: \\"{default_animation}\\"\\n"\n')
                                go_file.write('  "skin: \\"\\"\\n"\n')
                                go_file.write('  "material: \\"/defold-spine/assets/spine.material\\"\\n"\n')
                                go_file.write('  ""\n')
                                go_file.write('}\n\n')  # Double newline for readability

                                # Print the component and its animations
                                animations_str = ', '.join(animations)
                                print(f"{component_url} -> {animations_str}")
                except FileNotFoundError:
                    print(f"Error: {spinescene_file_path} not found.")
        else:
            print("No .spinescene files found.")

    print(f"\nGenerated embedded components have been written to {go_output_file_path}")

    # Path to the output file for Lua table
    lua_output_file_path = os.path.join(current_directory, "spine_tester", "generated", "data.lua")

    # Write the Lua table to data.lua
    with open(lua_output_file_path, "w") as lua_file:
        lua_file.write("local M = {\n")
        for component_url, animations in component_animations.items():
            animations_str = ', '.join(f'"{anim}"' for anim in animations)
            lua_file.write(f'  ["{component_url}"] = {{{animations_str}}},\n')
        lua_file.write("}\n")
        lua_file.write("return M\n")

    print(f"Lua table with animations has been written to {lua_output_file_path}")

# Run the function
if __name__ == "__main__":
    find_spinescene_files()
