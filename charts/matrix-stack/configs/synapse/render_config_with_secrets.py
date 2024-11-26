#!/usr/bin/env python3

# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import json
import os
import re
import sys
from pathlib import Path

import yaml


def deep_merge_dicts(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            deep_merge_dicts(value, destination.setdefault(key, {}))
        else:
            destination[key] = value


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage {sys.argv[0]} <source files>")
        sys.exit(1)

    source_filenames = sys.argv[1:]
    output = {}

    for source_filename in [Path(source_filename) for source_filename in source_filenames]:
        if not source_filename.exists():
            print(f"{source_filename} doesn't exist. Exitting")
            sys.exit(1)

        if not source_filename.is_file():
            continue

        source_fragment = source_filename.read_text(encoding="utf-8")

        env_var_names = re.findall(r"\$\{([^\}]+)\}", source_fragment)
        for env_var in env_var_names:
            if env_var not in os.environ:
                print(f"{env_var} is not present in the environment. Exitting")
                sys.exit(1)

            replacement_value = json.dumps(os.environ[env_var], ensure_ascii=False)
            source_fragment = source_fragment.replace(f"${{{env_var}}}", replacement_value)

        deep_merge_dicts(yaml.safe_load(source_fragment), output)

    print(yaml.dump(output, allow_unicode=True))
