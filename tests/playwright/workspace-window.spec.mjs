// `UI-04` — bảng kê phân trang theo BH và GIỮ NGÂN SÁCH DOM, trên fixture
// 5.000 dòng và trình duyệt THẬT.
//
// Vì sao phải là 5.000 dòng: mọi mệnh đề ở đây xanh với mọi kiến trúc trên
// 90 dòng, kể cả kiến trúc dựng 5.002 hàng `<tr>` cho một màn hình chừng
// bốn mươi hàng — đúng kiến trúc mà `UI-04` tồn tại để thay. Máy chủ riêng
// cho bộ này (`SCALE_URL`, xem `playwright.config.mjs`) để 5.000 dòng không
// làm mọi bài kiểm khác chậm đi mà không thêm mệnh đề nào cho chúng.
import { test, expect } from '@playwright/test';
import { SCALE_URL, SCALE_LINES } from '../../playwright.config.mjs';

const PAGE_URL = `${SCALE_URL}/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh`;

// `ROW_BUDGET` của `app.js`. Cộng thêm một khối BH: `trimToBudget` gỡ theo
// NHÓM, không theo hàng lẻ (gỡ nửa một BH để lại `rowspan` trỏ vào những
// hàng không còn tồn tại), nên số hàng còn lại có thể nhỉnh hơn ngưỡng đúng
// bằng phần đuôi của nhóm cuối cùng bị gỡ.
const ROW_BUDGET = 300;
const GROUP_SLACK = 8;

function dataRows(page) {
  return page.locator('table.sheet-table tr[data-order]');
}

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

test('trang đầu dựng ở SERVER và đã nằm trong ngân sách DOM', async ({ page }) => {
  // Server chỉ gửi MỘT trang: cả sheet có hàng nghìn dòng, DOM có hàng trăm.
  const rows = await dataRows(page).count();
  expect(rows).toBeGreaterThan(0);
  expect(rows).toBeLessThanOrEqual(ROW_BUDGET);

  const table = page.locator('table.sheet-table');
  const totalLines = Number(await table.getAttribute('data-total-lines'));
  expect(totalLines).toBeGreaterThan(rows * 5);
  // Và còn trang kế để đi tiếp.
  expect(await table.getAttribute('data-next-cursor')).not.toBe('');
});

test('cuộn/tải nhiều trang: số <tr> trong DOM LUÔN dưới ngân sách', async ({ page }) => {
  await page.evaluate(() => { window.__probe = 'con-song'; });
  const seen = [];
  for (let i = 0; i < 8; i += 1) {
    const more = page.locator('[data-metric="workspace-more"]');
    if (await more.count() === 0) break;
    const before = await dataRows(page).count();
    await more.click();
    // Trang mới đã về khi số hàng đổi HOẶC đường XEM TIẾP đã hết.
    await expect
      .poll(async () => (await dataRows(page).count()) !== before
        || (await page.locator('[data-metric="workspace-more"]').count()) === 0,
        { timeout: 10_000 })
      .toBe(true);
    const now = await dataRows(page).count();
    seen.push(now);
    expect(now).toBeLessThanOrEqual(ROW_BUDGET + GROUP_SLACK);
  }
  // Thật sự đã tải nhiều trang, không phải dừng ngay ở trang đầu.
  expect(seen.length).toBeGreaterThanOrEqual(4);
  // Và không lần nào tải lại trang.
  expect(await page.evaluate(() => window.__probe)).toBe('con-song');
});

test('một BH nhiều dòng KHÔNG bị cắt giữa hai trang', async ({ page }) => {
  // Đi hết năm trang rồi kiểm CẤU TRÚC: trong bảng, mọi hàng của cùng một
  // BH phải đứng LIỀN NHAU, và hàng đầu của mỗi khối phải là hàng mang
  // thông tin cấp BH (`bh-head`, nơi `rowspan` bắt đầu). Một BH bị cắt ở
  // ranh giới trang sẽ vi phạm một trong hai điều đó.
  for (let i = 0; i < 5; i += 1) {
    const more = page.locator('[data-metric="workspace-more"]');
    if (await more.count() === 0) break;
    const before = await dataRows(page).count();
    await more.click();
    await expect
      .poll(async () => (await dataRows(page).count()) !== before
        || (await page.locator('[data-metric="workspace-more"]').count()) === 0,
        { timeout: 10_000 })
      .toBe(true);
  }

  const report = await page.evaluate(() => {
    var rows = document.querySelectorAll('table.sheet-table tr[data-order]');
    var blocks = [];
    var current = null;
    for (var i = 0; i < rows.length; i++) {
      var key = rows[i].getAttribute('data-order');
      if (!current || current.key !== key) {
        current = { key: key, head: rows[i].getAttribute('data-metric'), rows: 0 };
        blocks.push(current);
      }
      current.rows += 1;
    }
    var keys = blocks.map(function (b) { return b.key; });
    return {
      blocks: blocks.length,
      // Một mã BH xuất hiện ở HAI khối rời nhau = nó đã bị cắt.
      split: keys.length !== new Set(keys).size,
      headless: blocks.filter(function (b) { return b.head !== 'bh-head'; })
        .map(function (b) { return b.key; }),
      multi: blocks.filter(function (b) { return b.rows > 1; }).length,
    };
  });
  expect(report.split).toBe(false);
  expect(report.headless).toEqual([]);
  // Và fixture thật sự có BH nhiều dòng trong cửa sổ đang xem — nếu không,
  // mệnh đề trên không chứng minh được gì.
  expect(report.multi).toBeGreaterThan(0);
});

test('TỔNG hiển thị là số của TOÀN KỲ, không phải của phần đã tải',
  async ({ page }) => {
    const totals = page.locator('tr[data-metric="sheet-totals"]');
    const before = await totals.locator('[data-metric="totals-sell"]').innerText();
    const kpiBefore = await page.locator('[data-metric="sales_revenue"]').innerText();
    const linesBefore = await page.locator('[data-metric="lines"]').innerText();

    // Con số "số dòng của sheet" trên đầu trang nói về CẢ kỳ, và nó lớn hơn
    // hẳn số hàng đang nằm trong DOM.
    expect(Number(linesBefore.replace(/\D/g, '')))
      .toBeGreaterThan(await dataRows(page).count());

    await page.click('[data-metric="workspace-more"]');
    await expect.poll(async () =>
      (await page.locator('[data-metric="workspace-more"]').count()) === 0
      || (await dataRows(page).count()) > 0, { timeout: 10_000 }).toBe(true);

    // Tải thêm một trang KHÔNG làm tổng nhúc nhích: nó là số server tính
    // trên cả kỳ, không phải phép cộng các dòng đang hiển thị.
    await expect(totals.locator('[data-metric="totals-sell"]')).toHaveText(before);
    await expect(page.locator('[data-metric="sales_revenue"]')).toHaveText(kpiBefore);
    await expect(page.locator('[data-metric="lines"]')).toHaveText(linesBefore);
  });

test('không JavaScript: XEM TIẾP là liên kết THẬT, mọi dòng vẫn tới được',
  async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(PAGE_URL);

    const before = await page.locator(
      'table.sheet-table tr[data-order]').first().getAttribute('data-order');
    const href = await page.locator('[data-metric="workspace-more"]')
      .getAttribute('href');
    expect(href).toContain('tu=');

    await page.goto(new URL(href, PAGE_URL).toString());
    const after = await page.locator(
      'table.sheet-table tr[data-order]').first().getAttribute('data-order');
    // Trang kế là một trang KHÁC, dựng bởi server, không cần một dòng JS nào.
    expect(after).not.toBe(before);
    expect(await page.locator('table.sheet-table tr[data-order]').count())
      .toBeGreaterThan(0);
    await context.close();
  });

test('fixture đúng là 5.000 dòng — ngân sách nói về một khối lượng thật',
  async ({ page }) => {
    // Sheet `noi-thanh` là sheet NHÓM: cả hai nhân viên của fixture đều
    // thuộc `NOI_THANH`, nên nó giữ trọn 5.000 dòng. Mệnh đề: ngân sách DOM
    // (300 hàng) đang nói về một khối lượng lớn hơn nó hơn mười sáu lần.
    const total = Number(await page.locator('table.sheet-table')
      .getAttribute('data-total-lines'));
    expect(total).toBe(SCALE_LINES);
    expect(total).toBeGreaterThan(ROW_BUDGET * 10);
  });

test('gỡ nhóm cũ KHÔNG làm mất vị trí cuộn của người đang xem', async ({ page }) => {
  // Tải đủ trang để `trimToBudget` thật sự phải gỡ — nếu không, bài này
  // xanh mà không kiểm gì.
  for (let i = 0; i < 3; i += 1) {
    const more = page.locator('[data-metric="workspace-more"]');
    if (await more.count() === 0) break;
    const before = await dataRows(page).count();
    await more.click();
    await expect
      .poll(async () => (await dataRows(page).count()) !== before
        || (await page.locator('[data-metric="workspace-more"]').count()) === 0,
        { timeout: 10_000 })
      .toBe(true);
  }
  expect(await dataRows(page).count()).toBeGreaterThan(ROW_BUDGET / 2);

  // Cuộn xuống gần cuối, rồi lấy hàng ĐANG NẰM TRONG KHUNG NHÌN làm mốc:
  // mệnh đề nói về chỗ người dùng đang NHÌN, không về một hàng bất kỳ.
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight - 900));
  const key = await page.evaluate(() => {
    var rows = document.querySelectorAll('table.sheet-table tr[data-order]');
    for (var i = 0; i < rows.length; i++) {
      var box = rows[i].getBoundingClientRect();
      if (box.top > 40 && box.bottom < window.innerHeight) {
        return rows[i].getAttribute('data-order');
      }
    }
    return null;
  });
  expect(key).not.toBeNull();
  const marker = page.locator(
    `table.sheet-table tr[data-order="${key}"]`).first();
  const topBefore = (await marker.boundingBox()).y;

  const more = page.locator('[data-metric="workspace-more"]');
  const rowsBefore = await dataRows(page).count();
  await more.click();
  await expect
    .poll(async () => (await dataRows(page).count()) !== rowsBefore,
      { timeout: 10_000 })
    .toBe(true);

  // Hàng mốc VẪN CÒN (nó thuộc phần mới, không phải phần bị gỡ) và nó vẫn
  // ở gần đúng chỗ cũ trên màn hình: `trimToBudget` đo chiều cao vừa gỡ và
  // trả lại đúng bằng `scrollBy`.
  const after = page.locator(
    `table.sheet-table tr[data-order="${key}"]`).first();
  await expect(after).toBeAttached();
  const topAfter = (await after.boundingBox()).y;
  expect(Math.abs(topAfter - topBefore)).toBeLessThan(4);
});
