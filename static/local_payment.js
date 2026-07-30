// home/static/js/local_payment.js

// 1. Generate a single, permanent UUID as soon as the checkout page loads
const finalTransactionUuid = "order_" + Date.now();

// Run this function immediately when the checkout screen loads
document.addEventListener("DOMContentLoaded", function() {
    // Inject the permanent UUID into the hidden eSewa form field right away
    $('#e_transaction_uuid').val(finalTransactionUuid);
    
    // Request the encrypted signature immediately
    generateEsewaSignature();
});

function generateEsewaSignature() {
    const totalAmount = orderTotalAmount; // Pulls from your template variable
    const productCode = $('#e_product_code').val();

    $.ajax({
        type: 'POST',
        url: '/generate-esewa-signature/',
        data: {
            'total_amount': totalAmount,
            'transaction_uuid': finalTransactionUuid, // Uses the locked permanent UUID
            'product_code': productCode,
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            // Update the form values with exactly what Python signed
            $('#e_amount').val(response.clean_amount);
            $('#e_total_amount').val(response.clean_amount);
            $('#e_signature').val(response.signature); // Lock in the signature
            console.log("eSewa Signature generated successfully: ", response.signature);
        },
        error: function(xhr, errmsg, err) {
            console.error("Signature request failed: " + errmsg);
        }
    });
}

function switchLocalGateway(gateway) {
    // 1. Hide all payment elements cleanly 
    $('#esewa-form').hide();
    $('#khalti-payment-wrapper').hide();
    $('#fonepay-payment-wrapper').hide();

    // 2. Un-hide the specifically selected payment method container
    if (gateway === 'esewa') {
        $('#esewa-form').show();
        generateEsewaSignature(); // Re-trigger signature check if amount changed
    } else if (gateway === 'khalti') {
        $('#khalti-payment-wrapper').show();
    } else if (gateway === 'fonepay') {
        $('#fonepay-payment-wrapper').show();
    }
}
function initializeKhaltiEngine() {
    // Check if the Khalti library is available in the browser namespace
    if (typeof KhaltiCheckout === 'undefined') {
        console.error("Khalti library script didn't load in time. Retrying in 500ms...");
        setTimeout(initializeKhaltiEngine, 500); // Wait half a second and try again
        return;
    }

    var khaltiConfig = {
        "publicKey": "test_public_key_dc74e0fd57cb46cd93832aee0a507256", 
        "productIdentity": "cart_order_" + Date.now(),
        "productName": "EStore Cart Checkout",
        "productUrl": window.location.origin,
        "paymentPreference": ["KHALTI", "EBANKING", "MOBILE_BANKING"],
        "eventHandler": {
            onSuccess(payload) {
                console.log("Khalti verified payment successfully: ", payload);
                window.location.href = `/khalti-success/?token=${payload.token}&amount=${payload.amount}`;
            },
            onError(error) {
                console.error("Khalti SDK Error Log: ", error);
                alert("Payment failed: " + error.message);
            },
            onClose() {
                console.log("Khalti wallet interface overlay closed by user.");
            }
        }
    };

    try {
        var khaltiCheckout = new KhaltiCheckout(khaltiConfig);
        var khaltiButton = document.getElementById("khalti-button");
        
        if (khaltiButton) {
            khaltiButton.onclick = function () {
                let amountInPaisa = Math.round(parseFloat(orderTotalAmount) * 100);
                khaltiCheckout.show({ amount: amountInPaisa });
            };
            console.log("Khalti Engine bound to button successfully.");
        }
    } catch (e) {
        console.error("Failed to initialize Khalti engine internally: ", e);
    }
}

// 3. Trigger the initializer safely when the document is fully ready
document.addEventListener("DOMContentLoaded", function() {
    initializeKhaltiEngine();
});

// 4. Mock Fonepay Verification Submission sequence handler
function triggerFonepayVerification() {
    $.ajax({
        type: 'POST',
        url: '/fonepay-success/',
        data: {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            window.location.href = '/payment-success/';
        }
    });
}