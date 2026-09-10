/*
 * `P1-6` — bộ khung nạp `app.js` THẬT vào một DOM thật (jsdom).
 *
 * Vì sao thư mục này tồn tại. Review độc lập chỉ ra rằng ba file trong
 * repo (`scripts/stab01_baseline.py`, `tests/test_stab02_download_
 * contract.py` hai chỗ) trỏ tới `tests/browser/` — một thư mục KHÔNG
 * TỒN TẠI. Và test duy nhất chạm `app.js` là một regex trên mã nguồn:
 * nó so vị trí chuỗi `isHtmlFragment` với `response.text()`, tức nó kiểm
 * một quy ước mà chính implementation tự đặt ra, không kiểm hành vi.
 *
 * Nó cũng chỉ ra hai lỗi THẬT mà chỉ một DOM thật tìm được:
 *
 *     `Content-Type` rỗng ⟹ byte `PK…` vào thẳng `#app-content`  (P2-1)
 *     hai form chậm cùng chờ, A lỗi ⟹ nút của B bị bật lại        (P2-2)
 *
 * ## Vì sao jsdom, không Playwright
 *
 * Cái cần kiểm ở đây là LOGIC của `app.js`: response nào được đưa vào
 * DOM, response nào bị chặn, response cũ có ghi đè response mới không,
 * nút nào được bật lại. Không mệnh đề nào trong đó cần một engine layout
 * hay một tiến trình browser thật.
 *
 * Điều jsdom KHÔNG kiểm được, và nó được nói ra ở đây thay vì để người
 * đọc số tưởng đã có: thời gian parse/render/paint, vị trí cuộn thật,
 * hành vi tải file thật của trình duyệt. Những thứ đó cần Playwright và
 * chúng thuộc phần QA của `UI-02` — chưa làm.
 *
 * ## Cách chạy
 *
 *     node --test tests/browser/
 *
 * `node --test` là test runner có sẵn của Node 18+; không thêm một
 * framework nào vào repo cho bốn file.
 */

import { readFileSync } from "node:fs";
import { JSDOM, VirtualConsole } from "jsdom";

const APP_JS = new URL("../../app/web/static/js/app.js", import.meta.url);

/** HTML của một trang đã tải THẬT: có wrapper, có bảng, có form. */
export const PAGE = `
<header class="tp-header"><button id="btnTheme"></button></header>
<nav class="ncc-tabs"><a class="ncc-tab" href="/kinh-doanh">Báo cáo</a></nav>
<main class="tp-main" id="app-content">
  <a id="loc-a" href="/kinh-doanh?loc=a">Lọc A</a>
  <a id="loc-b" href="/kinh-doanh?loc=b">Lọc B</a>
  <a id="loc-c" href="/kinh-doanh?loc=c">Lọc C</a>
  <a id="tai-excel" href="/kinh-doanh/xuat-excel?ky=2026-09" download>Tải Excel</a>
  <a id="tai-la" href="/bao-cao/khong-khai-type">Tải không khai type</a>
  <form id="f-idem" method="post" action="/kinh-doanh/nhan-vien/sua-bh"
        data-idempotent data-loading-label="Đang lưu…">
    <input name="gia_nhap" value="123">
    <button type="submit">XONG</button>
  </form>
  <form id="f-plain" method="post" action="/upload"
        data-loading-label="Đang chạy…">
    <button type="submit">CHẠY</button>
  </form>
</main>`;

/**
 * Dựng một DOM có `app.js` đã nạp, và một `fetch` giả điều khiển được.
 *
 * `routes` là `{đường dẫn hoặc tiền tố: () => response}`. Mỗi response
 * là `{status, headers, body, delayMs}` — `delayMs` là thứ làm test
 * "response cũ về sau" viết được mà không phụ thuộc thời gian thật.
 */
export function boot({ html = PAGE, routes = {} } = {}) {
  const calls = [];
  const navigations = [];

  /* Điều hướng THẬT được ghi qua `VirtualConsole`, không bằng cách thay
   * `window.location`.
   *
   * `window.location` của jsdom KHÔNG configurable, nên
   * `Object.defineProperty` trên nó ném "Cannot redefine property". Điều
   * jsdom LÀM khi mã gán `location.href` là phát một `jsdomError` mang
   * chữ "Not implemented: navigation" — và đó chính là tín hiệu ta cần:
   * nó nói app.js ĐÃ điều hướng thật, và jsdom chỉ không tải URL đó.
   *
   * URL đích không có trong thông điệp lỗi, nên `navigations` ghi lại
   * URL của lượt fetch/lượt bấm gần nhất mà `app.js` đang xử lý — xem
   * `noteNavigation()`. Đủ để trả lời câu hỏi của mọi test ở đây: "có
   * điều hướng thật không, và tới route nào".
   */
  const virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (error) => {
    const message = String(error && error.message);
    if (message.includes("Not implemented: navigation")) {
      navigations.push(lastIntent.url || "(không rõ)");
      return;
    }
    // Lỗi khác của jsdom KHÔNG được im lặng: một `TypeError` trong
    // `app.js` sẽ làm test xanh một cách vô nghĩa nếu ta bỏ qua nó.
    throw error;
  });
  // Bỏ hẳn tiếng ồn của `console.error` mà jsdom chuyển tiếp — nhưng
  // KHÔNG bỏ `jsdomError` ở trên.
  virtualConsole.on("error", () => {});

  const lastIntent = { url: null };
  /* Ghi lại số phận BODY của từng response giả: `read` khi `.text()`
   * được gọi, `cancel` khi `body.cancel()` được gọi. Đây là cách duy
   * nhất một test kiểm được `STAB-02` ("chặn TRƯỚC khi đọc body") và
   * `P2-6` ("huỷ luồng thay vì đọc rồi vứt") mà không đoán. */
  const bodyEvents = [];

  const dom = new JSDOM(`<!doctype html><html><body>${html}</body></html>`, {
    url: "https://reports.example/kinh-doanh",
    runScripts: "outside-only",
    pretendToBeVisual: true,
    virtualConsole,
  });
  const { window } = dom;

  /* Ghi lại ý định điều hướng của mỗi cú bấm: `app.js` gọi
   * `window.location.href = link.href` cho link tải file, và đó là lượt
   * duy nhất không đi qua `fetch`. */
  window.document.addEventListener("click", (event) => {
    const link = event.target.closest && event.target.closest("a[href]");
    if (link) lastIntent.url = link.href;
  }, true);

  window.fetch = (url, opts = {}) => {
    const path = String(url);
    lastIntent.url = path;
    calls.push({ url: path, method: (opts.method || "GET").toUpperCase(),
                 body: opts.body, headers: opts.headers || {},
                 signal: opts.signal });
    /* So khớp trên PHẦN ĐƯỜNG DẪN, không trên URL đầy đủ: `app.js` gọi
     * `fetch(link.href)` và `link.href` là URL tuyệt đối, trong khi
     * `routes` được viết bằng đường dẫn cho dễ đọc. So thẳng hai chuỗi
     * sẽ không khớp gì và mọi test trông như "không có route giả". */
    let relative = path;
    try {
      relative = new URL(path, "https://reports.example").pathname;
    } catch (e) { /* không phải URL: dùng nguyên chuỗi */ }
    const key = Object.keys(routes).find(
      (candidate) => relative === candidate || relative.startsWith(candidate)
        || path === candidate || path.startsWith(candidate));
    const make = key ? routes[key] : null;
    if (!make) {
      return Promise.reject(new Error("không có route giả: " + path));
    }
    const spec = make(path, opts) || {};
    const response = fakeResponse(spec, path, bodyEvents);
    if (spec.reject) return Promise.reject(spec.reject);
    if (!spec.delayMs) return Promise.resolve(response);
    return new Promise((resolve, reject) => {
      const timer = window.setTimeout(() => resolve(response), spec.delayMs);
      if (opts.signal) {
        opts.signal.addEventListener("abort", () => {
          window.clearTimeout(timer);
          const err = new Error("aborted");
          err.name = "AbortError";
          reject(err);
        });
      }
    });
  };

  /* `history.pushState` của jsdom hoạt động, nhưng ta thay `location` ở
   * trên nên nó không còn đồng bộ. Ghi lại các lần đẩy để test kiểm. */
  const pushes = [];
  window.history.pushState = (state, title, url) => { pushes.push(String(url)); };

  window.eval(readFileSync(APP_JS, "utf8"));
  window.document.dispatchEvent(new window.Event("DOMContentLoaded"));

  return { dom, window, document: window.document, calls, navigations,
           pushes, bodyEvents };
}

function fakeResponse(spec, path, bodyEvents) {
  const headers = new Map(
    Object.entries(spec.headers || { "Content-Type": "text/html; charset=utf-8" })
      .map(([name, value]) => [name.toLowerCase(), value]));
  const body = spec.body === undefined ? "<p>ok</p>" : spec.body;
  let bodyUsed = false;
  const cancelled = { value: false };
  return {
    ok: spec.status === undefined ? true : spec.status < 400,
    status: spec.status === undefined ? 200 : spec.status,
    url: spec.url || "https://reports.example" + path.replace(
      /^https:\/\/reports\.example/, ""),
    headers: { get: (name) => {
      const value = headers.get(String(name).toLowerCase());
      return value === undefined ? null : value;
    } },
    get bodyUsed() { return bodyUsed; },
    body: {
      cancel() {
        cancelled.value = true;
        bodyEvents.push({ path, kind: "cancel" });
        return Promise.resolve();
      },
    },
    get cancelled() { return cancelled.value; },
    text() {
      bodyUsed = true;
      bodyEvents.push({ path, kind: "read" });
      return Promise.resolve(body);
    },
  };
}

/** Chờ hết các microtask + timer đang treo. */
export function settle(window, ms = 0) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

/** HTML mảnh HỢP LỆ (không wrapper) — xem `STAB-04`. */
export function fragment(text) {
  return { headers: { "Content-Type": "text/html; charset=utf-8" },
           body: `<p data-marker="${text}">${text}</p>` };
}
