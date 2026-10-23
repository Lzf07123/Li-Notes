(function () {
  "use strict";

  var tables = Array.prototype.slice.call(document.querySelectorAll(".article-body table"));
  if (!tables.length) return;

  var query = window.matchMedia("(max-width: 640px)");

  function setLabels(table) {
    var headers = Array.prototype.map.call(
      table.querySelectorAll("thead th"),
      function (cell) { return (cell.textContent || "").trim(); }
    );
    Array.prototype.forEach.call(table.querySelectorAll("tbody tr"), function (row) {
      Array.prototype.forEach.call(row.children, function (cell, index) {
        cell.setAttribute("data-label", headers[index] || "");
      });
    });
  }

  function sync() {
    tables.forEach(function (table) {
      setLabels(table);
      table.classList.toggle("responsive-table", query.matches);
    });
  }

  sync();
  if (query.addEventListener) query.addEventListener("change", sync);
  else query.addListener(sync);
})();
