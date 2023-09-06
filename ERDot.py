#!/usr/bin/env python
# coding: utf-8

# In[6]:


import subprocess
import json
import cv2
import re

class ERDGenerator:
    def __init__(self, text):
        self.text = text

    def generate_erd_json(self, file_path="example.erd.json"):
        entities = re.findall(r"Entity: (\w+)", self.text)

        entities_attributes = re.findall(r"Attributes of (\w+): \[([^\]]+)\]", self.text)

        entity_attributes_dict = {}
        for entity, attributes in entities_attributes:
            attribute_list = re.findall(r"'([^']+)'", attributes)
            entity_attributes_dict[entity] = attribute_list

        relations = []
        relation_matches = re.findall(r"Relation: (\w+) is (\w+) with (\w+)", self.text)
        if relation_matches:
            for match in relation_matches:
                entity1, relation_type, entity2 = match
                if relation_type == "OTM":
                    relation_str = f"{entity1}: 1--* {entity2}:"
                elif relation_type == "OTO":
                    relation_str = f"{entity1}: 1--1 {entity2}:"
                else:
                    continue
                relations.append(relation_str)

        data = {
            "tables": {},
            "relations": relations,
            "rankAdjustments": "",
            "label": ""
        }
        for entity, attributes in entity_attributes_dict.items():
            data["tables"][entity] = {attr: "string" for attr in attributes}

        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        print("JSON file created successfully.")

    def generate_erd_image(self, json_file="example.erd.json", image_file="erd.png"):
        command = f"erdot {json_file}"
        image_file = "C:\\Users\\USER\\Desktop\\AIDD\\site\\" + image_file
        command2 = f"dot example.dot -Tpng -o {image_file}"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            result2 = subprocess.run(command2, shell=True, capture_output=True, text=True)
            if result2.returncode == 0:
                print("Image created")
            else:
                print("Command 2 execution failed")
                error = result2.stderr
                print("Error:", error)
        else:
            print("Command 1 execution failed")
            error = result.stderr
            print("Error:", error)
    def generate_erd_pdf(self, json_file="example.erd.json", pdf_file="erd.pdf"):
        command = f"erdot {json_file}"
        pdf_file = "C:\\Users\\USER\\Desktop\\AIDD\\site\\" + pdf_file 
        command2 = f"dot example.dot -Tpdf -o {pdf_file}"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            result2 = subprocess.run(command2, shell=True, capture_output=True, text=True)
            if result2.returncode == 0:
                print("pdf created")

            else:
                print("Command 2 execution failed")
                error = result2.stderr
                print("Error:", error)
        else:
            print("Command 1 execution failed")
            error = result.stderr
            print("Error:", error)


# In[ ]:




