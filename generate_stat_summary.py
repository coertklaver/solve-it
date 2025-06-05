"""
SOLVE-IT Knowledge Base Stats Exporter

This script generates a text summary in JSON form of the number of entities in the knowledge base

The script can be used directly from the command line

"""

import solveitcore
import pprint

def main():
    """Command-line entry point for the script."""
    kb = solveitcore.SOLVEIT('data', 'solve-it.json')

    output_json = {}
    output_json['num_objectives'] = len(kb.list_tactics())
    output_json['num_techniques'] = len(kb.list_techniques())
    output_json['num_weaknesses'] = len(kb.list_weaknesses())
    output_json['num_mitigations'] = len(kb.list_mitigations())

    pprint.pprint(output_json)

if __name__ == '__main__':
    main()