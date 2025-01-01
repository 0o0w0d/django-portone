function AlertModal(css_selector) {
  const modal_el = document.querySelector(css_selector);
  const myModal = new bootstrap.Modal(modal_el);
  this.show = function (message) {
    modal_el.querySelector(".modal-body").textContent = message;
    myModal.show();
  };
}
