/*
 * Componentes Alpine compartidos.
 *
 * La interactividad nueva vive aqui, no en `<script>` inline por pagina, para
 * poder reutilizarla y probarla. Cada componente es una funcion que devuelve el
 * objeto que Alpine expone como scope.
 */

/*
 * Autocompletado de productos sobre el endpoint JSON que ya existia
 * (`products:product_description_search`). Mantiene el codigo del producto en
 * `code` y la descripcion en `term`, que son los dos campos del formulario.
 */
function productSearch(config) {
    return {
        term: config.term || '',
        code: config.code || '',
        results: [],
        open: false,

        async search() {
            if (this.term.length < 2) {
                this.results = [];
                this.open = false;
                return;
            }
            const params = new URLSearchParams({
                description: this.term,
                search_type: config.type || 'PRODUCTOS',
            });
            const response = await fetch(config.url + '?' + params.toString(), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) {
                return;
            }
            this.results = await response.json();
            this.open = this.results.length > 0;
        },

        select(item) {
            this.term = item.label;
            this.code = item.code;
            this.results = [];
            this.open = false;
        },

        close() {
            this.open = false;
        },
    };
}

window.productSearch = productSearch;

/*
 * Autocompletado de proveedores sobre los endpoints JSON de compras. Elige por
 * razon social (rellena RUC, direccion y, si es locador, la orden) o por RUC de
 * 11 digitos. `is_service_provider` decide si la orden es editable.
 */
function supplierSearch(config) {
    return {
        tax_id: config.tax_id || '',
        business_name: config.business_name || '',
        address: config.address || '',
        order: config.order || '',
        is_service_provider: config.is_service_provider || false,
        results: [],
        open: false,

        async searchByName() {
            if (this.business_name.length < 2) {
                this.results = [];
                this.open = false;
                return;
            }
            const data = await fetchJson(
                config.nameUrl + '?business_name=' + encodeURIComponent(this.business_name));
            if (data === null) {
                return;
            }
            this.results = data;
            this.open = data.length > 0;
        },

        async searchByTaxId() {
            if (this.tax_id.length !== 11) {
                return;
            }
            const data = await fetchJson(
                config.taxIdUrl + '?tax_id=' + encodeURIComponent(this.tax_id));
            if (data === null) {
                return;
            }
            this.apply(data);
        },

        select(item) {
            this.business_name = item.label;
            this.tax_id = item.tax_id;
            this.address = item.address;
            this.is_service_provider = item.is_service_provider;
            if (item.is_service_provider) {
                this.order = item.order;
            }
            this.results = [];
            this.open = false;
        },

        apply(data) {
            this.business_name = data.business_name;
            this.address = data.address;
            this.is_service_provider = data.is_service_provider;
            if (data.is_service_provider) {
                this.order = data.order;
            }
        },

        close() {
            this.open = false;
        },
    };
}

window.supplierSearch = supplierSearch;

/*
 * Quita una fila de un formset de Django y renumera las restantes para que los
 * `name`/`id` (`form-<i>-campo`) queden contiguos y `TOTAL_FORMS` cuadre.
 */
function removeFormsetRow(button) {
    var row = button.closest('tr');
    var tbody = row.parentNode;
    row.remove();
    var rows = tbody.querySelectorAll('tr.quotation_detail_formset');
    rows.forEach(function (tr, index) {
        tr.querySelectorAll('input, select, textarea').forEach(function (element) {
            if (element.name) {
                element.name = element.name.replace(/^form-\d+-/, 'form-' + index + '-');
            }
            if (element.id) {
                element.id = element.id.replace(/^id_form-\d+-/, 'id_form-' + index + '-');
            }
        });
        tr.children[0].textContent = index + 1;
    });
    var total = tbody.querySelector('input[name="form-TOTAL_FORMS"]');
    if (total) {
        total.value = rows.length;
    }
}

window.removeFormsetRow = removeFormsetRow;

/*
 * Spinner de carga al enviar un formulario de importacion (el que sube archivo).
 * Antes cada plantilla de subida repetia el bloque de Spin.js.
 */
function showUploadSpinner() {
    if (document.getElementById('divSpin')) {
        return;
    }
    var target = document.createElement('div');
    target.id = 'divSpin';
    document.body.appendChild(target);
    new Spinner({
        lines: 13, length: 20, width: 10, radius: 30, corners: 1, rotate: 8,
        direction: 1, color: '#000', speed: 1, trail: 60, shadow: false,
        hwaccel: false, className: 'mySpin', zIndex: 2e9, top: '50%', left: '50%',
    }).spin(target);
}

document.addEventListener('submit', function (event) {
    var form = event.target;
    if (form.matches('form[enctype="multipart/form-data"]')
            && form.querySelector('input[type="file"]')) {
        showUploadSpinner();
    }
});

window.showUploadSpinner = showUploadSpinner;

/*
 * Confirmacion de borrado: abre el dialogo de `#dialog-confirm` y, al aceptar,
 * hace el POST y delega el resultado en `onSuccess`. Las plantillas de detalle
 * repetian el dialogo de jQuery UI y el $.ajax en cada una.
 */
function confirmDelete(url, data, onSuccess) {
    var ventana = $('#dialog-confirm').dialog({
        resizable: false,
        height: 140,
        modal: true,
        buttons: {
            "Borrar": function () {
                $.ajax({
                    url: url,
                    type: 'post',
                    data: data,
                    success: function (response) {
                        onSuccess(response);
                    },
                });
                ventana.dialog("close");
            },
            "Cancelar": function () {
                ventana.dialog("close");
            },
        },
    });
}

window.confirmDelete = confirmDelete;

async function fetchJson(url) {
    const response = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!response.ok) {
        return null;
    }
    return response.json();
}

/*
 * Ventana modal para el detalle/alta de administracion. Las plantillas la
 * invocan con `onclick="return abrir_modal(url, titulo)"`; el contenido es un
 * fragmento (sin `{% extends %}`) que se carga con jQuery UI.
 *
 * La definicion se habia perdido en un refactor y los enlaces de administracion
 * quedaban sin hacer nada. Se crea `#popup` si la pagina no lo trae.
 */
function abrir_modal(url, titulo) {
    var popup = $('#popup');
    if (!popup.length) {
        popup = $('<div id="popup"></div>').appendTo('body');
    }
    popup.dialog({
        title: titulo,
        modal: true,
        width: 1000,
        resizable: false,
        position: { my: 'center', at: 'center', of: '#page-wrapper' },
    }).dialog('open').load(url);
    return false;
}

function cerrar_modal() {
    $('#popup').dialog('close');
}

window.abrir_modal = abrir_modal;
window.cerrar_modal = cerrar_modal;
