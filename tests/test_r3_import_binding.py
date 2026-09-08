"""R3 §1 — nạp lại sổ đã sửa KHÔNG được gắn nhầm quyết định của Owner.

Bài toán mà cả file này nói về, viết bằng một ví dụ thật:

    Đơn `BH62511` có HAI dòng "Chi phí vận chuyển" (dữ liệu thật có đơn như
    thế). Owner gõ giá nhập cho dòng thứ nhất; quyết định đó được lưu dưới
    khoá `(BH62511, sha256("Chi phí vận chuyển"), 1)`.

    Kế toán sửa sổ và đảo hai dòng đó cho nhau. Trước R3, `occurrence_index`
    được đánh theo VỊ TRÍ dòng trong file, nên dòng vật lý thứ hai nhận chỉ
    số 1 — và giá nhập Owner gõ cho dòng kia lặng lẽ chuyển sang nó.

Toàn bộ các bài dưới đây đo đúng một tính chất: khoá của một dòng đi theo
NỘI DUNG của nó, không theo chỗ nó đứng; và khi nội dung không đủ để kết
luận, hệ thống dựng một NGOẠI LỆ thay vì đoán.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import insert, select

from app.history import keys
from app.history import line_binding
from app.history.models import LineKey
from app.web import history_store
from tools.db import schema

from tests.test_snapshot_repository import (  # noqa: F401 — fixture repository
    repository, result_line, rows, source_line, write,
)

FEE = "Chi phí vận chuyển"


def existing(*items) -> tuple:
    """Các khoá đang hiện hành của MỘT nhóm, viết gọn."""
    return tuple(
        line_binding.ExistingOccurrence(
            occurrence_index=index, fingerprint=fingerprint, imei=imei,
            owner_decisions=decisions,
        )
        for index, fingerprint, imei, decisions in items
    )


def group_of(line) -> tuple:
    return (line.key.order_key, line.key.product_key)


def indexes(result) -> dict:
    """``source_row → occurrence_index`` — hình dạng mà mọi bài dưới đây hỏi."""
    return {line.source_row: line.key.occurrence_index for line in result.lines}


# --- Tầng thuần: ba mỏ neo ------------------------------------------------

class TestFirstImportKeepsTheBehaviourItAlwaysHad:
    """Không có gì để neo vào ⟹ đánh số theo `source_row`, đúng như trước R3."""

    def test_a_group_with_no_history_is_numbered_by_source_row(self):
        lines = [source_line("BH1", product=FEE, row=9, sell_price="200000"),
                 source_line("BH1", product=FEE, row=6, sell_price="100000")]
        result = line_binding.bind_occurrences(lines, {})
        assert indexes(result) == {6: 1, 9: 2}
        assert result.ambiguities == ()
        # Thứ tự trả về đúng bằng thứ tự đã nhận vào — hợp đồng song song với
        # danh sách dòng KẾT QUẢ (`rebound_results`).
        assert [line.source_row for line in result.lines] == [9, 6]

    def test_a_brand_new_line_in_a_known_group_takes_a_fresh_index(self):
        old = source_line("BH1", product=FEE, row=6, sell_price="100000")
        new = source_line("BH1", product=FEE, row=7, sell_price="300000")
        result = line_binding.bind_occurrences(
            [old, new], {group_of(old): existing((1, old.fingerprint, None, ()))})
        assert indexes(result) == {6: 1, 7: 2}


class TestContentAnchorsTheKeyNotPosition:
    """Mỏ neo `FINGERPRINT` — bản sửa trung tâm của R3 §1."""

    def test_reordering_two_identical_lines_changes_nothing(self):
        """Hai dòng giống HỆT nhau: đảo chỗ không phải một thay đổi nào cả."""
        first = source_line("BH1", product=FEE, row=6, sell_price="100000")
        second = source_line("BH1", product=FEE, row=7, sell_price="100000")
        result = line_binding.bind_occurrences([first, second], {
            group_of(first): existing(
                (1, first.fingerprint, None, ("giá nhập tay",)),
                (2, second.fingerprint, None, ()),
            )})
        assert indexes(result) == {6: 1, 7: 2}
        assert result.ambiguities == ()

    def test_reordering_two_different_lines_moves_the_key_with_the_content(self):
        """ĐÂY là lỗi mà R3 §1 đóng lại.

        Dòng 100.000 và dòng 200.000 đổi chỗ trong file. Trước R3, dòng đứng
        trên nhận chỉ số 1 — tức 200.000 thừa hưởng quyết định của 100.000.
        Sau R3, mỗi khoá đi theo nội dung của chính nó.
        """
        cheap = source_line("BH1", product=FEE, row=7, sell_price="100000")
        dear = source_line("BH1", product=FEE, row=6, sell_price="200000")
        result = line_binding.bind_occurrences([cheap, dear], {
            group_of(cheap): existing(
                (1, cheap.fingerprint, None, ("giá nhập tay",)),
                (2, dear.fingerprint, None, ()),
            )})
        # Dòng 100.000 vẫn là occurrence 1 dù nay nó đứng DƯỚI trong file.
        assert indexes(result) == {7: 1, 6: 2}
        product = cheap.key.product_key
        assert result.anchors[LineKey("BH1", product, 1)] == \
            line_binding.ANCHOR_FINGERPRINT
        assert result.anchors[LineKey("BH1", product, 2)] == \
            line_binding.ANCHOR_FINGERPRINT

    def test_an_edited_single_line_keeps_its_key(self):
        """Một dòng vào, một khoá trống ⟹ ghép. Đây là ca `SOURCE_CHANGED`."""
        before = source_line("BH1", product="Tủ lạnh", row=6, sell_price="8000000")
        after = source_line("BH1", product="Tủ lạnh", row=6, sell_price="8500000")
        result = line_binding.bind_occurrences([after], {
            group_of(before): existing((1, before.fingerprint, None, ("giá nhập tay",)))})
        assert indexes(result) == {6: 1}
        assert result.anchors[after.key] == line_binding.ANCHOR_POSITION
        assert result.ambiguities == ()


class TestImeiIsTheStrongestAnchorTheBookHas:
    def test_an_edited_line_with_the_same_imei_keeps_its_key(self):
        """IMEI thắng fingerprint: sửa giá bán không đổi chiếc máy đang bán."""
        before = source_line("BH1", product="Tivi", row=6, sell_price="9000000",
                             imei="IMEI-A")
        other = source_line("BH1", product="Tivi", row=7, sell_price="7000000",
                            imei="IMEI-B")
        after = source_line("BH1", product="Tivi", row=6, sell_price="9500000",
                            imei="IMEI-A")
        result = line_binding.bind_occurrences([after], {
            group_of(before): existing(
                (1, other.fingerprint, "IMEI-B", ()),
                (2, before.fingerprint, "IMEI-A", ("giá nhập tay",)),
            )})
        assert indexes(result) == {6: 2}
        assert result.anchors[LineKey("BH1", after.key.product_key, 2)] == \
            line_binding.ANCHOR_IMEI

    def test_an_empty_imei_is_not_an_anchor(self):
        """Ô IMEI trống KHÔNG phải một danh tính.

        Coi chuỗi rỗng là một IMEI sẽ gộp mọi dòng không có IMEI vào cùng một
        mỏ neo — tức dựng lại đúng lỗi mà module này đóng.
        """
        assert line_binding.normalized_imei("  ") is None
        assert line_binding.normalized_imei(None) is None
        assert line_binding.normalized_imei(" 35 1234 ") == "351234"


# --- Khi không đoán được: ngoại lệ, không phải một phỏng đoán --------------

class TestAmbiguityIsRaisedOnlyWhenGuessingCouldMoveADecision:
    def test_two_edited_lines_with_a_decision_at_stake_raise_an_exception(self):
        cheap = source_line("BH1", product=FEE, row=6, sell_price="100000")
        dear = source_line("BH1", product=FEE, row=7, sell_price="200000")
        # CẢ HAI dòng đều đã bị sửa ⟹ không fingerprint nào khớp, không IMEI.
        edited_a = source_line("BH1", product=FEE, row=6, sell_price="110000")
        edited_b = source_line("BH1", product=FEE, row=7, sell_price="220000")
        result = line_binding.bind_occurrences([edited_a, edited_b], {
            group_of(cheap): existing(
                (1, cheap.fingerprint, None, ("giá nhập tay",)),
                (2, dear.fingerprint, None, ()),
            )})
        # Không khoá cũ nào bị tái sử dụng: hai dòng vào nhận khoá MỚI.
        assert set(indexes(result).values()) == {3, 4}
        assert len(result.ambiguities) == 2
        first = result.ambiguities[0]
        assert first.candidate_occurrence_indexes == (1, 2)
        assert first.protected_occurrence_indexes == (1,)
        assert first.protected_decisions == ("giá nhập tay",)

    def test_the_same_shape_without_any_decision_binds_quietly(self):
        """Không quyết định nào treo ⟹ ghép theo thứ tự, KHÔNG dựng ngoại lệ.

        Ghép sai ở đây không làm sai một đồng nào — nó chỉ cho ra một lịch sử
        version khác. Dựng ngoại lệ cho mọi lần đổi thứ tự dòng là tạo ra
        nhiễu mà Owner sẽ học cách bấm bỏ qua, và khi đó ngoại lệ THẬT ở bài
        trên cũng bị bỏ qua theo.
        """
        cheap = source_line("BH1", product=FEE, row=6, sell_price="100000")
        dear = source_line("BH1", product=FEE, row=7, sell_price="200000")
        edited_a = source_line("BH1", product=FEE, row=6, sell_price="110000")
        edited_b = source_line("BH1", product=FEE, row=7, sell_price="220000")
        result = line_binding.bind_occurrences([edited_a, edited_b], {
            group_of(cheap): existing(
                (1, cheap.fingerprint, None, ()),
                (2, dear.fingerprint, None, ()),
            )})
        assert indexes(result) == {6: 1, 7: 2}
        assert result.ambiguities == ()

    def test_one_incoming_against_two_protected_keys_is_still_ambiguous(self):
        """Một dòng vào, HAI khoá trống mang quyết định ⟹ vẫn không đoán."""
        a = source_line("BH1", product=FEE, row=6, sell_price="100000")
        b = source_line("BH1", product=FEE, row=7, sell_price="200000")
        edited = source_line("BH1", product=FEE, row=6, sell_price="150000")
        result = line_binding.bind_occurrences([edited], {
            group_of(a): existing(
                (1, a.fingerprint, None, ("giá nhập tay",)),
                (2, b.fingerprint, None, ("loại dòng khỏi báo cáo",)),
            )})
        assert indexes(result) == {6: 3}
        assert len(result.ambiguities) == 1
        assert result.ambiguities[0].protected_occurrence_indexes == (1, 2)


# --- Qua database THẬT: quyết định của Owner đi theo đúng dòng của nó ------

def seed_override(engine, *, order, product, occurrence, price):
    """Một giá nhập Owner đã gõ, ghi thẳng vào bảng quyết định.

    Ghi thẳng chứ không đi qua `BusinessDecisionStore`: bài test này nói về
    TẦNG GẮN DÒNG, và nó phải đúng bất kể đường ghi nào đã đặt quyết định ở đó.
    """
    with engine.begin() as connection:
        connection.execute(insert(schema.kpi_purchase_price_override).values(
            order_key=order, product_key=keys.product_key(product),
            occurrence_index=occurrence, origin=schema.ORIGIN_PIPELINE,
            purchase_price=Decimal(price), provenance="MANUAL",
            auto_price_at_entry=None, entered_at="2026-09-08T01:00:00",
            entered_by="owner-web", reason="Hàng ngoài bảng giá",
        ))


def current_rows(engine):
    return {
        (row["order_key"], row["occurrence_index"]): row
        for row in rows(engine, schema.order_line_current)
    }


def sell_price_of(engine, order, product, occurrence):
    """Giá bán ĐANG hiện hành của một khoá — dùng để hỏi "khoá này là dòng nào"."""
    with engine.connect() as connection:
        return connection.execute(
            select(schema.order_line_source_version.c.sell_price)
            .select_from(schema.order_line_current.join(
                schema.order_line_source_version,
                schema.order_line_source_version.c.id
                == schema.order_line_current.c.current_source_version_id))
            .where(schema.order_line_current.c.order_key == order)
            .where(schema.order_line_current.c.product_key == keys.product_key(product))
            .where(schema.order_line_current.c.occurrence_index == occurrence)
        ).scalar()


class TestReimportingAnEditedBookThroughTheRealRepository:
    def test_uploading_the_same_file_twice_changes_nothing(self, repository, history_engine):
        """Idempotency: hai lần nạp CÙNG một sổ ⟹ không version nguồn mới."""
        lines = [source_line("BH1", product=FEE, row=6, sell_price="100000"),
                 source_line("BH1", product=FEE, occurrence=2, row=7, sell_price="200000")]
        write(repository, lines, run_id="r1", created_at="2026-09-08T01:00:00")
        second = write(repository, lines, run_id="r2",
                       created_at="2026-09-08T02:00:00", fingerprint="fp-a")
        assert second.counts["SAME"] == 2
        assert second.counts["INSERT"] == 0
        assert second.counts["SOURCE_CHANGED"] == 0
        assert second.ambiguous_bindings == 0
        assert len(rows(history_engine, schema.order_line_source_version)) == 2

    def test_reordering_the_rows_keeps_each_override_on_its_own_line(
        self, repository, history_engine
    ):
        """Kịch bản trung tâm của R3 §1, đi hết qua database thật.

        Owner gõ giá cho dòng 100.000 (occurrence 1). Sổ được nạp lại với hai
        dòng đảo chỗ. Sau đó khoá số 1 PHẢI vẫn là dòng 100.000 — nếu không,
        giá Owner gõ cho dòng này đã chuyển sang dòng kia.
        """
        first = [source_line("BH1", product=FEE, row=6, sell_price="100000"),
                 source_line("BH1", product=FEE, occurrence=2, row=7, sell_price="200000")]
        write(repository, first, run_id="r1", created_at="2026-09-08T01:00:00")
        seed_override(history_engine, order="BH1", product=FEE, occurrence=1,
                      price="70000")
        assert sell_price_of(history_engine, "BH1", FEE, 1) == Decimal("100000")

        # Sổ mới: HAI DÒNG ĐẢO CHỖ, nội dung không đổi một chữ.
        swapped = [source_line("BH1", product=FEE, row=6, sell_price="200000"),
                   source_line("BH1", product=FEE, occurrence=2, row=7,
                               sell_price="100000")]
        outcome = write(repository, swapped, run_id="r2",
                        created_at="2026-09-08T02:00:00", fingerprint="fp-b")

        assert sell_price_of(history_engine, "BH1", FEE, 1) == Decimal("100000")
        assert sell_price_of(history_engine, "BH1", FEE, 2) == Decimal("200000")
        # Không dòng nào bị coi là "đã sửa": nội dung nghiệp vụ y nguyên.
        assert outcome.counts["SOURCE_CHANGED"] == 0
        assert outcome.counts["SAME"] == 2
        assert outcome.ambiguous_bindings == 0

    def test_when_it_cannot_tell_it_raises_an_exception_and_keeps_the_old_keys(
        self, repository, history_engine
    ):
        """Hai dòng cùng nhóm đều bị sửa, một khoá đang mang giá nhập tay.

        Không mỏ neo nào khớp. Hệ thống KHÔNG ghép: hai dòng vào nhận khoá
        mới, khoá cũ (và quyết định treo trên nó) KHÔNG bị đụng tới, và một
        ngoại lệ được ghi cho Owner.
        """
        first = [source_line("BH1", product=FEE, row=6, sell_price="100000"),
                 source_line("BH1", product=FEE, occurrence=2, row=7, sell_price="200000")]
        write(repository, first, run_id="r1", created_at="2026-09-08T01:00:00")
        seed_override(history_engine, order="BH1", product=FEE, occurrence=1,
                      price="70000")

        edited = [source_line("BH1", product=FEE, row=6, sell_price="110000"),
                  source_line("BH1", product=FEE, occurrence=2, row=7,
                              sell_price="220000")]
        outcome = write(repository, edited, run_id="r2",
                        created_at="2026-09-08T02:00:00", fingerprint="fp-c")

        assert outcome.ambiguous_bindings == 2
        assert outcome.counts["INSERT"] == 2
        assert outcome.counts["SOURCE_CHANGED"] == 0

        # Khoá cũ còn nguyên và VẪN trỏ tới nội dung cũ — không bị xoá, không
        # bị hủy, chỉ vắng mặt ở snapshot này (`NOT_SEEN`, PRA-002 slice B).
        assert sell_price_of(history_engine, "BH1", FEE, 1) == Decimal("100000")
        assert sell_price_of(history_engine, "BH1", FEE, 2) == Decimal("200000")
        # Hai dòng mới nằm ở khoá mới.
        assert sell_price_of(history_engine, "BH1", FEE, 3) == Decimal("110000")
        assert sell_price_of(history_engine, "BH1", FEE, 4) == Decimal("220000")
        # Giá nhập Owner đã gõ VẪN nằm đúng chỗ cũ, không chuyển sang dòng nào.
        override = rows(history_engine, schema.kpi_purchase_price_override)
        assert len(override) == 1
        assert override[0]["occurrence_index"] == 1

        raised = rows(history_engine, schema.line_binding_exception)
        assert len(raised) == 2
        assert {item["assigned_occurrence_index"] for item in raised} == {3, 4}
        assert all(item["resolved_at"] is None for item in raised)
        assert "giá nhập tay" in raised[0]["detail_json"]

    def test_an_edited_line_with_no_decision_at_stake_stays_quiet(
        self, repository, history_engine
    ):
        """Cùng hình dạng, KHÔNG quyết định nào treo ⟹ ghép, không ngoại lệ."""
        first = [source_line("BH1", product=FEE, row=6, sell_price="100000"),
                 source_line("BH1", product=FEE, occurrence=2, row=7, sell_price="200000")]
        write(repository, first, run_id="r1", created_at="2026-09-08T01:00:00")
        edited = [source_line("BH1", product=FEE, row=6, sell_price="110000"),
                  source_line("BH1", product=FEE, occurrence=2, row=7,
                              sell_price="220000")]
        outcome = write(repository, edited, run_id="r2",
                        created_at="2026-09-08T02:00:00", fingerprint="fp-d")
        assert outcome.ambiguous_bindings == 0
        assert outcome.counts["SOURCE_CHANGED"] == 2
        assert rows(history_engine, schema.line_binding_exception) == []

    def test_a_multi_line_order_of_different_products_is_untouched(
        self, repository, history_engine
    ):
        """Đơn nhiều hàng KHÁC NHAU: mỗi mặt hàng một nhóm, không có gì để nhầm."""
        lines = [source_line("BH1", product="Tủ lạnh", row=6),
                 source_line("BH1", product="Máy giặt", row=7),
                 source_line("BH1", product=FEE, row=8, sell_price="100000")]
        write(repository, lines, run_id="r1", created_at="2026-09-08T01:00:00")
        # Nạp lại với thứ tự HOÀN TOÀN khác.
        reordered = [source_line("BH1", product=FEE, row=6, sell_price="100000"),
                     source_line("BH1", product="Máy giặt", row=7),
                     source_line("BH1", product="Tủ lạnh", row=8)]
        outcome = write(repository, reordered, run_id="r2",
                        created_at="2026-09-08T02:00:00", fingerprint="fp-e")
        assert outcome.counts["SAME"] == 3
        assert outcome.counts["INSERT"] == 0
        assert outcome.ambiguous_bindings == 0

    def test_a_line_absent_from_the_later_file_is_never_deleted(
        self, repository, history_engine
    ):
        """Đơn vắng trong file tải sau KHÔNG tự bị xoá/hủy (yêu cầu R3).

        Nó chỉ nhận một cờ `NOT_SEEN_IN_LATEST_SNAPSHOT` — bản ghi, con trỏ
        hiện hành và quyết định của Owner đều còn nguyên.
        """
        lines = [source_line("BH1", product="Tủ lạnh", row=6),
                 source_line("BH2", product="Máy giặt", row=7)]
        write(repository, lines, run_id="r1", created_at="2026-09-08T01:00:00")
        seed_override(history_engine, order="BH2", product="Máy giặt",
                      occurrence=1, price="4000000")

        outcome = write(repository, [lines[0]], run_id="r2",
                        created_at="2026-09-08T02:00:00", fingerprint="fp-f")
        assert outcome.not_seen == 1
        assert ("BH2", 1) in current_rows(history_engine)
        assert len(rows(history_engine, schema.kpi_purchase_price_override)) == 1
