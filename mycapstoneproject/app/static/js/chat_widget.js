(() => {
  const launcher = document.getElementById("aiLauncher"),
    popover = document.getElementById("aiPopover"),
    close = document.getElementById("aiClose");
  if (!launcher || !popover) return;
  launcher.addEventListener("click", () => {
    popover.classList.toggle("open");
    launcher.classList.toggle("open");
  });
  close?.addEventListener("click", () => {
    popover.classList.remove("open");
    launcher.classList.remove("open");
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#floatingAi")) {
      popover.classList.remove("open");
      launcher.classList.remove("open");
    }
  });
})();
