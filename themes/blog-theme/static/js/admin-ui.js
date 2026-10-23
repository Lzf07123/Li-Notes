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

  function positionRowActionsMenu(menu) {
    var trigger = menu.querySelector(":scope > summary");
    var panel = menu.querySelector("[data-row-actions-menu]");
    if (!trigger || !panel) return;

    var margin = 12;
    var gap = 6;
    var viewportWidth = document.documentElement.clientWidth;
    var viewportHeight = window.innerHeight;
    var triggerRect = trigger.getBoundingClientRect();

    if (triggerRect.bottom < 0 || triggerRect.top > viewportHeight) {
      menu.open = false;
      return;
    }

    panel.style.maxHeight = Math.max(44, viewportHeight - margin * 2) + "px";
    var panelRect = panel.getBoundingClientRect();
    var width = Math.min(panelRect.width, viewportWidth - margin * 2);
    var left = Math.min(
      Math.max(margin, triggerRect.right - width),
      viewportWidth - width - margin
    );
    var below = triggerRect.bottom + gap;
    var above = triggerRect.top - panelRect.height - gap;
    var top = below;

    var dropUp = false;
    if (below + panelRect.height > viewportHeight - margin) {
      if (above >= margin) {
        top = above;
        dropUp = true;
      } else {
        top = Math.max(margin, viewportHeight - margin - panelRect.height);
      }
    }

    panel.style.left = Math.round(left) + "px";
    panel.style.top = Math.round(top) + "px";
    menu.classList.toggle("is-drop-up", dropUp);
  }

  var rowMenuFrame = 0;

  function scheduleRowMenuPosition() {
    if (rowMenuFrame) return;
    rowMenuFrame = window.requestAnimationFrame(function () {
      rowMenuFrame = 0;
      document.querySelectorAll("details.row-actions-more[open]").forEach(positionRowActionsMenu);
    });
  }

  document.querySelectorAll("details.row-actions-more[data-action-menu]").forEach(function (menu) {
    var trigger = menu.querySelector(":scope > summary");
    menu.addEventListener("toggle", function () {
      if (trigger) {
        trigger.setAttribute("aria-expanded", menu.open ? "true" : "false");
      }
      if (menu.open) {
        positionRowActionsMenu(menu);
        scheduleRowMenuPosition();
      } else {
        menu.classList.remove("is-drop-up");
      }
    });
  });

  window.addEventListener("resize", scheduleRowMenuPosition, { passive: true });
  window.addEventListener("scroll", scheduleRowMenuPosition, { capture: true, passive: true });

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
    var openMenu = document.querySelector("details[data-action-menu][open]");
    closeActionMenus(null);
    if (openMenu) {
      var trigger = openMenu.querySelector(":scope > summary");
      if (trigger) trigger.focus();
    }
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
