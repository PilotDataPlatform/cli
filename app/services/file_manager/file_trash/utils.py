# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Dict
from typing import List
from typing import Tuple

from app.models.item import ItemStatus
from app.models.item import ItemType
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.utils.aggregated import search_item


def parse_trash_paths(paths: List[str], zone: str, permanent: bool = False) -> Tuple[str, Dict[str, List[str]]]:
    '''
    Summary:
        Parse trash paths and get the corresponding item ids.
    Parameters:
        paths (List[str]): paths to trash.
        zone (str): zone.
        permanent (bool): whether to permanently delete the files.
    Returns:
        - items (Dict[str, List[str]]): parent item id and corresponding item ids.
            - root_folder (ItemType): root folder type.
            - items (List[str]): item ids.
        - project_code (str): project code.
    '''

    items, parent_cache = {}, {}
    project_code = None
    for path in paths:
        # assume path is project_code/<root>/<name_or_shared>/file for ACTIVE
        # for trashbin will be project_code/trash/file for TRASHED
        # raise the error if path is not in the correct format
        path_seg = path.split('/')
        if len(path_seg) < 3:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DELETE_PATH, True, path)
        project_code, root_path, item_path = path.split('/', 2)
        object_path = root_path + '/' + item_path
        parent_folder, _ = object_path.rsplit('/', 1)

        # detect root folder if it is users/shared/trash
        root_folder = ItemType.get_type_from_keyword(root_path)
        if root_folder == ItemType.TRASH and not permanent:
            SrvErrorHandler.customized_handle(ECustomizedError.ALREADY_TRASHED, True, path)
        if root_folder != ItemType.TRASH and len(path_seg) < 4:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DELETE_PATH, True, path)
        object_path = object_path.replace(root_path, root_folder.get_prefix_by_type()[:-1], 1)
        object_path = object_path.lstrip('/')

        # get item and corresponding parent item from cache or search
        status = ItemStatus.TRASHED if root_folder == ItemType.TRASH else ItemStatus.ACTIVE
        item = search_item(project_code, zone, object_path, status=status).get('result')
        if not item:
            SrvErrorHandler.customized_handle(ECustomizedError.DELETE_PATH_NOT_EXIST, True, path)

        # cache the parent item and item id
        if parent_folder not in parent_cache:
            parent_item = search_item(project_code, zone, parent_folder).get('result')
        else:
            parent_item = parent_cache[parent_folder]

        parent_id, item_id = parent_item.get('id'), item.get('id')
        if parent_id not in items:
            items[parent_id] = {'root_folder': root_folder, 'items': [item_id]}
            parent_cache[parent_folder] = parent_item
        else:
            items[parent_id]['items'].append(item_id)

    return project_code, items
