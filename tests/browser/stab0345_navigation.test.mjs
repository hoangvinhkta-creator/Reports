/*
 * `STAB-03`/`STAB-04`/`STAB-05` + `P1-5`/`P2-2` — hành vi điều hướng và
 * mutation, kiểm trên DOM THẬT.
 *
 * Những mệnh đề ở đây không kiểm được bằng regex trên mã nguồn, và một
 * trong số chúng (`P2-2`) là lỗi mà review tìm ra bằng chính cách này.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { boot, settle, fragment } from "./harness.mjs";

const APP_CONTENT = /id="app-content"/g;

function countWrappers(document) {
  return document.querySelectorAll("#app-content").length;
}

// --- STAB-04 -------------------------------------------------------------

test("STAB-04: ba lần điều hướng liên tiếp giữ ĐÚNG MỘT #app-content",
  async () => {
    const app = boot({
      routes: { "/kinh-doanh": (path) => fragment(path) },
    });
    assert.equal(countWrappers(app.document), 1, "trạng thái đầu");

    for (const id of ["loc-a", "loc-b", "loc-c"]) {
      app.document.getElementById(id) && app.document.getElementById(id).click();
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

test("STAB-04: mảnh mang wrapper VẪN không tạo phần tử thứ hai… và đó là lỗi",
  async () => {
    /* Test này ghi lại RANH GIỚI của lớp client: nếu server trả một mảnh
     * mang theo `<main id="app-content">` (tức hợp đồng `STAB-04` bị vi
     * phạm ở phía server), `innerHTML` sẽ tạo phần tử thứ hai và
     * `getElementById` sẽ trả về phần tử NGOÀI.
     *
     * Nó KHÔNG khẳng định client tự chữa được — client không chữa được,
     * và giả vờ ngược lại sẽ làm người đọc tưởng hợp đồng phía server là
     * tuỳ chọn. Cửa thật là `tests/test_stab04_fragment_contract.py`. */
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
    routes: { "/kinh-doanh/nhan-vien/sua-bh": () => fragment("da-luu") },
  });
  app.document.getElementById("f-idem").dispatchEvent(
    new app.window.Event("submit", { bubbles: true, cancelable: true }));
  await settle(app.window, 50);
  const posts = app.calls.filter((call) => call.method === "POST");
  assert.equal(posts.length, 1);
  assert.equal(posts[0].signal, undefined, "POST mang AbortSignal");
});

// --- STAB-03 -------------------------------------------------------------

test("STAB-03: fetch lỗi KHÔNG tự gửi lại mutation", async () => {
  const app = boot({
    routes: {
      "/kinh-doanh/nhan-vien/sua-bh": () => ({
        reject: new Error("mạng đứt"),
      }),
    },
  });
  const form = app.document.getElementById("f-idem");
  let nativeSubmits = 0;
  form.submit = () => { nativeSubmits += 1; };

  form.dispatchEvent(new app.window.Event(
    "submit", { bubbles: true, cancelable: true }));
  await settle(app.window, 50);

  assert.equal(nativeSubmits, 0,
    "form.submit() tự động đã chạy — đúng lỗi STAB-03");
  assert.equal(app.calls.filter((call) => call.method === "POST").length, 1,
    "mutation được gửi nhiều hơn một lần");
  // Draft còn nguyên: DOM không bị thay.
  assert.equal(form.querySelector("input[name=gia_nhap]").value, "123");
});

test("STAB-03: form có data-idempotent giữ NGUYÊN mã qua lần thử lại",
  async () => {
    const app = boot({
      routes: {
        "/kinh-doanh/nhan-vien/sua-bh": () => ({
          reject: new Error("mạng đứt"),
        }),
      },
    });
    const form = app.document.getElementById("f-idem");
    form.submit = () => {};
    form.dispatchEvent(new app.window.Event(
      "submit", { bubbles: true, cancelable: true }));
    await settle(app.window, 50);

    const retry = form.parentNode.querySelector("[data-save-retry]")
      || app.document.querySelector("[data-save-retry]");
    assert.ok(retry, "không có nút THỬ LẠI cho form data-idempotent");
    retry.click();
    await settle(app.window, 50);

    const posts = app.calls.filter((call) => call.method === "POST");
    assert.equal(posts.length, 2, "nút THỬ LẠI không gửi lại");
    const keys = posts.map((call) => call.body.get("idempotency_key"));
    assert.ok(keys[0], "mutation không mang idempotency_key");
    assert.equal(keys[0], keys[1],
      "lần thử lại sinh mã MỚI — server sẽ coi nó là một quyết định mới "
      + "và ghi lần thứ hai");
  });

test("P1-5: form KHÔNG khai data-idempotent thì KHÔNG gửi mã và KHÔNG có THỬ LẠI",
  async () => {
    /* Review chỉ ra rằng bản trước gắn `request_id` vào MỌI form POST
     * trong khi KHÔNG route HTML nào đọc nó — nên câu "server nhận ra và
     * không ghi hai lần" là một lời hứa không có gì đỡ. */
    const app = boot({
      routes: { "/upload": () => ({ reject: new Error("mạng đứt") }) },
    });
    const form = app.document.getElementById("f-plain");
    form.submit = () => {};
    form.dispatchEvent(new app.window.Event(
      "submit", { bubbles: true, cancelable: true }));
    await settle(app.window, 50);

    const posts = app.calls.filter((call) => call.method === "POST");
    assert.equal(posts.length, 1);
    assert.equal(posts[0].body.get("idempotency_key"), null,
      "gửi mã tới một route không đọc nó");
    assert.equal(app.document.querySelector("[data-save-retry]"), null,
      "mọc nút THỬ LẠI cho một route không chống lặp được");
    // Nhưng người dùng VẪN được nói cho biết, và draft vẫn còn.
    const status = form.querySelector("[data-save-status]");
    assert.ok(status && status.textContent.includes("Chưa xác nhận"), status);
    assert.ok(status.textContent.includes("tải lại trang"),
      "phải nói rõ phải tự kiểm tra — xem P1-5");
  });

// --- P2-2 ----------------------------------------------------------------

test("P2-2: A lỗi KHÔNG bật lại nút của form B đang còn bay", async () => {
  /* Đây là lỗi review tìm ra bằng chính bộ kiểm này: bản trước gọi
   * `restorePendingButtons()` không tham số, và nó bật lại nút của MỌI
   * form đang chờ — kể cả form mà request của nó vẫn đang bay. Bấm nút
   * đó là gửi trùng. */
  const app = boot({
    routes: {
      "/kinh-doanh/nhan-vien/sua-bh": () => ({
        reject: new Error("mạng đứt"),
      }),
      "/upload": () => ({ ...fragment("upload-xong"), delayMs: 120 }),
    },
  });
  const failing = app.document.getElementById("f-idem");
  const slow = app.document.getElementById("f-plain");
  failing.submit = () => {};
  slow.submit = () => {};

  const slowButton = slow.querySelector("button");
  slow.dispatchEvent(new app.window.Event(
    "submit", { bubbles: true, cancelable: true }));
  assert.equal(slowButton.disabled, true, "nút form chậm phải bị khoá");

  failing.dispatchEvent(new app.window.Event(
    "submit", { bubbles: true, cancelable: true }));
  await settle(app.window, 50);

  assert.equal(slowButton.disabled, true,
    "nút của form B đã được bật lại trong khi request của nó còn bay — "
    + "bấm nó là gửi trùng B (đúng lỗi P2-2)");
  // Còn nút của form A (form vừa lỗi) PHẢI được bật lại, nếu không người
  // dùng thấy một dòng "chưa xác nhận" cạnh một cái nút đã chết.
  assert.equal(failing.querySelector("button").disabled, false,
    "nút của form vừa lỗi không được bật lại");
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
      routes: {
        "/kinh-doanh/nhan-vien/sua-bh": () => ({
          ...fragment("da-luu"), delayMs: 60,
        }),
      },
    });
    const form = app.document.getElementById("f-idem");
    form.dispatchEvent(new app.window.Event(
      "submit", { bubbles: true, cancelable: true }));
    await settle(app.window, 10);
    assert.equal(form.getAttribute("data-save-state"), "saving");
    // Không có phần tử nào phủ cả trang.
    assert.equal(app.document.querySelectorAll(".tp-overlay, .page-spinner")
      .length, 0);
  });
