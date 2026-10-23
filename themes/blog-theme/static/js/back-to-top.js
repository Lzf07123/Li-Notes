(function () {
  "use strict";

  var button = document.querySelector(".back-to-top");
  if (!button) return;

  var threshold = 0;
  var ticking = false;

  function updateThreshold() {
    threshold = Math.max(480, Math.round(window.innerHeight * 0.75));
  }

  function updateVisibility() {
    var visible = window.scrollY > threshold;
    button.classList.toggle("is-visible", visible);
    button.tabIndex = visible ? 0 : -1;
    button.setAttribute("aria-hidden", visible ? "false" : "true");
    ticking = false;
  }

  function requestUpdate() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(updateVisibility);
  }

  function handleResize() {
    updateThreshold();
    requestUpdate();
  }

  updateThreshold();
  updateVisibility();
  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", handleResize, { passive: true });
  window.addEventListener("pageshow", requestUpdate);
})();
