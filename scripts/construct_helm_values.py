#!/usr/bin/env python3

# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader, select_autoescape


def find_sub_schemas(root_dir):
    sub_schemas_dirs = []

    for path in Path(root_dir).rglob('sub_schemas'):
        if path.is_dir():
            sub_schemas_dirs.append(path)
    return sub_schemas_dirs


def construct_values_file(source_values_template_path: Path, destination_values_path: Path):
    chart_path = Path(__file__).parent.parent / "charts" / "matrix-stack"
    shared_sub_schemas_path = chart_path / "sub_schemas"
    env = Environment(
        loader=FileSystemLoader([source_values_template_path.parent, shared_sub_schemas_path,
                                 *find_sub_schemas(chart_path)]),
        autoescape=select_autoescape,
        keep_trailing_newline=True,
    )
    template = env.get_template(source_values_template_path.name)

    with open(destination_values_path, "w") as destination_values_file:
        destination_values_file.write(template.render())


def main():
    typer.run(construct_values_file)


if __name__ == "__main__":
    main()
