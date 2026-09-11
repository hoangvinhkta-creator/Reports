// `UI-05` — GHIM tooltip biểu đồ và phân rã theo nhân viên, trên trình
// duyệt THẬT.
//
// Mệnh đề nền: đường RÊ CHUỘT cũ không được phá. `UI-05` mở rộng chính
// `.rev-tooltip` mà `app.js` đã dựng (hover), không thêm một phần tử thứ
// hai — hai phần tử cho cùng một thông tin là hai chỗ để chúng nói lệch
// nhau.
import { test, expect } from '@playwright/test';

const PAGE_URL = '/kinh-doanh/phan-tich?ky=2026-09&muc=ngay';
const CHART = '#bieu-do-doanh-thu-r6';
const POINT = `${CHART} .rev-line-point[data-metric="chart-bar"][data-key]`;

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
  await expect(page.locator(POINT).first()).toBeAttached();
});

test('rê chuột vẫn hiện tooltip cũ, và nó KHÔNG bị ghim', async ({ page }) => {
  await page.locator(POINT).nth(10).hover();
  const tip = page.locator('.rev-tooltip');
  await expect(tip).toBeVisible();
  await expect(tip).not.toHaveClass(/is-pinned/);

  // Rời con trỏ ⟹ tooltip biến mất, đúng hành vi trước `UI-05`.
  await page.mouse.move(2, 2);
  await expect(tip).toBeHidden();
});

test('bấm một điểm GHIM tooltip: con trỏ rời đi nó vẫn còn', async ({ page }) => {
  const point = page.locator(POINT).nth(10);
  const key = await point.getAttribute('data-key');
  await point.click();

  const tip = page.locator('.rev-tooltip');
  await expect(tip).toHaveClass(/is-pinned/);
  // GIÁ TRỊ CƠ BẢN có ngay, từ dữ liệu đã nằm sẵn trong trình duyệt —
  // không phải chờ một request nào.
  await expect(tip.locator('[data-metric="chart-pin-label"]')).toContainText(
    `${Number(key.slice(8, 10))}`.padStart(2, '0'));

  await page.mouse.move(2, 2);
  await expect(tip).toBeVisible();
  await expect(tip).toHaveClass(/is-pinned/);

  // Phân rã tải NỀN vào đúng popover đang ghim.
  await expect(tip.locator('[data-metric="chart-pin-summary"]')).toBeVisible();
  await expect(tip.locator('[data-metric="chart-pin-row"]').first()).toBeVisible();
});

test('bấm điểm KHÁC thay nội dung NGAY TRONG popover đang ghim', async ({ page }) => {
  const first = page.locator(POINT).nth(10);
  const second = page.locator(POINT).nth(14);
  await first.click();
  const tip = page.locator('.rev-tooltip');
  await expect(tip.locator('[data-metric="chart-pin-summary"]')).toBeVisible();
  const before = await tip.locator('[data-metric="chart-pin-label"]').innerText();
  // Giữ HANDLE của chính phần tử tooltip: mệnh đề là "không đóng-mở lại",
  // và cách duy nhất chứng minh điều đó là phần tử vẫn LÀ phần tử ấy.
  const handle = await page.evaluateHandle(
    () => document.querySelector('.rev-tooltip'));

  await second.click();
  await expect(tip.locator('[data-metric="chart-pin-label"]')).not.toHaveText(before);
  await expect(tip).toHaveClass(/is-pinned/);
  expect(await page.evaluate(
    (el) => el === document.querySelector('.rev-tooltip'), handle)).toBe(true);
  // Và popover không hề bị ẩn đi giữa chừng.
  await expect(tip).toBeVisible();
});

test('phân rã của điểm CŨ về muộn thì bị BỎ QUA', async ({ page, request }) => {
  const first = page.locator(POINT).nth(10);
  const second = page.locator(POINT).nth(14);
  const firstKey = await first.getAttribute('data-key');
  const secondKey = await second.getAttribute('data-key');

  // Số THẬT của hai mốc, đọc thẳng từ chính route mà trang gọi — để mệnh
  // đề dưới nói về nội dung, không chỉ về "có đổi hay không".
  const firstData = await (await request.get(
    `/api/v1/analytics/chart-breakdown?ky=2026-09&muc=ngay&moc=${firstKey}`)).json();
  const secondData = await (await request.get(
    `/api/v1/analytics/chart-breakdown?ky=2026-09&muc=ngay&moc=${secondKey}`)).json();
  expect(firstData.revenue.text_kvnd).not.toBe(secondData.revenue.text_kvnd);

  // Phân rã của mốc THỨ NHẤT về CHẬM 1,5 giây; mốc thứ hai về ngay.
  await page.route('**/api/v1/analytics/chart-breakdown*', async (route) => {
    const moc = new URL(route.request().url()).searchParams.get('moc');
    if (moc === firstKey) await new Promise((r) => setTimeout(r, 1500));
    await route.continue();
  });

  await first.click();
  await second.click();

  const tip = page.locator('.rev-tooltip');
  const summary = tip.locator('[data-metric="chart-pin-summary"]');
  await expect(summary).toContainText(secondData.revenue.text_kvnd);

  // Đợi QUA mốc 1,5 giây: response cũ đã về, và nó KHÔNG được vẽ đè.
  await page.waitForTimeout(2000);
  await expect(summary).toContainText(secondData.revenue.text_kvnd);
  await expect(summary).not.toContainText(firstData.revenue.text_kvnd);
});

test('bàn phím: Tab tới điểm, Enter ghim, mũi tên đổi nội dung tại chỗ',
  async ({ page }) => {
    const point = page.locator(POINT).nth(10);
    // `app.js` gắn `tabindex`/`role` — không phải template: không có
    // JavaScript thì bấm vào điểm không làm gì, và một phần tử nhận Tab mà
    // không có hành vi là một cái bẫy cho người dùng bàn phím.
    await expect(point).toHaveAttribute('tabindex', '0');
    await expect(point).toHaveAttribute('role', 'button');

    await point.focus();
    await page.keyboard.press('Enter');
    const tip = page.locator('.rev-tooltip');
    await expect(tip).toHaveClass(/is-pinned/);
    const before = await tip.locator('[data-metric="chart-pin-label"]').innerText();

    await page.keyboard.press('ArrowRight');
    // Focus đi sang điểm kế, và popover ĐANG GHIM đổi nội dung theo.
    await expect(tip.locator('[data-metric="chart-pin-label"]'))
      .not.toHaveText(before);
    await expect(tip).toHaveClass(/is-pinned/);
    expect(await page.evaluate(
      () => document.activeElement.getAttribute('data-metric')))
      .toBe('chart-bar');

    // Escape bỏ ghim và trả focus về đúng điểm đang chọn.
    await page.keyboard.press('Escape');
    await expect(tip).toBeHidden();
    expect(await page.evaluate(
      () => document.activeElement.getAttribute('data-metric')))
      .toBe('chart-bar');
  });

test('bấm lại ĐÚNG điểm đang ghim thì bỏ ghim', async ({ page }) => {
  const point = page.locator(POINT).nth(10);
  await point.click();
  const tip = page.locator('.rev-tooltip');
  await expect(tip).toHaveClass(/is-pinned/);
  await point.click();
  await expect(tip).toBeHidden();
});
