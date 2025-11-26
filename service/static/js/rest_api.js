$(document).ready(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    function flash_message(message) {
        $("#flash_message").text(message);
    }

    function clear_form_data() {
        $("#promotions_id").val("");
        $("#promotions_product_name").val("");
        $("#promotions_description").val("");
        $("#promotions_original_price").val("");
        $("#promotions_discount_value").val("");
        $("#promotions_discount_type").val("");
        $("#promotions_promotion_type").val("discount");
        $("#promotions_status").val("draft");
        $("#promotions_expiration_date").val("");
    }

    function update_form_data(data) {
        $("#promotions_id").val(data.id);
        $("#promotions_product_name").val(data.product_name);
        $("#promotions_description").val(data.description);
        $("#promotions_original_price").val(data.original_price);
        $("#promotions_discount_value").val(data.discount_value);
        $("#promotions_discount_type").val(data.discount_type);
        $("#promotions_promotion_type").val(data.promotion_type);
        $("#promotions_status").val(data.status);

        if (data.expiration_date) {
            let date = new Date(data.expiration_date);
            let year = date.getFullYear();
            let month = String(date.getMonth() + 1).padStart(2, '0');
            let day = String(date.getDate()).padStart(2, '0');
            let hours = String(date.getHours()).padStart(2, '0');
            let minutes = String(date.getMinutes()).padStart(2, '0');
            let formatted = `${year}-${month}-${day}T${hours}:${minutes}`;
            $("#promotions_expiration_date").val(formatted);
        } else {
            $("#promotions_expiration_date").val("");
        }
    }

    // ****************************************
    // Create a Promotion
    // ****************************************

    $("#create-btn").click(function () {

        let product_name = $("#promotions_product_name").val();
        let description = $("#promotions_description").val();
        let original_price = $("#promotions_original_price").val();
        let discount_value = $("#promotions_discount_value").val();
        let discount_type = $("#promotions_discount_type").val();
        let promotion_type = $("#promotions_promotion_type").val();
        let status = $("#promotions_status").val();
        let expiration_date = $("#promotions_expiration_date").val();

        // --- FIX: Make sure expiration_date always has seconds ---
        if (expiration_date && expiration_date.match(/^....-..-..T..:..$/)) {
            expiration_date = expiration_date + ":00";
        }

        let data = {
            "product_name": product_name,
            "description": description,
            "original_price": parseFloat(original_price),
            "promotion_type": promotion_type,
            "expiration_date": expiration_date,
            "status": status
        };

        if (discount_value) {
            data.discount_value = parseFloat(discount_value);
        }
        if (discount_type) {
            data.discount_type = discount_type;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/promotions",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res);
            flash_message("Success");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message);
        });
    });


    // ****************************************
    // Update a Promotion
    // ****************************************

    $("#update-btn").click(function () {

        let promotion_id = $("#promotions_id").val();
        let product_name = $("#promotions_product_name").val();
        let description = $("#promotions_description").val();
        let original_price = $("#promotions_original_price").val();
        let discount_value = $("#promotions_discount_value").val();
        let discount_type = $("#promotions_discount_type").val();
        let promotion_type = $("#promotions_promotion_type").val();
        let status = $("#promotions_status").val();
        let expiration_date = $("#promotions_expiration_date").val();

        // --- FIX for update too ---
        if (expiration_date && expiration_date.match(/^....-..-..T..:..$/)) {
            expiration_date = expiration_date + ":00";
        }

        let data = {
            "product_name": product_name,
            "description": description,
            "original_price": parseFloat(original_price),
            "promotion_type": promotion_type,
            "expiration_date": expiration_date,
            "status": status
        };

        if (discount_value) {
            data.discount_value = parseFloat(discount_value);
        }
        if (discount_type) {
            data.discount_type = discount_type;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/promotions/${promotion_id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function(res){
            update_form_data(res);
            flash_message("Success");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message);
        });

    });

    // ****************************************
    // Retrieve a Promotion
    // ****************************************

    $("#retrieve-btn").click(function () {
        let promotion_id = $("#promotions_id").val();
        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/promotions/${promotion_id}`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            update_form_data(res);
            flash_message("Success");
        });

        ajax.fail(function(res){
            clear_form_data();
            flash_message(res.responseJSON.message);
        });

    });

    // ****************************************
    // Delete a Promotion
    // ****************************************

    $("#delete-btn").click(function () {
        let promotion_id = $("#promotions_id").val();
        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/promotions/${promotion_id}`,
            contentType: "application/json",
            data: '',
        });

        ajax.done(function(res){
            clear_form_data();
            flash_message("Promotion has been Deleted!");
        });

        ajax.fail(function(res){
            flash_message("Server error!");
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#promotions_id").val("");
        clear_form_data();
    });

    // ****************************************
    // Search for Promotions
    // ****************************************

    $("#search-btn").click(function () {

        let product_name = $("#promotions_product_name").val();
        let queryString = "role=manager";

        if (product_name) {
            queryString += '&q=' + product_name;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/promotions?${queryString}`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">';
            table += '<thead><tr>';
            table += '<th>ID</th>';
            table += '<th>Product Name</th>';
            table += '<th>Description</th>';
            table += '<th>Original Price</th>';
            table += '<th>Discount Value</th>';
            table += '<th>Discount Type</th>';
            table += '<th>Promotion Type</th>';
            table += '<th>Status</th>';
            table += '<th>Expiration</th>';
            table += '</tr></thead><tbody id="results-body">';

            let firstPromotion = null;
            for(let i = 0; i < res.length; i++) {
                let promotion = res[i];
                let expiration = promotion.expiration_date ? new Date(promotion.expiration_date).toLocaleString() : '';
                table += `<tr id="row_${i}">
                    <td>${promotion.id}</td>
                    <td>${promotion.product_name}</td>
                    <td>${promotion.description || ''}</td>
                    <td>${promotion.original_price}</td>
                    <td>${promotion.discount_value || ''}</td>
                    <td>${promotion.discount_type || ''}</td>
                    <td>${promotion.promotion_type}</td>
                    <td>${promotion.status}</td>
                    <td>${expiration}</td>
                </tr>`;
                if (i == 0) {
                    firstPromotion = promotion;
                }
            }

            table += '</tbody></table>';
            $("#search_results").append(table);

            if (firstPromotion) {
                update_form_data(firstPromotion);
            }

            flash_message("Success");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message);
        });

    });

});
