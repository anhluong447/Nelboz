from typing import Any, List
import numpy as np
from src.domain.entities.geometry import BoundingBox
from src.domain.entities.comment import CommentUnit
from src.domain.ports.vision import ICommentGrouper


class CommentThreadGrouper(ICommentGrouper):
    """Groups comment text and their respective reply anchors by analyzing vertical Y spacing and horizontal X indentation."""

    def __init__(self, indent_threshold_px: int = 45):
        self.indent_threshold_px = indent_threshold_px

    def group_comments(self, thread_image: Any) -> List[CommentUnit]:
        if thread_image is None or not isinstance(thread_image, np.ndarray):
            return []
        return []
