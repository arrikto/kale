#  Copyright 2020 The Kale Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import re

import networkx as nx

from pyflakes import api as pyflakes_api
from pyflakes import reporter as pyflakes_reporter

from kale.utils import utils
from kale.static_analysis import ast as kale_ast


class StreamList:
    """Simulate a file object to store Flakes' report streams."""

    def __init__(self):
        self.out = list()

    def write(self, text):
        """Write to stream list."""
        self.out.append(text)

    def reset(self):
        """Clean the stream list."""
        self.out = list()
        return self

    def __call__(self):
        """Return the stream list."""
        return self.out


def pyflakes_report(code):
    """Inspect code using PyFlakes to detect any 'missing name' report.

    Args:
        code: A multiline string representing Python code

    Returns: a list of names that have been reported missing by Flakes
    """
    flakes_stdout = StreamList()
    flakes_stderr = StreamList()
    rep = pyflakes_reporter.Reporter(
        flakes_stdout.reset(),
        flakes_stderr.reset())
    pyflakes_api.check(code, filename="kale", reporter=rep)

    # the stderr stream should be used just for compilation error, so if any
    # message is found in the stderr stream, raise an exception
    if rep._stderr():
        raise RuntimeError("Flakes reported the following error:"
                           "\n{}".format('\t' + '\t'.join(rep._stderr())))

    # Match names
    p = r"'(.+?)'"

    out = rep._stdout()
    # Using a `set` to avoid repeating the same var names in case they are
    # reported missing multiple times by flakes
    undef_vars = set()
    # iterate over all the flakes report output, keeping only lines
    # with 'undefined name' reports
    for line in filter(lambda a: a != '\n' and 'undefined name' in a, out):
        var_search = re.search(p, line)
        undef_vars.add(var_search.group(1))
    return undef_vars


def detect_in_dependencies(nb_graph: nx.DiGraph,
                           pipeline_parameters: dict = None):
    """Detect missing names from the code blocks in the graph.

    Args:
        nb_graph: nx DiGraph with pipeline code blocks
        pipeline_parameters: Pipeline parameters dict
    """
    block_names = nb_graph.nodes()
    for block in block_names:
        source_code = '\n'.join(nb_graph.nodes(data=True)[block]['source'])
        commented_source_code = utils.comment_magic_commands(source_code)
        ins = pyflakes_report(code=commented_source_code)

        # Pipeline parameters will be part of the names that are missing,
        # but of course we don't want to marshal them in as they will be
        # present as parameters
        relevant_parameters = set()
        if pipeline_parameters:
            # Not all pipeline parameters are needed in every pipeline step,
            # these are the parameters that are actually needed by this step.
            relevant_parameters = ins.intersection(pipeline_parameters.keys())
            ins.difference_update(relevant_parameters)
        step_params = {k: pipeline_parameters[k] for k in relevant_parameters}
        nx.set_node_attributes(nb_graph, {block: {'ins': sorted(ins),
                                                  'parameters': step_params}})


def detect_out_dependencies(nb_graph: nx.DiGraph):
    """Detect the 'out' dependencies of each code block.

    These deps represent the variables that each code block must marshal to
    child steps of the pipeline. Out deps are detected by cycling though all
    the ancestors of each block. By knowing the 'ins' deps (e.g. missing names)
    of the current block, we can get the blocks were those names were declared.
    If an ancestor matches the `ins` entry then it will have a matching `outs`.

    Args:
        nb_graph: nx DiGraph with pipeline code blocks
    """
    for block_name in reversed(list(nx.topological_sort(nb_graph))):
        ins = nb_graph.nodes(data=True)[block_name]['ins']
        # for _a in nb_graph.predecessors(block_name):
        for _a in nx.ancestors(nb_graph, block_name):
            father_data = nb_graph.nodes(data=True)[_a]
            # Intersect the missing names of this father's child with all
            # the father's names. The intersection is the list of variables
            # that the father need to serialize
            outs = set(ins).intersection(father_data['all_names'])
            # include previous `outs` in case this father has multiple
            # children steps
            outs.update(father_data['outs'])
            # add to father the new `outs` variables
            nx.set_node_attributes(nb_graph, {_a: {'outs': sorted(outs)}})


def detect_fns_free_variables(source_code, imports_and_functions="",
                              step_parameters=None):
    """Return the function's free variables.

    Free variable: _If a variable is used in a code block but not defined
    there, it is a free variable._

    An Example:

    ```
    x = 5
    def foo():
        print(x)
    ```

    In the example above, `x` is a free variable for function `foo`, because
    it is defined outside of the context of `foo`.

    Here we run the PyFlakes report over the function body to get all the
    missing names (i.e. free variables), excluding the function arguments.

    Args:
        source_code: Multiline Python source code
        imports_and_functions: Multiline Python source that is prepended
            to every pipeline step. It should contain the code cells that
            where tagged as `import` and `functions`. We prepend this code to
            the function body because it will always be present in any pipeline
            step.
        step_parameters: Step parameters names. The step parameters
            are removed from the pyflakes report, as these names will always
            be available in the step's context.

    Returns (dict): A dictionary with the name of the function as key and
        a list of variables names + consumed pipeline parameters as values.
    """
    fns_free_vars = dict()
    # now check the functions' bodies for free variables. fns is a
    # dict function_name -> (function_body, function_args)
    fns = kale_ast.parse_functions(source_code)
    for fn_name, (fn_body, fn_args) in fns.items():
        code = imports_and_functions + "\n" + fn_body
        free_vars = pyflakes_report(code=code).difference(fn_args)
        # the pipeline parameters that are used in the function
        consumed_params = {}
        if step_parameters:
            consumed_params = free_vars.intersection(step_parameters.keys())
            # remove the used parameters form the free variables, as they
            # need to be handled differently.
            free_vars.difference_update(consumed_params)
        fns_free_vars[fn_name] = (free_vars, consumed_params)
    return fns_free_vars


def dependencies_detection(nb_graph: nx.DiGraph,
                           pipeline_parameters: dict = None):
    """Analyze the code blocks in the graph and detect the missing names.

    in each code block, annotating the nodes with `in` and `out` dependencies
    based in the topology of the graph.

    Args:
        nb_graph: nx DiGraph with pipeline code blocks
        pipeline_parameters: Pipeline parameters dict

    Returns: annotated graph
    """
    # First get all the names of each code block
    for block in nb_graph:
        block_data = nb_graph.nodes(data=True)[block]
        all_names = kale_ast.get_all_names('\n'.join(block_data['source']))
        nx.set_node_attributes(nb_graph, {block: {'all_names': all_names}})

    # annotate the graph inplace with all the variables dependencies between
    # graph nodes
    detect_in_dependencies(nb_graph, pipeline_parameters)
    detect_out_dependencies(nb_graph)

    return nb_graph
