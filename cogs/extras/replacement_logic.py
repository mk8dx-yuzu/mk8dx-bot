def replace(space, player, sub):
    if isinstance(space, list):
        return [replace(item, player, sub) for item in space]
    else:
        return sub if space == player else space

def swap(arr, one, two):
    arr = replace(arr, one, "dummy")
    arr = replace(arr, two, one)
    arr = replace(arr, "dummy", two)
    return arr