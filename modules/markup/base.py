from dataclasses import dataclass, field
from typing import Dict, Any

from..document import (
    BlockClassifiedType
)

@dataclass
class Markup:
    page: int
    geometry: Dict[str, float]  # {"left_mm", "top_mm", "right_mm", "bottom_mm"}
    label: str

    def get_color_by_label(self) -> tuple[float, float, float]:
        hex_color = BlockClassifiedType.get_color(self.label)
        if hex_color is None:
            return (0,0,0)
        
        hex_color = hex_color.lstrip('#')

        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return (r, g, b)



