import os
import json
import xlsxwriter

path_to_data = 'data'
path_to_weaknesses = os.path.join(path_to_data, 'weaknesses')
path_to_mitigations = os.path.join(path_to_data, 'mitigations')
path_to_techniques = os.path.join(path_to_data, 'techniques')

weaknesses = {}
mitigations = {}


def load_tactics(path_to_tactics_list):
    f = open(path_to_tactics_list)
    tactics_list = json.loads(f.read())
    return tactics_list

def load_techniques(path_to_techniques):
    '''Loads techniques from on disk json into dictionary'''
    techniques = {}
    for each in os.listdir(path_to_techniques):
        if each[-4:] == 'json':
            technique_path = os.path.join(path_to_techniques, each)
            f = open(technique_path)
            try:
                tech_dict = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                print('error loading JSON from {}'.format(technique_path))
                quit()
            techniques[tech_dict.get('id')] = tech_dict
    return techniques

def load_weaknesses(path_to_weaknesses):
    '''Loads weaknesses from on disk json into dictionary'''
    weaknesses = {}
    for each in os.listdir(path_to_weaknesses):
        if each[-4:] == 'json':
            f = open(os.path.join(path_to_weaknesses, each))
            weakness_dict = json.loads(f.read())
            weaknesses[weakness_dict.get('id')] = weakness_dict
            weaknesses[weakness_dict.get('id')]['in_techniques'] = []
    return weaknesses


def load_mitigations(path_to_mitigations):
    '''Loads mitigations from on disk json into dictionary'''
    mitigations = {}
    for each in os.listdir(path_to_mitigations):
        if each[-4:] == 'json':
            f = open(os.path.join(path_to_mitigations, each))
            mit_dict = json.loads(f.read())
            mitigations[mit_dict.get('id')] = mit_dict
            mitigations[mit_dict.get('id')]['in_techniques'] = []
            mitigations[mit_dict.get('id')]['in_weaknesses'] = []
    return mitigations



def format_headings_in_workbook(workbook):
    header_format = workbook.add_format()
    header_format.set_bold()
    header_format.set_align('vcenter')
    header_format.set_align('center')
    header_format.set_border(style=1)
    header_format.set_text_wrap()
    header_format.set_bg_color('#b5b8b7')

    worksheet = workbook.get_worksheet_by_name('Main')

    # format header row and columns
    worksheet.set_row(0, 50)
    # worksheet.set_row(1, 40)
    # worksheet.set_row(2, 40)
    # worksheet.set_row(3, 40)
    worksheet.set_column(0, len(tactics), 20)

    # write headers
    for i in range(0,len(tactics)):
        worksheet.write_string(0, i, tactics[i].get('name'), header_format)

    return workbook

def format_techinque_sheet(worksheet):
    worksheet.set_row(0, 40)
    return worksheet


def update_mitigation_usuages(mitigations, techniques):
    '''Adds a list of all techniques and weaknesses that reference the mitigation'''
    for each_technique in techniques:
        for each_weakness in techniques[each_technique].get('weaknesses'):
            for each_mitigation in weaknesses[each_weakness].get('mitigations'):
                if each_weakness not in mitigations[each_mitigation]['in_weaknesses']:
                    mitigations[each_mitigation]['in_weaknesses'].append(each_weakness)
                if each_technique not in mitigations[each_mitigation]['in_techniques']:
                    mitigations[each_mitigation]['in_techniques'].append(each_technique)
    return mitigations


def update_weakness_usages(weaknesses, techniques):
    '''Adds a list of all techqinues that reference the weakness'''
    for each_technique in techniques:
        for each_weakness in techniques[each_technique].get('weaknesses'):
            if each_technique not in weaknesses[each_weakness]['in_techniques']:
                    weaknesses[each_weakness]['in_techniques'].append(each_technique)
    return weaknesses

if __name__ == '__main__':

    tactics = load_tactics(os.path.join(path_to_data, 'solve-it.json'))
    tactics_name_list = [x.get('name') for x in tactics]

    techniques = load_techniques(path_to_techniques)
    weaknesses = load_weaknesses(path_to_weaknesses)
    mitigations = load_mitigations(path_to_mitigations)

    weaknesses = update_weakness_usages(weaknesses, techniques)
    mitigations = update_mitigation_usuages(mitigations, techniques)


    workbook = xlsxwriter.Workbook('solve-it.xlsx')
    workbook.add_worksheet(name='Main')
    workbook.set_size(2000,1024)
    format_headings_in_workbook(workbook)

    techniques_sheet = workbook.add_worksheet(name='Techniques')
    weaknesses_sheet = workbook.add_worksheet(name='Weaknesses')
    mitigations_sheet = workbook.add_worksheet(name='Mitigations')

    # Create all the worksheets
    print('Creating worksheets...')
    for each_technique_id in sorted(techniques):
        technique_name = techniques[each_technique_id].get('name')
        workbook.add_worksheet(each_technique_id)

    for i, each_technique in enumerate(sorted(techniques)):
        techniques_sheet.write_string(i, 0, each_technique)
        techniques_sheet.write_string(i, 1, techniques[each_technique].get('name'))
        techniques_sheet.write_number(i, 2, len(techniques[each_technique].get('weaknesses', [])))
        total_mits = 0
        for each_weakness in techniques[each_technique].get('weaknesses', []):
            total_mits += len(weaknesses[each_weakness].get('mitigations', []))
        techniques_sheet.write_number(i, 3, total_mits)
        techniques_sheet.write_string(0, 2, "Weaknesses")
        techniques_sheet.write_string(0, 3, "Mitigations")

    for i, each_weakness in enumerate(sorted(weaknesses)):
        weaknesses_sheet.write_string(i+1, 0, each_weakness)
        weaknesses_sheet.write_string(i+1, 1, weaknesses[each_weakness].get('name'))
        weaknesses_sheet.write_number(i+1, 2, len(weaknesses[each_weakness].get('mitigations', [])))
        if len(weaknesses[each_weakness].get('mitigations', [])) == 0:
            weaknesses_sheet.write_string(i+1, 3, "x")
        weaknesses_sheet.write_string(i + 1, 4, str(weaknesses[each_weakness].get('in_techniques')))

    # write some headers for weakness sheet
    weaknesses_sheet.write_string(0, 0, "ID")
    weaknesses_sheet.write_string(0, 1, "Description")
    weaknesses_sheet.write_string(0, 2, "Mitigations")
    weaknesses_sheet.write_string(0, 3, "Has none")
    weaknesses_sheet.write_string(0, 4, "In technique")


    for i, each_mitigation in enumerate(sorted(mitigations)):
        mitigations_sheet.write_string(i+1, 0, each_mitigation)
        mitigations_sheet.write_string(i+1, 1, mitigations[each_mitigation].get('name'))
        mitigations_sheet.write_string(i+1, 2, str(mitigations[each_mitigation].get('in_techniques')))
        mitigations_sheet.write_string(i+1, 3, str(mitigations[each_mitigation].get('in_weaknesses')))
        mitigations_sheet.write_number(i + 1, 4, len(mitigations[each_mitigation].get('in_weaknesses')))

    # write some headers for weakness sheet
    mitigations_sheet.write_string(0, 0, "ID")
    mitigations_sheet.write_string(0, 1, "Description")
    mitigations_sheet.write_string(0, 2, "In techniques")
    mitigations_sheet.write_string(0, 3, "In weakness")
    mitigations_sheet.write_string(0, 4, "Weakness occurances")

    print('worksheets added.')

    # records max row written so far for populating techinques in main
    tactics_row_indexes = {}
    for each in tactics:
        tactics_row_indexes[each.get('name')] = 1

    # set format for techniques in main
    techinique_format = workbook.add_format()
    techinique_format.set_bold(False)
    techinique_format.set_align('vcenter')
    techinique_format.set_align('center')
    techinique_format.set_border(style=1)
    techinique_format.set_text_wrap()

    # Set format to see which ones have some content populated
    techinique_format2 = workbook.add_format()
    techinique_format2.set_bold(False)
    techinique_format2.set_align('vcenter')
    techinique_format2.set_align('center')
    techinique_format2.set_text_wrap()
    techinique_format2.set_border(style=1)
    techinique_format2.set_bg_color("#E9E9E9")

    # set format for centralised x marks
    weakness_type_format = workbook.add_format()
    weakness_type_format.set_align('center')
    weakness_type_format.set_align('vcenter')

    # -------------------------------------------------------------------------------------------

    print('Updating Main with links to techniques...')
    main_worksheet = workbook.get_worksheet_by_name('Main')
    main_worksheet.set_default_row(60)

    techniques_added = []

    for each_tactic in tactics:
        tactic = each_tactic.get('name')
        column = tactics_name_list.index(tactic)

        for each_technique_id in sorted(each_tactic.get('techniques')):
            technique_name = techniques[each_technique_id].get('name')
            each_technique = techniques.get(each_technique_id)

            try:
                row = tactics_row_indexes[tactic]
                if len(each_technique['weaknesses']) == 0:
                    the_format = techinique_format
                else:
                    the_format = techinique_format2

                main_worksheet.write_url(row, column, 'internal:{}!A1'.format(each_technique_id),
                                         string=technique_name + '\n' + each_technique_id,
                                         cell_format=the_format)
                techniques_added.append(each_technique_id)
                tactics_row_indexes[tactic] += 1
            except KeyError:
                print('Technique {} ({}) had a tactic not found in the tactics ({})'.format(each_technique_id,
                                                                                            technique_name,
                                                                                            tactic))

    # ---------------------------------------------------------------------------------------------------------------
    # check if any are missed from index sheet

    for each in techniques:
        if each not in techniques_added:
            print("WARNING: Technique {} exists, but is not indexed in sheet".format(each))



    # ----------------------------------------------------------------------------------------------------------------
    print('Populating the individual techniques sheets...')
    for each_technique_id in techniques:
        technique_name = techniques[each_technique_id].get('name')

        # find tactics that it belongs to
        parent_tactics = []
        for each_tactic in tactics:
            if each_technique_id in each_tactic.get('techniques'):
                parent_tactics.append(each_tactic.get('name'))

        worksheet = workbook.get_worksheet_by_name(each_technique_id)

        techinique_format = workbook.add_format()
        techinique_format.set_text_wrap()

        bold_format = workbook.add_format()
        bold_format.set_bold()
        bold_format.set_text_wrap()

        worksheet.write_url(0, 2, 'internal:Main!A1', string='back to main')

        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 50)
        worksheet.set_column(8, 8, 60)

        worksheet.write_string(0, 0, 'Technique name: ', bold_format)
        worksheet.write_string(0, 1, technique_name)
        worksheet.write_string(1, 0, 'Technique ID: ', bold_format)
        worksheet.write_string(1, 1, each_technique_id)
        worksheet.write_string(2, 0, 'Category: ', bold_format)
        worksheet.write_string(2, 1, str(parent_tactics))

        worksheet.write_string(3, 0, 'Description: ', bold_format)
        worksheet.write_string(3, 1,  techniques[each_technique_id].get('description'), cell_format=techinique_format)
        worksheet.write_string(4, 0, 'Synonyms: ', bold_format)
        worksheet.write_string(4, 1,  str(techniques[each_technique_id].get('synonyms')))
        worksheet.write_string(5, 0, 'Details: ', bold_format)
        worksheet.write_string(5, 1,  techniques[each_technique_id].get('details'), cell_format=techinique_format)
        worksheet.write_string(6, 0, 'Subtechniques: ', bold_format)
        worksheet.write_string(6, 1,  str(techniques[each_technique_id].get('subtechniques')))

        worksheet.write_string(7, 0, 'CASE output entities: ', bold_format)
        worksheet.write_string(7, 1,  str(techniques[each_technique_id].get('CASE_output_classes')))

        worksheet.write_string(8, 0, 'Examples: ', bold_format)
        worksheet.write_string(8, 1,  str(techniques[each_technique_id].get('examples')),
                               cell_format=techinique_format) #TODO format properly

        worksheet.write_string(10, 0, 'Potential weaknesses:', bold_format)

        worksheet.write_string(11, 0, 'Weakness ID:', bold_format)
        worksheet.write_string(11, 1, 'Detail:', bold_format)
        worksheet.write_string(11, 2, 'INCOMP', bold_format)
        worksheet.write_string(11, 3, 'INAC-EX', bold_format)
        worksheet.write_string(11, 4, 'INAC-AS', bold_format)
        worksheet.write_string(11, 5, 'INAC-ALT', bold_format)
        worksheet.write_string(11, 6, 'INAC-COR', bold_format)
        worksheet.write_string(11, 7, 'MISINT', bold_format)
        worksheet.write_string(11, 8, 'Mitigations', bold_format)

        i = 0
        mit_list_for_this_technique = []
        err_list_start_row = 12
        for each_weakness in techniques[each_technique_id].get('weaknesses'):
            weakness_info = weaknesses.get(each_weakness)

            try:
                worksheet.write_string(err_list_start_row + i, 0, each_weakness)   # write ID
                worksheet.write_string(err_list_start_row + i, 1, weakness_info.get('name'), cell_format=techinique_format)
                worksheet.write_string(err_list_start_row + i, 2, weakness_info.get('INCOMP', ''), cell_format=weakness_type_format)
                worksheet.write_string(err_list_start_row + i, 3, weakness_info.get('INAC-EX', ''), cell_format=weakness_type_format)
                worksheet.write_string(err_list_start_row + i, 4, weakness_info.get('INAC-AS', ''), cell_format=weakness_type_format)
                worksheet.write_string(err_list_start_row + i, 5, weakness_info.get('INAC-ALT', ''), cell_format=weakness_type_format)
                worksheet.write_string(err_list_start_row + i, 6, weakness_info.get('INAC-COR', ''), cell_format=weakness_type_format)
                worksheet.write_string(err_list_start_row + i, 7, weakness_info.get('MISINT', ''), cell_format=weakness_type_format)
            except AttributeError:
                print('attribute error with {} in {}'.format(each_weakness, each_technique_id))
                quit()

            # Write the mitigations at the end of each weakness
            mit_string = ''
            for each_mitigation in weakness_info.get('mitigations'):
                mit_string = mit_string + each_mitigation + ','
                mit_list_for_this_technique.append(each_mitigation)

            worksheet.write_string(err_list_start_row + i, 8, mit_string, cell_format=techinique_format)
            i = i+1

        mitigation_start_row = err_list_start_row + i + 1
        worksheet.write_string(mitigation_start_row, 0, 'Mitigations:', bold_format)

        # ----------------------------------------------------------------------------------------------------------------
        # build list of *all* mitigations for this technique
        mits_written = []
        for each_mitigation in mit_list_for_this_technique:
            if each_mitigation not in mits_written:
                mits_written.append(each_mitigation)

        # do the write of the full mitigations list
        i = 1
        for each_mit in sorted(mits_written):
            worksheet.write_string(mitigation_start_row + i, 0, each_mit)
            try:
                if mitigations.get(each_mit).get('technique') is not None: # there is a link to a technqiue
                    cell_str = mitigations.get(each_mit).get('name')  + ' ({})'.format( mitigations.get(each_mit).get('technique'))
                    worksheet.write_url(mitigation_start_row + i, 1, 'internal:{}!A1'.format(mitigations.get(each_mit).get('technique')),
                                             string=cell_str,
                                             cell_format=techinique_format)
                else:
                    worksheet.write_string(mitigation_start_row + i, 1, mitigations.get(each_mit).get('name'), cell_format=techinique_format)
            except AttributeError:
                print("Mitigation not found '{}'".format(each_mit))
                quit()
            mits_written.append(each_mit)
            i += 1

        # ----------------------------------------------------------------------------------------------------------------
        #   Write references
        # ----------------------------------------------------------------------------------------------------------------

        # build big refs dict:
        references = {}
        # References from Technique
        for each_reference in techniques[each_technique_id].get('references'):
            if each_reference in references:
                if each_technique_id not in references[each_reference]:
                    references[each_reference].append(each_technique_id)
            else:
                references[each_reference] = [each_technique_id,]

        # References from weaknesses within technique
        technique_weaknesses = techniques[each_technique_id].get('weaknesses')
        for each_weakness_id in technique_weaknesses:
            if weaknesses.get(each_weakness_id).get('references') is not None:
                for each_reference in weaknesses.get(each_weakness_id).get('references'):
                    if each_reference in references:
                        if each_weakness_id not in references[each_reference]:
                            references[each_reference].append(each_weakness_id)
                    else:
                        references[each_reference] = [each_weakness_id, ]

        # References from mitigations within technique
        tech_mits = mits_written
        for each_mit_id in tech_mits:
            if mitigations.get(each_mit_id).get('references') is not None:
                for each_reference in mitigations.get(each_mit_id).get('references'):
                    if each_reference in references:
                        if each_mit_id not in references[each_reference]:
                            references[each_reference].append(each_mit_id)
                    else:
                        references[each_reference] = [each_mit_id,]


        # write the header
        refs_start = mitigation_start_row + i + 2
        worksheet.write_string(refs_start, 0, 'References:', bold_format)
        i = 0

        # write the actual references, with indication as to whether they came from T, E or M
        for each_reference in references:
            # worksheet.setrow(refs_start+i+1, 100)
            worksheet.merge_range("B" + str(refs_start+i+1) + ":H" + str(refs_start+i+1), "")
            worksheet.write_string(refs_start + i, 1, each_reference, cell_format=techinique_format)
            worksheet.write_string(refs_start + i, 8, str(references.get(each_reference)), cell_format=techinique_format)
            i += 1

    # for each_mitigation_id in mitigations:
        #     if mitigations[each_mitigation_id].get('references') is not None:
        #         for each_mit_ref in mitigations[each_mitigation_id].get('references'):
        #             worksheet.write_string(refs_start + i, 1, each_mit_ref, cell_format=techinique_format)
        #             worksheet.write_string(refs_start + i, 2, each_mitigation_id, cell_format=techinique_format)
        #             i += 1

    # ----------------------------------------------------------------------------------------------------------------

    workbook.close()





