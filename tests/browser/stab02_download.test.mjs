/*
 * `STAB-02` + `P2-1`/`P2-6` — byte `PK…` KHÔNG BAO GIỜ vào được trang.
 *
 * Đây là bài kiểm mà review yêu cầu và repo còn thiếu: "ít nhất một
 * browser test hoặc test DOM thực tế chứng minh PK... không thể bị chèn
 * vào trang". Bản trước chỉ có một regex so vị trí chuỗi trong mã nguồn.
 *
 * Các cửa được kiểm RIÊNG, vì chúng đóng những đường khác nhau:
 *
 *     1. route CÓ tên trong `DOWNLOAD_PATHS`  → không gọi fetch lần nào
 *     2. `Content-Disposition: attachment`    → chặn dù không có tên
 *     3. `Content-Type` KHÔNG phải html       → chặn
 *     4. `Content-Type` RỖNG                  → chặn  (đây là `P2-1`)
 *     5. redirect tới file                    → chặn theo header CUỐI
 *     6. `204` không body                     → chặn, không xoá trắng bảng
 *     7. response file của lượt CŨ            → không ép điều hướng (`P2-6`)
 *
 * Cửa 4 là lỗi review tìm ra bằng chính bộ này: bản trước coi thiếu
 * header là "server cũ không khai" và cho response vào DOM.
 */

import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { boot, settle, fragment, installErrorGuard } from "./harness.mjs";

installErrorGuard(afterEach);

/* Byte MỞ ĐẦU THẬT của một file .xlsx (ZIP): `PK\x03\x04`.
 *
 * Viết bằng escape của JavaScript, KHÔNG dán byte thô vào file: một byte
 * NUL trong mã nguồn làm git coi cả file là BINARY, và khi đó mỗi lần
 * review không đọc được diff của nó. Chuỗi lúc chạy vẫn chứa đúng những
 * byte ấy, nên bài kiểm vẫn nói về đúng thứ nó định nói. */
const ZIP = "PK\u0003\u0004\u0014\u0000\u0008\u0000rác nhị phân";

const XLSX_TYPE = "application/vnd.openxmlformats-officedocument"
  + ".spreadsheetml.sheet";

function reads(app) {
  return app.bodyEvents.filter((event) => event.kind === "read");
}

test("route tải file trong danh sách: KHÔNG gọi fetch lần nào", async () => {
  const app = boot({ routes: {} });
  app.document.getElementById("tai-excel").click();
  await settle(app.window);
  assert.equal(app.calls.length, 0,
    "link tải file bị chặn qua lớp mảnh — phải để trình duyệt tự tải");
  assert.ok(!app.document.body.textContent.includes("PK"));
});

test("attachment ngoài danh sách: chặn TRƯỚC khi đọc body", async () => {
  const app = boot({
    routes: {
      "/bao-cao/khong-khai-type": () => ({
        headers: {
          "Content-Type": XLSX_TYPE,
          "Content-Disposition": 'attachment; filename="bao-cao.xlsx"',
        },
        body: ZIP,
      }),
    },
  });
  app.document.getElementById("tai-la").click();
  await settle(app.window);

  assert.ok(!app.document.body.textContent.includes("PK"),
    "byte PK… đã vào DOM");
  // `.text()` KHÔNG được gọi: đọc body của một file .xlsx thành chuỗi đã
  // là việc sai, và chuỗi đó chính là thứ đã từng được ghi vào trang.
  assert.deepEqual(reads(app), [], "body được đọc dù response là file");
  assert.ok(app.navigations.some((url) => url.includes("khong-khai-type")),
    "phải điều hướng THẬT để trình duyệt tải file");
});

test("P2-1: Content-Type RỖNG cũng bị chặn", async () => {
  /* Lỗi review tìm ra bằng chính bộ này. Bản trước trả `true` cho một
   * `Content-Type` rỗng ("server cũ không khai"), nên một response mang
   * byte `PK…` mà không khai type đi thẳng vào `#app-content`. */
  const app = boot({
    routes: {
      "/bao-cao/khong-khai-type": () => ({
        headers: {},            // không khai gì cả
        body: ZIP,
      }),
    },
  });
  app.document.getElementById("tai-la").click();
  await settle(app.window);
  assert.ok(!app.document.body.textContent.includes("PK"),
    "Content-Type rỗng vẫn cho byte PK… vào DOM — đúng lỗi P2-1");
  assert.deepEqual(reads(app), [],
    "body được đọc dù Content-Type không xác nhận là HTML");
});

test("Content-Type json cũng không phải nội dung trang", async () => {
  const app = boot({
    routes: {
      "/bao-cao/khong-khai-type": () => ({
        headers: { "Content-Type": "application/json" },
        body: '{"error":{"code":"X"}}',
      }),
    },
  });
  app.document.getElementById("tai-la").click();
  await settle(app.window);
  assert.ok(!app.document.body.textContent.includes('"code"'),
    "JSON bị đưa vào DOM như nội dung trang");
});

test("P2-1: redirect tới file bị chặn theo header CUỐI", async () => {
  /* `fetch` tự đi theo redirect, nên `response.headers` là header của
   * response CUỐI. Một route HTML redirect sang một file vì thế phải bị
   * chặn bằng cùng cửa — cửa kiểm đọc header cuối, không đọc route đầu. */
  const app = boot({
    routes: {
      "/kinh-doanh": () => ({
        url: "https://reports.example/kinh-doanh/xuat-excel?ky=2026-09",
        headers: { "Content-Disposition": 'attachment; filename="a.xlsx"',
                   "Content-Type": XLSX_TYPE },
        body: ZIP,
      }),
    },
  });
  app.document.getElementById("loc-a").click();
  await settle(app.window);
  assert.ok(!app.document.body.textContent.includes("PK"),
    "response sau redirect mang byte PK… đã vào DOM");
  assert.deepEqual(reads(app), [], "body được đọc dù đích là file");
});

test("P2-1: response 204 không body cũng không xoá trắng bảng", async () => {
  /* Một response không khai `Content-Type` và không có body: cửa
   * fail-closed phải chặn nó thay vì chèn một chuỗi rỗng vào
   * `#app-content`. */
  const app = boot({
    routes: {
      "/kinh-doanh": () => ({ status: 204, headers: {}, body: "" }),
    },
  });
  const before = app.document.getElementById("app-content").innerHTML;
  app.document.getElementById("loc-a").click();
  await settle(app.window, 50);
  assert.equal(app.document.getElementById("app-content").innerHTML, before,
    "response 204 đã xoá trắng nội dung");
});

test("HTML hợp lệ VẪN được swap — cửa chặn không chặn oan", async () => {
  const app = boot({
    routes: {
      "/kinh-doanh": () => ({
        headers: { "Content-Type": "text/html; charset=utf-8" },
        body: '<p data-marker="da-swap">nội dung mới</p>',
      }),
    },
  });
  app.document.getElementById("loc-a").click();
  await settle(app.window);
  assert.ok(app.document.querySelector('[data-marker="da-swap"]'),
    "HTML hợp lệ không được swap — cửa chặn đang chặn oan");
});

test("P2-6: body của response file bị HUỶ, không đọc rồi vứt", async () => {
  const app = boot({
    routes: {
      "/bao-cao/khong-khai-type": () => ({
        headers: { "Content-Disposition": "attachment",
                   "Content-Type": "application/octet-stream" },
        body: ZIP,
      }),
    },
  });
  app.document.getElementById("tai-la").click();
  await settle(app.window);

  // Với một bản xuất lớn, đọc-rồi-vứt là gấp đôi băng thông cho một file
  // người dùng sẽ tải lại bằng điều hướng thật ngay sau đó.
  assert.deepEqual(app.bodyEvents.map((event) => event.kind), ["cancel"],
    "body phải bị HUỶ đúng một lần, không đọc lần nào");
  assert.equal(app.calls.length, 1, "file bị kéo về nhiều hơn một lượt");
  assert.ok(app.navigations.length >= 1, "không điều hướng để tải file");
});

test("P2-6: response tải file CŨ không ép điều hướng sau khi lượt mới thắng",
  async () => {
    /* Nghiệm thu của brief cho `STAB-05`, áp cho cả nhánh tải file: một
     * response file của lượt bấm CŨ không được cưỡng bức điều hướng sau
     * khi người dùng đã đi tiếp. Bản trước miễn cho nhánh này.
     *
     * `abortController: false` là BẮT BUỘC để test này nói được điều gì:
     * với `AbortController`, lượt cũ bị abort TRƯỚC khi response về, nên
     * nhánh `isDownload` không chạy tới và cửa `isLatest` trong đó không
     * được kiểm. Tắt abort là cách duy nhất buộc BỘ ĐẾM tuần tự tự làm
     * việc — và bộ đếm mới là thứ quyết định "response nào được phép
     * hành động", đúng docstring của `STAB-05`. */
    const app = boot({
      abortController: false,
      routes: {
        // Lượt A: một file, về CHẬM.
        "/bao-cao/khong-khai-type": () => ({
          headers: { "Content-Disposition": "attachment",
                     "Content-Type": "application/octet-stream" },
          body: ZIP, delayMs: 120,
        }),
        // Lượt B: HTML hợp lệ, về NGAY.
        "/kinh-doanh": () => ({ ...fragment("b-thang"), delayMs: 5 }),
      },
    });

    app.document.getElementById("tai-la").click();   // A — file, chậm
    app.document.getElementById("loc-b").click();    // B — HTML, nhanh
    await settle(app.window, 300);

    assert.ok(app.document.querySelector('[data-marker="b-thang"]'),
      "lượt B không được swap — test không chứng minh được mệnh đề");
    // Lượt A THẬT SỰ đã về (không bị abort) — nếu không, cửa `isLatest`
    // trong nhánh `isDownload` chưa được chạm tới và test này rỗng nghĩa.
    assert.ok(app.bodyEvents.some((event) => event.kind === "cancel"),
      "response tải file của lượt A chưa về — test chưa kiểm được cửa nào");
    assert.deepEqual(app.navigations, [],
      `response tải file của lượt CŨ đã ép điều hướng: ${app.navigations}`);
  });
