document.addEventListener("DOMContentLoaded", function () {
    if (window.location.hash === "#attendance") {
        // small timeout to let bootstrap js init
        setTimeout(function () {
            var tab = document.querySelector('#attendance-tab'); 
            if (tab) {
                var tabObj = new bootstrap.Tab(tab);
                tabObj.show();
            }
        }, 80);
    }
});
