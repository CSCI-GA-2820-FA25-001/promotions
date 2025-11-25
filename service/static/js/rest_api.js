$(function () {

    // -------------------------------------------------------------
    // Utility functions
    // -------------------------------------------------------------

    function update_form_data(res) {
        $("#promo_id").val(res.id);
        $("#promo_name").val(res.promotion_name || "");
        $("#promo_product").val(res.product_name);
        $("#promo_original_price").val(res.original_price);
        $("#promo_discount").val(res.discount_value);
        $("#promo_discount_type").val(res.discount_type);
        $("#promo_status").val(res.status);
        $("#promo_expiration").val(res.expiration_date);
    }

    function clear_form_data() {
        $("#promo_id").val("");
        $("#promo_name").val("");
        $("#promo_product").val("");
        $("#promo_original_price").val("");
        $("#promo_discount").val("");
        $("#promo_discount_type").val("");
        $("#promo_status").val("draft");
        $("#promo_expiration").val("");
    }

    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // -------------------------------------------------------------
    // CREATE
    // -------------------------------------------------------------
    $("#create-btn").click(function () {

        let data = {
            "product_name": $("#promo_product").val(),
            "description": $("#promo_name").val(),
            "original_price": parseFloat($("#promo_original_price").val()),
            "promotion_type": "discount",
            "discount_value": $("#promo_discount").val() ? parseFloat($("#promo_discount").val()) : null,
            "discount_type": $("#promo_discount_type").val(),
            "start_date": null,
            "expiration_date": $("#promo_expiration").val(),
            "status": $("#promo_status").val()
        };

        let ajax = $.ajax({
            type: "POST",
            url: "/promotions",
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function (res) {
            flash_message("Promotion created!");
            update_form_data(res);
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
        });
    });

    // -------------------------------------------------------------
    // RETRIEVE
    // -------------------------------------------------------------
    $("#retrieve-btn").click(function () {

        let id = $("#promo_id").val();

        let ajax = $.ajax({
            type: "GET",
            url: `/promotions/${id}`,
            contentType: "application/json"
        });

        ajax.done(function (res) {
            flash_message("Promotion retrieved!");
            update_form_data(res);
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
            clear_form_data();
        });
    });

    // -------------------------------------------------------------
    // UPDATE
    // -------------------------------------------------------------
    $("#update-btn").click(function () {

        let id = $("#promo_id").val();

        let data = {
            "product_name": $("#promo_product").val(),
            "description": $("#promo_name").val(),
            "original_price": parseFloat($("#promo_original_price").val()),
            "promotion_type": "discount",
            "discount_value": $("#promo_discount").val() ? parseFloat($("#promo_discount").val()) : null,
            "discount_type": $("#promo_discount_type").val(),
            "start_date": null,
            "expiration_date": $("#promo_expiration").val(),
            "status": $("#promo_status").val()
        };

        let ajax = $.ajax({
            type: "PUT",
            url: `/promotions/${id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function (res) {
            flash_message("Promotion updated!");
            update_form_data(res);
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
        });
    });

    // -------------------------------------------------------------
    // DELETE
    // -------------------------------------------------------------
    $("#delete-btn").click(function () {

        let id = $("#promo_id").val();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/promotions/${id}`,
            contentType: "application/json"
        });

        ajax.done(function () {
            flash_message("Promotion deleted!");
            clear_form_data();
        });

        ajax.fail(function (res) {
            flash_message("Server error.");
        });
    });

    // -------------------------------------------------------------
    // CLEAR
    // -------------------------------------------------------------
    $("#clear-btn").click(function () {
        clear_form_data();
        flash_message("");
    });

    // -------------------------------------------------------------
    // SEARCH
    // -------------------------------------------------------------
    $("#search-btn").click(function () {

        let keyword = $("#promo_product").val();
        let query = keyword ? `?keyword=${keyword}` : "";

        let ajax = $.ajax({
            type: "GET",
            url: `/promotions${query}`,
            contentType: "application/json"
        });

        ajax.done(function (res) {
            $("#results-body").empty();

            flash_message("Search complete.");

            for (let i = 0; i < res.length; i++) {
                let p = res[i];

                let row = `
                    <tr>
                        <td>${p.id}</td>
                        <td>${p.description || ""}</td>
                        <td>${p.product_name}</td>
                        <td>${p.original_price}</td>
                        <td>${p.discount_value || ""}</td>
                        <td>${p.discount_type || ""}</td>
                        <td>${p.status}</td>
                        <td>${p.expiration_date}</td>
                    </tr>
                `;

                $("#results-body").append(row);

                // Populate form with first result
                if (i === 0) {
                    update_form_data(p);
                }
            }
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
        });
    });

});
