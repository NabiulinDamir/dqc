from .color_marker import ColorMarker

def get_marker(method: str = ""):
    match(method):
        case _: 
            return ColorMarker()







