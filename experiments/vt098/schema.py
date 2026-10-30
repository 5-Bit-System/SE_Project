"""Load the real request schema without importing runtime/auth/DB integrations.

The baseline schema is a standalone class using only these three Pydantic names.
If it gains external dependencies, loading fails rather than silently copying it.
No route, decorator, module-level import or other repository code is executed.
"""

import ast
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def load_plan_input():
    source = Path(__file__).resolve().parents[2] / 'app/api/academic.py'
    tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
    declarations = [node for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == 'SemesterPlanInput']
    if len(declarations) != 1:
        raise RuntimeError('Expected exactly one real SemesterPlanInput declaration')
    module = ast.Module(body=declarations, type_ignores=[])
    namespace = {'BaseModel': BaseModel, 'ConfigDict': ConfigDict, 'Field': Field,
                 '__name__': __name__}
    exec(compile(module, str(source), 'exec'), namespace)
    return namespace['SemesterPlanInput']


SemesterPlanInput = load_plan_input()
