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
