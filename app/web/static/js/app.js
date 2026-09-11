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

  /* `UI-01`/`UI-02` — panel sửa đơn (khối script cuối file) mở/đóng bằng
   * `history.pushState`/`history.back()` trên HASH của trang (`#sua=...`),
   * không đụng tới `#app-content`. Popstate của MỘT trong hai lượt đó phải
   * KHÔNG rơi vào `navigate()` ở dưới — làm vậy sẽ fetch lại cả mảnh và
   * đóng panel một cách vô nghĩa, đúng lỗi mà panel tồn tại để tránh.
   *
   * Thay vì để module này BIẾT tên cơ chế panel (hai module theo hai lớp
   * mối quan tâm khác nhau), một `CustomEvent` HUỶ ĐƯỢC (`cancelable`) được
   * phát trước: panel nghe sự kiện này, và nếu chính nó xử lý popstate thì
   * gọi `preventDefault()` — cùng giao thức `app:content-updated` đã dùng
   * ở nơi khác trong file này. */
  function onPopState() {
    var event = new window.CustomEvent("app:popstate", { cancelable: true });
    document.dispatchEvent(event);
    if (event.defaultPrevented) return;
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
  /* `UI-03` — popover nay còn được dán vào chỗ bằng một lượt fetch nhỏ
   * (route `/api/v1/periods/<kỳ>/identify`) thay vì bằng một lần dựng lại
   * cả `#app-content`. Sự kiện RIÊNG cho đúng việc đó: `app:content-updated`
   * mang nghĩa "cả vùng nội dung vừa bị thay" và kéo theo những việc khác
   * (đóng panel sửa đơn, ẩn tooltip) không đúng ở đây. */
  document.addEventListener("app:identify-updated", sync);
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

/*
 * `UI-01`/`UI-02` — panel sửa MỘT ĐƠN tại chỗ, thay cho `?sua=` dựng lại
 * cả bảng. Đây là lớp TĂNG CƯỜNG đúng kỷ luật đầu file: nút "Sửa" của mỗi
 * BH vẫn là một `<a href="?sua=...">` THẬT — tắt JS thì nó vẫn mở đúng
 * chế độ sửa cũ, dựng bởi server, y hệt trước `UI-01`. Có JS thì khối này
 * `preventDefault()` cú bấm đó, mở một `<dialog>` dựng bởi CHÍNH JS ngay
 * cạnh hàng/nút vừa bấm, gọi `GET /api/v1/orders/<order_key>` lấy dữ liệu,
 * và `PATCH` cùng route đó để lưu — không một lần nào dựng lại `#app-content`.
 *
 * ## Ba hình dạng, một cơ chế
 *
 * `<dialog>` là MỘT phần tử cho cả ba hình dạng brief đòi (popover/side
 * panel/bottom sheet); CSS (`tinphat-ui.css`, khối `.tp-order-panel`)
 * quyết định nó TRÔNG như gì:
 *
 *   `--popover`  BH ít dòng: neo cạnh nút vừa bấm, như `.identify-pop`.
 *   `--side`     BH nhiều dòng: cố định bên phải, cao hết màn hình.
 *   mobile       CSS (`@media max-width: 760px`) ĐÈ cả hai thành bottom
 *                sheet — JS không cần biết mình đang chạy trên máy nào,
 *                đúng nguyên tắc "trạng thái mặc định đúng ngay ở khung
 *                hình đầu tiên" mà khối toggle Hãng/IMEI phía trên đã dùng.
 *
 * `showModal()` cho CẢ BA: nền mờ + bẫy focus + phím Esc phát sự kiện
 * `cancel` đều là cơ chế NỀN TẢNG của `<dialog>`, không phải thứ JS này tự
 * dựng — cùng cách `target-edit-inline` đã dùng ở trên.
 *
 * ## Sâu liên kết qua HASH, không qua query `sua=`
 *
 * `?sua=<order_key>` VẪN LÀ đường không-JS — server đọc nó, dựng lại toàn
 * trang ở chế độ sửa cũ. Panel KHÔNG dùng query đó (dùng nó sẽ khiến mọi
 * điều hướng/refresh chạy lại đường dựng-lại-cả-bảng mà `UI-01` tồn tại để
 * tránh). Panel ghi trạng thái của nó vào HASH (`#sua=<order_key>`) bằng
 * `history.pushState`: Back/Forward đổi hash, `onPopState` (ở IIFE đầu
 * file) phát `app:popstate` — panel bắt sự kiện đó, tự mở/đóng, và gọi
 * `preventDefault()` để `onPopState` KHÔNG fetch lại mảnh.
 *
 * ## Vì sao `changed_nothing`/`already_applied` không đổi luồng UI
 *
 * `PATCH` có thể trả về mà KHÔNG ghi gì (`plan.changes_nothing`) hoặc là
 * một lần THỬ LẠI đã có kết quả (`already_applied`) — cả hai vẫn là
 * response THÀNH CÔNG (status 200, có đủ `lines`/`totals`), nên panel xử
 * lý chúng y hệt một lần ghi thật: cập nhật hàng + trạng thái "Đã lưu".
 * Phân biệt hai ca đó không đổi gì những gì người dùng cần thấy.
 */
(function () {
  "use strict";

  var MAIN_REGION_ID = "app-content";
  var HASH_PREFIX = "#sua=";

  function contentEl() { return document.getElementById(MAIN_REGION_ID); }

  /* Thoát HTML của mọi chữ đến từ server (tên khách hàng, tên mặt hàng…)
   * trước khi ghép vào `innerHTML` — panel này KHÔNG dùng `textContent`
   * cho từng ô vì cấu trúc lồng khá sâu, nên mọi chỗ nội suy chữ động đều
   * phải đi qua hàm này, không có ngoại lệ. */
  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  /* Chuỗi thập phân CHÍNH XÁC do server gửi (`"5000000"`) → chữ có dấu
   * chấm ngăn nghìn để GÕ VÀO ("5.000.000"), đúng quy ước `PRICE_INPUT_
   * NOTE` mà ô giá của form HTML cũ dùng. Đây là ĐỊNH DẠNG CHỮ thuần tuý
   * (chèn dấu chấm), không phải một phép tính — không vi phạm ranh giới
   * "không tính lại con số nghiệp vụ nào ở client" mà `order_api.py` đặt
   * ra, vì không có phép cộng/chia/làm tròn nào ở đây. */
  function dottedInput(exact) {
    if (!exact) return "";
    var neg = exact.charAt(0) === "-";
    var digits = neg ? exact.slice(1) : exact;
    var dot = digits.indexOf(".");
    var intPart = dot === -1 ? digits : digits.slice(0, dot);
    var frac = dot === -1 ? "" : digits.slice(dot);
    var withDots = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (neg ? "-" : "") + withDots + frac;
  }

  function uuid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return "p" + Date.now().toString(36) + "-" +
      Math.random().toString(36).slice(2, 10);
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(value);
    }
    return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  }

  /* --- Vùng "response cũ" của lượt GET chi tiết đơn -----------------
   * Cùng ý tưởng `STAB-05` của IIFE điều hướng chính, tự dựng lại ở đây vì
   * hai module không chia sẻ trạng thái riêng của nhau (mỗi IIFE đóng kín).
   * Mở panel A rồi B thật nhanh: response của A về SAU response của B phải
   * bị bỏ, không được vẽ đè lên panel đang hiện B. */
  var detailSeq = 0;
  function nextDetailTicket() { detailSeq += 1; return detailSeq; }
  function isLatestDetail(ticket) { return ticket === detailSeq; }

  /* Trạng thái panel đang mở, hoặc `null`. Tại một thời điểm chỉ MỘT panel
   * được mở — mở panel khác tự đóng panel cũ trước (`openPanel`). */
  var panel = null;

  var STATUS_TEXT = {
    loading: "Đang tải…",
    idle: "",
    saving: "Đang lưu…",
    saved: "Đã lưu",
    conflict: "Đơn này đã được thay đổi từ lúc bạn mở nó.",
    unconfirmed: "Chưa xác nhận được kết quả. Dữ liệu bạn nhập vẫn còn — " +
      "bấm THỬ LẠI để gửi lại đúng lần ghi này.",
    error: "Không mở được panel."
  };

  function setStatus(dialog, state, extra) {
    var host = dialog.querySelector('[data-metric="order-panel-status"]');
    if (!host) return;
    var text = STATUS_TEXT[state] || state;
    host.textContent = extra ? text + " " + extra : text;
    host.setAttribute("data-state", state);
    var retry = dialog.querySelector('[data-metric="order-panel-retry"]');
    if (retry) retry.hidden = (state !== "unconfirmed" && state !== "conflict");
  }

  /* --- Mở panel -------------------------------------------------------- */

  function orderKeyFromHash() {
    var hash = window.location.hash;
    if (hash.indexOf(HASH_PREFIX) !== 0) return null;
    try { return decodeURIComponent(hash.slice(HASH_PREFIX.length)); }
    catch (e) { return null; }
  }

  function openerFor(orderKey) {
    var el = contentEl();
    if (!el) return null;
    return el.querySelector(
      '[data-metric="bh-edit"][data-order="' + cssEscape(orderKey) + '"]');
  }

  function tableOf(orderKey) {
    var opener = openerFor(orderKey);
    return opener && opener.closest("table.sheet-table");
  }

  /* `orderKey` + tuỳ chọn `{opener, pushHistory}`. `pushHistory` sai khi
   * lời gọi này ĐẾN TỪ một popstate (hash đã đổi rồi, đẩy thêm một lần
   * nữa sẽ nhân đôi entry) hoặc từ việc khôi phục một deep-link lúc tải
   * trang (hash đã có sẵn trên URL, không phải một cú bấm mới). */
  function openPanel(orderKey, opts) {
    opts = opts || {};
    if (panel && panel.orderKey === orderKey) {
      panel.dialog.focus();
      return;
    }
    if (panel) teardownPanel();

    var opener = opts.opener || openerFor(orderKey);
    var table = tableOf(orderKey);
    var period = table ? table.dataset.period : "";
    var sheet = table ? table.dataset.sheet : "";

    var dialog = document.createElement("dialog");
    dialog.className = "tp-order-panel tp-order-panel--popover";
    dialog.setAttribute("data-metric", "order-panel");
    dialog.setAttribute("data-order", orderKey);
    dialog.setAttribute("aria-label", "Sửa đơn " + orderKey);
    dialog.innerHTML =
      '<div class="tp-order-panel-head">' +
        '<h3>Đơn <span data-metric="order-panel-title"></span></h3>' +
        '<button type="button" class="ghost btn-mini" ' +
          'data-metric="order-panel-close" aria-label="Đóng">&#10005;</button>' +
      "</div>" +
      '<div class="tp-order-panel-body" data-metric="order-panel-body">' +
        '<p class="empty">Đang tải…</p>' +
      "</div>";
    dialog.querySelector('[data-metric="order-panel-title"]').textContent = orderKey;
    document.body.appendChild(dialog);

    panel = {
      orderKey: orderKey, dialog: dialog, opener: opener || null,
      period: period, sheet: sheet, pushedHistory: false, torn: false,
      idempotencyKey: uuid(), orderRevision: null, periodRevision: null
    };

    if (opts.pushHistory) {
      history.pushState({ tpPanel: orderKey }, "",
        "#sua=" + encodeURIComponent(orderKey));
      panel.pushedHistory = true;
    }

    wireDialogChrome(dialog);
    try {
      dialog.showModal();
      positionPopover(dialog, opener);
    } catch (e) {
      /* Môi trường không hỗ trợ `showModal()` (jsdom cũ, browser rất cũ):
       * vẫn hiện panel bằng thuộc tính `open` — không modal, nhưng dùng
       * được, cùng lối dự phòng `upgradeDialogs()` đã dùng ở trên. */
      dialog.setAttribute("open", "");
    }

    loadDetail(orderKey, period, dialog);
  }

  function wireDialogChrome(dialog) {
    dialog.addEventListener("cancel", function (event) {
      event.preventDefault();
      requestClose();
    });
    dialog.addEventListener("click", function (event) {
      if (event.target !== dialog) return;
      var rect = dialog.getBoundingClientRect();
      var outside = event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) requestClose();
    });
    dialog.addEventListener("click", function (event) {
      var close = event.target.closest &&
        event.target.closest('[data-metric="order-panel-close"]');
      if (close) requestClose();
    });
  }

  /* Neo panel cạnh nút vừa bấm (chỉ hình dạng `--popover`; `--side` cố
   * định bằng CSS, không cần toạ độ). Không có `opener` (deep-link tới một
   * đơn không có mặt trên bảng đang hiện, hoặc mở bằng bàn phím) thì để
   * CSS mặc định (giữa màn hình) — cùng quy ước `identify-pop` đã dùng. */
  function positionPopover(dialog, opener) {
    if (!opener || !dialog.classList.contains("tp-order-panel--popover")) return;
    var pad = 8;
    var anchor = opener.getBoundingClientRect();
    var rect = dialog.getBoundingClientRect();
    var x = anchor.left;
    var y = anchor.bottom + 10;
    if (x + rect.width > window.innerWidth - pad) {
      x = window.innerWidth - rect.width - pad;
    }
    if (y + rect.height > window.innerHeight - pad) {
      y = anchor.top - rect.height - 10;
    }
    dialog.classList.add("is-anchored");
    dialog.style.left = Math.max(pad, x) + "px";
    dialog.style.top = Math.max(pad, y) + "px";
  }

  /* Số dòng NGƯỠNG để coi một đơn là "đơn giản" (popover) hay "nhiều
   * dòng" (side panel). Ba trở xuống là một BH điển hình của một hoá đơn
   * lẻ; brief không cho một con số cứng nên đây là một lựa chọn trình bày,
   * không phải một luật nghiệp vụ — đổi nó không ảnh hưởng gì tới dữ liệu. */
  var SIMPLE_LINE_THRESHOLD = 3;

  function upgradeShape(dialog, lineCount) {
    if (lineCount <= SIMPLE_LINE_THRESHOLD) return;
    dialog.classList.remove("tp-order-panel--popover");
    dialog.classList.add("tp-order-panel--side");
    dialog.classList.remove("is-anchored");
    dialog.style.left = "";
    dialog.style.top = "";
  }

  /* --- GET chi tiết đơn -------------------------------------------------- */

  function loadDetail(orderKey, period, dialog) {
    var ticket = nextDetailTicket();
    var url = "/api/v1/orders/" + encodeURIComponent(orderKey) +
      "?period=" + encodeURIComponent(period || "");
    fetch(url, { headers: { Accept: "application/json" } })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!isLatestDetail(ticket) || !panel || panel.dialog !== dialog) return;
        if (!result.ok) {
          renderLoadError(dialog,
            (result.body && result.body.error && result.body.error.message) ||
            "Không mở được panel.");
          return;
        }
        panel.orderRevision = result.body.order_revision;
        panel.periodRevision = result.body.period_revision;
        renderDetail(dialog, result.body);
      })
      .catch(function (error) {
        if (error && error.name === "AbortError") return;
        if (!isLatestDetail(ticket) || !panel || panel.dialog !== dialog) return;
        renderLoadError(dialog,
          "Không kết nối được máy chủ. Bấm THỬ LẠI để tải lại panel này.");
      });
  }

  function renderLoadError(dialog, message) {
    var body = dialog.querySelector('[data-metric="order-panel-body"]');
    body.innerHTML =
      '<p class="error" data-metric="order-panel-load-error">' + esc(message) +
      "</p>" +
      '<p><button type="button" class="ghost btn-mini" ' +
        'data-metric="order-panel-load-retry">THỬ LẠI</button></p>';
    body.querySelector('[data-metric="order-panel-load-retry"]')
      .addEventListener("click", function () {
        if (!panel) return;
        body.innerHTML = '<p class="empty">Đang tải…</p>';
        loadDetail(panel.orderKey, panel.period, dialog);
      });
  }

  function employeeOptionsHtml(employees, selected) {
    var html = "";
    for (var i = 0; i < employees.length; i++) {
      var opt = employees[i];
      html += '<option value="' + esc(opt.value) + '"' +
        (opt.value === selected ? " selected" : "") + ">" +
        esc(opt.label) + "</option>";
    }
    return html;
  }

  function lineRowHtml(line, canEdit) {
    var editable = canEdit && line.scope === "reported";
    var priceCell = editable
      ? '<input type="text" inputmode="numeric" class="op-price-input" ' +
        'data-metric="order-panel-price" ' +
        'value="' + esc(dottedInput(line.purchase_price_input)) + '" ' +
        'aria-label="Giá nhập của ' + esc(line.product_raw) + '">'
      : '<span title="' + esc(line.purchase_price.text) + '">' +
        esc(line.purchase_price.text) + "</span>";
    return (
      '<tr data-metric="order-panel-line" ' +
      'data-product-key="' + esc(line.product_key) + '" ' +
      'data-occurrence-index="' + esc(line.occurrence_index) + '" ' +
      'data-scope="' + esc(line.scope) + '">' +
        '<td>' + esc(line.product_raw) +
          (editable ? "" : ' <span class="tp-unit">(' +
            (line.scope === "excluded" ? "đã loại" : "vắng trong sổ") +
            ")</span>") +
        "</td>" +
        '<td class="num">' + esc(line.quantity) + "</td>" +
        '<td class="num">' + priceCell + "</td>" +
        '<td class="num">' + esc(line.sell_price.text) + "</td>" +
        '<td class="num' + (line.kpi_profit.value == null ? " empty-cell" : "") +
          '" data-metric="order-panel-profit">' + esc(line.kpi_profit.text) +
          "</td>" +
      "</tr>"
    );
  }

  function renderDetail(dialog, payload) {
    var body = dialog.querySelector('[data-metric="order-panel-body"]');
    var reportedLines = payload.lines.filter(function (line) {
      return line.scope === "reported";
    });
    var otherLines = payload.lines.filter(function (line) {
      return line.scope !== "reported";
    });
    var canEdit = payload.permissions && payload.permissions.can_edit &&
      reportedLines.length > 0;

    var html = "";
    html += '<p class="insight" data-metric="order-panel-customer">' +
      esc(payload.customer_name || "—") +
      (payload.customer_phone ? " · " + esc(payload.customer_phone) : "") +
      (payload.customer_address ? " · " + esc(payload.customer_address) : "") +
      "</p>";
    if (payload.period_closed) {
      html += '<p class="notice" data-metric="order-panel-closed">' +
        "Kỳ đã chốt — panel chỉ để xem, không thể lưu.</p>";
    }
    html += '<div class="tp-scroll"><table class="tp-order-panel-lines">' +
      "<tr><th>Mặt hàng</th><th>SL</th><th>Giá nhập</th><th>Giá bán</th>" +
      "<th>Lợi nhuận</th></tr>";
    for (var i = 0; i < reportedLines.length; i++) {
      html += lineRowHtml(reportedLines[i], canEdit);
    }
    for (var j = 0; j < otherLines.length; j++) {
      html += lineRowHtml(otherLines[j], canEdit);
    }
    html += "</table></div>";

    if (canEdit) {
      if (payload.employees && payload.employees.length) {
        html += '<label class="tp-label">Nhân viên<br>' +
          '<select data-metric="order-panel-employee">' +
          employeeOptionsHtml(payload.employees, payload.employee_value) +
          "</select></label>";
      }
      html += '<label class="tp-label" data-metric="order-panel-reason-wrap"' +
        (payload.reason_required ? "" : ' hidden') + ">" +
        "Lý do (chỉ cần khi thay một giá đã có)<br>" +
        '<input type="text" data-metric="order-panel-reason" ' +
        'placeholder="Vì sao thay giá tự động?"></label>';
    }

    html += '<div data-metric="order-panel-status" role="status" ' +
      'aria-live="polite"></div>';
    html += '<div class="tp-order-panel-actions">';
    if (canEdit) {
      html += '<button type="button" class="act btn-mini" ' +
        'data-metric="order-panel-save">LƯU</button>';
    }
    html += '<button type="button" class="ghost btn-mini" hidden ' +
      'data-metric="order-panel-retry">THỬ LẠI</button>';
    html += "</div>";

    body.innerHTML = html;
    upgradeShape(dialog, reportedLines.length);
    positionPopover(dialog, panel && panel.opener);

    var save = body.querySelector('[data-metric="order-panel-save"]');
    if (save) save.addEventListener("click", function () { doSave(dialog); });
    var retry = body.querySelector('[data-metric="order-panel-retry"]');
    if (retry) retry.addEventListener("click", function () { doSave(dialog); });

    var firstFocusable = body.querySelector(
      'input, select, button[data-metric="order-panel-save"]');
    (firstFocusable || dialog).focus();
  }

  /* --- PATCH lưu --------------------------------------------------------- */

  function collectPrices(dialog) {
    var rows = dialog.querySelectorAll(
      '[data-metric="order-panel-line"][data-scope="reported"]');
    var prices = [];
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var input = row.querySelector('[data-metric="order-panel-price"]');
      if (!input) continue;
      prices.push({
        product_key: row.dataset.productKey,
        occurrence_index: parseInt(row.dataset.occurrenceIndex, 10),
        value: input.value
      });
    }
    return prices;
  }

  /* Giữ NGUYÊN `idempotency_key` hiện có của panel là hành vi MẶC ĐỊNH,
   * VÔ ĐIỀU KIỆN của hàm này — không có tham số nào chọn giữa "giữ mã" và
   * "sinh mã mới" ở đây. THỬ LẠI của một lần ghi CHƯA XÁC NHẬN (lỗi mạng)
   * gọi thẳng `doSave(dialog)` nên tự động giữ mã cũ, để server nhận ra và
   * không ghi hai lần (`STAB-03` của IIFE điều hướng chính, cùng nguyên
   * tắc). Một lần GỬI LẠI sau `REVISION_CONFLICT` thì KHÁC — đó là một
   * quyết định MỚI (server đã trả lời rõ ràng, không có gì mơ hồ để "thử
   * lại") — nên nơi gọi (`applyConflict()`) tự sinh `panel.idempotencyKey`
   * mới TRƯỚC khi gọi `doSave(dialog)`, thay vì hàm này tự phân nhánh.
   *
   * `REPAIR` (independent review, finding P2) — bản trước có tham số
   * `opts.sameIntent` nhưng không đọc nó ở đâu cả; việc giữ mã "đúng" chỉ
   * vì đây là hành vi MẶC ĐỊNH, không phải vì cờ đó. Xoá tham số chết thay
   * vì để code và chú thích tiếp tục nói hai chuyện khác nhau. */
  function doSave(dialog) {
    if (!panel || panel.dialog !== dialog) return;
    var prices = collectPrices(dialog);
    var employeeField = dialog.querySelector('[data-metric="order-panel-employee"]');
    var reasonField = dialog.querySelector('[data-metric="order-panel-reason"]');
    var changes = { prices: prices };
    if (employeeField) changes.employee = employeeField.value;

    var body = {
      idempotency_key: panel.idempotencyKey,
      base_revision: panel.orderRevision,
      changes: changes,
      reason: (reasonField && reasonField.value) || null
    };

    var saveBtn = dialog.querySelector('[data-metric="order-panel-save"]');
    var retryBtn = dialog.querySelector('[data-metric="order-panel-retry"]');
    if (saveBtn) saveBtn.disabled = true;
    if (retryBtn) retryBtn.hidden = true;
    setStatus(dialog, "saving");

    var url = "/api/v1/orders/" + encodeURIComponent(panel.orderKey) +
      "?period=" + encodeURIComponent(panel.period || "") +
      "&sheet=" + encodeURIComponent(panel.sheet || "");

    /* KHÔNG `signal` — mutation không bao giờ bị abort (đóng panel không
     * huỷ lượt PATCH đang bay; xem `requestClose()`/`teardownPanel()`). */
    fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body)
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          return { status: response.status, ok: response.ok, payload: payload };
        });
      })
      .then(function (result) { handleSaveResult(dialog, result); })
      .catch(function () { handleSaveNetworkError(dialog); });
  }

  function handleSaveNetworkError(dialog) {
    if (!panel || panel.dialog !== dialog) return;
    var saveBtn = dialog.querySelector('[data-metric="order-panel-save"]');
    if (saveBtn) saveBtn.disabled = false;
    setStatus(dialog, "unconfirmed");
  }

  /* `REPAIR` (independent review, finding P0) — bản trước bọc TOÀN BỘ hàm
   * này (kể cả nhánh `result.ok`) trong `if (!panel || panel.dialog !==
   * dialog) return;`. Đóng panel (Escape/nút Đóng/mở panel khác) TRƯỚC KHI
   * PATCH resolve làm `panel`/`panel.dialog` đổi trước khi response về —
   * nhánh thành công khi đó `return` sớm, và `applySuccess()` (cùng
   * `patchTableFromPayload()` bên trong nó) KHÔNG BAO GIỜ chạy dù server đã
   * ghi thành công. Bảng nền giữ giá trị CŨ tới khi F5 — mâu thuẫn trực
   * tiếp với chú thích "Bảng nền LUÔN được cập nhật" ngay trong
   * `applySuccess()`.
   *
   * Sửa: `isCurrentDialog` chỉ gác phần UI CỦA CHÍNH panel đang mở (bật lại
   * nút LƯU, và — bên trong các hàm dưới — vẽ trạng thái conflict/lỗi lên
   * đúng dialog đó). Nhánh `result.ok` gọi `applySuccess()` VÔ ĐIỀU KIỆN:
   * `applySuccess()` tự quyết định phần nào của NÓ cần `panel.dialog ===
   * dialog` (cập nhật ô nhập/trạng thái của panel), còn việc vá bảng nền
   * (`patchTableFromPayload()`) đứng NGOÀI điều kiện đó trong chính hàm ấy
   * — đây là nơi lời hứa "PATCH không bao giờ bị mất vì panel đã đóng" thật
   * sự đúng theo cấu tạo, không chỉ đúng trong chú thích. */
  function handleSaveResult(dialog, result) {
    var isCurrentDialog = !!(panel && panel.dialog === dialog);
    if (isCurrentDialog) {
      var saveBtn = dialog.querySelector('[data-metric="order-panel-save"]');
      if (saveBtn) saveBtn.disabled = false;
    }

    if (result.ok) {
      applySuccess(dialog, result.payload);
      return;
    }

    // Các nhánh dưới đây đều là cập nhật TRẠNG THÁI HIỂN THỊ của panel
    // (conflict/lỗi + các nút đi kèm) — không có gì để vẽ khi panel đã đóng
    // hoặc đã chuyển sang đơn khác, và `panel.orderRevision`/`panel.
    // conflictCurrent` mà `applyConflict()` ghi PHẢI thuộc về đúng panel
    // đang mở, không phải một panel đã đóng hay panel của đơn khác.
    if (!isCurrentDialog) return;

    var err = result.payload && result.payload.error;
    var code = err && err.code;
    if (code === "REVISION_CONFLICT") {
      applyConflict(dialog, err);
      return;
    }
    if (code === "REQUEST_IN_FLIGHT") {
      setStatus(dialog, "unconfirmed",
        "Một lần gửi khác của chính lần lưu này đang xử lý — thử lại sau.");
      return;
    }
    /* VALIDATION_ERROR/PERIOD_CLOSED/NOT_FOUND — lỗi RÕ RÀNG, không mơ hồ
     * như lỗi mạng. Một lần GỬI LẠI ở đây (nếu người dùng sửa lại rồi bấm
     * LƯU lần nữa) là một quyết định MỚI, không phải thử lại cùng một lần
     * ghi — nên mã KHÔNG cần giữ nguyên qua nhánh này, và nút LƯU (không
     * phải nút THỬ LẠI) là đường quay lại. */
    setStatus(dialog, "error", (err && err.message) || "Lưu thất bại.");
  }

  function applyConflict(dialog, err) {
    /* Draft (những gì người dùng đã gõ) GIỮ NGUYÊN trên input — không có
     * dòng nào ở đây chạm vào `value` của ô giá/nhân viên/lý do. Chỉ trạng
     * thái + hai đường lựa chọn được thêm vào. */
    panel.orderRevision = err.order_revision;
    panel.periodRevision = err.period_revision;
    panel.conflictCurrent = err.current;
    setStatus(dialog, "conflict", "Bản nháp của bạn vẫn còn.");

    var actions = dialog.querySelector(".tp-order-panel-actions");
    if (actions && !actions.querySelector('[data-metric="order-panel-conflict-reload"]')) {
      var reload = document.createElement("button");
      reload.type = "button";
      reload.className = "ghost btn-mini";
      reload.setAttribute("data-metric", "order-panel-conflict-reload");
      reload.textContent = "LẤY GIÁ TRỊ MỚI";
      reload.addEventListener("click", function () {
        reload.remove();
        applyServerValuesToDraft(dialog, panel.conflictCurrent);
        setStatus(dialog, "idle");
      });
      actions.appendChild(reload);
    }
    var retry = dialog.querySelector('[data-metric="order-panel-retry"]');
    if (retry) {
      retry.hidden = false;
      retry.textContent = "GỬI LẠI VỚI BẢN MỚI";
      retry.onclick = function () {
        /* Quyết định MỚI (`§doSave` giải thích vì sao) — mã chống lặp mới,
         * `base_revision` đã được cập nhật ở trên. */
        panel.idempotencyKey = uuid();
        retry.textContent = "THỬ LẠI";
        doSave(dialog);
      };
    }
  }

  function applyServerValuesToDraft(dialog, current) {
    var rows = dialog.querySelectorAll('[data-metric="order-panel-line"]');
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var line = findLine(current.lines, row.dataset.productKey,
        row.dataset.occurrenceIndex);
      if (!line) continue;
      var input = row.querySelector('[data-metric="order-panel-price"]');
      if (input) input.value = dottedInput(line.purchase_price_input);
    }
    var employeeField = dialog.querySelector('[data-metric="order-panel-employee"]');
    if (employeeField) employeeField.value = current.employee_value;
  }

  function findLine(lines, productKey, occurrenceIndex) {
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].product_key === productKey &&
          String(lines[i].occurrence_index) === String(occurrenceIndex)) {
        return lines[i];
      }
    }
    return null;
  }

  function applySuccess(dialog, payload) {
    if (panel && panel.dialog === dialog) {
      panel.orderRevision = payload.order_revision;
      panel.periodRevision = payload.period_revision;
      panel.idempotencyKey = uuid(); // lần ghi kế tiếp là một quyết định MỚI
      var reasonField = dialog.querySelector('[data-metric="order-panel-reason"]');
      if (reasonField) reasonField.value = "";
      setStatus(dialog, "saved");
      for (var i = 0; i < payload.lines.length; i++) {
        var line = payload.lines[i];
        var row = dialog.querySelector(
          '[data-metric="order-panel-line"][data-product-key="' +
          cssEscape(line.product_key) + '"][data-occurrence-index="' +
          cssEscape(line.occurrence_index) + '"]');
        if (row) {
          var input = row.querySelector('[data-metric="order-panel-price"]');
          if (input) input.value = dottedInput(line.purchase_price_input);
          var profit = row.querySelector('[data-metric="order-panel-profit"]');
          if (profit) profit.textContent = line.kpi_profit.text;
        }
      }
    }
    /* Bảng nền LUÔN được cập nhật, kể cả khi panel đã bị đóng trong lúc
     * PATCH còn bay (đóng panel không huỷ mutation — xem `requestClose()`).
     * Đây là nơi item `§4` "chỉ cập nhật các hàng đã đổi" thật sự xảy ra
     * trên trang, không phải bên trong panel. */
    patchTableFromPayload(payload);
  }

  /* --- Vá lại BẢNG NỀN sau một lần lưu thành công ------------------------
   *
   * KHÔNG dựng lại `#app-content`. Mỗi dòng đã đổi được tìm bằng đúng khoá
   * ổn định (`data-product-key`/`data-occurrence-index`, gắn ở template —
   * xem `kinh_doanh_nhan_vien.html`), và chỉ những Ô đã có `data-metric`
   * sẵn mới bị ghi — không dòng HTML nào bị dựng lại từ đầu.
   *
   * Hàng TỔNG (Giá nhập/Giá bán) được vá bằng `totals.sheet.row_totals` —
   * SERVER tính, cùng hàm trình bày mà lần render đầy đủ dùng
   * (`workspace_presentation.sheet_detail_totals`, xem `order_api.py`).
   * Dải KPI phía trên (Doanh thu/DS quy đổi/So Target…) KHÔNG được vá:
   * những ô đó mang nhãn CHÍNH THỨC/CHƯA HOÀN CHỈNH (`R-S7`) dựng từ một
   * đối tượng gate mà response PATCH không mang theo, và đoán gate đó ở
   * client là đúng lớp lỗi "dựng thẩm quyền nghiệp vụ thứ hai" mà
   * `order_api.py` cấm ngay ở docstring đầu file — nên panel để nguyên,
   * đúng như brief `§4` cho phép ("KPI/summary MÀ SERVER TRẢ VỀ").
   */
  function patchTableFromPayload(payload) {
    var opener = openerFor(payload.order_key);
    var table = opener ? opener.closest("table.sheet-table") : null;
    if (!table) return;

    for (var i = 0; i < payload.lines.length; i++) {
      var line = payload.lines[i];
      if (line.scope !== "reported") continue;
      // `data-order` PHẢI có mặt trong selector: `product_key` định danh
      // một MẶT HÀNG, không phải một dòng — hai đơn khác nhau đặt cùng một
      // mặt hàng ở vị trí đầu tiên (`occurrence_index` = 1 của cả hai) là
      // chuyện bình thường, và thiếu `data-order` sẽ vá NHẦM hàng của đơn
      // khác (khớp phần tử ĐẦU TIÊN trong DOM, không phải phần tử ĐÚNG).
      var row = table.querySelector(
        'tr[data-order="' + cssEscape(payload.order_key) +
        '"][data-product-key="' + cssEscape(line.product_key) +
        '"][data-occurrence-index="' + cssEscape(line.occurrence_index) + '"]');
      if (!row) continue;
      patchPriceCell(row, line.purchase_price);
      patchDerivedCell(row, "line-profit", line.kpi_profit);
      patchDerivedCell(row, "line-converted", line.converted_sales);
    }
    // Nhân viên thuộc về CẢ đơn, không về từng dòng (`§27`) — vá MỘT lần
    // cho cả BH bằng dòng đầu tiên, thay vì lặp lại việc này ở mỗi dòng.
    if (payload.lines.length) {
      var first = payload.lines[0];
      patchEmployeeCells(table, payload.order_key, first.employee,
        first.employee_resolved);
    }

    if (payload.totals && payload.totals.sheet && payload.totals.sheet.row_totals) {
      var rt = payload.totals.sheet.row_totals;
      patchTotalsCell(table, "totals-purchase", rt.purchase_price,
        rt.purchase_price_full);
      patchTotalsCell(table, "totals-sell", rt.sell_price, rt.sell_price_full);
    }
  }

  function patchPriceCell(row, money) {
    var cell = row.querySelector('td[data-metric="purchase_price"]');
    if (!cell) return;
    var span = cell.querySelector("span");
    if (!span) { span = document.createElement("span"); cell.appendChild(span); }
    span.textContent = money.text;
    if (money.value != null) span.title = money.text + " đồng";
    else span.removeAttribute("title");
  }

  function patchDerivedCell(row, metric, money) {
    var cell = row.querySelector('td[data-metric="' + metric + '"]');
    if (!cell) return;
    cell.textContent = money.text;
    cell.classList.toggle("empty-cell", money.value == null);
    if (money.value != null) cell.title = money.text + " đồng";
    else cell.removeAttribute("title");
  }

  function patchEmployeeCells(table, orderKey, employee, resolved) {
    var rows = table.querySelectorAll(
      'tr[data-order="' + cssEscape(orderKey) + '"]');
    for (var i = 0; i < rows.length; i++) {
      var cell = rows[i].querySelector('td[data-metric="line-employee"]');
      if (!cell || cell.querySelector("select")) continue;
      cell.textContent = employee || "";
      cell.classList.toggle("empty-cell", !resolved);
    }
  }

  function patchTotalsCell(table, metric, text, fullText) {
    var cell = table.querySelector('td[data-metric="' + metric + '"]');
    if (!cell) return;
    cell.textContent = text;
    cell.title = fullText + " đồng";
  }

  /* --- Đóng panel ---------------------------------------------------------
   *
   * Escape/nút Đóng/bấm ra ngoài đi qua `requestClose()`. Nếu panel này ĐÃ
   * đẩy một history entry lúc mở (`pushedHistory`), đóng nó là LÙI một
   * bước (`history.back()`) — popstate quay lại chạy `handlePanelPopState`
   * và đó là nơi DOM thật sự bị gỡ (`teardownPanel`). Nếu panel không đẩy
   * gì (khôi phục từ một deep-link đã có sẵn hash lúc tải trang), không có
   * gì để lùi — gỡ DOM thẳng và tự xoá hash bằng `replaceState`. */
  function requestClose() {
    if (!panel) return;
    if (panel.pushedHistory) { history.back(); return; }
    teardownPanel();
    history.replaceState(null, "", window.location.pathname + window.location.search);
  }

  function teardownPanel() {
    if (!panel || panel.torn) return;
    var current = panel;
    current.torn = true;
    panel = null;
    if (current.dialog.open) {
      try { current.dialog.close(); } catch (e) { /* đã đóng: bỏ qua */ }
    }
    current.dialog.remove();
    if (current.opener && current.opener.isConnected) current.opener.focus();
  }

  /* --- Móc vào cú bấm "Sửa" và vào popstate ------------------------------
   *
   * PHẢI đăng ký ở PHA "CAPTURE" (`true`), không phải bubble mặc định.
   * `onClick()` của IIFE điều hướng chính (đầu file) cũng nghe `click` trên
   * `document`, ở PHA BUBBLE, và nó chặn MỌI link cùng origin trong
   * `#app-content` không phải đường tải file — kể cả link `bh-edit`. Đăng
   * ký ở bubble (như ban đầu) khiến listener đó chạy TRƯỚC (nó đăng ký
   * trước trong file), tự `preventDefault()` + `navigate()` rồi thay
   * `#app-content` bằng trang chỉnh sửa CŨ — đúng lỗi mà `UI-01` tồn tại
   * để đóng, chỉ đổi chỗ. Capture chạy TRƯỚC bubble bất kể thứ tự đăng ký,
   * và `stopPropagation()` ở đây chặn hẳn listener bubble kia nhận được
   * sự kiện. */
  document.addEventListener("click", function (event) {
    var el = contentEl();
    if (!el) return;
    var link = event.target.closest &&
      event.target.closest('[data-metric="bh-edit"]');
    if (!link || !el.contains(link)) return;
    if (event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    event.stopPropagation();
    var orderKey = link.dataset.order;
    if (orderKey) openPanel(orderKey, { opener: link, pushHistory: true });
  }, true);

  /* `app:popstate` — xem chú thích ở `onPopState()` của IIFE điều hướng
   * chính. Panel xử lý một popstate khi hash MỚI mang một đơn (Back/
   * Forward đưa người dùng vào một trạng thái "đang mở panel X"), HOẶC khi
   * panel đang mở (Back/Forward đưa người dùng RA khỏi trạng thái đó) — cả
   * hai đều `preventDefault()` để `navigate()` không chạy. */
  document.addEventListener("app:popstate", function (event) {
    var order = orderKeyFromHash();
    if (!order && !panel) return; // popstate không liên quan gì tới panel
    event.preventDefault();
    if (order) {
      if (!panel || panel.orderKey !== order) {
        openPanel(order, { opener: openerFor(order), pushHistory: false });
      }
    } else if (panel) {
      teardownPanel();
    }
  });

  /* Điều hướng THẬT (đổi kỳ/sheet, bấm một tab khác…) thay cả
   * `#app-content` — DOM của panel (nếu còn) tham chiếu tới những hàng
   * không còn tồn tại. Đóng thẳng, không qua `requestClose()`: không có
   * "lùi một bước" nào đúng nghĩa ở đây, `swapContent()` đã tự thay cả URL. */
  document.addEventListener("app:content-updated", function () {
    if (panel) teardownPanel();
  });

  /* Deep-link lúc tải trang: URL đã mang sẵn `#sua=...` (chia sẻ một liên
   * kết, hoặc Back đưa thẳng vào trang này từ một trang khác). Không đẩy
   * history — hash đã là hash HIỆN TẠI của URL, không phải một trạng thái
   * mới. */
  document.addEventListener("DOMContentLoaded", function () {
    var order = orderKeyFromHash();
    if (order) openPanel(order, { opener: openerFor(order), pushHistory: false });
  });
})();

/*
 * `UI-03`/`UI-04` — GHI TẠI CHỖ và TẢI THEO TRANG trên bảng kê nhân viên.
 *
 * Cùng kỷ luật "lớp tăng cường" của cả file: mọi lối vào ở đây là một
 * `<a href>` hoặc một `<form method="post">` THẬT do server dựng. Tắt
 * JavaScript thì phân loại, loại dòng, khôi phục dòng và xem trang kế đều
 * chạy y như trước — qua điều hướng thật và POST thật. Có JavaScript thì
 * khối này chặn cú bấm và gửi CÙNG những request ấy bằng `fetch`, rồi dán
 * lại đúng những mảnh HTML mà server trả về.
 *
 * ## Client KHÔNG dựng một hàng bảng kê nào
 *
 * Đây là ràng buộc trung tâm, và nó quyết định hình dạng của mọi payload ở
 * đây. Một hàng bảng kê mang `rowspan` theo số dòng của BH, ba cột tuỳ chọn
 * ẩn bằng CSS, bốn loại nhãn trạng thái, hai đường vào phân loại và một ô
 * nhập thuộc về một `<form>` đứng NGOÀI bảng. Ghép lại tất cả những thứ đó
 * bằng JavaScript là dựng một BẢN THỨ HAI của bảng kê — và bản thứ hai sẽ
 * lệch khỏi bản thứ nhất ở lần đầu ai đó thêm một cột, không test template
 * nào soi tới. Nên server trả về CHÍNH những `<tr>` ấy (dựng bởi
 * `_workspace_table.html`, cùng macro mà trang đầy đủ gọi) và ở đây chỉ có
 * `insertBefore` + `remove`.
 *
 * Thứ duy nhất khối này tự dựng là CHROME: một thẻ `<p>` mang câu thông báo
 * của server (`flash`), và hộp xác nhận — mà cả CÂU CHỮ của hộp ấy cũng do
 * server viết, nằm sẵn trong trang dưới dạng `<template>`.
 *
 * ## Ba nguyên tắc kế thừa từ `UI-02`, không được nới ở đây
 *
 * 1. KHÔNG tự gửi lại. Một lỗi mạng không phân biệt được "server chưa nhận"
 *    với "server đã ghi xong nhưng response thất lạc" (`STAB-03`). Popover
 *    giữ nguyên, câu lỗi hiện ra, người dùng bấm lại bằng tay.
 * 2. KHÔNG abort một mutation đang bay. Đóng popover không huỷ request; kết
 *    quả của nó vẫn được áp vào bảng khi nó về.
 * 3. Response CŨ không ghi đè response MỚI cho các lượt ĐỌC (`STAB-05`) —
 *    xem `pageSeq`/`identifySeq` bên dưới.
 */
(function () {
  "use strict";

  var MAIN_REGION_ID = "app-content";
  var SCHEMA = "R7-WORKSPACE-1";

  /* Ngân sách hàng `<tr>` gắn trong DOM cùng lúc. Vượt ngưỡng thì các NHÓM
   * cũ nhất bị GỠ (`trimToBudget`) — nhóm, không phải hàng lẻ: gỡ nửa một BH
   * để lại `rowspan` trỏ vào những hàng không còn tồn tại.
   *
   * 300 chứ không phải 100 (= một trang): người dùng vừa tải trang kế phải
   * còn thấy phần cuối trang trước ngay phía trên, nếu không mỗi lần tải là
   * một lần màn hình nhảy. Ba trang là khoảng đệm nhỏ nhất cho điều đó. */
  var ROW_BUDGET = 300;

  var NETWORK_NOTE = "Chưa xác nhận được kết quả — hãy bấm lại.";

  function contentEl() { return document.getElementById(MAIN_REGION_ID); }

  function tableEl() {
    var el = contentEl();
    return el ? el.querySelector("table.sheet-table") : null;
  }

  function regionEl(name) {
    var el = contentEl();
    return el ? el.querySelector('[data-region="' + name + '"]') : null;
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(value);
    }
    return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  }

  /* `<tr>` KHÔNG phân tích được ngoài ngữ cảnh bảng: gán thẳng vào
   * `innerHTML` của một `<div>` thì trình duyệt vứt bỏ các thẻ hàng và chỉ
   * giữ lại phần chữ. `<template>` thì phân tích đúng nội dung bảng, nên nó
   * là cách duy nhất đọc được một chuỗi `<tr>` do server trả về. */
  function parseRows(html) {
    var host = document.createElement("template");
    host.innerHTML = "<table><tbody>" + html + "</tbody></table>";
    var body = host.content.querySelector("tbody");
    var frag = document.createDocumentFragment();
    while (body && body.firstChild) frag.appendChild(body.firstChild);
    return frag;
  }

  function groupRows(table, orderKey) {
    return table.querySelectorAll(
      'tr[data-order="' + cssEscape(orderKey) + '"]');
  }

  /* Đặt (thay HOẶC chèn) một khối BH vào bảng.
   *
   * Ba nhánh, và nhánh thứ hai là một ca CÓ THẬT chứ không phải phòng xa:
   * khôi phục dòng CUỐI CÙNG của một đơn vừa bị loại — khi ấy cả khối đã
   * biến mất khỏi bảng, nên không có hàng nào để thay, phải CHÈN. Chỗ chèn
   * đọc từ `spec.before`/`spec.after` (server gửi, xem `_workspace_group_
   * html`), không suy ra ở client: thứ tự hiển thị là thứ tự theo NGÀY của
   * cả sheet, và client chỉ giữ một cửa sổ của nó.
   *
   * Cả hai hàng xóm đều vắng ⟹ BH này nằm NGOÀI cửa sổ đang tải. Không chèn
   * gì: nối nó vào cuối bảng sẽ đặt một đơn của ngày 3 xuống dưới một đơn
   * của ngày 28 — sai thứ tự mà không ô nào trên màn hình nói ra. */
  function placeGroup(table, orderKey, spec) {
    var rows = groupRows(table, orderKey);
    if (rows.length) {
      var anchor = rows[0];
      anchor.parentNode.insertBefore(parseRows(spec.html), anchor);
      for (var i = 0; i < rows.length; i++) rows[i].remove();
      return true;
    }
    var before = spec.before ? groupRows(table, spec.before) : [];
    if (before.length) {
      before[0].parentNode.insertBefore(parseRows(spec.html), before[0]);
      return true;
    }
    var after = spec.after ? groupRows(table, spec.after) : [];
    if (after.length) {
      var last = after[after.length - 1];
      last.parentNode.insertBefore(parseRows(spec.html), last.nextSibling);
      return true;
    }
    return false;
  }

  function dropGroup(table, orderKey) {
    var rows = groupRows(table, orderKey);
    for (var i = 0; i < rows.length; i++) rows[i].remove();
  }

  /* --- Vùng HTML do server dựng ---------------------------------------- */

  function applyRegions(regions) {
    Object.keys(regions || {}).forEach(function (name) {
      if (name === "sheet-totals") {
        /* Hàng TỔNG là một `<tr>`: nó không có vùng bọc nào để thay
         * `innerHTML` (một `<div>` giữa `<table>` và `<tr>` không hợp lệ),
         * nên nó được thay bằng chính nó. */
        var table = tableEl();
        var row = table && table.querySelector('tr[data-metric="sheet-totals"]');
        if (!row) return;
        row.parentNode.insertBefore(parseRows(regions[name]), row);
        row.remove();
        return;
      }
      var host = regionEl(name);
      if (host) host.innerHTML = regions[name];
    });
    if (regions && Object.prototype.hasOwnProperty.call(regions, "identify")) {
      /* Popover phân loại vừa đổi chỗ trong DOM — khối neo popover (ở trên
       * trong file này) tự đặt lại toạ độ khi nghe sự kiện này. Một sự kiện
       * RIÊNG chứ không dùng `app:content-updated`: sự kiện kia có nghĩa
       * "cả `#app-content` vừa bị thay", và nó đóng panel sửa đơn đang mở. */
      document.dispatchEvent(new CustomEvent("app:identify-updated"));
    }
  }

  function flash(message, kind) {
    var host = regionEl("flash");
    if (!host) return;
    host.textContent = "";
    if (!message) return;
    var line = document.createElement("p");
    line.className = kind === "error" ? "error" : "insight";
    line.setAttribute("data-metric", kind === "error" ? "error" : "saved");
    /* `textContent`, không `innerHTML`: câu này đến từ server nhưng nó đi
     * qua đúng một đường mà một tên hàng do người dùng gõ có thể lọt vào
     * (`IdentityGatewayError`), và không có lý do gì để nó là HTML. */
    line.textContent = message;
    host.appendChild(line);
  }

  /* --- Ngữ cảnh của bảng đang mở --------------------------------------- */

  function tableContext() {
    var table = tableEl();
    if (!table) return null;
    return {
      table: table,
      period: table.getAttribute("data-period") || "",
      sheet: table.getAttribute("data-sheet") || ""
    };
  }

  function bodyFor(fields) {
    var ctx = tableContext();
    var body = new URLSearchParams();
    body.set("ky", ctx ? ctx.period : "");
    body.set("sheet", ctx ? ctx.sheet : "");
    Object.keys(fields).forEach(function (name) {
      body.set(name, fields[name] == null ? "" : String(fields[name]));
    });
    return body;
  }

  function errorText(payload) {
    var err = payload && payload.error;
    return (err && err.message) || "Không ghi được thay đổi.";
  }

  /* --- Một lần GHI ------------------------------------------------------
   *
   * KHÔNG `signal`: mutation không bao giờ bị abort (nguyên tắc 2 ở đầu
   * khối). KHÔNG nhánh `catch` nào gửi lại (nguyên tắc 1). */
  function sendWrite(url, fields, onDone, onFail) {
    fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
      },
      body: bodyFor(fields).toString()
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          return { ok: response.ok, payload: payload };
        }, function () {
          /* Không phải JSON (một trang lỗi HTML của `abort(400/404)`):
           * cùng cách xử lý như một lỗi rõ ràng, KHÔNG gửi lại. */
          return { ok: false, payload: null };
        });
      })
      .then(function (result) {
        if (result.ok && result.payload) {
          applyWrite(result.payload);
          onDone();
          return;
        }
        onFail(result.payload ? errorText(result.payload)
                              : "Máy chủ từ chối thao tác này.");
      })
      .catch(function () { onFail(NETWORK_NOTE); });
  }

  function applyWrite(payload) {
    if (payload.schema_version !== SCHEMA) {
      /* Server nói một thứ tiếng khác — tải lại thay vì đọc sai. Cùng hợp
       * đồng `order_api.SCHEMA_VERSION` mà panel sửa đơn dùng. */
      window.location.reload();
      return;
    }
    var table = tableEl();
    if (table) {
      var groups = payload.groups || {};
      Object.keys(groups).forEach(function (key) {
        placeGroup(table, key, groups[key]);
      });
      (payload.removed_order_keys || []).forEach(function (key) {
        dropGroup(table, key);
      });
    }
    applyRegions(payload.regions);
    flash(payload.message);
  }

  /* --- Hộp xác nhận neo cạnh nút vừa bấm (`UI-03` §4) ------------------- */

  var confirmBox = null;

  function closeConfirm() {
    if (confirmBox && confirmBox.parentNode) confirmBox.remove();
    confirmBox = null;
  }

  function anchorTo(node, opener) {
    var pad = 8;
    node.classList.add("is-anchored");
    var box = node.getBoundingClientRect();
    var at = opener.getBoundingClientRect();
    var x = at.left;
    var y = at.bottom + 8;
    if (x + box.width > window.innerWidth - pad) {
      x = window.innerWidth - box.width - pad;
    }
    if (y + box.height > window.innerHeight - pad) {
      y = at.top - box.height - 8;
    }
    node.style.left = Math.max(pad, x) + "px";
    node.style.top = Math.max(pad, y) + "px";
  }

  /* `kind` = `"loai"` | `"khoi-phuc"`. Trả `false` khi trang không mang
   * `<template>` câu chữ — khi đó nơi gọi để nguyên hành vi mặc định của
   * trình duyệt, tức đi đúng đường HTML thật. */
  function askConfirm(kind, opener, onYes) {
    var tpl = document.querySelector(
      'template[data-metric="confirm-copy"][data-kind="' + kind + '"]');
    if (!tpl || !tpl.content.firstElementChild) return false;
    closeConfirm();
    confirmBox = tpl.content.firstElementChild.cloneNode(true);
    document.body.appendChild(confirmBox);
    anchorTo(confirmBox, opener);

    var ok = confirmBox.querySelector('[data-metric="line-confirm-ok"]');
    var cancel = confirmBox.querySelector('[data-metric="line-confirm-cancel"]');
    var problem = confirmBox.querySelector('[data-metric="line-confirm-error"]');
    var box = confirmBox;
    if (cancel) cancel.addEventListener("click", function () { closeConfirm(); });
    if (ok) {
      ok.addEventListener("click", function () {
        ok.disabled = true;
        if (problem) { problem.hidden = true; problem.textContent = ""; }
        onYes(
          function () { if (box === confirmBox) closeConfirm(); },
          function (message) {
            /* `UI-03` §5 — popover Ở LẠI, nút bật lại, KHÔNG tự gửi lần
             * thứ hai. Người dùng quyết định có bấm lại hay không. */
            ok.disabled = false;
            if (problem) { problem.hidden = false; problem.textContent = message; }
          });
      });
    }
    (ok || box).focus();
    return true;
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && confirmBox) {
      event.preventDefault();
      closeConfirm();
    }
  });

  document.addEventListener("click", function (event) {
    if (!confirmBox || confirmBox.contains(event.target)) return;
    closeConfirm();
  });

  /* --- Khoá nghiệp vụ của một dòng, đọc từ URL của lối vào -------------- */

  function lineKeysFromHref(href) {
    var url;
    try { url = new URL(href, window.location.href); } catch (e) { return null; }
    var order = url.searchParams.get("order_key");
    var product = url.searchParams.get("product_key");
    var occurrence = url.searchParams.get("occurrence_index");
    if (!order || !product || occurrence == null) return null;
    return {
      order_key: order, product_key: product, occurrence_index: occurrence
    };
  }

  function lineKeysFromForm(form) {
    function field(name) {
      var el = form.querySelector('[name="' + name + '"]');
      return el ? el.value : null;
    }
    var order = field("order_key");
    var product = field("product_key");
    var occurrence = field("occurrence_index");
    if (!order || !product || occurrence == null) return null;
    return {
      order_key: order, product_key: product, occurrence_index: occurrence
    };
  }

  /* --- Bảng chọn phân loại: MỞ bằng một lượt fetch nhỏ ------------------ */

  var identifySeq = 0;

  function openIdentify(href) {
    var ctx = tableContext();
    var keys = lineKeysFromHref(href);
    if (!ctx || !keys) return false;
    identifySeq += 1;
    var ticket = identifySeq;
    var url = "/api/v1/periods/" + encodeURIComponent(ctx.period) +
      "/identify?sheet=" + encodeURIComponent(ctx.sheet) +
      "&phan-loai=1" +
      "&order_key=" + encodeURIComponent(keys.order_key) +
      "&product_key=" + encodeURIComponent(keys.product_key) +
      "&occurrence_index=" + encodeURIComponent(keys.occurrence_index);
    fetch(url, { headers: { Accept: "application/json" } })
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        /* `STAB-05` — bấm nhanh hai dòng khác nhau: response của dòng thứ
         * nhất về SAU không được vẽ đè lên popover của dòng thứ hai. */
        if (ticket !== identifySeq) return;
        applyRegions(payload.regions);
      })
      .catch(function () {
        if (ticket !== identifySeq) return;
        flash("Chưa mở được bảng chọn mặt hàng — hãy thử lại.", "error");
      });
    return true;
  }

  function closeIdentify() {
    var host = regionEl("identify");
    if (host) host.textContent = "";
  }

  /* --- `UI-04`: tải trang kế và giữ ngân sách DOM ----------------------- */

  var pageSeq = 0;
  var loading = false;

  /* Gỡ các NHÓM cũ nhất cho tới khi số hàng về trong ngân sách.
   *
   * Vị trí cuộn: gỡ những hàng nằm TRƯỚC phần người dùng đang nhìn sẽ kéo
   * nội dung lên đúng bằng chiều cao của chúng. Nên chiều cao bị mất được
   * đo và trả lại bằng `window.scrollBy` ngay trong cùng một khung hình —
   * người dùng không thấy màn hình nhảy. */
  function trimToBudget(table) {
    var rows = table.querySelectorAll("tr[data-order]");
    var excess = rows.length - ROW_BUDGET;
    if (excess <= 0) return;
    var top = table.getBoundingClientRect().top;
    var seen = {};
    var order = [];
    for (var i = 0; i < rows.length; i++) {
      var key = rows[i].getAttribute("data-order");
      if (!seen[key]) { seen[key] = []; order.push(key); }
      seen[key].push(rows[i]);
    }
    var removed = 0;
    for (var j = 0; j < order.length && removed < excess; j++) {
      var group = seen[order[j]];
      for (var k = 0; k < group.length; k++) group[k].remove();
      removed += group.length;
    }
    var shift = top - table.getBoundingClientRect().top;
    if (shift) window.scrollBy(0, -shift);
  }

  function loadNextPage(cursor, done) {
    var ctx = tableContext();
    if (!ctx || !cursor || loading) { if (done) done(); return; }
    loading = true;
    pageSeq += 1;
    var ticket = pageSeq;
    var url = "/api/v1/periods/" + encodeURIComponent(ctx.period) +
      "/workspace?sheet=" + encodeURIComponent(ctx.sheet) +
      "&cursor=" + encodeURIComponent(cursor);
    fetch(url, { headers: { Accept: "application/json" } })
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        loading = false;
        if (ticket !== pageSeq) return;
        if (payload.schema_version !== SCHEMA) {
          window.location.reload();
          return;
        }
        var table = tableEl();
        if (!table) return;
        var body = table.tBodies[0] || table;
        body.appendChild(parseRows(payload.rows_html));
        table.setAttribute("data-next-cursor", payload.next_cursor || "");
        applyRegions(payload.regions);
        trimToBudget(table);
      })
      .catch(function () {
        loading = false;
        if (ticket !== pageSeq) return;
        /* Không tự gọi lại: `XEM TIẾP` vẫn nằm đó, người dùng bấm lại. */
        flash("Chưa tải được trang kế — hãy bấm XEM TIẾP lần nữa.", "error");
      })
      .then(function () { if (done) done(); });
  }

  /* --- Móc vào các cú bấm ----------------------------------------------
   *
   * PHA CAPTURE, cùng lý do đã viết ở khối panel sửa đơn: `onClick()` của
   * bộ điều hướng chính (đầu file) nghe `click` ở pha BUBBLE và chặn MỌI
   * link cùng origin trong `#app-content`. Capture chạy trước bubble bất
   * kể thứ tự đăng ký, và `stopPropagation()` ở đây chặn hẳn listener kia.
   *
   * Khối neo popover phân loại (cũng ở file này, đăng ký capture TRƯỚC khối
   * này) vẫn nhận được cú bấm và vẫn ghi lại toạ độ: `stopPropagation()`
   * không chặn các listener khác trên CÙNG một nút. */
  document.addEventListener("click", function (event) {
    var el = contentEl();
    if (!el || !event.target.closest) return;
    if (event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    var target = event.target;

    /* 1. MỞ bảng chọn phân loại (tên hàng xanh, hoặc nhãn trạng thái). */
    var opener = target.closest(
      "[data-metric='identity-open'], [data-metric='identity-label']");
    if (opener && el.contains(opener) && opener.getAttribute("href")) {
      if (openIdentify(opener.getAttribute("href"))) {
        event.preventDefault();
        event.stopPropagation();
      }
      return;
    }

    /* 2. ĐÓNG bảng chọn. */
    var cancel = target.closest("[data-metric='identify-cancel']");
    if (cancel && el.contains(cancel)) {
      event.preventDefault();
      event.stopPropagation();
      closeIdentify();
      return;
    }

    /* 3. XÁC NHẬN một mã Tracking, hoặc "không có trên bảng giá". Hai nút
     *    khác nhau, hai route khác nhau, cùng một cách gửi. */
    var confirmBtn = target.closest(
      "[data-metric='identify-confirm'], " +
      "[data-metric='identify-out-of-catalog-confirm']");
    if (confirmBtn && el.contains(confirmBtn)) {
      var form = confirmBtn.form || confirmBtn.closest("form");
      var keys = form && lineKeysFromForm(form);
      if (!form || !keys) return;      /* thiếu khoá ⟹ để form thật chạy */
      event.preventDefault();
      event.stopPropagation();
      var fields = keys;
      var code = form.querySelector('[name="ma_tracking"]');
      if (code) fields = Object.assign({}, keys, { ma_tracking: code.value });
      confirmBtn.disabled = true;
      sendWrite(form.getAttribute("action"), fields,
        function () { /* popover được đóng bởi chính `regions.identify` rỗng */ },
        function (message) {
          /* `UI-03` §5 — popover Ở LẠI nguyên trạng, nút bật lại. */
          confirmBtn.disabled = false;
          flash(message, "error");
        });
      return;
    }

    /* 4. LOẠI một dòng — qua hộp xác nhận neo cạnh cái thùng rác. */
    var exclude = target.closest("[data-metric='line-exclude']");
    if (exclude && el.contains(exclude) && exclude.getAttribute("href")) {
      var excludeKeys = lineKeysFromHref(exclude.getAttribute("href"));
      if (!excludeKeys) return;
      var asked = askConfirm("loai", exclude, function (done, fail) {
        sendWrite("/kinh-doanh/nhan-vien/loai-dong", excludeKeys, done, fail);
      });
      if (asked) { event.preventDefault(); event.stopPropagation(); }
      return;
    }

    /* 5. KHÔI PHỤC một dòng — cùng hộp xác nhận, câu chữ khác. */
    var restore = target.closest("[data-metric='line-restore']");
    if (restore && el.contains(restore)) {
      var restoreForm = restore.form || restore.closest("form");
      var restoreKeys = restoreForm && lineKeysFromForm(restoreForm);
      if (!restoreKeys) return;
      var fieldsWithAction = Object.assign(
        {}, restoreKeys, { "hanh-dong": "khoi-phuc" });
      var askedRestore = askConfirm("khoi-phuc", restore, function (done, fail) {
        sendWrite("/kinh-doanh/nhan-vien/loai-dong", fieldsWithAction,
                  done, fail);
      });
      if (askedRestore) { event.preventDefault(); event.stopPropagation(); }
      return;
    }

    /* 6. XEM TIẾP — nối thêm một trang vào chính bảng đang mở. */
    var more = target.closest("[data-metric='workspace-more']");
    if (more && el.contains(more)) {
      var cursor = more.getAttribute("data-next-cursor");
      if (!cursor) return;
      event.preventDefault();
      event.stopPropagation();
      more.disabled = true;
      loadNextPage(cursor, null);
      return;
    }
  }, true);

  /* Điều hướng thật (đổi kỳ/sheet) thay cả `#app-content` — hộp xác nhận
   * đang mở trỏ tới một dòng không còn tồn tại. */
  document.addEventListener("app:content-updated", closeConfirm);
})();
