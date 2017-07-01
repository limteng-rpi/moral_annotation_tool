/**
 * Created by limteng on 5/21/17.
 */
var _dataset = null;
$(document).ready(function() {
    init_document();
    init_toolbar();
});

function init_toolbar() {
    $('#toolbar').w2toolbar({
        name: 'toolbar',
        tooltip: 'top',
        items: [
            {
                type: 'menu-radio',
                id: 'dataset',
                text: '',
                selected: null,
                icon: 'fa fa-file-text',
                items: []
            },
            { type: 'spacer' },
            {
                type: 'button',
                id: 'annotate',
                text: 'Annotate',
                icon: 'fa fa-circle-o-notch fa-spin',
                tooltip: 'Start annotating this data set',
                onClick: function(event) {
                    var dataset = w2ui.toolbar.get('dataset:' + w2ui.toolbar.get('dataset').selected).id;
                    window.location.replace('/annotation?dataset=' + dataset);
                }
            }
        ],
         onClick: function(event) {
            event.done(function() {
                if (event.target.match(/dataset:\w+/) !== null) {
                    select_dataset();
                }
            });
        }
    });

    $.getJSON('/operation?entry=get_dataset_names', function(response) {
        if (response.code === 200) {
            var result = response.result;
            var dataset_list = [];
            $.each(result, function(i, dataset) {
                dataset_list.push({
                    'id': dataset,
                    'text': dataset
                });
            });
            w2ui.toolbar.set(['dataset'], {
                items: dataset_list,
                selected: dataset_list[0]['id'],
                text: function () {
                        var menu = this.get('dataset');
                        var selected = this.get('dataset:' + menu.selected);
                        return 'Dataset: ' + selected.text;
                    }
            });
            select_dataset();
        }
    })
}

function init_document() {
    $('#document').w2grid({
        name: 'document',
        header: 'Document',
        show: {
            header: true,
            toolbar: false,
            footer: true
        },
        columns: [
            {
                field: 'tid',
                caption: 'Tweet ID',
                size: '20%',
                sortable: true
            },
            {
                field: 'text',
                caption: 'Text',
                size: '40%',
                sortable: true
            },
            {
                field: 'annotated',
                caption: 'Annotated',
                size: '10%',
                attr: "align=center",
                sortable: true
            },
            {
                field: 'retweet',
                caption: 'Retweet',
                attr: "align=center",
                size: '10%',
                sortable: true
            },
            {
                field: 'timestamp',
                caption: 'Timestamp',
                size: '20%',
                sortable: true
            }
        ],
        onClick: function(event) {
            var grid = this;
            var record = grid.get(event.recid);
            var tid = record['tid'];
            // window.open('/annotation?doc_id=' + doc_id);
            window.location.replace('/annotation/' + encodeURIComponent(_dataset)
                + '/' + encodeURIComponent(tid));
        }
    })
}

function select_dataset() {
    var dataset = w2ui.toolbar.get('dataset:' + w2ui.toolbar.get('dataset').selected).id;
    var username = $('#main').attr('username');
    $.getJSON('/operation?entry=get_user_document&username=' + username
        + '&dataset=' + dataset, function(response) {
        if (response.code === 200) {
            var doc_list = response.result;
            w2ui.document.clear();
            w2ui.document.add(doc_list);
            _dataset = dataset;
        }
    });
}