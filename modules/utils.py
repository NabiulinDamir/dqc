import json
import numpy as np
from enum import Enum
from pathlib import Path
# from modules.document import (
#     Document, 
#     DocumentBlock,
#     BlockClassifiedType,
#     BlockParsedType,
#     TextBlockData,
#     TextTypography, 
#     BlockGeometry, 
#     TableBlockData, 
#     ImageBlockData, 
#     ParsedBlockData,
#     NormalizeTextBlockData,
#     TableCell,
#     PageParameters
# )

# KNOWN_CLASSES = {
#     "Document":                    Document,               
#     "DocumentBlock":               DocumentBlock,         
#     "BlockClassifiedType":         BlockClassifiedType,   
#     "BlockParsedType":             BlockParsedType,       
#     "TextBlockData":               TextBlockData,         
#     "TextTypography":              TextTypography,         
#     "BlockGeometry":               BlockGeometry,          
#     "TableBlockData":              TableBlockData,         
#     "ImageBlockData":              ImageBlockData,         
#     "ParsedBlockData":             ParsedBlockData,           
#     "NormalizeTextBlockData":      NormalizeTextBlockData,
#     "TableCell":                   TableCell,             
#     "PageParameters":              PageParameters,     
# }

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
            
        return super().default(obj)

