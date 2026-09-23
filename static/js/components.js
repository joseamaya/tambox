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
 * Modal propio (sin jQuery UI). Un unico overlay reutilizable con cabecera,
 * cuerpo y pie. `openModal` devuelve el cuerpo para poder inyectar HTML.
 */
function ensureModal() {
    var overlay = document.getElementById('app-modal');
    if (overlay) {
        return overlay;
    }
    overlay = document.createElement('div');
    overlay.id = 'app-modal';
    overlay.className = 'app-modal-overlay';
    overlay.hidden = true;
    overlay.innerHTML =
        '<div class="app-modal" role="dialog" aria-modal="true">' +
        '  <div class="app-modal-header">' +
        '    <span class="app-modal-title"></span>' +
        '    <button type="button" class="app-modal-close" aria-label="Cerrar">&times;</button>' +
        '  </div>' +
        '  <div class="app-modal-body"></div>' +
        '  <div class="app-modal-footer" hidden></div>' +
        '</div>';
    document.body.appendChild(overlay);
    overlay.querySelector('.app-modal-close').addEventListener('click', closeModal);
    overlay.addEventListener('mousedown', function (event) {
        if (event.target === overlay) {
            closeModal();
        }
    });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !overlay.hidden) {
            closeModal();
        }
    });
    return overlay;
}

function openModal(options) {
    var overlay = ensureModal();
    overlay.querySelector('.app-modal').className =
        'app-modal' + (options.small ? ' app-modal--sm' : '');
    overlay.querySelector('.app-modal-title').textContent = options.title || '';
    var body = overlay.querySelector('.app-modal-body');
    body.innerHTML = options.html || '';
    var footer = overlay.querySelector('.app-modal-footer');
    footer.innerHTML = '';
    var buttons = options.buttons || [];
    buttons.forEach(function (button) {
        var element = document.createElement('button');
        element.type = 'button';
        element.className = 'btn ' + (button.className || 'btn-default');
        element.textContent = button.label;
        element.addEventListener('click', button.onClick);
        footer.appendChild(element);
    });
    footer.hidden = buttons.length === 0;
    overlay.hidden = false;
    return body;
}

function closeModal() {
    var overlay = document.getElementById('app-modal');
    if (overlay) {
        overlay.hidden = true;
        overlay.querySelector('.app-modal-body').innerHTML = '';
    }
}

window.openModal = openModal;
window.closeModal = closeModal;

/*
 * Confirmacion de borrado: abre el modal con el titulo de `#dialog-confirm` y,
 * al aceptar, hace el POST y delega el resultado en `onSuccess`.
 */
function confirmDelete(url, data, onSuccess) {
    var dialog = document.getElementById('dialog-confirm');
    var title = (dialog && dialog.getAttribute('title')) || 'Eliminar';
    openModal({
        title: title,
        small: true,
        buttons: [
            {
                label: 'Borrar',
                className: 'btn-danger',
                onClick: function () {
                    closeModal();
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': window.CSRF_TOKEN || '',
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams(data).toString(),
                    }).then(function (response) {
                        var type = response.headers.get('content-type') || '';
                        return type.indexOf('application/json') === 0
                            ? response.json() : response.text();
                    }).then(function (payload) {
                        if (onSuccess) {
                            onSuccess(payload);
                        }
                    });
                },
            },
            { label: 'Cancelar', onClick: closeModal },
        ],
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
 * Autocompletado de productos sin jQuery. Sustituye al autocomplete de jQuery
 * UI que cada plantilla reimplementaba con `bindAutoComplete`.
 *
 * `config`:
 *   url             endpoint JSON (products:product_description_search,
 *                   warehouse:product_warehouse_search o
 *                   administration:receiver_name_search)
 *   searchType      PRODUCTOS | SERVICIOS | TODOS (si no se filtra por almacen)
 *   warehouseInput  selector del almacen del que depende la busqueda
 *   sourceField     sufijo del campo que se escribe (por defecto 'name')
 *   fields          sufijo destino -> clave del item
 *                   (por defecto code/name/unit/price)
 *   query           funcion que devuelve los parametros de la peticion
 *   minLength       minimo de caracteres para buscar (por defecto 2)
 */
function productAutocomplete(input, config) {
    var sourceField = config.sourceField || 'name';
    var minLength = config.minLength || 2;
    var fields = config.fields || { code: 'code', name: 'description', unit: 'unit', price: 'price' };
    var prefix = input.name.slice(0, input.name.length - sourceField.length);
    var form = input.form;
    var menu = document.createElement('div');
    menu.className = 'product-autocomplete';
    menu.hidden = true;
    document.body.appendChild(menu);
    var timer = null;

    function setField(suffix, value) {
        var element = (form && form.elements[prefix + suffix])
            || document.getElementById('id_' + prefix + suffix);
        if (element) {
            element.value = value;
        }
    }

    function close() {
        menu.hidden = true;
        menu.innerHTML = '';
    }

    function render(items) {
        menu.innerHTML = '';
        items.forEach(function (item) {
            var option = document.createElement('a');
            option.href = '#';
            option.className = 'product-autocomplete-item';
            option.textContent = item.label;
            option.addEventListener('mousedown', function (event) {
                event.preventDefault();
                Object.keys(fields).forEach(function (suffix) {
                    setField(suffix, item[fields[suffix]]);
                });
                input.value = item.description || item.label;
                close();
                input.dispatchEvent(new Event('change', { bubbles: true }));
            });
            menu.appendChild(option);
        });
        var rect = input.getBoundingClientRect();
        menu.style.left = (rect.left + window.scrollX) + 'px';
        menu.style.top = (rect.bottom + window.scrollY) + 'px';
        menu.style.minWidth = rect.width + 'px';
        menu.hidden = items.length === 0;
    }

    async function search() {
        if (input.value.length < minLength) {
            close();
            return;
        }
        var query;
        if (config.query) {
            query = config.query(input);
        } else {
            query = { description: input.value };
            if (config.warehouseInput) {
                var warehouse = document.querySelector(config.warehouseInput);
                query.warehouse = warehouse ? warehouse.value : '';
            } else {
                query.search_type = config.searchType || 'PRODUCTOS';
            }
        }
        var data = await fetchJson(config.url + '?' + new URLSearchParams(query).toString());
        if (data === null) {
            return;
        }
        render(data);
    }

    input.addEventListener('input', function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(search, 200);
    });
    input.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            close();
        }
    });
    input.addEventListener('blur', function () {
        window.setTimeout(close, 150);
    });
}

/*
 * Engancha el autocompletado a los campos `.productos` que aun no lo tengan.
 * Es idempotente: las plantillas la llaman al cargar y despues de cada swap de
 * htmx (alta de fila o transferencia).
 */
function initProductAutocomplete(root, config) {
    var selector = '.' + (config.className || 'productos');
    root.querySelectorAll(selector).forEach(function (input) {
        if (input.dataset.autocompleteReady) {
            return;
        }
        input.dataset.autocompleteReady = '1';
        productAutocomplete(input, config);
    });
}

window.productAutocomplete = productAutocomplete;
window.initProductAutocomplete = initProductAutocomplete;

/*
 * Ventana modal para el detalle/alta de administracion. Las plantillas la
 * invocan con `onclick="return abrir_modal(url, titulo)"`; el contenido es un
 * fragmento (sin `{% extends %}`) que se carga con fetch.
 */
function abrir_modal(url, titulo) {
    var body = openModal({ title: titulo, html: '<p class="text-center">Cargando&hellip;</p>' });
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (response) { return response.text(); })
        .then(function (html) { body.innerHTML = html; })
        .catch(function () { body.innerHTML = '<p>No se pudo cargar.</p>'; });
    return false;
}

function cerrar_modal() {
    closeModal();
}

window.abrir_modal = abrir_modal;
window.cerrar_modal = cerrar_modal;
