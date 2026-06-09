document.addEventListener("DOMContentLoaded", () => {
  initPasswordToggles();
  initWizard();
});

function initPasswordToggles() {
  document.querySelectorAll("[data-password-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.passwordToggle);
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.textContent = isPassword ? "Hide" : "Show";
      btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
  });
}

function initWizard() {
  const wizard = document.getElementById("profile-wizard");
  if (!wizard) return;

  const steps = wizard.querySelectorAll(".wizard-step");
  const progressFill = document.getElementById("wizard-progress-fill");
  const stepLabels = wizard.querySelectorAll(".wizard-progress__labels span");
  const btnBack = document.getElementById("wizard-back");
  const btnNext = document.getElementById("wizard-next");
  const btnSubmit = document.getElementById("wizard-submit");
  const btnSkip = document.getElementById("wizard-skip");
  let current = 0;

  function showStep(index) {
    steps.forEach((s, i) => s.classList.toggle("active", i === index));
    stepLabels.forEach((l, i) => l.classList.toggle("active", i === index));
    const pct = ((index + 1) / steps.length) * 100;
    if (progressFill) progressFill.style.width = pct + "%";
    if (btnBack) btnBack.style.visibility = index === 0 ? "hidden" : "visible";
    if (btnNext) btnNext.style.display = index === steps.length - 1 ? "none" : "inline-flex";
    if (btnSubmit) btnSubmit.style.display = index === steps.length - 1 ? "inline-flex" : "none";
    if (btnSkip) btnSkip.style.display = index === 0 ? "none" : "inline-flex";
    current = index;
  }

  if (btnBack) {
    btnBack.addEventListener("click", () => {
      if (current > 0) showStep(current - 1);
    });
  }

  if (btnNext) {
    btnNext.addEventListener("click", () => {
      if (current < steps.length - 1) showStep(current + 1);
    });
  }

  if (btnSkip) {
    btnSkip.addEventListener("click", () => wizard.submit());
  }

  showStep(0);
}
