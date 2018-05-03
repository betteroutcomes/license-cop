#!/usr/bin/python

#This file parses the output of the license cop script to fill in missing Licenses
#or other info that I have added manually to license_cleanup.jackson
import sys
import pandas as pd
import json
print("Loading Excel file " + sys.argv[1])
df = pd.read_excel(sys.argv[1])

print("Loading JSON file " + 'license_cleanup.json')
correction_json = json.load(open('license-cleanup.json'))

license_replacements = correction_json['license_replacements']
individual_updates = correction_json['individual_updates']
license_urls = correction_json['license_urls']
to_be_removed = correction_json['remove_packages']

df2 = df.copy()
#Remove packages we don't want in report
df2 = df2[df2['Package'].map(lambda x: x not in to_be_removed)]

#Standardize license wordings: i.e. ("3-CLAUSE-bSd licents" -> "BSD-3-Clause"
df2['Licenses'] = df2['Licenses'].apply(lambda license_name: license_replacements.get(license_name, license_name))

#Row -> String,
#Either returns the current contents of the License column for this row,
#or returns a new value based on the "individual_updates" dictionary.
def update_individuals(row):
    package_info = individual_updates.get(row['Package'])
    if package_info:
        versions_info = package_info.get('versions')
        if versions_info and versions_info.get(row['Package Version']):
            version_info = versions_info.get(row['Package Version'])
            return version_info.get('license', row['Licenses'])
        else:
            return package_info.get('license', row['Licenses'])
    else:
        return row['Licenses']

# Updates licenses for individual packages
df2['Licenses'] = df2.apply(lambda row: update_individuals(row), axis = 1)

#Gets links to licenses from dictionary
df2['URL'] = df2.apply(lambda row: license_urls.get(row['Licenses'], "Missing"), axis=1)

import openpyxl
writer = pd.ExcelWriter(sys.argv[2])
df2.to_excel(writer)
writer.save()