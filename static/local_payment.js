let activePaymentMethod = 'fonepay';

// 1. Manages form display switching smoothly without page reloads
function switchLocalGateway(gateway) {
    activePaymentMethod = gateway;
    
    if (gateway === 'fonepay') {
        $('#fonepay-fields-block').show();
        $('#cod-fields-block').hide();
        $('#submit-order-btn').css('background-color', '#dc3545').removeClass('btn-success').addClass('btn-danger');
        $('#submit-order-btn').html(`<span class="spinner-border spinner-border-sm d-none" id="checkout-spinner" role="status"></span><span id="checkout-btn-text">Submit Order (Rs.${orderTotalAmount})</span>`);
    } else if (gateway === 'cod') {
        $('#fonepay-fields-block').hide();
        $('#cod-fields-block').show();
        $('#submit-order-btn').css('background-color', '#198754').removeClass('btn-danger').addClass('btn-success');
        $('#submit-order-btn').html(`<span class="spinner-border spinner-border-sm d-none" id="checkout-spinner" role="status"></span><span id="checkout-btn-text">Confirm Cash Order (Rs.${orderTotalAmount})</span>`);
    }
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