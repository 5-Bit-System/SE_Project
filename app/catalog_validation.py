from app.errors import StorageDataError
from app.models import Program


def validate_curriculum_selections(program: Program, course_codes: set[str]) -> None:
    """Validate catalog structure independently of its storage backend."""
    groups = {group.id for group in program.choice_groups}
    if len(groups) != len(program.choice_groups):
        raise StorageDataError("Nhóm lựa chọn bị trùng")
    tracks = program.track_selection.tracks
    track_ids = {track.id for track in tracks}
    if len(track_ids) != len(tracks):
        raise StorageDataError("Track bị trùng")
    for track in tracks:
        if not set(track.choice_group_ids) <= groups:
            raise StorageDataError("Track chứa nhóm lựa chọn không tồn tại")
    paths = program.graduation_selection.paths
    if len({path.id for path in paths}) != len(paths):
        raise StorageDataError("Nhánh tốt nghiệp bị trùng")
    for path in paths:
        if not set(path.course_codes) <= course_codes:
            raise StorageDataError("Nhánh tốt nghiệp chứa môn không tồn tại")
        if not set(path.allowed_track_ids) <= track_ids:
            raise StorageDataError("Nhánh tốt nghiệp chứa track không tồn tại")
