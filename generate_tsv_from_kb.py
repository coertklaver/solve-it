"""
SOLVE-IT Knowledge Base TSV Exporter

This script generates a TSV text of the SOLVE-IT knoweldge base to stdout

The script can be used directly from the command line

"""


import re
import argparse
import solveitcore


def main():
    """Command-line entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate TSV output for parts of the SOLVE-IT knowledge base")
    parser.add_argument('--objectives', '-o', action='store_true',
                        help="Print the objectives from SOLVE-IT in TSV format")
    parser.add_argument('--techniques', '-t', action='store_true',
                        help="Print the techniques from SOLVE-IT in TSV format")
    parser.add_argument('--weaknesses', '-w', action='store_true',
                        help="Print the weaknesses from SOLVE-IT in TSV format")
    parser.add_argument('--mitigations', '-m', action='store_true',
                        help="Print the mitigations from SOLVE-IT in TSV format")
    args = parser.parse_args()

    kb = solveitcore.SOLVEIT('data', 'solve-it.json')

    if args.objectives is True:
        print('Objective\tDescription')
        objectives_name_list = kb.list_tactics()
        for each_objective in objectives_name_list:
            print("{}\t{}".format(each_objective, 'todo'))
    elif args.techniques is True:
        print('ID\tName\tDescription\tSynonyms')
        techniques = kb.list_techniques()
        for each_technique_id in techniques:
            if each_technique_id != "T1000":
                each_technique = kb.get_technique(each_technique_id)
                print('{}\t{}\t{}\t{}'.format(each_technique_id,
                                                  each_technique.get('name'),
                                                  each_technique.get('description'),
                                                  each_technique.get('synonyms'),)
                      )
    elif args.weaknesses is True:
        print('ID\tName')
        for each_weakness in kb.list_weaknesses():
            w = kb.get_weakness(each_weakness)
            print("{}\t{}".format(each_weakness,
                                      w.get('name')
                                      ))
    elif args.mitigations is True:
        print('ID\tName')
        for each_mitigation in kb.list_mitigations():
            m = kb.get_mitigation(each_mitigation)
            print("{}\t{}".format(each_mitigation, m.get('name')))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

