import os
from pathlib import Path


def create_requirements_file(directory, save_file_path):
    lines = []
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if name == 'requirements.txt':
                file_path = Path(root, name)
                print(file_path)
                with open(file_path) as fid:
                    for line in fid:
                        module = line.strip()
                        if module.startswith('#'):
                            continue
                        elif module and module not in lines:
                            lines.append(module)

    # Remove duplicates
    keep_dict = {}
    for item in sorted(set(lines)):
        item = item.strip()
        if item.startswith('#'):
            continue
        split_item = item.strip().split('==')
        pack = split_item[0]
        keep_dict.setdefault(pack, set())
        keep_dict[pack].add(item)

    keep_list = []
    for key, value in keep_dict.items():
        if len(value) == 1:
            keep_list.append(list(value)[0])
        else:
            keep_list.append(key)

    # Write to file
    with open(save_file_path, 'w') as fid:
        fid.write('\n'.join(sorted(set(keep_list), reverse=True)))  # reverse to have the -e lines last

    return save_file_path
