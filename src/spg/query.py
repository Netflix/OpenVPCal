import json
import os


def get_config_folder():
    """ Gets the folder which holds the pre installed configs

    :return: folder to the configs directory
    """
    config_folder_path = (
        os.path.join(os.path.dirname(__file__),
                     '..',
                     '..',
                     'configs'
                     )
    )
    return config_folder_path


def get_ocio_configs():
    results = {}
    config_folder = get_config_folder()
    ocio_folder = os.path.join(config_folder, "ocio")

    for root, dirs, files in os.walk(ocio_folder, topdown=False):
        for name in files:
            if not name.endswith(".ocio"):
                continue
            root_name = os.path.basename(root)
            results[root_name] = os.path.join(root, name)

    return results


def get_config(config_name):
    """ Placeholder for getting configs from files on disk whilst we look to implement the database and UI elements

    :param config_name: the name of the config we want to get
    :return: filepath for the given config file
    """
    config_path = os.path.join(get_config_folder(), config_name)

    if not os.path.exists(config_path):
        raise IOError("Config Not Found: " + config_path)

    return config_path


def load_json_from_file(file_path):
    """ For the given file_path we open the file, load and return the json data

    :param file_path: the filepath to the json structure
    :return: dict of json data
    """
    with open(file_path) as handle:
        return json.load(handle)


def get_panels_config(query_database=False, file_path=""):
    """ Gets the panel configs which stores all the panel makes available, this can be returned from a database query,
    or from a serialized file_path

    :param query_database: whether we want to query the database or not
    :param file_path: and override file path to serialized data
    :return: the dict of json data representing all the panels available
    """
    if query_database:
        pass

    if not file_path:
        file_path = get_config('panel_settings.json')
    return load_json_from_file(file_path)


def get_walls_config(query_database=False, file_path=""):
    """ Gets the wall configs which stores all the panel makes available, this can be returned from a database query,
    or from a serialized file_path

    :param query_database: whether we want to query the database or not
    :param file_path: and override file path to serialized data
    :return: the dict of json data representing all the panels available
    """
    if query_database:
        pass

    if not file_path:
        file_path = get_config('led_wall_settings.json')
    return load_json_from_file(file_path)


def get_raster_config(query_database=False, file_path=""):
    """ Gets the raster configs which stores how our led walls are arranged into raster maps, this can be returned
     from a database query, or from a serialized file_path

    :param query_database: whether we want to query the database or not
    :param file_path: and override file path to serialized data
    :return: the dict of json data representing all the panels available
    """
    if query_database:
        pass

    if not file_path:
        file_path = get_config('raster_settings.json')

    return load_json_from_file(file_path)


def get_project_settings(query_database=False, file_path=""):
    """ Gets the project settings configs which stores global data about our project, such as frame rate, this can be
    returned from a database query, or from a serialized file_path

    :param query_database: whether we want to query the database or not
    :param file_path: and override file path to serialized data
    :return: the dict of json data representing all the panels available
    """
    if query_database:
        pass

    if not file_path:
        file_path = get_config('project_settings.json')

    return load_json_from_file(file_path)


def get_pattern_settings(query_database=False, file_path=""):
    """ Gets the pattern settings which stores the recipe for the patterns we want to generate and the settings used to
    generate each pattern, this can be returned from a database query, or from a serialized file_path

    :param query_database: whether we want to query the database or not
    :param file_path: and override file path to serialized data
    :return: the dict of json data representing all the panels available
    """
    if query_database:
        pass

    if not file_path:
        file_path = get_config('pattern_settings.json')

    return load_json_from_file(file_path)
