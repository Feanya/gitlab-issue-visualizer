def dict_string(d: dict, padding=0, include_falsy=True):
    """Constructs a string from a dictionary, where every key value pair is on its line

    Arguments:
        padding: Optional value to pad out each line with spaces in the front.
        include_falsy: Optional. If False it only prints key value pairs with a value that is a truthy [Default=True]
    """
    string = ""
    for k, v in d.items():
        if include_falsy or v:
            string += f"{'':{padding}}{k, v}\n"
    return string[1:-1]


def time_string(time_in_seconds: float) -> str:
    return f"{int(time_in_seconds // 60)}m {int(time_in_seconds % 60)}s {int((time_in_seconds*1000)%1000)}ms"
