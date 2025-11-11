document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("popupFormModal");
  const closeBtn = document.querySelector(".close-popup");
  const form = document.getElementById("popupForm");

  // Show modal after 10 seconds
  setTimeout(() => {
    modal.classList.add("show");
  }, 5000);

  // Close modal when clicking the close button
  closeBtn.addEventListener("click", () => {
    modal.classList.remove("show");
  });

  // Handle form submission
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    // Show success message
    const successMessage = document.createElement("div");
    successMessage.className = "success-message";
    successMessage.textContent = "Thank you for subscribing!";
    form.innerHTML = "";
    form.appendChild(successMessage);

    // Close modal after 3 seconds
    setTimeout(() => {
      modal.classList.remove("show");
    }, 1000);
  });

  const checkbox = document.getElementById("termsCheckbox");
  const submitBtn = document.getElementById("submitBtn");

  checkbox.addEventListener("change", () => {
    if (checkbox.checked) {
      submitBtn.disabled = false;
      submitBtn.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
      submitBtn.disabled = true;
      submitBtn.classList.add("opacity-50", "cursor-not-allowed");
    }
  });
});
