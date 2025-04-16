import graphviz
import solveitcore

def render1(kb, g, technique_list):

    print(technique_list)

    for each in technique_list:
        g.node(each, label=each + '\n' + kb.get_technique(each).get('name'))

    for each in deps:
        g.edge(each[0], each[1], shape='box')

    # Load weaknesses
    f = open('dependency_examples/abstract_w.csv')
    weakness_list = {}
    w_deps = []
    t_w_deps = []
    for eachline in f.readlines():
        parts = eachline.split(',')
        w_deps.append([parts[1], parts[3].strip()])   # weaknesses dependency

        a_to_add = [parts[0], parts[1]]
        if a_to_add not in t_w_deps:
            t_w_deps.append(a_to_add)   # maps techniques to weakness (1)

        b_to_add = [parts[2], parts[3]]
        if b_to_add not in t_w_deps:
            t_w_deps.append([parts[2], parts[3].strip()])   # maps techniques to weakness (2)

        weakness_list[parts[1]] = ''
        weakness_list[parts[3].strip()] = ''

    # draws the weakness nodes
    for each in weakness_list:
        g.node(each, label=each + '\n' + kb.get_weakness(each).get('name'), color='red', shape='box')

    # maps dependencies between weaknesses
    for each in w_deps:
        g.edge(each[0], each[1], color='red')

    # maps the techniques to weaknesses
    for each in t_w_deps:
        g.edge(each[0], each[1], color='red')




def render2(kb, g, technique_list):
    # Shows all weaknesses
    for each_t in technique_list:
        for each_w in kb.get_technique(each_t).get('weaknesses'):
            g.edge(each_t, each_w, color='red')


def render3(kb, g, technique_list):
    # Load weaknesses
    f = open('dependency_examples/abstract_w.csv')
    weakness_list = []
    w_deps = []
    t_w_deps = []
    for eachline in f.readlines():
        parts = eachline.split(',')
        w_deps.append([parts[1], parts[3].strip()])  # weaknesses dependency

        a_to_add = [parts[0], parts[1]]
        if a_to_add not in t_w_deps:
            t_w_deps.append(a_to_add)  # maps techniques to weakness (1)

        b_to_add = [parts[2], parts[3]]
        if b_to_add not in t_w_deps:
            t_w_deps.append([parts[2], parts[3].strip()])  # maps techniques to weakness (2)

        a_to_add = [parts[1], parts[0]]
        if a_to_add not in weakness_list:
            weakness_list.append(a_to_add)

        b_to_add = [parts[3].strip(), parts[2]]
        if b_to_add not in weakness_list:
            weakness_list.append(b_to_add)

    # draws the weakness nodes
    for each in weakness_list:
        g.node(each[0], label=each[0] + ' (in {}:{})'.format(each[1], kb.get_technique(each[1]).get('name')) + '\n' + kb.get_weakness(each[0]).get('name'), color='black', shape='box')

    # maps dependencies between weaknesses
    for each in w_deps:
        g.edge(each[0], each[1], color='red')





if __name__ == '__main__':

    kb = solveitcore.SOLVEIT('data')

    g = graphviz.Digraph('SOLVE-IT Abstract Tool Example',
                         filename='output/solve-it-dependency-example.gv',
                         engine='dot')

    # load techqniue dependencies from a text file
    deps = []
    technique_list = {}
    f = open('dependency_examples/abstract_t.csv')
    for eachline in f.readlines():
        parts = eachline.split(',')
        deps.append([parts[0], parts[1].strip()])
        technique_list[parts[0]] = ''
        technique_list[parts[1].strip()] = ''

    # render1(kb, g, technique_list)
    #render2(kb, g, technique_list)
    render3(kb, g, technique_list)

    g.view()