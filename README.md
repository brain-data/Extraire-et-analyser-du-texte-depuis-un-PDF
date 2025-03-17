# ETL_A9Number_v4

## Overview
This Python module extracts text from a PDF while removing unwanted content such as figure captions and page numbers. 

The cleaned text is automatically stored in the `SAMPLE_TEXT_FOR_BENCH` variable when the module is imported or run. 

Additionally, the module includes functions to count how many times a given word appears in the text.


## Installation
Run the following commands to set up a virtual environment, install dependencies, and run the tests:
```bash
$ python -m venv venv && source venv/bin/activate && pip install pytest && pip install -r requirements.txt
$ python -m pytest _etl_a9number_v4.py

Oussama BOUACEM 
