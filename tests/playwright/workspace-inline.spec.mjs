// `UI-03` — phân loại / loại / khôi phục NGAY TRONG bảng kê, trên trình
// duyệt THẬT: không tải lại trang, không dựng lại `#app-content`, và một
// quyết định phân loại chạm NHIỀU dòng thì CẢ NHIỀU dòng ấy được vá.
//
// Bổ sung cho `tests/browser/` (jsdom): những mệnh đề dưới đây cần một
// engine layout/focus thật (toạ độ neo của hộp xác nhận, thứ tự hàng sau
// khi khôi phục) mà jsdom khai rõ mình không làm được.
import { test, expect } from '@playwright/test';

const PAGE_URL = '/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh';

// Ba BH dựng riêng trong `fixture_server.py`, dùng CHUNG một câu tên hàng
// chưa phân loại — xem `SHARED_IDENTITY_ORDERS` ở đó.
const SHARED = ['BH78001', 'BH78002', 'BH78003'];

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
  await page.evaluate(() => { window.__probe = 'con-song'; });
});

/** Trang KHÔNG tải lại thật: biến toàn cục đặt ở `beforeEach` còn nguyên. */
async function stillTheSamePage(page) {
  expect(await page.evaluate(() => window.__probe)).toBe('con-song');
}

test('mở bảng chọn phân loại không dựng lại bảng kê', async ({ page }) => {
  const contentHandle = await page.evaluateHandle(
    () => document.getElementById('app-content'));
  const rowsBefore = await page.locator('table.sheet-table tr[data-order]').count();

  await page.click(`tr[data-order="${SHARED[0]}"] [data-metric="identity-open"]`);
  await expect(page.locator('[data-metric="identify-panel"]')).toBeVisible();

  await stillTheSamePage(page);
  // `#app-content` vẫn là ĐÚNG phần tử DOM từ trước khi bấm, và bảng kê
  // không hề bị dựng lại — đúng lý do `UI-03` tồn tại.
  expect(await page.evaluate(
    (el) => el === document.getElementById('app-content'), contentHandle)).toBe(true);
  expect(await page.locator('table.sheet-table tr[data-order]').count())
    .toBe(rowsBefore);
  // Popover được NEO (toạ độ do JS tính), không phải một khối đứng đầu trang.
  await expect(page.locator('[data-metric="identify-panel"]'))
    .toHaveClass(/is-anchored/);
});

// Bài này đứng TRƯỚC bài phân loại có chủ ý: nó đọc một dòng CHƯA
// phân loại, và bài dưới ghi quyết định phân loại cho chính dòng ấy.
test('không JavaScript: nút phân loại/loại vẫn là đường HTTP thật', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(PAGE_URL);

  // Lối vào phân loại là một `<a href>` THẬT, dẫn tới đúng trang cũ.
  const href = await page.locator(
    `tr[data-order="${SHARED[0]}"] [data-metric="identity-open"]`)
    .getAttribute('href');
  expect(href).toContain('phan-loai=1');
  await page.goto(href);
  await expect(page.locator('[data-metric="identify-panel"]')).toBeVisible();
  // Và nó là form POST thật, không phải một nút do JS dựng.
  const action = await page.locator(
    '[data-metric="identify-out-of-catalog-confirm"]')
    .evaluate((el) => el.form.getAttribute('action'));
  expect(action).toContain('/kinh-doanh/nhan-vien/ngoai-bang');
  await context.close();
});

test('một quyết định phân loại vá TẤT CẢ các dòng dùng chung tên hàng', async ({ page }) => {
  // Trước: cả ba BH đều mở được bảng chọn (tức cả ba đang "Chưa phân loại").
  for (const order of SHARED) {
    await expect(page.locator(
      `tr[data-order="${order}"] [data-metric="identity-open"]`)).toHaveCount(1);
  }
  // Bảng chọn nói ra phạm vi THẬT trước khi ghi.
  await page.click(`tr[data-order="${SHARED[0]}"] [data-metric="identity-open"]`);
  await expect(page.locator('[data-metric="identify-scope"]'))
    .toContainText(`${SHARED.length}`);
  for (const order of SHARED) {
    await expect(page.locator('[data-metric="identify-scope"]')).toContainText(order);
  }

  await page.click('[data-metric="identify-out-of-catalog-confirm"]');

  // Câu server trả về hiện ra, popover tự đóng.
  await expect(page.locator('[data-metric="saved"]')).toBeVisible();
  await expect(page.locator('[data-metric="identify-panel"]')).toHaveCount(0);

  // MỆNH ĐỀ CHÍNH: cả ba dòng đổi trạng thái, không riêng dòng vừa bấm.
  for (const order of SHARED) {
    // Lối vào phân loại VẪN CÒN có chủ ý — R2 §4.3 gọi nó là đường NỐI LẠI
    // Tracking khi mặt hàng xuất hiện trên bảng giá về sau. Thứ phải đổi là
    // TRẠNG THÁI của dòng, và nó đổi ở CẢ BA BH.
    await expect(page.locator(
      `tr[data-order="${order}"] td[data-metric="line-product"]`))
      .toHaveAttribute('data-classification', 'OUT_OF_CATALOG');
  }
  await stillTheSamePage(page);
});

test('loại một dòng: hộp xác nhận nói hậu quả TRƯỚC, rồi dòng biến mất không tải lại',
  async ({ page }) => {
    const row = page.locator('tr[data-order] [data-metric="line-exclude"]').first();
    const order = await row.evaluate(
      (el) => el.closest('tr').getAttribute('data-order'));
    const productKey = await row.evaluate(
      (el) => el.closest('tr').getAttribute('data-product-key'));
    const occurrence = await row.evaluate(
      (el) => el.closest('tr').getAttribute('data-occurrence-index'));
    // ĐỦ BA PHẦN. Fixture có dòng LẶP (cùng BH, cùng mặt hàng,
    // `occurrence_index` tăng), nên hai phần khớp hai hàng khác nhau.
    const rowSelector = `tr[data-order="${order}"]` +
      `[data-product-key="${productKey}"][data-occurrence-index="${occurrence}"]`;
    await expect(page.locator(rowSelector)).toHaveCount(1);

    await row.click();
    // Hộp xác nhận neo cạnh nút, và nó nói hậu quả TRƯỚC khi ghi — đúng
    // những gạch đầu dòng mà `EXCLUDE_CONFIRM_POINTS` (server) viết.
    const box = page.locator('[data-metric="line-confirm"]');
    await expect(box).toBeVisible();
    await expect(box).toHaveClass(/is-anchored/);
    await expect(box.locator('[data-metric="line-confirm-point"]').first())
      .toContainText('doanh thu');
    // Chưa ghi gì: dòng vẫn còn nguyên trên bảng.
    await expect(page.locator(rowSelector)).toHaveCount(1);

    await box.locator('[data-metric="line-confirm-ok"]').click();

    await expect(page.locator(rowSelector)).toHaveCount(0);
    await expect(page.locator('[data-metric="line-confirm"]')).toHaveCount(0);
    // Nó nằm trong danh sách "đã loại", với đường khôi phục.
    await expect(page.locator(
      `[data-metric="excluded-row"][data-order="${order}"]`)).toHaveCount(1);
    await stillTheSamePage(page);

    // Trả máy chủ fixture về nguyên trạng trước khi rời bài này. Các bài
    // dưới chọn dòng theo VỊ TRÍ (`.first()`), nên một dòng bị loại sót lại
    // sẽ làm chúng chọn nhầm dòng — và bài đỏ khi ấy không nói về lỗi thật
    // nào của sản phẩm. Máy chủ fixture là một tiến trình dùng chung cho cả
    // file (`workers: 1`), nên dọn dẹp là việc của chính bài vừa ghi.
    await page.click(`[data-metric="excluded-row"][data-order="${order}"] ` +
                     '[data-metric="line-restore"]');
    await page.click('[data-metric="line-confirm-ok"]');
    await expect(page.locator(rowSelector)).toHaveCount(1);
  });

test('HỦY trong hộp xác nhận không ghi gì', async ({ page }) => {
  const excludedBefore = await page.locator('[data-metric="excluded-row"]').count();
  const row = page.locator('tr[data-order] [data-metric="line-exclude"]').first();
  await row.click();
  await page.click('[data-metric="line-confirm-cancel"]');
  await expect(page.locator('[data-metric="line-confirm"]')).toHaveCount(0);
  expect(await page.locator('[data-metric="excluded-row"]').count())
    .toBe(excludedBefore);
  await expect(page.locator('[data-metric="saved"]')).toHaveCount(0);
});

test('khôi phục đưa dòng trở lại ĐÚNG khối BH của nó', async ({ page }) => {
  const trash = page.locator('tr[data-order] [data-metric="line-exclude"]').first();
  const order = await trash.evaluate(
    (el) => el.closest('tr').getAttribute('data-order'));
  const productKey = await trash.evaluate(
    (el) => el.closest('tr').getAttribute('data-product-key'));
  const occurrence = await trash.evaluate(
    (el) => el.closest('tr').getAttribute('data-occurrence-index'));
  const rowSelector = `tr[data-order="${order}"]` +
    `[data-product-key="${productKey}"][data-occurrence-index="${occurrence}"]`;

  await trash.click();
  await page.click('[data-metric="line-confirm-ok"]');
  await expect(page.locator(rowSelector)).toHaveCount(0);

  await page.click(`[data-metric="excluded-row"][data-order="${order}"] ` +
                   '[data-metric="line-restore"]');
  const box = page.locator('[data-metric="line-confirm"]');
  await expect(box).toBeVisible();
  await box.locator('[data-metric="line-confirm-ok"]').click();

  await expect(page.locator(rowSelector)).toHaveCount(1);
  await expect(page.locator(
    `[data-metric="excluded-row"][data-order="${order}"]`)).toHaveCount(0);
  // Dòng trở lại ĐÚNG khối của nó: mọi hàng mang `data-order` ấy đứng liền
  // nhau, và hàng đầu vẫn là hàng mang thông tin cấp BH (`bh-head`).
  const classes = await page.locator(`tr[data-order="${order}"]`).first()
    .getAttribute('data-metric');
  expect(classes).toBe('bh-head');
  await stillTheSamePage(page);
});

test('lỗi mạng: hộp xác nhận Ở LẠI, KHÔNG tự gửi lại', async ({ page }) => {
  let attempts = 0;
  await page.route('**/kinh-doanh/nhan-vien/loai-dong', async (route) => {
    attempts += 1;
    await route.abort('failed');
  });
  const excludedBefore = await page.locator('[data-metric="excluded-row"]').count();
  const trash = page.locator('tr[data-order] [data-metric="line-exclude"]').first();
  await trash.click();
  await page.click('[data-metric="line-confirm-ok"]');

  const box = page.locator('[data-metric="line-confirm"]');
  await expect(box).toBeVisible();
  await expect(box.locator('[data-metric="line-confirm-error"]')).toBeVisible();
  // Nút bật lại được — người dùng quyết định bấm lần nữa, không phải JS.
  await expect(box.locator('[data-metric="line-confirm-ok"]')).toBeEnabled();
  // Và không có lần gửi thứ hai nào tự xảy ra.
  await page.waitForTimeout(500);
  expect(attempts).toBe(1);
  // Và không dòng nào bị loại: một lần ghi thất bại không được để lại dấu.
  expect(await page.locator('[data-metric="excluded-row"]').count())
    .toBe(excludedBefore);
});
