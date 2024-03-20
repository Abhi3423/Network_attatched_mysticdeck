import json


with open('database/everydata.json', 'r') as b:
    data = json.load(b)

# Iterate through each entry in the data dictionary
for key in data["Geography"]["states and cities"]["Cards"]:
# Update the value of the "image" key to "maharashtra"
   data["Geography"]["states and cities"]["Cards"][key]["image"] = "maharashtra"

# Print the updated data
print(data)

with open('database/everydata.json','w') as y:
        json.dump(data, y)