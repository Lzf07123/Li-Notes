(function () {
  "use strict";

  function visibleLinks(nav) {
    return Array.prototype.slice.call(nav.querySelectorAll(".admin-nav-link"));
  }

  function filterNav(nav, query) {
    if (!nav) return;
    var q = query.trim().toLowerCase();
    var links = visibleLinks(nav);
    links.forEach(function (link) {
      link.hidden = !!q && link.textContent.toLowerCase().indexOf(q) < 0;
    });
    nav.querySelectorAll("[data-nav-group]").forEach(function (group) {
      var links = Array.prototype.slice.call(group.querySelectorAll(".admin-nav-link"));
      group.hidden = links.length > 0 && links.every(function (link) { return link.hidden; });
      if (q && !group.hidden) group.open = true;
    });
    var empty = nav.querySelector("[data-nav-empty]");
    if (empty) {
      empty.hidden = !q || links.some(function (link) { return !link.hidden; });
    }
  }

  var desktopFilter = document.getElementById("admin-nav-filter");
  var desktopNav = document.getElementById("admin-nav");
  if (desktopFilter && desktopNav) {
    desktopFilter.addEventListener("input", function () {
      filterNav(desktopNav, desktopFilter.value);
    });
    desktopFilter.addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      var first = visibleLinks(desktopNav).find(function (link) { return !link.hidden; });
      if (first) window.location.href = first.getAttribute("href");
    });
  }

  var navDialog = document.getElementById("admin-nav-dialog");
  var dialogFilter = document.getElementById("admin-nav-dialog-filter");
  var dialogNav = document.getElementById("admin-nav-dialog-list");
  var openButtons = document.querySelectorAll("[data-open-admin-nav]");
  var navTrigger = null;

  openButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      if (!navDialog) return;
      navTrigger = button;
      if (!navDialog.open) navDialog.showModal();
      if (dialogFilter) {
        dialogFilter.value = "";
        filterNav(dialogNav, "");
        window.setTimeout(function () { dialogFilter.focus(); }, 0);
      }
    });
  });

  if (dialogFilter && dialogNav) {
    dialogFilter.addEventListener("input", function () {
      filterNav(dialogNav, dialogFilter.value);
    });
  }

  if (navDialog) {
    navDialog.addEventListener("close", function () {
      if (navTrigger) navTrigger.focus();
    });
    navDialog.addEventListener("click", function (event) {
      if (event.target === navDialog) navDialog.close();
    });
    navDialog.querySelectorAll("[data-close-admin-nav]").forEach(function (button) {
      button.addEventListener("click", function () { navDialog.close(); });
    });
  }

  function closeActionMenus(except) {
    document.querySelectorAll("details[data-action-menu][open]").forEach(function (menu) {
      if (menu !== except) menu.open = false;
    });
  }

  document.querySelectorAll("details[data-action-menu]").forEach(function (menu) {
    menu.addEventListener("toggle", function () {
      if (menu.open) closeActionMenus(menu);
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest("details[data-action-menu]")) closeActionMenus(null);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (navDialog && navDialog.open) {
      event.preventDefault();
      navDialog.close();
    }
    closeActionMenus(null);
  });

  var bulkForm = document.getElementById("bulk-form");
  if (bulkForm) {
    var actionSelect = bulkForm.querySelector('select[name="action"]');
    var tagInput = bulkForm.querySelector('input[name="tag"]');
    var bulkPanel = bulkForm.closest("details");
    var bulkSummary = bulkPanel ? bulkPanel.querySelector("summary") : null;
    var bulkCount = document.getElementById("bulk-count");
    var selectAll = document.getElementById("bulk-select-all");
    var filterTotalEl = document.getElementById("bulk-filter-total");

    function updateBulkSummary() {
      var selected = document.querySelectorAll(".bulk-check:checked").length;
      var all = !!(selectAll && selectAll.checked);
      var total = filterTotalEl ? parseInt(filterTotalEl.textContent, 10) || 0 : 0;
      var text = all ? "批量操作 · 将处理全部 " + total + " 篇" : "批量操作 · 已选 " + selected + " 篇";
      if (bulkSummary) bulkSummary.textContent = text;
      if (bulkCount) bulkCount.textContent = all ? "将处理当前筛选结果" : "已选 " + selected + " 篇";
    }

    function toggleTagInput() {
      if (!actionSelect || !tagInput) return;
      var needsTag = actionSelect.value === "add_tag" || actionSelect.value === "remove_tag";
      tagInput.hidden = !needsTag;
      tagInput.required = needsTag;
      var field = tagInput.closest(".bulk-field");
      if (field) field.hidden = !needsTag;
    }

    document.querySelectorAll(".bulk-check").forEach(function (checkbox) {
      checkbox.addEventListener("change", updateBulkSummary);
    });
    if (selectAll) selectAll.addEventListener("change", updateBulkSummary);
    if (actionSelect) actionSelect.addEventListener("change", toggleTagInput);
    toggleTagInput();
    updateBulkSummary();
  }
})();
