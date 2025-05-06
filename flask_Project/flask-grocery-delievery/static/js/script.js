// Main JavaScript file for Grocery Delivery

document.addEventListener("DOMContentLoaded", () => {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))
  
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
      var alerts = document.querySelectorAll(".alert")
      alerts.forEach((alert) => {
        var bsAlert = new bootstrap.Alert(alert)
        bsAlert.close()
      })
    }, 5000)
  
    // Add to cart animation
    const addToCartButtons = document.querySelectorAll('form[action^="/add_to_cart"] button')
    addToCartButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        // You could add a nice animation here
        button.innerHTML = '<i class="fas fa-check"></i> Added'
        setTimeout(() => {
          button.innerHTML = '<i class="fas fa-cart-plus"></i> Add'
        }, 1000)
      })
    })
  })
  