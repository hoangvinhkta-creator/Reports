/*
 * TASK-OWNER-UIUX-004 — lớp TĂNG CƯỜNG (progressive enhancement), không
 * phải kiến trúc mới. Mọi liên kết/form trong #app-content vẫn là những
 * URL/method HTTP thật, dựng bởi server — tắt JS thì mọi thứ vẫn hoạt động
 * y hệt trước đây (điều hướng thật, tải lại trang). Có JS thì cùng những
 * liên kết/form đó được gửi qua fetch() với header X-Fragment:1, server
 * trả về ĐÚNG nội dung bên trong #app-content (xem layout.html), và ở đây
 * chỉ thay thế đúng vùng đó — không tải lại trang, không mất trạng thái
 * cuộn của thanh điều hướng chính.
 *
 * Thanh tab chính (nav.ncc-tabs) đứng NGOÀI #app-content nên click vào đó
 * KHÔNG bị chặn ở đây — chuyển tab vẫn là điều hướng thật, đúng yêu cầu
 * "chuyển tab thì tải lại link, làm việc trong tab thì xử lý tĩnh".
 *
 * ────────────────────────────────────────────────────────────────────────
 * ĐỢT STAB (STAB-02/03/05) đóng ba lớp lỗi của CHÍNH lớp điều hướng này.
 * Chúng được kể ở đây một lần, rồi từng chỗ chỉ trỏ ngược lên:
 *
 * STAB-02 — TẢI FILE BỊ ĐỌC THÀNH TRANG. `onClick` chặn mọi link cùng
 *   origin rồi `fetchFragment()` đọc MỌI response thành text và đưa vào
 *   DOM. Link xuất Excel không mang `download` (nó là một GET trả
 *   `Content-Disposition: attachment`, và HTML không có cách nào biết điều
 *   đó trước khi gọi), nên các byte `PK…` của file .xlsx được ghi thẳng vào
 *   trang thay vì tải về. Hai lớp chặn được thêm: một danh sách route tải
 *   file mà bộ điều hướng KHÔNG chạm, và một cửa kiểm `Content-Type`/
 *   `Content-Disposition` ở `fetchFragment()` — cửa sau là cửa thật, vì nó
 *   đúng cho cả những route tải file chưa ai nghĩ tới.
 *
 * STAB-03 — TỰ ĐỘNG GỬI LẠI MUTATION. `submitForm()` gọi `form.submit()`
 *   trong `catch`. Một lỗi fetch KHÔNG phân biệt được "server chưa nhận"
 *   với "server đã ghi xong nhưng response thất lạc", nên nhánh đó có thể
 *   gửi lần thứ hai một quyết định đã được ghi. Nay không có đường nào tự
 *   gửi lại: draft giữ nguyên, người dùng thấy "chưa xác nhận được kết
 *   quả", và nút thử lại gửi ĐÚNG `request_id` cũ — server nhận ra và trả
 *   lại kết quả lần ghi trước thay vì ghi lần thứ hai.
 *
 * STAB-05 — RESPONSE CŨ GHI ĐÈ RESPONSE MỚI. Không có gì đánh số các lượt
 *   fetch, nên đổi bộ lọc A → B → C mà B trả về cuối sẽ hiện B. Nay mỗi
 *   vùng có một bộ đếm, và một response chỉ được swap khi nó là response
 *   MỚI NHẤT của vùng đó; các lượt cũ bị `AbortController` huỷ.
 * ────────────────────────────────────────────────────────────────────────
 */
(function () {
  "use strict";

  var CONTENT_ID = "app-content";

  function contentEl() {
    return document.getElementById(CONTENT_ID);
  }

  function isModifiedClick(event) {
    return event.defaultPrevented || event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
  }

  function sameOrigin(url) {
    try {
      return new URL(url, window.location.href).origin === window.location.origin;
    } catch (e) {
      return false;
    }
  }

  /* Băm (#...) trỏ tới một chỗ trong TRANG HIỆN TẠI (vd "#bieu-do-doanh-thu"
   * của nút đổi mức gộp biểu đồ) không đổi URL đường dẫn — vẫn phải qua
   * fetch để lấy nội dung mới, nhưng giữ nguyên vị trí cuộn thay vì nhảy
   * lên neo, vì neo đó không còn ý nghĩa "cuộn tới" khi nội dung được thay
   * tại chỗ, không phải điều hướng trang mới. */
  function stripHash(url) {
    var i = url.indexOf("#");
    return i === -1 ? url : url.slice(0, i);
  }

  /* --- STAB-02: những đường KHÔNG bao giờ đi qua lớp mảnh -------------
   *
   * Đây là lớp chặn THỨ NHẤT (danh sách), rẻ và đọc được: một link tới
   * những đường này giữ nguyên hành vi mặc định của trình duyệt, tức là
   * tải file như trước khi có lớp JS nào.
   *
   * Nó KHÔNG phải lớp chặn duy nhất, và không được là lớp duy nhất: một
   * route tải file thêm về sau sẽ không có tên ở đây. Cửa kiểm
   * `Content-Type` trong `fetchFragment()` là cửa đúng cho mọi route, kể
   * cả route chưa tồn tại. Hai lớp cùng tồn tại vì chúng trả lời hai câu
   * khác nhau: danh sách này tránh gọi mạng một lần vô ích, còn cửa kiểm
   * kia tránh đưa rác vào DOM.
   */
  var DOWNLOAD_PATHS = [
    "/kinh-doanh/xuat-excel",
    "/artifact/"
  ];

  function isDownloadUrl(url) {
    var path;
    try {
      path = new URL(url, window.location.href).pathname;
    } catch (e) {
      return false;
    }
    for (var i = 0; i < DOWNLOAD_PATHS.length; i++) {
      if (path === DOWNLOAD_PATHS[i] || path.indexOf(DOWNLOAD_PATHS[i]) === 0) {
        return true;
      }
    }
    return false;
  }

  /* --- STAB-02: cửa kiểm nội dung trước khi chạm DOM ------------------
   *
   * `fetchFragment()` cũ đọc MỌI response thành text. Hàm này là điều kiện
   * để một response được coi là HTML thay cho nội dung trang:
   *
   *   1. KHÔNG mang `Content-Disposition: attachment` — một response nói
   *      "tôi là file để tải" thì nó là file để tải, kể cả khi nó cũng
   *      khai là HTML.
   *   2. `Content-Type` là `text/html` (hoặc rỗng — server cũ/response 204
   *      không khai; ta chấp nhận và để bước sau xử lý).
   *
   * Trả `false` ⟹ người gọi phải điều hướng THẬT tới URL đó, không swap.
   */
  function isHtmlFragment(response) {
    var disposition = response.headers.get("Content-Disposition") || "";
    if (/attachment/i.test(disposition)) return false;
    var type = (response.headers.get("Content-Type") || "").toLowerCase();
    /* `P2-1` — `Content-Type` RỖNG KHÔNG được coi là HTML.
     *
     * Bản trước trả `true` ở đây ("server cũ không khai"), và kiểm thử DOM
     * (jsdom) chứng minh hậu quả: một response mang byte `PK…` mà không
     * khai type đi thẳng vào `#app-content` — đúng lỗi mà `STAB-02` tồn
     * tại để đóng, chỉ qua một cửa khác.
     *
     * Fail closed: không khai thì không được vào DOM. Cái mất đi là khả
     * năng thay mảnh cho một response không khai type, và không có
     * response nào như vậy trên đường này (`send_file` và `render_template`
     * của Flask đều khai). Cái được là cửa không còn phụ thuộc vào việc
     * mọi tầng trung gian đều giữ nguyên header. */
    if (!type) return false;
    return type.indexOf("text/html") > -1;
  }

  /* Lỗi mang cờ `isDownload` — người gọi phân biệt được "response này là
   * file, hãy để trình duyệt tải nó" với "mạng lỗi". Hai việc phải làm
   * khác nhau: một cái điều hướng thật, một cái KHÔNG được gửi lại gì. */
  function DownloadResponse(url) {
    var err = new Error("response không phải HTML — đây là file để tải");
    err.isDownload = true;
    err.url = url;
    return err;
  }

  /* --- STAB-05: mỗi vùng một bộ đếm ----------------------------------
   *
   * `seq[region]` tăng ở MỖI lượt fetch của vùng đó. Response nào mang số
   * nhỏ hơn số hiện tại là response CŨ, và nó bị bỏ — không swap, không
   * báo lỗi. Đây là điều làm cho "đổi bộ lọc A → B → C luôn hiện C" đúng
   * theo cấu tạo, chứ không nhờ may mắn về thứ tự mạng trả về.
   *
   * `AbortController` là phần thứ hai, và nó KHÔNG thay thế bộ đếm: abort
   * chỉ giảm lưu lượng vô ích, còn cái quyết định "response nào được ghi"
   * vẫn là bộ đếm. Một response đã về tới hàng đợi trước khi abort kịp
   * chạy vẫn phải bị bộ đếm chặn lại.
   *
   * MUTATION KHÔNG BAO GIỜ BỊ ABORT. Huỷ một POST đang bay không huỷ được
   * việc server đã ghi; nó chỉ làm ta không biết kết quả — đúng cái tình
   * huống STAB-03 tồn tại để đóng. Nên `submitForm()` không dùng cơ chế
   * này, và điều đó được nói lại ở chính chỗ ấy.
   */
  var seq = Object.create(null);
  var inflight = Object.create(null);

  function nextTicket(region) {
    seq[region] = (seq[region] || 0) + 1;
    var controller = null;
    if (inflight[region]) {
      try { inflight[region].abort(); } catch (e) { /* đã xong: bỏ qua */ }
    }
    if (typeof AbortController === "function") {
      controller = new AbortController();
      inflight[region] = controller;
    }
    return { region: region, n: seq[region], signal: controller && controller.signal };
  }

  function isLatest(ticket) {
    return seq[ticket.region] === ticket.n;
  }

  function swapContent(html, pushUrl) {
    var el = contentEl();
    if (!el) return false;
    var scrollY = window.scrollY;
    el.innerHTML = html;
    if (pushUrl) {
      history.pushState({ fragment: true }, "", pushUrl);
    }
    window.scrollTo(0, scrollY);
    el.dispatchEvent(new CustomEvent("app:content-updated", { bubbles: true }));
    upgradeDialogs();
    return true;
  }

  function fetchFragment(url, opts) {
    opts = opts || {};
    var headers = Object.assign({ "X-Fragment": "1" }, opts.headers || {});
    return fetch(url, Object.assign({}, opts, { headers: headers }))
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        /* STAB-02 — cửa kiểm đứng TRƯỚC `response.text()`. Đọc body của
         * một file .xlsx thành text đã là việc sai: nó nạp cả file vào bộ
         * nhớ dưới dạng chuỗi, và chuỗi đó là thứ đã từng được ghi vào
         * trang. */
        if (!isHtmlFragment(response)) {
          /* `P2-6` — HUỶ luồng body thay vì để nó chảy hết rồi vứt đi.
           * Với một bản xuất Excel lớn, đọc-rồi-vứt là gấp đôi băng thông
           * cho một file người dùng sẽ tải lại bằng điều hướng thật ngay
           * sau đó.
           *
           * `response.body` có thể vắng (một số môi trường test, response
           * 204), nên mọi thứ ở đây được bọc — một lần huỷ không được là
           * lý do làm sập đường tải file. */
          try {
            if (response.body && !response.bodyUsed) response.body.cancel();
          } catch (e) { /* không huỷ được: chỉ tốn băng thông, không sai */ }
          throw DownloadResponse(response.url || url);
        }
        return response.text().then(function (html) {
          return { html: html, url: response.url };
        });
      });
  }

  /* Vùng mặc định của điều hướng cả trang. Các panel/popover của đợt
   * UI-02 dùng vùng riêng theo `order_key`, nên một lượt tải chi tiết đơn
   * không huỷ lượt tải bảng đang chạy và ngược lại. */
  var MAIN_REGION = "app-content";

  function navigate(url, options) {
    options = options || {};
    var fetchUrl = stripHash(url);
    /* STAB-02 — link tải file không đi qua đây. Kiểm cả ở `onClick` (để
     * không chặn hành vi mặc định) và ở đây (để mọi đường gọi
     * `navigate()` bằng tay cũng an toàn). */
    if (isDownloadUrl(fetchUrl)) {
      window.location.href = url;
      return Promise.resolve(false);
    }
    var ticket = nextTicket(options.region || MAIN_REGION);
    return fetchFragment(fetchUrl, { method: "GET", signal: ticket.signal })
      .then(function (result) {
        /* STAB-05 — response CŨ dừng ở đây. Không swap, không báo lỗi:
         * người dùng đã đi tiếp, và một thông báo về một lượt tải họ đã
         * bỏ là tiếng ồn. */
        if (!isLatest(ticket)) return false;
        swapContent(result.html, options.push !== false ? result.url : null);
        return true;
      })
      .catch(function (error) {
        if (error && error.name === "AbortError") return false;
        /* Response là FILE: để trình duyệt tải nó bằng điều hướng thật.
         * Đây không phải một lỗi của người dùng.
         *
         * `P2-6` — kiểm `isLatest` TRƯỚC khi điều hướng: một response tải
         * file của lượt bấm CŨ không được cưỡng bức điều hướng sau khi
         * người dùng đã đi tiếp. Cùng luật với mọi response khác (STAB-05);
         * bản trước miễn cho nhánh này. */
        if (error && error.isDownload) {
          if (isLatest(ticket)) window.location.href = error.url || url;
          return false;
        }
        if (!isLatest(ticket)) return false;
        /* GET thất bại thì điều hướng thật là an toàn: một GET không ghi
         * gì, nên gọi lại nó không tạo ra bản ghi thứ hai. Đây là chỗ
         * KHÁC HẲN mutation — xem `submitForm()`. */
        window.location.href = url;
        return false;
      });
  }

  /* --- STAB-03: mutation ---------------------------------------------
   *
   * Ba thứ mỗi mutation mang theo, và cả ba do CHỖ NÀY gắn vào chứ không
   * do từng form tự nhớ:
   *
   *   `request_id`     mã của LẦN GỬI này. Giữ NGUYÊN qua các lần thử
   *                    lại — đó là toàn bộ điểm của nó: server thấy lại
   *                    cùng mã thì trả lại kết quả lần ghi trước thay vì
   *                    ghi lần thứ hai.
   *   `base_revision`  bản của đối tượng mà người dùng ĐÃ NHÌN THẤY khi
   *                    bắt đầu sửa. Server so nó với bản hiện tại; lệch
   *                    thì trả xung đột thay vì âm thầm ghi đè.
   *   submitter        nút nào đã bấm. `new FormData(form)` không tự biết
   *                    (xem chú thích trong hàm).
   *
   * `request_id` được nhớ TRÊN CHÍNH FORM (`dataset.requestId`), không
   * sinh mới mỗi lần gọi: một lần thử lại sinh mã mới là một lần ghi thứ
   * hai được cho phép, và đó đúng là lỗi cũ mặc một cái áo mới.
   */
  function uuid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    /* Dự phòng cho browser không có `randomUUID` (Safari cũ, http không
     * phải localhost). Không cần chất lượng mật mã: mã này chỉ cần KHÁC
     * mã của các lần gửi khác trên cùng một máy. */
    return "r" + Date.now().toString(36) + "-" +
      Math.random().toString(36).slice(2, 10);
  }

  function requestIdOf(form) {
    if (!form.dataset.requestId) form.dataset.requestId = uuid();
    return form.dataset.requestId;
  }

  /* Sau khi server đã XÁC NHẬN, lần gửi kế tiếp là một quyết định MỚI và
   * phải mang mã mới — nếu không, nó sẽ bị chính cơ chế chống lặp coi là
   * lần thử lại của quyết định cũ và không được ghi. */
  function clearRequestId(form) {
    delete form.dataset.requestId;
  }

  /* Trạng thái lưu của MỘT form, hiện tại đúng chỗ nó thuộc về (`§UI-02`).
   * Năm trạng thái của brief, và không có spinner toàn trang nào. */
  var SAVE_STATES = {
    dirty: "Đã thay đổi",
    saving: "Đang lưu…",
    saved: "Đã lưu",
    conflict: "Có thay đổi mới từ người khác",
    unconfirmed: "Chưa xác nhận được kết quả",
    failed: "Chưa lưu được"
  };

  function statusHost(form) {
    var host = form.querySelector("[data-save-status]");
    if (host) return host;
    /* Form chưa khai chỗ hiện trạng thái: dựng một chỗ ở cuối form thay
     * vì im lặng. Một mutation không nói được nó đang ở đâu là lý do
     * người dùng bấm lần thứ hai. */
    host = document.createElement("span");
    host.className = "tp-save-status";
    host.setAttribute("data-save-status", "");
    host.setAttribute("role", "status");
    host.setAttribute("aria-live", "polite");
    form.appendChild(host);
    return host;
  }

  function setSaveState(form, state, extra) {
    var host = statusHost(form);
    var text = SAVE_STATES[state] || state;
    if (state === "saved") {
      var now = new Date();
      text += " lúc " + String(now.getHours()).padStart(2, "0") + ":" +
        String(now.getMinutes()).padStart(2, "0");
    }
    host.textContent = extra ? text + " — " + extra : text;
    host.setAttribute("data-save-state", state);
    form.setAttribute("data-save-state", state);
  }

  function submitForm(form, submitter) {
    var method = (form.getAttribute("method") || "GET").toUpperCase();
    var action = form.getAttribute("action") || window.location.href;
    var opts = { method: method };
    /* Một nút bấm mang `name`/`value` riêng (vd `hanh-dong=khoi-phuc`) chỉ
     * được trình duyệt gộp vào dữ liệu gửi đi khi CHÍNH nút đó kích hoạt
     * submit — `new FormData(form)` không tự biết điều này, phải truyền
     * `submitter` tường minh (chữ ký hai tham số của `FormData`, cùng quy
     * tắc trình duyệt dùng cho submit thật). Thiếu bước này, một form có
     * hai nút submit khác `value` (như "Loại"/"Khôi phục" cùng route) sẽ
     * gửi thiếu đúng trường quyết định hành động nào. */
    var data = submitter && submitter.name
      ? new FormData(form, submitter) : new FormData(form);
    if (method === "GET") {
      var params = new URLSearchParams(data);
      var qs = params.toString();
      action = stripHash(action) + (qs ? "?" + qs : "");
      /* GET không ghi gì ⟹ nó là điều hướng, và nó đi qua đúng cơ chế
       * chống-response-cũ của `navigate()` (STAB-05). Đây là đường của
       * ô chọn kỳ/sheet có `data-auto-submit`. */
      return navigate(action, { region: form.dataset.region || MAIN_REGION });
    }

    /* `P1-5` — `idempotency_key` CHỈ được gắn cho form KHAI rằng route
     * của nó đọc mã đó (`data-idempotent`).
     *
     * Bản trước gắn `request_id` vào MỌI form POST, và review chỉ ra rằng
     * KHÔNG route HTML nào đọc nó: `business_save_order`, upload, target,
     * chốt kỳ đều nhận thêm một trường bị bỏ qua. Hệ quả tệ hơn một
     * trường thừa — câu trong giao diện ("server nhận ra và không ghi hai
     * lần") thành một lời hứa không có gì đỡ, và người dùng bấm THỬ LẠI
     * dựa trên lời hứa đó.
     *
     * Nay `showRetry()` chỉ mọc nút THỬ LẠI cho form có `data-idempotent`.
     * Form không có nó vẫn giữ nguyên draft và vẫn nói "chưa xác nhận
     * được kết quả", nhưng nó nói THÊM rằng phải tự kiểm tra — đó là sự
     * thật về những route ấy hôm nay. */
    var requestId = null;
    if (form.hasAttribute("data-idempotent")) {
      requestId = requestIdOf(form);
      data.set("idempotency_key", requestId);
    }
    /* `base_revision` chỉ được gắn khi form KHAI nó. Bịa một giá trị ở
     * đây sẽ làm server so với một bản không ai từng nhìn thấy. */
    if (form.dataset.baseRevision) {
      data.set("base_revision", form.dataset.baseRevision);
    }
    opts.body = data;
    /* KHÔNG có `signal` ở đây, có chủ đích. Huỷ một POST đang bay không
     * huỷ được việc server đã ghi — nó chỉ làm ta không biết kết quả. */
    setSaveState(form, "saving");
    return fetchFragment(action, opts)
      .then(function (result) {
        clearRequestId(form);
        swapContent(result.html, result.url);
        return true;
      })
      .catch(function (error) {
        if (error && error.isDownload) {
          /* Một mutation trả về file (xuất Excel sau khi lưu) — để trình
           * duyệt tải, và KHÔNG gửi lại gì. */
          clearRequestId(form);
          restorePendingButtons(form);
          window.location.href = error.url || action;
          return false;
        }
        /* ĐÂY là chỗ `form.submit()` từng đứng, và vì sao nó bị gỡ:
         *
         * Một lỗi fetch KHÔNG phân biệt được ba tình huống — server chưa
         * nhận, server đang ghi, server đã ghi xong rồi response thất
         * lạc. `form.submit()` ở đây gửi lần thứ hai trong CẢ BA, nên nó
         * ghi trùng trong tình huống thứ ba. Không có cách nào đọc được
         * `error` để biết là tình huống nào.
         *
         * Nên nhánh này KHÔNG gửi gì. Nó giữ nguyên draft (DOM không bị
         * thay), nói ra rằng kết quả chưa xác nhận được, và để người dùng
         * quyết định. `request_id` KHÔNG bị xoá: nút thử lại gửi lại đúng
         * mã đó, và server nhận ra nó.
         */
        /* Câu chữ nói ĐÚNG cái đang có, và nó khác nhau ở hai loại form —
         * xem `P1-5` trong `submitForm()`. Hứa "server nhận ra và không
         * ghi hai lần" cho một route không đọc mã nào là một lời hứa sai. */
        if (form.hasAttribute("data-idempotent")) {
          setSaveState(form, "unconfirmed",
            "Dữ liệu bạn nhập vẫn còn. Bấm THỬ LẠI để gửi lại đúng lần ghi " +
            "này — server nhận ra mã của lần gửi này và không ghi hai lần.");
          showRetry(form);
        } else {
          setSaveState(form, "unconfirmed",
            "Dữ liệu bạn nhập vẫn còn, nhưng KHÔNG rõ máy chủ đã ghi hay " +
            "chưa. Hãy tải lại trang để xem trạng thái thật rồi quyết " +
            "định — gửi lại từ đây có thể ghi lần thứ hai.");
        }
        /* Nút gửi của CHÍNH form này được bật lại — nếu không, người dùng
         * thấy một dòng "chưa xác nhận" cạnh một cái nút đã chết. Xem
         * `onSlowSubmit`. */
        restorePendingButtons(form);
        return false;
      });
  }

  /* Nút THỬ LẠI, dựng cạnh chỗ hiện trạng thái. Nó gửi lại CÙNG form với
   * CÙNG `request_id` — không sinh mã mới, xem `requestIdOf`. */
  function showRetry(form) {
    var host = statusHost(form);
    if (host.parentNode.querySelector("[data-save-retry]")) return;
    var button = document.createElement("button");
    button.type = "button";
    button.className = "ghost btn-mini";
    button.setAttribute("data-save-retry", "");
    button.setAttribute("data-metric", "save-retry");
    button.textContent = "THỬ LẠI";
    button.addEventListener("click", function () {
      button.remove();
      submitForm(form, null);
    });
    host.parentNode.insertBefore(button, host.nextSibling);
  }

  function onClick(event) {
    var el = contentEl();
    if (!el || isModifiedClick(event)) return;
    var link = event.target.closest("a[href]");
    if (!link || !el.contains(link)) return;
    var href = link.getAttribute("href");
    if (!href || href.charAt(0) === "#" && href.length === 1) return;
    if (link.target && link.target !== "" && link.target !== "_self") return;
    if (link.hasAttribute("download")) return;
    if (!sameOrigin(link.href)) return;
    /* STAB-02 — lớp chặn thứ nhất: không `preventDefault()`, nên trình
     * duyệt xử lý link này y như khi không có JS. */
    if (isDownloadUrl(link.href)) return;
    event.preventDefault();
    navigate(link.href, { region: link.dataset.region || MAIN_REGION });
  }

  function onSubmit(event) {
    var el = contentEl();
    var form = event.target;
    if (!el || !el.contains(form) || form.tagName !== "FORM") return;
    if (form.hasAttribute("data-no-ajax")) return;
    event.preventDefault();
    submitForm(form, event.submitter);
  }

  function onChange(event) {
    var el = contentEl();
    var field = event.target;
    if (!el || !el.contains(field)) return;
    if (!field.matches("[data-auto-submit]")) return;
    var form = field.form;
    if (form) submitForm(form);
  }

  function onPopState() {
    navigate(window.location.href, { push: false });
  }

  /* Hộp thoại Target (`<dialog>`): server dựng sẵn `open` khi
   * `sua-target=1` để KHÔNG-JS vẫn đọc được nội dung (một `<dialog open>`
   * không có JS chỉ hiện như một khối bình thường trong luồng trang, không
   * modal — vẫn đúng, chỉ không nổi lên trên). Có JS thì nâng nó thành modal
   * thật bằng `showModal()` để có nền mờ + bẫy focus + phím Esc đóng. */
  function upgradeDialogs() {
    var el = contentEl();
    if (!el) return;
    var dialogs = el.querySelectorAll("dialog[open]");
    for (var i = 0; i < dialogs.length; i++) {
      var dlg = dialogs[i];
      if (typeof dlg.showModal !== "function" || dlg.dataset.upgraded) continue;
      // `open` đến từ SERVER (cho trường hợp không JS) — `showModal()` ném
      // lỗi "đã mở" nếu gọi thẳng trên một dialog đã mang sẵn `open`. Gỡ nó
      // ra rồi gọi lại mới thật sự vào chế độ MODAL (nền mờ, bẫy focus).
      dlg.removeAttribute("open");
      try {
        dlg.showModal();
        dlg.dataset.upgraded = "1";
      } catch (e) {
        dlg.setAttribute("open", "");
      }
    }
  }

  function onDialogCancel(event) {
    var dlg = event.target;
    if (!dlg || dlg.tagName !== "DIALOG") return;
    var closeLink = dlg.querySelector("[data-metric='target-edit-close']");
    if (closeLink) {
      event.preventDefault();
      navigate(closeLink.href);
    }
  }

  /* Dấu hiệu "đang chạy" cho các form CHẬM (upload workbook + chạy pipeline
   * production, có thể mất hàng chục giây từ R1 vì nó gọi thêm Tracking
   * đồng bộ). Không có gì khác trên trang đổi trong lúc chờ — không có dấu
   * hiệu nào thì một request chậm-nhưng-bình-thường trông y hệt một trang
   * treo. Chỉ áp dụng cho form khai `data-loading-label` (opt-in), tránh
   * đụng các form khác chưa cần việc này.
   *
   * Đặt sau `onSubmit` trong cùng danh sách listener của `document`, cùng
   * capture phase: theo thứ tự đăng ký, hàm này chạy SAU khi `onSubmit` đã
   * quyết định preventDefault hay chưa — nhưng bản thân nó không quan tâm
   * AJAX hay native, chỉ cần khoá nút lại trước khi request (dù đi đường
   * nào) bắt đầu chờ máy chủ.
   *
   * `STAB-03` ĐỔI MỘT ĐIỀU Ở ĐÂY, và nó là một sửa lỗi chứ không phải một
   * chi tiết: bản trước KHÔNG bật lại nút bao giờ, và lý do được ghi là
   * "nhánh AJAX thất bại rơi về `form.submit()` thật, nên request thật vẫn
   * đang chờ". Nhánh đó đã bị gỡ (xem `submitForm()`), nên lý do ấy không
   * còn đúng: một lần gửi thất bại nay DỪNG LẠI ở browser, và một cái nút
   * bị khoá vĩnh viễn sẽ khoá luôn đường thử lại của người dùng.
   *
   * Nên nút được bật lại ĐÚNG khi lần gửi kết thúc mà DOM vẫn còn nó:
   *
   *   thành công  → `#app-content` bị thay, nút cũ biến mất cùng DOM cũ,
   *                 không có gì phải bật lại (và `restore` không tìm thấy
   *                 nút nào — nó kiểm `isConnected`).
   *   thất bại    → nút còn đó, được bật lại cùng nhãn cũ, cạnh dòng
   *                 trạng thái "Chưa xác nhận được kết quả" và nút THỬ LẠI.
   *   native      → trang tải lại hẳn, không ai còn nhìn nút cũ.
   *
   * Nhãn gốc được nhớ trong `dataset` chứ không đọc lại từ DOM: nội dung
   * nút đã bị thay bằng spinner + nhãn "đang chạy" rồi. */
  function onSlowSubmit(event) {
    var form = event.target;
    if (!form || form.tagName !== "FORM" || !form.hasAttribute("data-loading-label")) return;
    var btn = (event.submitter && event.submitter.tagName === "BUTTON")
      ? event.submitter : form.querySelector("button[type=submit], button:not([type])");
    if (!btn || btn.disabled) return;
    btn.dataset.idleLabel = btn.textContent;
    btn.disabled = true;
    var spin = document.createElement("span");
    spin.className = "tp-spinner";
    spin.setAttribute("aria-hidden", "true");
    btn.textContent = "";
    btn.appendChild(spin);
    btn.appendChild(document.createTextNode(form.getAttribute("data-loading-label")));
    pendingButtons.push(btn);
  }

  /* Các nút đang ở trạng thái "đang chạy". Một danh sách chứ không một
   * biến: hai form chậm có thể cùng chờ (upload ở một tab nghiệp vụ, lưu
   * đơn ở một tab khác), và một biến sẽ làm nút thứ nhất kẹt mãi. */
  var pendingButtons = [];

  /* `P2-2` — phục hồi nút của ĐÚNG MỘT form, không phải của mọi form đang
   * chờ.
   *
   * Bản trước bật lại tất cả, và kiểm thử DOM (jsdom) chứng minh hậu quả:
   * hai form chậm cùng bay, form A thất bại, và nút của form B — request
   * của nó VẪN đang chờ máy chủ — được bật lại. Bấm nó là gửi trùng B.
   *
   * `form` bắt buộc: gọi không tham số từng là mặc định "tất cả", và một
   * mặc định như thế là cách lỗi trên quay lại mà không ai thấy. */
  function restorePendingButtons(form) {
    if (!form) return [];
    var still = [];
    var restored = [];
    for (var i = 0; i < pendingButtons.length; i++) {
      var btn = pendingButtons[i];
      /* Nút đã rời DOM (`#app-content` bị thay sau một lần lưu thành
       * công): không có gì phải phục hồi, và giữ nó trong danh sách là
       * giữ một tham chiếu tới DOM đã chết. */
      if (!btn.isConnected) continue;
      /* Nút của form KHÁC: để nguyên trạng thái "đang chạy" — request của
       * nó chưa xong. `btn.form` là form mà trình duyệt gắn nút vào, kể cả
       * khi nút dùng thuộc tính `form="…"` để trỏ ra ngoài bảng. */
      if (btn.form !== form) {
        still.push(btn);
        continue;
      }
      btn.disabled = false;
      if (btn.dataset.idleLabel !== undefined) {
        btn.textContent = btn.dataset.idleLabel;
        delete btn.dataset.idleLabel;
      }
      restored.push(btn);
    }
    pendingButtons = still;
    return restored;
  }

  document.addEventListener("click", onClick);
  document.addEventListener("submit", onSubmit, true);
  document.addEventListener("submit", onSlowSubmit, true);
  document.addEventListener("change", onChange);
  document.addEventListener("cancel", onDialogCancel, true);
  window.addEventListener("popstate", onPopState);
  document.addEventListener("DOMContentLoaded", upgradeDialogs);

  /* ------------------------------------------------------------------
   * Biểu đồ: tooltip khi rê chuột, thay vì phải ước lượng qua trục Y.
   * `<title>` gốc vẫn còn nguyên (không JS vẫn xem được, chỉ chậm hơn) —
   * đây chỉ là một lớp hiện nhanh hơn, không thay thế thông tin gốc.
   * ------------------------------------------------------------------ */
  var tooltip = null;

  function ensureTooltip() {
    if (tooltip && document.body.contains(tooltip)) return tooltip;
    tooltip = document.createElement("div");
    tooltip.className = "rev-tooltip";
    tooltip.hidden = true;
    document.body.appendChild(tooltip);
    return tooltip;
  }

  function pointLabel(point) {
    return point.getAttribute("title") || "";
  }

  function showTooltip(point, event) {
    var tip = ensureTooltip();
    var text = pointLabel(point);
    if (!text) return;
    tip.textContent = text;
    tip.hidden = false;
    positionTooltip(tip, event);
  }

  function positionTooltip(tip, event) {
    var pad = 14;
    var x = event.clientX + pad;
    var y = event.clientY + pad;
    var rect = tip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - pad;
    if (y + rect.height > window.innerHeight) y = event.clientY - rect.height - pad;
    tip.style.left = Math.max(4, x) + "px";
    tip.style.top = Math.max(4, y) + "px";
  }

  function hideTooltip() {
    if (tooltip) tooltip.hidden = true;
  }

  function chartPointTarget(event) {
    return event.target.closest(
      ".rev-line-dot, .rev-line-point[data-metric='chart-bar']," +
      " .rev-line-point[data-metric='chart-bar-prev']");
  }

  document.addEventListener("mouseover", function (event) {
    var point = chartPointTarget(event);
    if (point) showTooltip(point, event);
  });
  document.addEventListener("mousemove", function (event) {
    if (tooltip && !tooltip.hidden) {
      var point = chartPointTarget(event);
      if (point) positionTooltip(tooltip, event);
      else hideTooltip();
    }
  });
  document.addEventListener("mouseout", function (event) {
    var point = chartPointTarget(event);
    if (point && !event.relatedTarget) hideTooltip();
  });
  document.addEventListener("app:content-updated", hideTooltip);
})();


/* --- R5 §5: một nút mở/đóng chung cho Hãng & IMEI ------------------------
 *
 * Hai cột này ẩn bằng CSS dựa trên `data-optional-hidden` trên chính bảng,
 * nên trạng thái mặc định đúng ngay ở khung hình đầu tiên và trang không
 * JavaScript vẫn hiện một bảng gọn. Đoạn dưới đây chỉ thêm cái NÚT.
 *
 * Lựa chọn được nhớ trong `localStorage`, không gửi lên server: nó là một
 * sở thích xem của một người trên một máy, không phải một quyết định nghiệp
 * vụ. Gửi nó lên server sẽ biến một thao tác xem thành một lần ghi, và biến
 * một tuỳ chọn giao diện thành một thứ phải có vòng đời, phải sao lưu, phải
 * giải thích khi hai người thấy hai bảng khác nhau.
 *
 * `localStorage` không dùng được (chế độ riêng tư, trình duyệt chặn) là một
 * trạng thái BÌNH THƯỜNG ở đây: nút vẫn bấm được, chỉ không nhớ qua các lần
 * tải trang. Vì vậy mọi lần đọc/ghi đều bọc `try`.
 */
(function () {
  var KEY = "tp.workspace.optionalColumns";

  function stored() {
    try { return window.localStorage.getItem(KEY) === "1"; } catch (e) { return false; }
  }

  function remember(on) {
    try { window.localStorage.setItem(KEY, on ? "1" : "0"); } catch (e) { /* bỏ qua */ }
  }

  function apply(on) {
    var tables = document.querySelectorAll(".sheet-table");
    for (var i = 0; i < tables.length; i++) {
      if (on) tables[i].removeAttribute("data-optional-hidden");
      else tables[i].setAttribute("data-optional-hidden", "1");
    }
    var buttons = document.querySelectorAll("[data-optional-toggle]");
    for (var j = 0; j < buttons.length; j++) {
      buttons[j].textContent = on
        ? buttons[j].getAttribute("data-hide-label")
        : buttons[j].getAttribute("data-show-label");
      buttons[j].setAttribute("aria-pressed", on ? "true" : "false");
    }
  }

  function sync() {
    if (document.querySelector("[data-optional-toggle]")) apply(stored());
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-optional-toggle]");
    if (!button) return;
    var on = button.getAttribute("aria-pressed") !== "true";
    remember(on);
    apply(on);
  });

  document.addEventListener("DOMContentLoaded", sync);
  document.addEventListener("app:content-updated", sync);
  sync();
})();


/* --- R5 §5: popover phân loại neo tại chỗ bấm ---------------------------
 *
 * Trước R5, bảng chọn mặt hàng nằm PHÍA TRÊN bảng kê: bấm một dòng ở giữa
 * trang là màn hình nhảy lên đầu, chọn xong lại phải cuộn tìm về chỗ cũ. Với
 * một sheet vài trăm dòng, việc đó xảy ra ở mỗi lần phân loại.
 *
 * Lớp này KHÔNG đổi kiến trúc: server vẫn dựng đúng khối ấy ở đúng chỗ ấy,
 * và tắt JavaScript thì nó vẫn là một bảng chọn dùng được với những POST
 * thật. Ở đây chỉ có ba việc — dời khối tới toạ độ vừa bấm, giữ nó trong
 * khung nhìn, và đóng bằng Escape hay một cú bấm ra ngoài.
 *
 * Toạ độ được nhớ ở `lastClick` khi Owner bấm vào một lối vào phân loại, chứ
 * không đọc lúc popover xuất hiện: giữa hai thời điểm đó có một lượt fetch,
 * và con trỏ chuột lúc ấy đã ở đâu thì không ai biết.
 */
(function () {
  "use strict";

  var PAD = 8;
  var lastClick = null;

  function isOpener(target) {
    return target.closest(
      "[data-metric='identity-open'], [data-metric='identity-label']");
  }

  document.addEventListener("click", function (event) {
    if (isOpener(event.target)) {
      lastClick = { x: event.clientX, y: event.clientY };
    }
  }, true);

  function place(pop) {
    if (!lastClick) return;               /* mở bằng bàn phím/URL: để nguyên */
    pop.classList.add("is-anchored");
    var rect = pop.getBoundingClientRect();
    var x = lastClick.x;
    var y = lastClick.y + 12;
    if (x + rect.width > window.innerWidth - PAD) {
      x = window.innerWidth - rect.width - PAD;
    }
    if (y + rect.height > window.innerHeight - PAD) {
      y = lastClick.y - rect.height - 12;
    }
    pop.style.left = Math.max(PAD, x) + "px";
    pop.style.top = Math.max(PAD, y) + "px";
    var box = pop.querySelector("[data-identify-search]");
    if (box) box.focus();
  }

  function current() {
    return document.querySelector("[data-identify-pop]");
  }

  function close() {
    var pop = current();
    if (!pop) return false;
    var cancel = pop.querySelector("[data-metric='identify-cancel']");
    if (cancel) cancel.click();
    return true;
  }

  function sync() {
    var pop = current();
    if (pop) place(pop);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && current()) {
      event.preventDefault();
      close();
    }
  });

  document.addEventListener("click", function (event) {
    var pop = current();
    if (!pop || pop.contains(event.target) || isOpener(event.target)) return;
    close();
  });

  document.addEventListener("app:content-updated", sync);
  document.addEventListener("DOMContentLoaded", sync);
  sync();
})();

/*
 * `DEC-213` — nút CHỦ ĐỀ SÁNG/TỐI, chép cơ chế của Tracking.
 *
 * Đây là một tuỳ chọn TRÌNH BÀY thuần tuý: nó chỉ bật/tắt lớp `dark` trên
 * `<body>` và ghi lựa chọn vào `localStorage`. Nó không gọi một route nào,
 * không đọc/ghi một con số nghiệp vụ nào, và tắt JS thì trang vẫn dùng chủ
 * đề sáng — đúng cùng kỷ luật "lớp tăng cường" mà cả file này đứng trên.
 *
 * Lớp `dark` được ĐẶT sớm hơn, bởi một script inline trong `layout.html`
 * chạy trước lần vẽ đầu tiên; ở đây chỉ còn việc vẽ nút và xử lý cú bấm.
 * Chia hai chỗ là có lý do: gộp cả vào file này (nạp ở cuối trang) thì
 * người dùng nền tối thấy một nháy trắng ở mỗi lần tải trang.
 */
(function () {
  "use strict";

  var KEY = "tp_theme";

  /* Biểu tượng vẽ VIỆC SẼ XẢY RA khi bấm, không vẽ trạng thái đang có —
   * đang sáng thì hiện mặt trăng (bấm để sang tối). Cùng quy ước Tracking. */
  var MOON = '<svg class="tp-ico" viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M20.5 14.6A8.5 8.5 0 1 1 9.4 3.5a6.8 6.8 0 0 0 11.1 11.1Z"/></svg>';
  var SUN = '<svg class="tp-ico" viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true">' +
    '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.2M12 19.2v2.2' +
    'M4.6 12H2.4M21.6 12h-2.2M6.8 6.8 5.2 5.2M18.8 18.8l-1.6-1.6' +
    'M6.8 17.2l-1.6 1.6M18.8 5.2l-1.6 1.6"/></svg>';

  function stored() {
    /* `localStorage` NÉM lỗi ở chế độ ẩn danh của vài trình duyệt. Một tuỳ
     * chọn giao diện không được làm hỏng cả trang, nên mọi lần chạm đều
     * được bọc và lỗi đọc là "chưa chọn gì". */
    try {
      return window.localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function remember(value) {
    try {
      window.localStorage.setItem(KEY, value);
    } catch (e) { /* không lưu được thì lựa chọn chỉ sống trong phiên này */ }
  }

  function render() {
    var button = document.getElementById("btnTheme");
    if (!button) return;
    var dark = document.body.classList.contains("dark");
    button.innerHTML = dark ? SUN : MOON;
    button.title = dark ? "Chuyển sang giao diện sáng"
                        : "Chuyển sang giao diện tối";
    button.setAttribute("aria-label", button.title);
    button.setAttribute("aria-pressed", dark ? "true" : "false");
  }

  function toggle() {
    var dark = !document.body.classList.contains("dark");
    document.body.classList.toggle("dark", dark);
    remember(dark ? "toi" : "sang");
    render();
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("#btnTheme");
    if (!button) return;
    event.preventDefault();
    toggle();
  });

  /* Thanh đầu trang nằm NGOÀI `#app-content`, nên nó sống sót qua mỗi lần
   * thay mảnh — nút chỉ cần vẽ một lần. Vẫn nghe `app:content-updated` để
   * một lần điều hướng THẬT (tải lại cả trang) cũng vẽ lại đúng. */
  document.addEventListener("DOMContentLoaded", render);
  if (stored() === "toi") document.body.classList.add("dark");
  render();
})();
