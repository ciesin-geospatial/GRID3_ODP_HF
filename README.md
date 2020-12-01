## GRID3 Health Facility Cleaning
The GRID3 open source project for cleaning names and defining types for health facilities. 

## GRID3's Mission
GRID3’s mission is to build spatial data solutions that make development goals achievable. GRID3 combines the expertise of partners in government, the United Nations, academia and the private sector to design adaptable and relevant spatial data solutions based on the capacity and development needs of each country. Find out more [here.](https://greid3.org)

## Project Goals
The goal of the project is to clean, standardize, and validate spatial health facility data. Specifically the name of the facility, the type of the facility, and the location of the facility across different countries. Language, spelling, and types of facilities vary from country to country and should be take into consideration. Choosing the correct location when multiple geographic points for the same facility may exist but have varying degrees of accuracy.

## Problems we are trying to solve.
1. Cleaning names and types - It is often the case that a single field will contain both the name and the type of a facility. The goal is to create two new fields, one with the name of the facility (clean_name) and one with the type of the facility (clean_type). The clean_name facility will contain just the name of the facility with the correct punctuation, and formatting. Clean_types will contain the type of the facility with puncutaion
  - Punctuation: Special characters, extra spaces, dashes, and roman numerals are removed or converted to single spaces, numbers, or letters.
  - Formatting: Names should be in title case with abbreviations in upper case.
  - Spelling: We cannot confirm the spelling of a facility but all facility types should be consistent with no spelling errors. It is important to note that each country may have different spellings for the same facility type.

2. Defining the type of facility - Each country has its own set of standards for defining the type of facility. Along with that, each data provider may also have a generic set of types that they use. The goal for the clean_types field is to represent a consistent type based on the standards used by each country. 

3. Validating spatial accuracy - This is a spatial problem where the other two are based on cleaning the attributes for each health facility. 


