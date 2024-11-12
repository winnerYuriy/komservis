const date = new Date();
document.querySelector(".year").innerHTML = date.getFullYear();


setTimeout(function () {
  $("#message").fadeOut("slow");
}, 3000);

$(document).on('click', '#add-button', function (e) {
        e.preventDefault();

        $.ajax({
            type: 'POST',
            url: '{% url "cart:add-to-cart" %}',
            data: {
                product_id: $('#add-button').val(),
                product_qty: $('#select option:selected').text(),
                csrfmiddlewaretoken: '{{ csrf_token }}',
                action: 'post'
            },
            success: function (response) {
                document.getElementById('lblCartCount').textContent = response.qty;
                const addButton = document.getElementById('add-button');
                addButton.disabled = true;
                addButton.innerText = "Added to cart";
                addButton.className = "btn btn-success btn-sm";
            },
            error: function (error) {
                console.log(error);
            }
        });
});

function toggleTable() {
    var additionalRows = document.querySelectorAll('.additional-attributes');
    if (additionalRows.length === 0) return; // Перевірка на наявність елементів
 
    var showMoreButton = document.getElementById('show-more');
    
    // Перевірка, чи додаткові характеристики приховані чи показані
    if (additionalRows[0].style.display === 'none') {
        additionalRows.forEach(function(row) {
            row.style.display = 'table-row';  // Показуємо рядок
        });
        showMoreButton.textContent = 'Сховати характеристики';
    } else {
        additionalRows.forEach(function(row) {
            row.style.display = 'none';  // Приховуємо рядок
        });
        showMoreButton.textContent = 'Показати всі характеристики';
    }
 }