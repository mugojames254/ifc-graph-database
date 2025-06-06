# Filtered IFC-BIM Graph Database

## Description
- A simple python package that generates graph relationships from ifc bim model files 
- The relationship graphs are filtered to represent only the physical entities such as ifcwall, ifcdoors etc. of a bim model file
- This increases the parsing speed from ifc to graph database 
- The package can be optimized for an llm Q/A system on BIM ifc model files

![Neo4j Graph Data](./images/neo4j_level2.png)

## Usage
- Clone the repository to your local system.
- Setup a virtual environment.
- Download and create a neo4j database
- Save your neo4j database access credentials in a .env file and load them in the main.py 

```bash
# for linux users 
python -m venv 'virtual_environment_name'

# activate the environment 
source virtual_environment_name/bin/activate

# install project requirements

pip install -r requirements.txt

```
- Run the main file.

```bash
python main.py 
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
