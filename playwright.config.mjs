// `UI-01`/`UI-02` — cấu hình Playwright cho bộ kiểm browser THẬT của panel
// sửa đơn (`tests/playwright/*.spec.mjs`). Đây là lớp QA mà `tests/browser/`
// (jsdom, xem `harness.mjs`) khai rõ mình KHÔNG làm được: thời gian parse/
// render/paint, vị trí cuộn thật, bẫy focus thật của `<dialog>`.
//
// Trình duyệt Chromium đã được cài sẵn trong môi trường chạy CI/session này
// (`/opt/pw-browsers/chromium`, biến `PLAYWRIGHT_BROWSERS_PATH` +
// `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` chặn `npm install` tải lại) — cấu
// hình dưới đây trỏ THẲNG vào đó thay vì để Playwright tự tìm theo version
// nó pin, đúng hướng dẫn môi trường. Một môi trường khác không có sẵn
// đường dẫn đó có thể ghi đè bằng biến `PLAYWRIGHT_CHROMIUM_PATH`, hoặc bỏ
// hẳn tuỳ chọn này rồi chạy `npx playwright install chromium` một lần.
import { defineConfig } from '@playwright/test';

const PORT = Number(process.env.REPORTS_PLAYWRIGHT_PORT || 8931);
const BASE_URL = `http://127.0.0.1:${PORT}`;
// `UI-04` — máy chủ THỨ HAI, 5.000 dòng. Ngân sách DOM chỉ có nghĩa trên một
// khối lượng đại diện: trên 90 dòng (máy chủ chính) mọi kiến trúc đều xanh,
// kể cả kiến trúc dựng 5.002 hàng `<tr>` cho một màn hình bốn mươi hàng.
// Hai máy chủ chứ không một: fixture 5.000 dòng làm mọi bài kiểm khác chậm
// đi mà không thêm một mệnh đề nào cho chúng.
const SCALE_PORT = Number(process.env.REPORTS_PLAYWRIGHT_SCALE_PORT || 8932);
export const SCALE_URL = `http://127.0.0.1:${SCALE_PORT}`;
export const SCALE_LINES = 5000;
const CHROMIUM_PATH =
  process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const PYTHON = process.env.REPORTS_PYTHON ||
  (process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python');

export default defineConfig({
  testDir: 'tests/playwright',
  testMatch: '*.spec.mjs',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  // Fixture server dùng MỘT engine SQLite trong tiến trình, không đa luồng
  // (`fixture_server.py`) — chạy test song song sẽ đua nhau trên cùng một
  // đơn. Bộ này nhỏ (dưới 15 test), một worker là đủ nhanh và không flake.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: BASE_URL,
    launchOptions: CHROMIUM_PATH ? { executablePath: CHROMIUM_PATH } : {},
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `${PYTHON} tests/playwright/fixture_server.py --port ${PORT}`,
      url: `${BASE_URL}/kinh-doanh/nhan-vien?ky=2026-09`,
      // `UI-03` GHI thật vào máy chủ fixture (phân loại, loại dòng). Dùng
      // lại một máy chủ còn sống từ lần chạy trước ⟹ lần chạy thứ hai
      // thấy dòng ĐÃ phân loại và các mệnh đề im lặng biến mất. Mỗi lần
      // chạy phải khởi động một máy chủ SẠCH.
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `${PYTHON} tests/playwright/fixture_server.py` +
        ` --port ${SCALE_PORT} --lines ${SCALE_LINES} --no-extras`,
      url: `${SCALE_URL}/kinh-doanh/nhan-vien?ky=2026-09`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
