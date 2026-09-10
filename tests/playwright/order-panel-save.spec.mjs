// `UI-01`/`UI-02` — PATCH qua panel: lưu thành công vá đúng hàng trong
// bảng nền, lỗi mạng giữ draft + THỬ LẠI không tự động, xung đột revision
// (409) giữ draft + hai đường lựa chọn, và một response GET cũ (đơn A) bị
// bỏ qua khi panel đã chuyển sang đơn B trước khi nó về.
import { test, expect } from '@playwright/test';

const SIMPLE_ORDER = 'BH70001';
const OTHER_ORDER = 'BH70002';
const PAGE_URL = '/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh';

async function openPanel(page, orderKey) {
  await page.click(`[data-metric="bh-edit"][data-order="${orderKey}"]`);
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog.locator('[data-metric="order-panel-line"]').first())
    .toBeVisible();
  return dialog;
}

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

test('lưu thành công: vá đúng hàng trong bảng, không tải lại danh sách', async ({ page }) => {
  const dialog = await openPanel(page, SIMPLE_ORDER);
  const firstLine = dialog.locator('[data-metric="order-panel-line"]').first();
  const productKey = await firstLine.getAttribute('data-product-key');
  const occurrenceIndex = await firstLine.getAttribute('data-occurrence-index');

  // `data-order` PHẢI có mặt: `product_key` định danh một MẶT HÀNG, và hai
  // đơn khác nhau đặt cùng mặt hàng ở dòng đầu (`occurrence_index=1`) là
  // chuyện bình thường — thiếu `data-order` sẽ khớp NHẦM hàng của đơn khác.
  const tableCell = page.locator(
    `tr[data-order="${SIMPLE_ORDER}"][data-product-key="${productKey}"]`
    + `[data-occurrence-index="${occurrenceIndex}"] td[data-metric="purchase_price"]`);
  const before = await tableCell.textContent();

  await page.evaluate(() => { window.__probe = 'con-song'; });

  const priceInput = firstLine.locator('[data-metric="order-panel-price"]');
  await priceInput.fill('7.777.000');
  const reason = dialog.locator('[data-metric="order-panel-reason"]');
  if (await reason.isVisible()) await reason.fill('kiểm tra Playwright — UI-01/UI-02');
  await dialog.locator('[data-metric="order-panel-save"]').click();

  await expect(dialog.locator('[data-metric="order-panel-status"]'))
    .toHaveAttribute('data-state', 'saved');

  // Bảng nền được vá TẠI CHỖ — không có lần tải lại danh sách nào xảy ra.
  expect(await page.evaluate(() => window.__probe)).toBe('con-song');
  await expect(tableCell).not.toHaveText(before || '');

  // Panel không tự đóng sau khi lưu — đóng vẫn là một hành động của người
  // dùng (Escape/nút Đóng), và dữ liệu đã lưu vẫn còn trên bảng sau đó.
  await dialog.locator('[data-metric="order-panel-close"]').click();
  await expect(dialog).toBeHidden();
  await expect(tableCell).not.toHaveText(before || '');
});

test('lỗi mạng: giữ nguyên draft, KHÔNG tự gửi lại — chỉ gửi khi bấm THỬ LẠI', async ({ page }) => {
  let patchAttempts = 0;
  await page.route('**/api/v1/orders/**', async (route) => {
    const request = route.request();
    if (request.method() !== 'PATCH') return route.continue();
    patchAttempts += 1;
    if (patchAttempts === 1) {
      await route.abort('failed');
      return;
    }
    return route.continue();
  });

  const dialog = await openPanel(page, SIMPLE_ORDER);
  const firstLine = dialog.locator('[data-metric="order-panel-line"]').first();
  const priceInput = firstLine.locator('[data-metric="order-panel-price"]');
  await priceInput.fill('8.888.000');
  const reason = dialog.locator('[data-metric="order-panel-reason"]');
  if (await reason.isVisible()) await reason.fill('kiểm tra lỗi mạng — Playwright');
  await dialog.locator('[data-metric="order-panel-save"]').click();

  const status = dialog.locator('[data-metric="order-panel-status"]');
  await expect(status).toHaveAttribute('data-state', 'unconfirmed');
  expect(patchAttempts).toBe(1);
  // Draft còn nguyên — không có gì xoá ô người dùng vừa gõ.
  await expect(priceInput).toHaveValue('8.888.000');

  const retry = dialog.locator('[data-metric="order-panel-retry"]');
  await expect(retry).toBeVisible();
  await retry.click();
  await expect(status).toHaveAttribute('data-state', 'saved');
  expect(patchAttempts).toBe(2);
});

test('409 REVISION_CONFLICT: giữ draft, hiện hai lựa chọn, gửi lại thành công', async ({ page }) => {
  let capturedRevision = null;
  let capturedPeriodRevision = null;
  page.on('response', async (response) => {
    if (response.request().method() !== 'GET') return;
    if (!/\/api\/v1\/orders\//.test(response.url())) return;
    const body = await response.json().catch(() => null);
    if (body && body.order_revision) {
      capturedRevision = body.order_revision;
      capturedPeriodRevision = body.period_revision;
    }
  });

  const dialog = await openPanel(page, SIMPLE_ORDER);
  expect(capturedRevision).toBeTruthy();

  // Phân biệt lượt gửi bằng CHÍNH `idempotency_key` trong body, không bằng
  // một cờ "đã gửi chưa" đếm số lần route được gọi — mã đầu tiên luôn được
  // giả xung đột (kể cả nếu vì lý do gì nó gửi lại), còn một mã KHÁC (lần
  // GỬI LẠI của `app.js` sau conflict luôn sinh mã mới) đi thẳng tới máy
  // chủ thật. Bền hơn một cờ boolean phụ thuộc thứ tự.
  let fakedKey = null;
  await page.route('**/api/v1/orders/**', async (route) => {
    const request = route.request();
    if (request.method() !== 'PATCH') return route.continue();
    const key = request.postDataJSON()?.idempotency_key;
    if (fakedKey !== null && key !== fakedKey) return route.continue();
    fakedKey = key;
    await route.fulfill({
      status: 409,
      contentType: 'application/json',
      body: JSON.stringify({
        error: {
          code: 'REVISION_CONFLICT',
          message: 'Đơn này đã được thay đổi từ lúc bạn mở nó.',
          request_id: 'test-trace-conflict',
          order_revision: capturedRevision,
          period_revision: capturedPeriodRevision,
          current: { lines: [], employee_value: '' },
        },
      }),
    });
  });

  const firstLine = dialog.locator('[data-metric="order-panel-line"]').first();
  const priceInput = firstLine.locator('[data-metric="order-panel-price"]');
  await priceInput.fill('9.999.000');
  const reason = dialog.locator('[data-metric="order-panel-reason"]');
  if (await reason.isVisible()) await reason.fill('kiểm tra conflict — Playwright');
  await dialog.locator('[data-metric="order-panel-save"]').click();

  const status = dialog.locator('[data-metric="order-panel-status"]');
  await expect(status).toHaveAttribute('data-state', 'conflict');
  await expect(priceInput).toHaveValue('9.999.000'); // draft KHÔNG bị xoá
  await expect(dialog.locator('[data-metric="order-panel-conflict-reload"]'))
    .toBeVisible();

  const retry = dialog.locator('[data-metric="order-panel-retry"]');
  await expect(retry).toHaveText('GỬI LẠI VỚI BẢN MỚI');
  await retry.click();
  await expect(status).toHaveAttribute('data-state', 'saved');
});

test('response GET cũ của một đơn đã đóng KHÔNG ghi đè panel đang mở của đơn khác', async ({ page }) => {
  let delayed = false;
  await page.route('**/api/v1/orders/**', async (route) => {
    const request = route.request();
    const url = request.url();
    if (request.method() === 'GET' && url.includes(SIMPLE_ORDER) && !delayed) {
      delayed = true;
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
    return route.continue();
  });

  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  // KHÔNG chờ load xong (GET của A đang bị trì hoãn) — đóng ngay rồi mở B.
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-metric="order-panel"]')).toBeHidden();

  const dialogB = await openPanel(page, OTHER_ORDER);
  await expect(dialogB.locator('[data-metric="order-panel-title"]'))
    .toHaveText(OTHER_ORDER);

  // Chờ đủ lâu để response CŨ (A) chắc chắn đã về — panel vẫn phải hiện B.
  await page.waitForTimeout(1500);
  const dialogs = page.locator('[data-metric="order-panel"]');
  await expect(dialogs).toHaveCount(1);
  await expect(dialogs.locator('[data-metric="order-panel-title"]'))
    .toHaveText(OTHER_ORDER);
});
