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
        return response.text().then(function (html) {
          return { html: html, url: response.url };
        });
      });
  }

  function navigate(url, options) {
    options = options || {};
    var fetchUrl = stripHash(url);
    return fetchFragment(fetchUrl, { method: "GET" })
      .then(function (result) {
        swapContent(result.html, options.push !== false ? result.url : null);
      })
      .catch(function () {
        window.location.href = url;
      });
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
    } else {
      opts.body = data;
    }
    return fetchFragment(action, opts)
      .then(function (result) {
        swapContent(result.html, result.url);
      })
      .catch(function () {
        form.submit();
      });
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
    event.preventDefault();
    navigate(link.href);
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
   * KHÔNG tự bật lại nút: nhánh AJAX thành công thay nguyên `#app-content`
   * (nút cũ biến mất cùng DOM cũ); nhánh native thành công thì trang tải
   * lại hẳn. Nhánh AJAX THẤT BẠI rơi về `form.submit()` thật trong
   * `submitForm()` — `HTMLFormElement.submit()` không tự phát sự kiện
   * `submit` (đặc tả DOM), nên hàm này không chạy lại lần hai; nút giữ
   * nguyên trạng thái "đang xử lý" đúng lúc request thật đang chờ, không
   * có khoảng hở nào để bấm gửi trùng lần nữa. */
  function onSlowSubmit(event) {
    var form = event.target;
    if (!form || form.tagName !== "FORM" || !form.hasAttribute("data-loading-label")) return;
    var btn = (event.submitter && event.submitter.tagName === "BUTTON")
      ? event.submitter : form.querySelector("button[type=submit], button:not([type])");
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    var spin = document.createElement("span");
    spin.className = "tp-spinner";
    spin.setAttribute("aria-hidden", "true");
    btn.textContent = "";
    btn.appendChild(spin);
    btn.appendChild(document.createTextNode(form.getAttribute("data-loading-label")));
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
