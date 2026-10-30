# AC/risk → case → executable test → commit → evidence

Ký hiệu: C=`tests/integrations/test_course_search_contract.py`,
U=`tests/catalogs/test_course_search.py`. Test trước patch tại a5aab95;
implementation tại cb3b35d. Tên dưới là pytest symbol thật, các param expansion
hiện trong red.log/mutation.log; không tự sinh expected bằng production algorithm.

| AC/risk | Case | Symbol/file | Version/evidence/kết quả | Residual risk |
|---|---|---|---|---|
| AC01 search/filter/isolation |TC02/03/13/14 |C::test_literal_search_and_combined_filters; C::test_program_isolation_and_single_snapshot_load |a5aab95RED→cb3b35dGREEN; green/after-mutation.log; passed |Không kiểm mọi Unicode form/nguồn trường thật |
| AC02 page/total/bounds |TC04/05/07/08/09/16 |C::test_new_provider_envelope_defaults_and_course_metadata; test_pagination_total_no_duplicate_or_missing_results; test_empty_result_is_valid_success; test_query_validation_error_contract; test_pagination_boundaries |42APIcases và4unit trong46passed; red→green |Data đổi giữa page không có snapshot guarantee |
| AC03 stable order/R2 |TC06/15 |C::test_stable_sort_ties_and_repository_order; U::test_total_order_survives_all_permutations_of_tied_rows; U::test_repeated_filter_sort_page_does_not_mutate_shared_catalog |green.log; flaky-runs6×46passed; coverage service4/4branch |Assume code unique như repository contract; không Vietnamese collation |
| AC04 legacy contract/R1 |TC01/12 |C::test_legacy_consumer_array_fields_types_order_and_extras; test_required_program_and_unknown_program_contract; test_failure_contract_never_returns_default_success với /courses |baseline32pass; legacy5casepass ngay RED; green78pass; final review AST |Consumer legacy có thật nhưng app.js không active; không chứng minh mọi client ngoài repo |
| AC05 failure/default/R3 |TC10/11/12 |C::test_failure_contract_never_returns_default_success; test_unexpected_exception_is_500_not_empty_success |mutation3failed39passed đúng200vs503/500; branch đúng46passed; patch ở evidence |Một mutant, không proof suite hoàn hảo; message StorageUnavailable vẫn theo contract repo |
| NFC01 tải/R5 |TC17 |tools.bt3.http_experiment::measure; http_fixture::check_response |cb3b35d app;12000correct/0errors; performance*.json/csv; SLO failed2configs |Không đáp ứng ổn định3s; chưa đo PG/production, local sharedCPU |
| NFC02 an toàn/scope |TC01/12 |tools.bt3.audit_root; tools.bt3.final_review; tests/conftest.py::isolated_runtime |root before/after và final-review artifacts; no DB migration/query shared |Pattern scanner không chứng minh phát hiện mọi secret |
| NFC03 deterministic/concurrency |TC06/15/17 |tools.bt3.flaky; U; Event gate/ready queue trong measure |6freshpytestprocess passed; peak100trong6runs; REPORT.flaky |Timing SLO vẫn biến thiên; chưa mọi race/backend |
| Browser slice |TC18 |tools.bt3.browser_smoke::main |browser.log/results.json passed, mock_routes=false |Browser fetch API, không UI tìm kiếm mới/real VNU/login |

Publication commit/link và remote CI cập nhật ở PUBLICATION.md sau push thật.
Các câu “passed” ở bảng chỉ dựa lệnh đã thực thi; risk coverage không làm thay
đổi trạng thái draft_unverified của catalog hoặc biến fixture thành nguồn học vụ.
