let activePaymentMethod = 'fonepay';

// 1. Manages form display switching smoothly without page reloads
$(document).on('change', '#id_city', function() {
    recalculateCheckoutTotals();
});

function recalculateCheckoutTotals() {
    let selectedLocation = $('#id_city').val();
    let baseItemsTotal = parseFloat(orderTotalAmount) || 0;
    let shippingCost = 0;

    // Evaluate dynamic delivery bounds criteria
    if (selectedLocation === 'Inside Kathmandu Valley') {
        shippingCost = 50;
    } else if (selectedLocation === 'Outside Kathmandu Valley') {
        shippingCost = 150;
    }

    let finalGrandTotal = baseItemsTotal + shippingCost;

    // 1. Update the visual text nodes inside your Order Summary Card
    $('#shipping-fee-display').text("Rs." + shippingCost);
    $('#grand-total-display').text(finalGrandTotal.toFixed(2));

    // 2. Sync the text labels directly inside your submission action buttons
    if (activePaymentMethod === 'fonepay') {
        $('#submit-order-btn').find('#checkout-btn-text').text("Submit Order (Rs." + finalGrandTotal.toFixed(2) + ")");
    } else if (activePaymentMethod === 'cod') {
        $('#submit-order-btn').find('#checkout-btn-text').text("Confirm Cash Order (Rs." + finalGrandTotal.toFixed(2) + ")");
    }
}

// Update your existing switchLocalGateway function to preserve shipping logic on method toggles
function switchLocalGateway(gateway) {
    activePaymentMethod = gateway;
    
    if (gateway === 'fonepay') {
        $('#fonepay-fields-block').show();
        $('#cod-fields-block').hide();
        $('#submit-order-btn').css('background-color', '#dc3545').removeClass('btn-success').addClass('btn-danger');
    } else if (gateway === 'cod') {
        $('#fonepay-fields-block').hide();
        $('#cod-fields-block').show();
        $('#submit-order-btn').css('background-color', '#198754').removeClass('btn-danger').addClass('btn-success');
    }
    
    // Trigger total refresh to make sure button labels inherit any applied shipping balances
    recalculateCheckoutTotals();
}

// 2. Compiles user input details and handles transaction submission requests
function submitCheckoutOrder() {
    let phone = $('#id_phone').val() || "";
    let address = $('#id_shipping_address').val() || "";
    let city = $('#id_city').val() || "";
    
    if (!phone || !address || !city) {
        alert("Please complete your delivery address and contact information fields first.");
        return;
    }

    let txnId = $('#fonepay_tx_code').val() ? $('#fonepay_tx_code').val().trim() : "";
    let fileInput = document.getElementById('fonepay_screenshot_file');

    if (activePaymentMethod === 'fonepay') {
        if (!txnId) {
            alert("Please enter your Fonepay Transaction ID.");
            return;
        }
        if (!fileInput || fileInput.files.length === 0) {
            alert("Please upload a screenshot of your verification payment success slip.");
            return;
        }
    }

    // Capture dynamic button state label text before activating processing spinner
    let originalBtnText = $('#submit-order-btn').html();
    $('#submit-order-btn').html(`<span class="spinner-border spinner-border-sm" role="status"></span> Processing...`).prop('disabled', true);

    // Construct unified multipart form payload
    let formData = new FormData();
    formData.append('phone', phone);
    formData.append('shipping_address', address + ", " + city);
    formData.append('payment_method', activePaymentMethod);
    
    // FIX: Pulls from your globally defined secure token variable parameter
    formData.append('csrfmiddlewaretoken', djangoCsrfToken); 

    // --- SUBMISSION LOGIC BRANCHING ---
    if (activePaymentMethod === 'fonepay') {
        formData.append('fonepay_txn_id', txnId);
        formData.append('payment_screenshot', fileInput.files[0]);

        $.ajax({
            type: 'POST',
            url: '/fonepay-success/',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                window.location.href = '/payment-success/';
            },
            error: function(xhr) {
                alert("Fonepay checkout submission encountered an error. Please try again.");
                resetCheckoutButton(originalBtnText);
            }
        });

    } else if (activePaymentMethod === 'cod') {
        $.ajax({
            type: 'POST',
            url: '/cod-success/',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                window.location.href = '/payment-success/';
            },
            error: function(xhr) {
                alert("COD Request failed. Please try again.");
                resetCheckoutButton(originalBtnText);
            }
        });
    }
}

function resetCheckoutButton(fallbackHtmlText) {
    $('#submit-order-btn').html(fallbackHtmlText).prop('disabled', false);
}

function showCustomErrorToast(message) {
    $('#errorToastMessage').text(message);
    let toastEl = document.getElementById('errorToast');
    let toast = new bootstrap.Toast(toastEl);
    toast.show();
}