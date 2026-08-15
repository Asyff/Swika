// home/static/js/local_payment.js

// home/static/js/local_payment.js

const finalTransactionUuid = "order_" + Date.now();
let activeGrandTotal = 0; // FIX 1: Declared globally at the top of your namespace file

let activePaymentMethod = 'fonepay';

// 1. Manages form display switching smoothly without page reloads
function switchLocalGateway(method) {
    activePaymentMethod = method;
    
    if (method === 'fonepay') {
        $('#fonepay-fields-block').show();
        $('#cod-fields-block').hide();
        // Update action button style context
        $('#submit-order-btn').css('background-color', '#dc3545').text(`Submit Order (Rs.${orderTotalAmount})`);
    } else if (method === 'cod') {
        $('#fonepay-fields-block').hide();
        $('#cod-fields-block').show();
        $('#submit-order-btn').css('background-color', '#198754').text(`Confirm COD Order (Rs.${orderTotalAmount})`);
    }
}

// 2. Compiles user input details and handles transaction submission requests
function submitCheckoutOrder() {
    let txnId = $('#fonepay_tx_code').val().trim();
    let fileInput = document.getElementById('fonepay_screenshot_file');

    // Fonepay specific verification rules validation checks
    if (activePaymentMethod === 'fonepay') {
        if (!txnId) {
            alert("Please enter your Fonepay Transaction ID.");
            return;
        }
        if (fileInput.files.length === 0) {
            alert("Please upload a screenshot of your verification payment success slip.");
            return;
        }
    }

    // Toggle Loading Spinners ON
    let originalBtnText = $('#submit-order-btn').text();
    $('#submit-order-btn').html(`<span class="spinner-border spinner-border-sm" role="status"></span> Processing...`).prop('disabled', true);

    // Build the dynamic Form Data payload module stream
    let formData = new FormData();
    formData.append('phone', $('#id_phone').val() || "");
    formData.append('shipping_address', $('#id_shipping_address').val() || "");
    formData.append('payment_method', activePaymentMethod); // Tells Django whether it is Fonepay or COD
    formData.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());

    // Only attach image variables if Fonepay interface path is chosen
    if (activePaymentMethod === 'fonepay') {
        formData.append('fonepay_txn_id', txnId);
        formData.append('payment_screenshot', fileInput.files[0]);
    }

    $.ajax({
        type: 'POST',
        url: '/fonepay-success/', // Unified processing views endpoint path name
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            window.location.href = '/payment-success/';
        },
        error: function(xhr, errmsg, err) {
            alert("Checkout submission encountered an exception error. Please try again.");
            $('#submit-order-btn').html(originalBtnText).prop('disabled', false);
        }
    });
}
function showCustomErrorToast(message) {
    $('#errorToastMessage').text(message);
    let toastEl = document.getElementById('errorToast');
    let toast = new bootstrap.Toast(toastEl);
    toast.show();
}