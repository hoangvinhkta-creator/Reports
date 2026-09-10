// `UI-01`/`UI-02` — mở/đóng panel sửa đơn trên trình duyệt THẬT: không tải
// lại trang, giữ vị trí cuộn, hình dạng đúng theo số dòng, Escape + focus,
// và Back/Forward khôi phục đúng trạng thái. Bổ sung cho `tests/browser/`
// (jsdom) — những mệnh đề này cần một engine layout/focus thật, jsdom
// không làm được (xem chú thích đầu `tests/browser/harness.mjs`).
import { test, expect } from '@playwright/test';

const SIMPLE_ORDER = 'BH70001'; // 2 dòng — hình dạng popover
const MULTILINE_ORDER = 'BH79999'; // 5 dòng — hình dạng side panel
const PAGE_URL = '/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh';

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

test('bấm Sửa mở panel tại chỗ — không tải lại trang, không đổi #app-content', async ({ page }) => {
  await page.evaluate(() => { window.__probe = 'con-song'; });
  const contentHandle = await page.evaluateHandle(
    () => document.getElementById('app-content'));

  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog).toBeVisible();
  await expect(dialog.locator('[data-metric="order-panel-title"]'))
    .toHaveText(SIMPLE_ORDER);

  // Trang KHÔNG tải lại thật: biến toàn cục còn nguyên, và #app-content vẫn
  // là ĐÚNG phần tử DOM từ trước khi bấm (so sánh handle, không so nội dung).
  expect(await page.evaluate(() => window.__probe)).toBe('con-song');
  const sameContent = await page.evaluate(
    (el) => el === document.getElementById('app-content'), contentHandle);
  expect(sameContent).toBe(true);

  // URL query giữ nguyên (?ky=&sheet=), chỉ hash mang trạng thái panel —
  // đúng thiết kế "deep-link qua hash, không qua `?sua=`" của `app.js`.
  const url = new URL(page.url());
  expect(url.hash).toBe(`#sua=${SIMPLE_ORDER}`);
  expect(url.searchParams.get('sua')).toBeNull();
});

test('mở panel không đổi vị trí cuộn của trang', async ({ page }) => {
  await page.evaluate(() => window.scrollTo(0, 600));
  const before = await page.evaluate(() => window.scrollY);
  expect(before).toBeGreaterThan(0);

  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  await expect(page.locator('[data-metric="order-panel"]')).toBeVisible();

  const after = await page.evaluate(() => window.scrollY);
  expect(after).toBe(before);
});

test('đơn ít dòng mở dạng popover; đơn nhiều dòng mở dạng side panel', async ({ page }) => {
  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  const simpleDialog = page.locator('[data-metric="order-panel"]');
  await expect(simpleDialog.locator('[data-metric="order-panel-line"]').first())
    .toBeVisible();
  await expect(simpleDialog).toHaveClass(/tp-order-panel--popover/);
  await expect(simpleDialog).not.toHaveClass(/tp-order-panel--side/);
  await page.keyboard.press('Escape');
  await expect(simpleDialog).toBeHidden();

  await page.click(`[data-metric="bh-edit"][data-order="${MULTILINE_ORDER}"]`);
  const bigDialog = page.locator('[data-metric="order-panel"]');
  await expect(bigDialog.locator('[data-metric="order-panel-line"]').first())
    .toBeVisible();
  const lineCount = await bigDialog.locator('[data-metric="order-panel-line"]').count();
  expect(lineCount).toBeGreaterThan(3);
  await expect(bigDialog).toHaveClass(/tp-order-panel--side/);
});

test('Escape đóng panel và trả focus về đúng nút Sửa đã mở nó', async ({ page }) => {
  const opener = page.locator(
    `[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  await opener.click();
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();
});

test('nút Đóng trong panel cũng trả focus về nút Sửa', async ({ page }) => {
  const opener = page.locator(
    `[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  await opener.click();
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog).toBeVisible();
  await dialog.locator('[data-metric="order-panel-close"]').click();
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();
});

test('bẫy focus: Tab trong panel không thoát ra ngoài trang', async ({ page }) => {
  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog.locator('[data-metric="order-panel-line"]').first())
    .toBeVisible();

  for (let i = 0; i < 12; i += 1) {
    await page.keyboard.press('Tab');
    const where = await page.evaluate((dlg) => {
      const el = document.activeElement;
      if (dlg.contains(el)) return 'inside';
      // Chromium dừng MỘT nhịp Tab ở `<body>` khi đi hết focusable CUỐI của
      // một `<dialog>` modal trước khi lượt Tab kế tiếp vòng lại đầu dialog
      // — đây là hành vi trình duyệt khi đóng vai trò "không còn ứng viên
      // TIẾP theo", không phải focus thật sự thoát ra một phần tử khác của
      // trang (mọi phần tử khác đều `inert` khi dialog đang modal). Chấp
      // nhận `<body>` là một trạng thái trung chuyển hợp lệ; bất kỳ phần tử
      // NÀO KHÁC (link/nút thật của trang phía sau) mới là thoát bẫy thật.
      return el === document.body ? 'body' : 'escaped:' + el.tagName;
    }, await dialog.elementHandle());
    expect(where, `lần Tab thứ ${i + 1} thoát khỏi panel`).not.toMatch(/^escaped/);
  }
});

test('Back đóng panel, Forward mở lại đúng panel đó', async ({ page }) => {
  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`#sua=${SIMPLE_ORDER}$`));

  await page.goBack();
  await expect(dialog).toBeHidden();
  const url = new URL(page.url());
  expect(url.hash).toBe('');

  await page.goForward();
  const reopened = page.locator('[data-metric="order-panel"]');
  await expect(reopened).toBeVisible();
  await expect(reopened.locator('[data-metric="order-panel-title"]'))
    .toHaveText(SIMPLE_ORDER);
});

test('đóng một panel rồi mở panel khác — Back từ panel thứ hai về trang không panel', async ({ page }) => {
  await page.click(`[data-metric="bh-edit"][data-order="${SIMPLE_ORDER}"]`);
  await expect(page.locator('[data-metric="order-panel"]')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-metric="order-panel"]')).toBeHidden();

  await page.click(`[data-metric="bh-edit"][data-order="${MULTILINE_ORDER}"]`);
  const dialog = page.locator('[data-metric="order-panel"]');
  await expect(dialog.locator('[data-metric="order-panel-title"]'))
    .toHaveText(MULTILINE_ORDER);

  await page.goBack(); // đóng panel MULTILINE_ORDER — entry của SIMPLE_ORDER
  // đã bị `pushState` của lần mở thứ hai cắt bỏ (đúng hành vi history chuẩn).
  await expect(page.locator('[data-metric="order-panel"]')).toBeHidden();
  const url = new URL(page.url());
  expect(url.hash).toBe('');
});
