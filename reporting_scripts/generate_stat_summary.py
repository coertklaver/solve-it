"""
SOLVE-IT Knowledge Base Stats Exporter

This script generates a text summary in JSON form of the number of entities in the knowledge base

The script can be used directly from the command line

"""

import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from solve_it_library import KnowledgeBase
import pprint

# Configure logging to show errors to console
logging.basicConfig(level=logging.ERROR, format='ERROR: %(message)s')

def main():
    """Command-line entry point for the script."""
    # Calculate the path to the solve-it directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solve_it_root = os.path.dirname(script_dir)  # Go up from reporting_scripts to solve-it root
    
    kb = KnowledgeBase(solve_it_root, 'solve-it.json')

    output_json = {}
    output_json['num_objectives'] = len(kb.list_tactics())
    output_json['num_techniques'] = len(kb.list_techniques())
    output_json['num_weaknesses'] = len(kb.list_weaknesses())
    output_json['num_mitigations'] = len(kb.list_mitigations())

    pprint.pprint(output_json)

if __name__ == '__main__':
    main()
