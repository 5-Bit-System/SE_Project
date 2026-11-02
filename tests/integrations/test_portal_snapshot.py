import pytest

from app.integrations.daotao.snapshot import (
    PortalFailure,
    snapshot,
    source_profile,
    verified_subject,
)


def test_identity_requires_explicit_matching_subject():
    assert verified_subject("Mã sinh viên: demo001", "DEMO001") == "demo001"
    for value in ("demo001", "MSSV: other", "MSSV: demo001 MSSV: other"):
        with pytest.raises(PortalFailure):
            verified_subject(value, "demo001")


def test_identity_from_fresh_login_is_accepted_without_optional_label():
    assert verified_subject("Trang xem điểm", "DEMO001",
                            authenticated_subject="demo001") == "demo001"
    with pytest.raises(PortalFailure):
        verified_subject("Trang xem điểm", "demo001", authenticated_subject="other")
    with pytest.raises(PortalFailure):
        verified_subject("MSSV: other", "demo001", authenticated_subject="demo001")


def test_identity_accepts_separate_cells_and_common_label_variants():
    for value in ("Mã sinh viên\ndemo001", "Mã SV: demo001", "MSV： demo001"):
        assert verified_subject(value, "demo001") == "demo001"


def test_snapshot_preserves_retakes_blanks_unknown_and_source_grades():
    rows = [["HỌC KỲ 1 - 2099-2100"],
            ["1", "TEST001E", "Môn thử", "3", "8,5", "B+", "3,5"],
            ["2", "TEST001E", "Môn thử", "3", "", "", ""],
            ["Chưa hiểu", "giữ lại"], ["Tổng tín chỉ: 6"]]
    result = snapshot(rows)
    assert result["rows"] == rows
    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["grade10"] == "8,5"
    assert result["attempts"][1]["grade10"] == ""
    assert result["unknown_rows"][0]["cells"] == rows[3]
    assert result["completeness"] == "unknown"
    assert result["digest"] == snapshot(rows)["digest"]


def test_changed_structure_rejected():
    with pytest.raises(PortalFailure):
        snapshot([["new table"]])


def test_profile_reads_only_explicit_source_labels_and_preserves_values():
    result = source_profile(["Họ và tên: Sinh viên giả lập\nNgành học\tNgành nguồn thử\n"
                             "Khóa học： QH-2099\nMSSV: fake001"])
    assert result == {"name": "Sinh viên giả lập", "program": "Ngành nguồn thử",
                      "cohort": "QH-2099"}


def test_profile_does_not_infer_from_id_terms_catalog_or_unlabelled_prose():
    assert source_profile(["Họ và tên\nĐăng xuất\nMSSV: 2099001\n"
                           "HỌC KỲ 1 - 2099-2100\nKhoa học dữ liệu"]) == {
                               "name": None, "program": None, "cohort": None}


def test_profile_conflicts_and_ambiguous_multi_field_rows_remain_unknown():
    assert source_profile(["Họ tên: A\nKhóa học: QH-2099",
                           "Họ và tên: B\nKhóa học: QH-2099",
                           "Ngành học: X\tKhóa học: QH-2100"]) == {
                               "name": None, "program": None, "cohort": "QH-2099"}


def test_management_class_supplies_display_cohort_and_program():
    assert source_profile(["Họ và tên: Sinh viên giả lập\n"
                           "Khóa học: QH.2099.TEST\nNgành học: Giá trị trang khác\n"
                           "Lớp quản lý\t79 Ngành thử liên ngành"]) == {
                               "name": "Sinh viên giả lập",
                               "program": "Ngành thử liên ngành", "cohort": "79"}


@pytest.mark.parametrize("value", ["", "79", "Ngành thử", "QH.2099 Ngành thử",
                                  "79 123", "79 Ngành thử\tKhóa: khác"])
def test_malformed_management_class_is_not_guessed(value):
    result = source_profile([f"Lớp quản lý\t{value}"])
    assert result["program"] is result["cohort"] is None


def test_conflicting_management_classes_remain_unknown():
    result = source_profile(["Lớp quản lý: 79 Ngành A", "Lớp quản lý: 80 Ngành B"])
    assert result["program"] is result["cohort"] is None
