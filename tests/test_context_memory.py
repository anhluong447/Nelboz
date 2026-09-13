import pytest
from src.domain.entities.context_memory import PostContextMemory


def test_context_memory_empty():
    mem = PostContextMemory()
    assert mem.get_full_context() == ""
    assert mem.line_count == 0
    assert not mem.is_sufficient()


def test_context_memory_add_and_filter_noise():
    mem = PostContextMemory()
    raw = """
    Anh Luong
    Hôm nay thời tiết Hà Nội thật tuyệt vời.
    Thích
    Bình luận
    Chia sẻ
    Viết bình luận công khai...
    """
    added = mem.add_ocr_result(raw)
    assert added == 2
    assert "Anh Luong" in mem.get_full_context()
    assert "Hôm nay thời tiết Hà Nội thật tuyệt vời." in mem.get_full_context()
    assert "Thích" not in mem.get_full_context()
    assert "Bình luận" not in mem.get_full_context()


def test_context_memory_deduplication():
    mem = PostContextMemory()
    pass1 = """
    Anh Luong
    Hôm nay thời tiết Hà Nội thật tuyệt vời.
    Gió mùa về se se lạnh.
    """
    mem.add_ocr_result(pass1)

    # Pass 2 scrolls down slightly, overlapping some lines
    pass2 = """
    Gió mùa về se se lạnh.
    Đi dạo hồ Tây ngắm hoàng hôn là nhất!
    [Hình ảnh cây hoa sữa]
    """
    added = mem.add_ocr_result(pass2)
    assert added == 2  # Only new lines added

    full = mem.get_full_context()
    # Check that "Gió mùa về se se lạnh." appears only once
    assert full.count("Gió mùa về se se lạnh.") == 1
    assert "Đi dạo hồ Tây ngắm hoàng hôn là nhất!" in full
    assert mem.is_sufficient()
