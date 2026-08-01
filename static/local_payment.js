// home/static/js/local_payment.js

// home/static/js/local_payment.js

const finalTransactionUuid = "order_" + Date.now();
let activeGrandTotal = 0; // FIX 1: Declared globally at the top of your namespace file

// Execute calculations immediately when the document is fully ready in the browser
$(document).ready(function() {
    if (typeof orderTotalAmount !== 'undefined' && parseFloat(orderTotalAmount) === 0) {
        $('#cart_quantity').text('0');
        $('#nav-cart-badge').text('0');
        $('.quantity').text('0');
    }
    $('#e_transaction_uuid').val(finalTransactionUuid);
    
    // 1. Initialize the layout starting calculations on page load
    calculateDynamicShipping();
    
    // 2. Initialize and compile the Khalti Web Modal framework engine safely
    initializeKhaltiEngine();
});

// Dynamic Shipping Recalculator Core Engine
function calculateDynamicShipping() {
    // Read select choices dropdown text nodes parameters
    let region = $('#shipping-region').val();
    let shippingCharge = (region === 'inside') ? 50 : 150;
    
    // Compute total financial balances
    activeGrandTotal = baseCartSubtotal + shippingCharge;

    // Update screen display elements instantly
    $('#summary-shipping').text(shippingCharge);
    $('#summary-grand-total').text(activeGrandTotal);

    // Synchronize button price tags dynamically across all payment views
    $('#esewa-form button').text(`Pay with eSewa (Rs. ${activeGrandTotal})`);
    $('#khalti-button').text(`Pay with Khalti (Rs. ${activeGrandTotal})`);
    $('#cod-payment-wrapper button').text(`Place Order via Cash on Delivery (Rs. ${activeGrandTotal})`);

    // Update hidden eSewa payload parameters elements strings fields
    $('#e_product_delivery_charge').val(shippingCharge);
    $('#e_total_amount').val(activeGrandTotal);

    // Re-trigger eSewa HMAC security hash signing
    generateEsewaSignature();
}

function generateEsewaSignature() {
    const productCode = $('#e_product_code').val();

    $.ajax({
        type: 'POST',
        url: '/generate-esewa-signature/',
        data: {
            'total_amount': activeGrandTotal,
            'transaction_uuid': finalTransactionUuid,
            'product_code': productCode,
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            $('#e_signature').val(response.signature);
        }
    });
}

function switchLocalGateway(gateway) {
    // Hide all checkout wrapper areas cleanly
    $('#esewa-form').hide();
    $('#khalti-payment-wrapper').hide();
    $('#fonepay-payment-wrapper').hide();
    $('#cod-payment-wrapper').hide();

    // Show the selected layout framework container block
    if (gateway === 'esewa') {
        $('#esewa-form').show();
    } else if (gateway === 'khalti') {
        $('#khalti-payment-wrapper').show();
    } else if (gateway === 'fonepay') {
        $('#fonepay-payment-wrapper').show();
    } else if (gateway === 'cod') {
        $('#cod-payment-wrapper').show();
    }
}

// Khalti Modal Configuration Initializer
function initializeKhaltiEngine() {
    if (typeof KhaltiCheckout === 'undefined') {
        console.error("Khalti library delayed. Retrying hook in 300ms...");
        setTimeout(initializeKhaltiEngine, 300);
        return;
    }

    var khaltiConfig = {
        "publicKey": "test_public_key_dc74e0fd57cb46cd93832aee0a507256", 
        "productIdentity": finalTransactionUuid,
        "productName": "EStore Cart Checkout",
        "productUrl": window.location.origin,
        "paymentPreference": ["KHALTI", "EBANKING", "MOBILE_BANKING"],
        "eventHandler": {
            onSuccess(payload) {
                // Forward the success authorization parameters directly back to your success view
                window.location.href = `/khalti-success/?token=${payload.token}&amount=${payload.amount}`;
            },
            onError(error) {
                showCustomErrorToast("Khalti payment failed: " + error.message);
            },
            onClose() {
                console.log("Khalti payment panel closed.");
            }
        }
    };

    var khaltiCheckout = new KhaltiCheckout(khaltiConfig);
    
    // Bind click trigger listener directly onto the Khalti element button
    document.getElementById("khalti-button").onclick = function () {
        // Convert to paisa required by the Khalti API engine (Rs. * 100)
        let amountInPaisa = Math.round(parseFloat(activeGrandTotal) * 100);
        khaltiCheckout.show({ amount: amountInPaisa });
    };
}

function triggerFonepayVerification() {
    let typedPhone = $('#id_phone').val() || $('input[placeholder="Phone Number"]').val() || "";
    let typedAddress = $('#id_shipping_address').val() || $('input[placeholder="123 Main St"]').val() || "";
    let selectedRegion = $('#shipping-region option:selected').text();

    if (!typedPhone.trim() || !typedAddress.trim()) {
        showCustomErrorToast("Please fill out your Phone Number and Delivery Address fields first.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/fonepay-success/', 
        data: {
            'phone': typedPhone,
            'shipping_address': typedAddress,
            'region': selectedRegion,
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            $('#cart_quantity').text('0');
            $('#nav-cart-badge').text('0');
            $('.quantity').text('0');
            $('.nav-cart-badge-class').text('0');
            
            window.location.replace('/payment-success/');
        },
        error: function(xhr) {
            let errorMsg = "Fulfillment processing failure.";
            if (xhr.responseText) {
                try {
                    let errData = JSON.parse(xhr.responseText);
                    if (errData.error) {
                        errorMsg = errData.error;
                    }
                    if (errData.status === 'out_of_stock') {
                        showCustomErrorToast(errorMsg + " Redirecting back to cart...");
                        setTimeout(function() {
                            window.location.replace('/cart_summary/'); 
                        }, 3000);
                        return;
                    }
                } catch(e) {
                    console.error("Failed to parse JSON response: ", e);
                }
            }
            showCustomErrorToast(errorMsg);
        }
    });
}

function triggerCodOrder() {
    let typedPhone = $('#id_phone').val() || $('input[placeholder="Phone Number"]').val() || "";
    let typedAddress = $('#id_shipping_address').val() || $('input[placeholder="123 Main St"]').val() || "";
    let selectedRegion = $('#shipping-region option:selected').text();

    if (!typedPhone.trim() || !typedAddress.trim()) {
        showCustomErrorToast("Please complete your Phone Number and Delivery Address fields first.");
        return;
    }

    $.ajax({
        type: 'POST',
        url: '/cod-success/',
        data: {
            'phone': typedPhone,
            'shipping_address': typedAddress,
            'region': selectedRegion,
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            $('#cart_quantity').text('0');
            $('#nav-cart-badge').text('0');
            $('.quantity').text('0');
            $('.nav-cart-badge-class').text('0');
            
            window.location.replace('/payment-success/');
        },
        // FIX 2: Fully restored the missing closing code block syntax parameters
        error: function(xhr) {
            let errorMsg = "Fulfillment processing failure.";
            if (xhr.responseText) {
                try {
                    let errData = JSON.parse(xhr.responseText);
                    if (errData.error) {
                        errorMsg = errData.error;
                    }
                    if (errData.status === 'out_of_stock') {
                        showCustomErrorToast(errorMsg + " Redirecting back to cart...");
                        setTimeout(function() {
                            window.location.replace('/cart_summary/'); 
                        }, 3000);
                        return;
                    }
                } catch(e) {
                    console.error("Failed to parse JSON response: ", e);
                }
            }
            showCustomErrorToast(errorMsg);
        }
    });
}

function showCustomErrorToast(message) {
    $('#errorToastMessage').text(message);
    let toastEl = document.getElementById('errorToast');
    let toast = new bootstrap.Toast(toastEl);
    toast.show();
}