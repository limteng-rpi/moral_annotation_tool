/**
 * Created by limteng on 5/21/17.
 */
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
            toolbar: true,
            footer: true
        },
        columns: [
            {
                field: 'tid',
                caption: 'Tweet ID',
                size: '10%',
                sortable: true
            },
            {
                field: 'text',
                caption: 'Text',
                size: '35%',
                sortable: true
            },
            {
                field: 'category',
                caption: 'Category',
                size: '20%',
                sortable: true
            },
            {
                field: 'annotator',
                caption: 'Annotator',
                size: '10%',
                sortable: true
            },
            {
                field: 'retweet',
                caption: 'Retweet',
                size: '10%',
                sortable: true
            },
            {
                field: 'unclear',
                caption: 'Unclear',
                size: '10%',
                sortable: true
            },
            {
                field: 'skip',
                caption: 'Skip',
                size: '10%',
                sortable: true
            },
            {
                field: 'timestamp',
                caption: 'Timestamp',
                size: '15%',
                sortable: true
            }
        ],
        searches: [
            {field: 'tid', caption: 'Tweet ID', type: 'text'},
            {field: 'annotator', caption: 'Annotator', type: 'text'},
        ]
    })
}

function select_dataset() {
    var dataset = w2ui.toolbar.get('dataset:' + w2ui.toolbar.get('dataset').selected).id;
    $.getJSON('/progress?dataset=' + username
        + '&dataset=' + dataset, function(response) {
        if (response.code === 200) {
            var doc_list = response.result;
            w2ui.document.clear();
            w2ui.document.add(doc_list);
        }
    });
}