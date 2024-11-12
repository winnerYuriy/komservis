document.addEventListener("DOMContentLoaded", function() {
    const nameInput = document.querySelector('input[name="name"]');
    const slugInput = document.querySelector('input[name="slug"]');

    if (nameInput && slugInput) {
        nameInput.addEventListener("blur", function() {
            // Генерація slug на основі значення name
            const slug = nameInput.value
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')  // Заміна всіх неприпустимих символів на дефіс
                .replace(/^-+|-+$/g, '');      // Видалення зайвих дефісів на початку та кінці

            slugInput.value = slug;
        });
    }
});
