"""Allowlisted block codes and messages; never log prompts, keys or raw errors."""
import logging

from app.schemas.hus import HUSDiagnostic

MAJOR_LABELS = {'mathematics': 'Toán học', 'mathematics_informatics': 'Toán tin',
                'computer_science': 'Khoa học máy tính và thông tin', 'data_science': 'Khoa học dữ liệu'}
LOGGER = logging.getLogger('hus.diagnostics')


def generation_diagnostic(generation):
    if generation is None or generation.used:
        return None
    reason = generation.fallback_reason
    if reason in {'basic_chat', 'not_answered', 'no_sources', 'f3_opt_out', 'ineligible_dataset'}:
        return None
    if reason == 'http_error' and generation.http_status == 429:
        code = 'quota'
    elif reason in {'invalid_output', 'evidence_coverage', 'invalid_response', 'invalid_result', 'output_budget'}:
        code = 'output_rejected'
    elif reason in {'configuration', 'disabled', 'pipeline_unavailable'}:
        code = 'configuration_error'
    elif reason in {'prompt_budget', 'unsafe_prompt'}:
        code = 'context_budget'
    elif reason == 'busy':
        code = 'busy'
    else:
        code = 'provider_error'
    return HUSDiagnostic(code=code, http_status=generation.http_status)


def log_block(diagnostic):
    # No caller-provided prose, question, model, exception or credential in log.
    if isinstance(diagnostic, HUSDiagnostic):
        LOGGER.info('hus_chat_block code=%s', diagnostic.code)


def model_error_message(diagnostic):
    if diagnostic.code == 'output_rejected':
        return 'AI đã phản hồi nhưng đầu ra chưa đạt kiểm tra nội dung/định dạng. Không hiển thị câu trả lời bị chặn.'
    if diagnostic.code == 'configuration_error' or diagnostic.http_status in {401, 403}:
        return 'Cấu hình hoặc quyền truy cập AI chưa hợp lệ. Kiểm tra key/project ở backend.'
    if diagnostic.code == 'context_budget':
        return 'Bằng chứng chưa gửi được tới AI vì vượt giới hạn hoặc không phù hợp. Hãy hỏi phạm vi hẹp hơn.'
    if diagnostic.code == 'busy':
        return 'Đang có một yêu cầu AI khác được xử lý. Hãy thử lại sau.'
    return 'Dịch vụ AI chưa kết nối được hoặc tạm thời chưa sẵn sàng. Hãy kiểm tra mạng hoặc thử lại sau.'
