from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Markup:
    page: int
    geometry: Dict[str, float]  # {"left_mm", "top_mm", "right_mm", "bottom_mm"}
    label: str

    def get_color_by_label(self) -> tuple[float, float, float]:
        mapping = {
            "header": (0, 0, 1),  # Синий
            "text": (0.7, 1, 1),  # Белый (или прозрачный)
            "image": (0, 1, 0),  # Зеленый
            "table": (1, 0.5, 0),  # Оранжевый
            "number_list": (1, 1, 0),  # Желтый
            "marker_list": (1, 0.5, 0),
            "empty": (1, 0, 0),  # Красный
        }
        return mapping.get(self.label, (0, 0, 0))  # Черный по умолчанию


