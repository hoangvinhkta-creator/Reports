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

/* Mọi DOM đã dựng trong test đang chạy.
 *
 * Vì sao là một sổ chung thay vì để từng test tự kiểm: một `TypeError`
 * trong `app.js` phát ra `jsdomError`, và nếu không ai đọc nó thì test
 * xanh một cách vô nghĩa. Bắt từng test nhớ gọi một hàm kiểm là bảo đảm
 * sẽ có test quên — nên `installErrorGuard()` gắn MỘT `afterEach` cho cả
 * file, và không test nào phải nhớ gì.
 */
const booted = [];

/**
 * Gắn `afterEach` kiểm lỗi jsdom cho cả file test. Gọi MỘT lần ở đầu file.
 */
export function installErrorGuard(afterEach) {
  afterEach(() => {
    const failures = [];
    for (const app of booted) {
      if (app.jsdomErrors.length) {
        failures.push(...app.jsdomErrors);
      }
    }
    booted.length = 0;
    if (failures.length) {
      throw new Error("app.js gây lỗi jsdom ngoài dự kiến:\n  "
        + failures.join("\n  "));
    }
  });
}

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
  <!-- f-idem: form KHAI data-idempotent.
     Route /kiem/idempotent-gia-lap là GIẢ LẬP, có chủ đích: hôm nay KHÔNG
     template production nào khai data-idempotent, vì không route HTML nào
     đọc idempotency_key. Trỏ form này vào một route thật sẽ ngụ ý route ấy
     chống lặp được — đúng lời hứa sai mà P1-5 gỡ đi. Xem
     tests/test_p1_5_html_form_idempotency.py.
     LƯU Ý CÚ PHÁP: cả chuỗi PAGE này là một template literal của
     JavaScript, nên KHÔNG được dùng dấu backtick ở đây (kể cả trong một
     comment HTML) — nó kết thúc chuỗi giữa câu và cho một SyntaxError ở
     một dòng chẳng liên quan gì. Dấu tiếng Việt thì vô hại. -->
  <form id="f-idem" method="post" action="/kiem/idempotent-gia-lap"
        data-idempotent data-loading-label="Đang lưu…">
    <input name="gia_nhap" value="123">
    <button type="submit">XONG</button>
  </form>
  <!-- f-plain: hình dạng THẬT của mọi form mutation HTML hôm nay — không
     khai data-idempotent, nên không gửi mã và không mọc nút THỬ LẠI. -->
  <form id="f-plain" method="post" action="/kinh-doanh/nhan-vien/sua-bh"
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
export function boot({ html = PAGE, routes = {}, abortController = true }
    = {}) {
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
  /* Lỗi jsdom KHÔNG được bỏ qua im lặng: một `TypeError` trong `app.js`
   * sẽ làm mọi test xanh một cách vô nghĩa. Nhưng cũng KHÔNG `throw` ở
   * đây — một ngoại lệ ném ra từ trong listener của `EventEmitter` không
   * quay về được test đã gọi, nó đi thẳng lên uncaught và có thể bị nuốt.
   *
   * Nên chúng được GOM lại, và `assertNoUnexpectedErrors()` là chỗ test
   * đọc chúng. Bản trước `throw` ở đây, và vì thế nó vừa không dừng được
   * test vừa che mất lỗi thật. */
  virtualConsole.on("jsdomError", (error) => {
    const message = String(error && error.message);
    if (message.includes("Not implemented: navigation")) {
      navigations.push(lastIntent.url || "(không rõ)");
      return;
    }
    jsdomErrors.push(message);
  });
  // Bỏ hẳn tiếng ồn của `console.error` mà jsdom chuyển tiếp — nhưng
  // KHÔNG bỏ `jsdomError` ở trên.
  virtualConsole.on("error", () => {});

  const lastIntent = { url: null };
  /* Lỗi jsdom KHÔNG phải navigation. Xem handler `jsdomError` ở trên. */
  const jsdomErrors = [];
  /* Vị trí cuộn mà `app.js` yêu cầu. jsdom KHÔNG hiện thực
   * `window.scrollTo`, nên mỗi lần `swapContent()` gọi nó, jsdom phát một
   * `jsdomError` — và bản trước của bộ khung này để lỗi đó lẫn vào cùng
   * kênh với lỗi thật. Stub nó ở đây làm hai việc: dọn kênh lỗi, và cho
   * test đọc được `app.js` đã cố giữ vị trí cuộn nào. */
  const scrollCalls = [];
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

  window.scrollTo = (x, y) => { scrollCalls.push([x, y]); };

  /* `abortController: false` — mô phỏng browser KHÔNG có
   * `AbortController` (Safari cũ, và `app.js` khai rõ nó hỗ trợ đường đó:
   * `if (typeof AbortController === "function")`).
   *
   * Đây là cấu hình DUY NHẤT mà bộ đếm tuần tự phải tự làm hết việc —
   * với `AbortController`, một lượt GET bị vượt luôn bị abort trước khi
   * response về, nên nhánh "response cũ vừa về" không chạy tới. Muốn kiểm
   * bộ đếm thì phải tắt abort. */
  if (!abortController) delete window.AbortController;

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
    /* `reject` + `delayMs` = một request THẤT BẠI CHẬM. Cần thiết cho các
     * test `P2-2`: mệnh đề "nút của form B vẫn khoá trong khi request B
     * còn bay" chỉ kiểm được nếu B vẫn đang bay lúc A thất bại, và một
     * `reject` tức thì làm B xong trước A. */
    if (spec.reject && !spec.delayMs) return Promise.reject(spec.reject);
    if (!spec.delayMs) return Promise.resolve(response);
    return new Promise((resolve, reject) => {
      const timer = window.setTimeout(
        () => (spec.reject ? reject(spec.reject) : resolve(response)),
        spec.delayMs);
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

  const app = {
    dom, window, document: window.document, calls, navigations, pushes,
    bodyEvents, jsdomErrors, scrollCalls,
  };
  booted.push(app);
  return app;
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
