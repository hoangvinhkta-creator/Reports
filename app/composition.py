"""Production composition seam — Golden #1 Repair Batch #1 (B01) + `TASK-105E`.

`app/pipeline.py` là một thư viện THUẦN (S051 §9, S054 §3): `identity_registry`,
`confirmed_adjustment_source`, `eligible_costs_authority`, `price_composition`
đều là tham số DI mặc định "không nối gì" -> Pending, nên mọi lời gọi
`run_import()` đã tồn tại (test hay production, cũ hay mới) giữ nguyên hành vi
như trước khi bất kỳ tham số nào trong số đó ra đời. Sự thuần khiết ấy là kiến
trúc đúng, nhưng nó cũng có nghĩa: một caller BÌNH THƯỜNG, KHÔNG PHẢI TEST,
gọi `run_import(raw_path)` với mặc định thì nhận 100% Pending — không có gì
trong `app/pipeline.py` tự nạp các nguồn canonical đã commit.

Module này là seam tường minh nhỏ nhất đóng khoảng trống đó: nó nạp các nguồn
canonical từ đường dẫn cố định trong repo rồi gọi `run_import()` thật — không
stub, không mock, không bypass, không nhánh riêng cho Golden, không hard-code
order/BH nào.

## `TASK-105E` — nhánh post-cutover

Trước `TASK-105E`, seam này chỉ nạp ba nguồn của nhánh PRE-cutover, và mọi
dòng `sale_date >= CUTOVER_DATE` rơi vào `PendingPriceProvider`: pipeline
production **không hề gọi** Reports History Reader V1, dù reader đã được
review và tích hợp. Nay seam nạp thêm bằng chứng giá post-cutover
(`PriceResolutionSources`) và truyền một `PostCutoverPriceComposition` vào
`run_import()`.

Nguồn nào vắng mặt trên đĩa thì nhánh của nó Pending kèm lý do "nguồn chưa
được nối" — KHÁC hẳn "sản phẩm không có giá". Không đường nào đoán giá, đoán
mã, hay lấy giá hiện tại lấp vào một đơn cũ.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.modules.adjustment.confirmed_adjustment_source import (
    load_confirmed_adjustments_from_jsonl,
)
from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority
from app.modules.pricing.resolution.composition import PostCutoverPriceComposition
from app.modules.pricing.resolution.sources import load_price_resolution_sources
from app.modules.product.identity.registry_store import load_registry_from_jsonl
from app.pipeline import DEFAULT_CONFIG_DIR, ImportResult, run_import

# Canonical committed sources, fixed repository paths — same footing as
# `DEFAULT_CONFIG_DIR` ("config/") in `app/pipeline.py`.
HISTORICAL_REGISTRY_PATH = Path("data/historical_confirmed/registry.jsonl")
CONFIRMED_ADJUSTMENTS_PATH = Path(
    "data/confirmed_adjustments/confirmed_adjustments.jsonl"
)
ELIGIBLE_COSTS_PATH = Path("config/eligible_costs.yaml")


def build_price_composition(
    config_dir: Path = DEFAULT_CONFIG_DIR,
) -> PostCutoverPriceComposition:
    """Dựng composition post-cutover từ các nguồn canonical đã commit.

    Tách khỏi `run_import_production()` để một caller cần AUDIT (tool đo lường,
    test tích hợp, phiên review) giữ được tham chiếu tới chính instance đã
    chạy và đọc `records`/`evidence` của nó — `ImportResult` không có chỗ cho
    provenance từng dòng, và mở rộng nó nằm ngoài phạm vi `TASK-105E`.

    Mọi nguồn được đọc ĐÚNG MỘT LẦN ở đây; instance trả về là ảnh chụp bằng
    chứng đông lạnh của một lần import (§15 — reproducibility).
    """
    return PostCutoverPriceComposition(
        load_price_resolution_sources(config_dir=config_dir)
    )


def run_import_production(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_composition: Optional[PostCutoverPriceComposition] = None,
) -> ImportResult:
    """The normal, non-test production entry point: loads the canonical
    committed historical-confirmed registry, confirmed-adjustment source,
    eligible-cost authority and post-cutover price evidence, then runs the
    real `run_import()` pipeline.

    Any loader above failing closed (missing/invalid file) propagates as the
    corresponding `Pending`/`SOURCE_UNAVAILABLE` outcome inside `run_import()`
    — this function performs no extra error handling of its own.

    `price_composition` cho phép caller TRUYỀN VÀO chính instance nó đang giữ
    để đọc audit trail sau đó; bỏ trống thì hàm tự dựng một instance mới từ
    cùng các nguồn ấy.
    """
    return run_import(
        raw_path,
        config_dir=config_dir,
        identity_registry=load_registry_from_jsonl(HISTORICAL_REGISTRY_PATH),
        confirmed_adjustment_source=load_confirmed_adjustments_from_jsonl(
            CONFIRMED_ADJUSTMENTS_PATH
        ),
        eligible_costs_authority=load_eligible_costs_authority(ELIGIBLE_COSTS_PATH),
        price_composition=(
            price_composition
            if price_composition is not None
            else build_price_composition(config_dir)
        ),
    )
