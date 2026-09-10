/*
 * `STAB-03`/`STAB-04`/`STAB-05` + `P1-5`/`P2-2` — hành vi điều hướng và
 * mutation, kiểm trên DOM THẬT.
 *
 * Những mệnh đề ở đây không kiểm được bằng regex trên mã nguồn, và một
 * trong số chúng (`P2-2`) là lỗi mà review tìm ra bằng chính cách này.
 *
 * Hai form trong fixture (xem `PAGE` trong `harness.mjs`) KHÁC NHAU có
 * chủ đích, và cái khác biệt ấy chính là `P1-5`:
 *
 *     `f-idem`   khai `data-idempotent` → gửi `idempotency_key`, mọc nút
 *                THỬ LẠI. Route của nó (`/kiem/idempotent-gia-lap`) là
 *                GIẢ LẬP: hôm nay KHÔNG template production nào khai
 *                `data-idempotent`, vì không route HTML nào đọc mã.
 *     `f-plain`  hình dạng THẬT của mọi form mutation HTML hôm nay →
 *                không gửi mã, không mọc nút THỬ LẠI.
 *
 * Cửa chặn "một template khai `data-idempotent` mà route không đọc mã"
 * nằm ở `tests/test_p1_5_html_form_idempotency.py`, không ở đây: nó là
 * một mệnh đề về server, và một DOM giả không kiểm được nó.
 */

import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { boot, settle, fragment, installErrorGuard } from "./harness.mjs";

installErrorGuard(afterEach);

const IDEM_ROUTE = "/kiem/idempotent-gia-lap";
const PLAIN_ROUTE = "/kinh-doanh/nhan-vien/sua-bh";

function countWrappers(document) {
  return document.querySelectorAll("#app-content").length;
}

function submit(app, form) {
  form.dispatchEvent(new app.window.Event(
    "submit", { bubbles: true, cancelable: true }));
}

function posts(app) {
  return app.calls.filter((call) => call.method === "POST");
}

// --- STAB-04 -------------------------------------------------------------

test("STAB-04: ba lần điều hướng liên tiếp giữ ĐÚNG MỘT #app-content",
  async () => {
    const app = boot({
      routes: { "/kinh-doanh": (path) => fragment(path) },
    });
    assert.equal(countWrappers(app.document), 1, "trạng thái đầu");

    for (const id of ["loc-a", "loc-b", "loc-c"]) {
      const first = app.document.getElementById(id);
      if (first) first.click();
      await settle(app.window);
      // Sau lần swap đầu, các link cũ đã biến khỏi DOM — dựng lại một
      // link mới trong mảnh để bấm tiếp.
      const host = app.document.getElementById("app-content");
      const link = app.document.createElement("a");
      link.id = "tiep";
      link.href = "/kinh-doanh?buoc=" + id;
      host.appendChild(link);
      app.document.getElementById("tiep").click();
      await settle(app.window);
      assert.equal(countWrappers(app.document), 1,
        `sau khi thay mảnh ${id}: có ${countWrappers(app.document)} wrapper`);
    }
  });

test("STAB-04: mảnh mang wrapper VẪN tạo phần tử thứ hai… và đó là lỗi",
  async () => {
    /* Test này ghi lại RANH GIỚI của lớp client: nếu server trả một mảnh
     * mang theo `<main id="app-content">` (tức hợp đồng `STAB-04` bị vi
     * phạm ở phía server), `innerHTML` sẽ tạo phần tử thứ hai và
     * `getElementById` sẽ trả về phần tử NGOÀI.
     *
     * Nó KHÔNG khẳng định client tự chữa được — client không chữa được,
     * và giả vờ ngược lại sẽ làm người đọc tưởng hợp đồng phía server là
     * tuỳ chọn. Cửa thật là `tests/test_stab02_download_contract.py`. */
    const app = boot({
      routes: {
        "/kinh-doanh": () => ({
          headers: { "Content-Type": "text/html" },
          body: '<main class="tp-main" id="app-content"><p>lồng</p></main>',
        }),
      },
    });
    app.document.getElementById("loc-a").click();
    await settle(app.window);
    assert.equal(countWrappers(app.document), 2,
      "mảnh mang wrapper phải tạo ra 2 phần tử — nếu không, test này đang "
      + "nói sai về cơ chế và cửa phía server không còn cần thiết");
  });

// --- STAB-05 -------------------------------------------------------------

test("STAB-05: A→B→C, mạng trả C,B,A ⟹ màn hình hiện C", async () => {
  /* Đây là nghiệm thu nguyên văn của brief: "đổi filter nhanh A → B → C
   * luôn hiển thị C, kể cả khi response B trả về cuối". */
  const delays = { a: 60, b: 40, c: 5 };
  const app = boot({
    routes: {
      "/kinh-doanh": (path) => {
        const which = /loc=([abc])/.exec(path);
        const tag = which ? which[1] : "x";
        return { ...fragment(tag), delayMs: delays[tag] || 0 };
      },
    },
  });

  app.document.getElementById("loc-a").click();
  app.document.getElementById("loc-b").click();
  app.document.getElementById("loc-c").click();
  await settle(app.window, 200);

  const markers = [...app.document.querySelectorAll("[data-marker]")]
    .map((node) => node.dataset.marker);
  assert.deepEqual(markers, ["c"],
    `màn hình hiện ${JSON.stringify(markers)} thay vì C`);
  assert.equal(countWrappers(app.document), 1);
});

test("STAB-05: KHÔNG có AbortController, BỘ ĐẾM vẫn phải chặn response cũ",
  async () => {
    /* Test trên KHÔNG chứng minh được bộ đếm làm việc: với
     * `AbortController`, lượt A và B bị abort trước khi response về, nên
     * `isLatest()` không bao giờ bị hỏi về một response cũ ĐÃ VỀ. Mà theo
     * chính docstring của `STAB-05` trong `app.js`, abort chỉ giảm lưu
     * lượng — cái quyết định "response nào được ghi" là bộ đếm.
     *
     * Tắt `AbortController` là cách duy nhất buộc bộ đếm tự làm hết việc:
     * cả ba response ĐỀU về, và chỉ C được phép swap. */
    const delays = { a: 90, b: 60, c: 5 };
    const app = boot({
      abortController: false,
      routes: {
        "/kinh-doanh": (path) => {
          const which = /loc=([abc])/.exec(path);
          const tag = which ? which[1] : "x";
          return { ...fragment(tag), delayMs: delays[tag] || 0 };
        },
      },
    });

    app.document.getElementById("loc-a").click();
    app.document.getElementById("loc-b").click();
    app.document.getElementById("loc-c").click();
    await settle(app.window, 300);

    assert.equal(app.calls.length, 3, "không đủ ba lượt để nói về bộ đếm");
    assert.deepEqual(app.calls.filter((call) => call.signal), [],
      "vẫn có AbortSignal — cấu hình không tắt được abort, test rỗng nghĩa");
    /* Cả ba response ĐÃ về và ĐÃ được đọc: nếu không, bộ đếm chưa bị hỏi
     * về một response cũ nào và test này không kiểm được gì. */
    assert.equal(
      app.bodyEvents.filter((event) => event.kind === "read").length, 3,
      "có response chưa về — bộ đếm chưa bị hỏi về response cũ");

    const markers = [...app.document.querySelectorAll("[data-marker]")]
      .map((node) => node.dataset.marker);
    assert.deepEqual(markers, ["c"],
      `response cũ đã ghi đè: màn hình hiện ${JSON.stringify(markers)}`);
  });

test("STAB-05: lượt fetch cũ được abort", async () => {
  const app = boot({
    routes: {
      "/kinh-doanh": (path) => ({
        ...fragment(path), delayMs: /loc=c/.test(path) ? 5 : 80,
      }),
    },
  });
  app.document.getElementById("loc-a").click();
  app.document.getElementById("loc-c").click();
  await settle(app.window, 200);
  const signals = app.calls.map((call) => call.signal).filter(Boolean);
  assert.equal(signals.length, 2, "GET phải mang AbortSignal");
  assert.equal(signals[0].aborted, true, "lượt A không bị abort");
});

test("STAB-05: mutation KHÔNG mang AbortSignal", async () => {
  /* Huỷ một POST đang bay không huỷ được việc server đã ghi — nó chỉ làm
   * ta không biết kết quả, đúng tình huống `STAB-03` tồn tại để đóng. */
  const app = boot({
    routes: { [IDEM_ROUTE]: () => fragment("da-luu") },
  });
  submit(app, app.document.getElementById("f-idem"));
  await settle(app.window, 50);
  assert.equal(posts(app).length, 1);
  assert.equal(posts(app)[0].signal, undefined, "POST mang AbortSignal");
});

test("STAB-05: swap giữ lại vị trí cuộn, không nhảy về đầu trang",
  async () => {
    /* "Không làm bảng nhảy vị trí, không mất scroll" là nghiệm thu của
     * brief. `window.scrollY` trong jsdom luôn là 0, nên điều kiểm được ở
     * đây là `app.js` CÓ gọi `scrollTo` với vị trí đọc TRƯỚC khi thay
     * `innerHTML` — chứ không để trình duyệt tự về đầu trang.
     *
     * Vị trí cuộn THẬT sau khi layout chạy lại cần một engine layout
     * thật; nó thuộc phần QA Playwright của `UI-02` và chưa làm. Nói ra ở
     * đây thay vì để con số này trông như một bằng chứng đủ. */
    const app = boot({ routes: { "/kinh-doanh": () => fragment("da-swap") } });
    app.document.getElementById("loc-a").click();
    await settle(app.window, 50);
    assert.ok(app.document.querySelector('[data-marker="da-swap"]'),
      "chưa swap — test chưa nói được gì về cuộn");
    assert.deepEqual(app.scrollCalls, [[0, 0]],
      `app.js không giữ vị trí cuộn: scrollTo=${JSON.stringify(app.scrollCalls)}`);
  });

// --- STAB-03 -------------------------------------------------------------

test("STAB-03: fetch lỗi KHÔNG tự gửi lại mutation", async () => {
  const app = boot({
    routes: { [IDEM_ROUTE]: () => ({ reject: new Error("mạng đứt") }) },
  });
  const form = app.document.getElementById("f-idem");
  let nativeSubmits = 0;
  form.submit = () => { nativeSubmits += 1; };

  submit(app, form);
  await settle(app.window, 50);

  assert.equal(nativeSubmits, 0,
    "form.submit() tự động đã chạy — đúng lỗi STAB-03");
  assert.equal(posts(app).length, 1, "mutation được gửi nhiều hơn một lần");
  // Draft còn nguyên: DOM không bị thay.
  assert.equal(form.querySelector("input[name=gia_nhap]").value, "123");
});

test("STAB-03: form có data-idempotent giữ NGUYÊN mã qua lần thử lại",
  async () => {
    const app = boot({
      routes: { [IDEM_ROUTE]: () => ({ reject: new Error("mạng đứt") }) },
    });
    const form = app.document.getElementById("f-idem");
    form.submit = () => {};
    submit(app, form);
    await settle(app.window, 50);

    const retry = app.document.querySelector("[data-save-retry]");
    assert.ok(retry, "không có nút THỬ LẠI cho form data-idempotent");
    retry.click();
    await settle(app.window, 50);

    const sent = posts(app);
    assert.equal(sent.length, 2, "nút THỬ LẠI không gửi lại");
    const keys = sent.map((call) => call.body.get("idempotency_key"));
    assert.ok(keys[0], "mutation không mang idempotency_key");
    assert.equal(keys[0], keys[1],
      "lần thử lại sinh mã MỚI — server sẽ coi nó là một quyết định mới "
      + "và ghi lần thứ hai");
  });

test("STAB-03: sau khi server ĐÃ xác nhận, lần gửi sau mang mã KHÁC",
  async () => {
    /* Mặt còn lại của mệnh đề trên, và nó cũng quan trọng: nếu mã được
     * giữ sau một lần lưu THÀNH CÔNG, chính cơ chế chống lặp sẽ nuốt
     * quyết định kế tiếp của người dùng và không ghi gì. Xem
     * `clearRequestId()`. */
    const app = boot({
      routes: { [IDEM_ROUTE]: () => fragment("da-luu") },
    });
    const form = app.document.getElementById("f-idem");
    submit(app, form);
    await settle(app.window, 50);
    // Lần lưu thành công đã thay `#app-content`; dựng lại form để gửi lần hai.
    const again = app.document.createElement("form");
    again.method = "post";
    again.action = IDEM_ROUTE;
    again.setAttribute("data-idempotent", "");
    app.document.getElementById("app-content").appendChild(again);
    // Cùng ĐỐI TƯỢNG form thì phải mất mã cũ — kiểm trên chính form đầu.
    assert.equal(form.dataset.requestId, undefined,
      "mã của lần ghi đã xác nhận vẫn còn trên form — lần gửi kế tiếp sẽ "
      + "bị server coi là bản sao và không được ghi");
    submit(app, again);
    await settle(app.window, 50);
    const keys = posts(app).map((call) => call.body.get("idempotency_key"));
    assert.equal(keys.length, 2);
    assert.notEqual(keys[0], keys[1], `hai lần ghi dùng cùng mã: ${keys[0]}`);
  });

test("P1-5: form KHÔNG khai data-idempotent thì KHÔNG gửi mã, KHÔNG THỬ LẠI",
  async () => {
    /* Review chỉ ra rằng bản trước gắn `request_id` vào MỌI form POST
     * trong khi KHÔNG route HTML nào đọc nó — nên câu "server nhận ra và
     * không ghi hai lần" là một lời hứa không có gì đỡ. `f-plain` là
     * hình dạng thật của mọi form mutation HTML hôm nay. */
    const app = boot({
      routes: { [PLAIN_ROUTE]: () => ({ reject: new Error("mạng đứt") }) },
    });
    const form = app.document.getElementById("f-plain");
    form.submit = () => {};
    submit(app, form);
    await settle(app.window, 50);

    const sent = posts(app);
    assert.equal(sent.length, 1);
    assert.equal(sent[0].body.get("idempotency_key"), null,
      "gửi mã tới một route không đọc nó");
    assert.equal(app.document.querySelector("[data-save-retry]"), null,
      "mọc nút THỬ LẠI cho một route không chống lặp được");
    // Nhưng người dùng VẪN được nói cho biết, và draft vẫn còn.
    const status = form.querySelector("[data-save-status]");
    assert.ok(status, "không có chỗ nào nói cho người dùng biết");
    assert.ok(status.textContent.includes("Chưa xác nhận"), status.textContent);
    assert.ok(status.textContent.includes("tải lại trang"),
      "phải nói rõ phải tự kiểm tra — xem P1-5");
    assert.ok(!/không ghi hai lần|không ghi trùng/.test(status.textContent),
      "hứa 'không ghi hai lần' cho một route server KHÔNG chống lặp — "
      + "đúng lỗi P1-5");
  });

// --- P2-2 ----------------------------------------------------------------

test("P2-2: A lỗi chỉ bật lại nút của A; nút B khoá tới khi B xong",
  async () => {
    /* Đây là lỗi review tìm ra bằng chính bộ kiểm này: bản trước gọi
     * `restorePendingButtons()` không tham số, và nó bật lại nút của MỌI
     * form đang chờ — kể cả form mà request của nó vẫn đang bay. Bấm nút
     * đó là gửi trùng.
     *
     * Năm mệnh đề, đúng thứ tự thời gian, và cả năm đều bị kiểm:
     *
     *     1. A và B cùng gửi ⟹ cả hai nút bị khoá
     *     2. A thất bại      ⟹ nút A được bật lại
     *     3.                     nút B VẪN khoá
     *     4. bấm nút B lúc đó ⟹ KHÔNG có POST thứ hai của B
     *     5. B hoàn tất      ⟹ nút B thôi bị khoá (ở đây: rời DOM cùng
     *                            `#app-content` bị thay sau khi lưu xong)
     */
    const app = boot({
      routes: {
        [IDEM_ROUTE]: () => ({ reject: new Error("mạng đứt") }),
        [PLAIN_ROUTE]: () => ({ ...fragment("b-xong"), delayMs: 120 }),
      },
    });
    const a = app.document.getElementById("f-idem");
    const b = app.document.getElementById("f-plain");
    a.submit = () => {};
    b.submit = () => {};
    const buttonA = a.querySelector("button");
    const buttonB = b.querySelector("button");

    // (1) cả hai cùng gửi, cả hai nút bị khoá.
    submit(app, b);
    submit(app, a);
    assert.equal(buttonB.disabled, true, "nút form B không bị khoá khi gửi");
    assert.equal(buttonA.disabled, true, "nút form A không bị khoá khi gửi");

    await settle(app.window, 50);   // A đã lỗi, B CÒN ĐANG BAY

    // (2) nút A được bật lại — nếu không, người dùng thấy một dòng "chưa
    // xác nhận" cạnh một cái nút đã chết.
    assert.equal(buttonA.disabled, false,
      "nút của form vừa lỗi không được bật lại");
    // (3) nút B vẫn khoá.
    assert.equal(buttonB.disabled, true,
      "nút của form B đã được bật lại trong khi request của nó còn bay — "
      + "bấm nó là gửi trùng B (đúng lỗi P2-2)");
    assert.equal(buttonB.textContent.includes("Đang chạy"), true,
      "nhãn 'đang chạy' của B bị xoá dù B chưa xong");

    // (4) và vì nó còn khoá, bấm nó KHÔNG gửi được lần thứ hai.
    const before = posts(app).length;
    buttonB.click();
    await settle(app.window, 10);
    assert.equal(posts(app).length, before,
      "gửi được lần thứ hai của B trong lúc lần thứ nhất còn bay");
    assert.equal(posts(app).filter((call) => call.url.includes(PLAIN_ROUTE))
      .length, 1, "B bị gửi trùng");

    // (5) B hoàn tất: `#app-content` bị thay, nút cũ rời DOM cùng nó.
    await settle(app.window, 200);
    assert.ok(app.document.querySelector('[data-marker="b-xong"]'),
      "B chưa hoàn tất — mệnh đề (5) chưa được kiểm");
    assert.equal(buttonB.isConnected, false,
      "nút B còn trong DOM sau khi B xong — nếu nó còn thì nó phải được "
      + "bật lại, và không nhánh nào làm việc đó");
  });

test("P2-2: nút NGOÀI form (thuộc tính form=…) cũng thuộc đúng form của nó",
  async () => {
    /* Vì sao có test riêng: `restorePendingButtons()` phân loại nút bằng
     * `btn.form`, không bằng `closest("form")`. Với một nút đứng NGOÀI
     * form và trỏ vào form bằng `form="…"` — đúng hình dạng của một nút
     * hành động trong ô cuối một hàng bảng — `closest("form")` trả `null`
     * và mọi nút như thế sẽ bị coi là "của form khác" mãi mãi, tức khoá
     * vĩnh viễn. Test này giữ `btn.form` đứng đúng chỗ nó. */
    const app = boot({
      routes: {
        [IDEM_ROUTE]: () => ({ reject: new Error("mạng đứt") }),
        // B thất bại CHẬM: nó phải CÒN ĐANG BAY lúc A thất bại, nếu không
        // test chỉ kiểm được rằng B tự phục hồi nút của chính nó.
        [PLAIN_ROUTE]: () => ({ reject: new Error("mạng đứt"), delayMs: 120 }),
      },
    });
    const a = app.document.getElementById("f-idem");
    const b = app.document.getElementById("f-plain");
    a.submit = () => {};
    b.submit = () => {};

    const outside = app.document.createElement("button");
    outside.type = "submit";
    outside.setAttribute("form", "f-plain");
    outside.textContent = "LƯU HÀNG NÀY";
    app.document.getElementById("app-content").appendChild(outside);
    assert.equal(outside.form, b, "fixture sai: nút ngoài không trỏ vào B");

    outside.click();                       // B gửi qua nút NGOÀI
    assert.equal(outside.disabled, true, "nút ngoài không bị khoá khi gửi");

    submit(app, a);                        // A gửi rồi lỗi
    await settle(app.window, 50);
    assert.equal(outside.disabled, true,
      "lỗi của A đã bật lại nút NGOÀI của B — đúng lỗi P2-2, ở dạng khó "
      + "thấy hơn");

    await settle(app.window, 200);         // giờ B cũng lỗi
    assert.equal(outside.disabled, false,
      "nút ngoài của B không được bật lại sau khi B lỗi — `btn.form` "
      + "không nhận ra nó thuộc B, và nút bị khoá vĩnh viễn");
  });

// --- popstate / GET thất bại --------------------------------------------

test("popstate tải lại qua fetch và KHÔNG đẩy thêm history", async () => {
  const app = boot({
    routes: { "/kinh-doanh": (path) => fragment(path) },
  });
  app.pushes.length = 0;
  app.window.dispatchEvent(new app.window.Event("popstate"));
  await settle(app.window, 50);
  assert.equal(app.calls.length, 1, "popstate không tải lại nội dung");
  assert.deepEqual(app.pushes, [],
    "popstate đẩy thêm một mục history — Back sẽ không bao giờ ra khỏi trang");
});

test("GET thất bại rơi về điều hướng THẬT", async () => {
  /* Một GET không ghi gì, nên gọi lại nó không tạo bản ghi thứ hai. Đây
   * là chỗ KHÁC HẲN mutation. */
  const app = boot({
    routes: { "/kinh-doanh": () => ({ reject: new Error("mạng đứt") }) },
  });
  app.document.getElementById("loc-a").click();
  await settle(app.window, 50);
  assert.ok(app.navigations.length >= 1,
    "GET lỗi phải rơi về điều hướng thật");
});

test("loading của mutation nằm TẠI form, không phải overlay toàn trang",
  async () => {
    const app = boot({
      routes: { [IDEM_ROUTE]: () => ({ ...fragment("da-luu"), delayMs: 60 }) },
    });
    const form = app.document.getElementById("f-idem");
    submit(app, form);
    await settle(app.window, 10);
    assert.equal(form.getAttribute("data-save-state"), "saving");
    // Không có phần tử nào phủ cả trang.
    assert.equal(app.document.querySelectorAll(".tp-overlay, .page-spinner")
      .length, 0);
    await settle(app.window, 120);
  });
