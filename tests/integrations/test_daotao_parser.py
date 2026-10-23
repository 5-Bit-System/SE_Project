from app.integrations.daotao.parser import normalize_rows


def test_normalize_preserves_missing_cells_and_grade_text():
    assert normalize_rows([
        [" Mã\n môn ", " Điểm "],
        [" MAT1001 ", " 8,5 "],
        ["MAT1002", ""],
        [" ", "\n"],
    ]) == [["Mã môn", "Điểm"], ["MAT1001", "8,5"], ["MAT1002", ""]]


def test_read_transcript_selects_nearest_table_and_keeps_semester_and_totals():
    from app.integrations.daotao.client import DaotaoClient

    expected = [["HỌC KỲ 1 - 2099-2100. MÃ HỌC KỲ 991"],
                ["1", "TEST001", "Môn giả lập", "3", "", "", ""],
                ["Tổng tín chỉ: 3"]]

    class Table:
        def evaluate(self, script):
            return expected

    class Cell:
        def locator(self, selector):
            assert selector == "xpath=ancestor::table[1]"
            return Table()

    client = object.__new__(DaotaoClient)
    def wait_for_data_cell(selector, timeout):
        assert selector == '#divList3 td[title="Mã môn học"]'
        return Cell()

    client._wait_for_element = wait_for_data_cell
    assert client.read_transcript() == expected
