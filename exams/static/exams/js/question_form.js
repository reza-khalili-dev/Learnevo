document.addEventListener("DOMContentLoaded", function () {
    const qtypeSelect = document.getElementById("id_qtype");
    const audioField = document.getElementById("audioField");
    const imageField = document.getElementById("imageField");

    function toggleFields() {
        const value = qtypeSelect.value;

        // hide all by default
        audioField.style.display = "none";
        imageField.style.display = "none";

        // show based on type
        if (value === "audio_mcq" || value === "audio_essay") {
            audioField.style.display = "block";
        } else if (value === "image_mcq" || value === "image_essay") {
            imageField.style.display = "block";
        }
    }

    qtypeSelect.addEventListener("change", toggleFields);
    toggleFields(); // run once on load
});
