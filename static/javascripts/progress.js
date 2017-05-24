/**
 * Created by limteng on 5/21/17.
 */
$(document).ready(function() {
    init_document();
    init_toolbar();
});

var show_unclear = false;
var show_skip = false;

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

function selectListener(event) {
    event.done(function () {
        var document = w2ui.document;
        var selection = document.getSelection();
        if (selection.length == 0) {
            document.toolbar.disable('export');
        } else {
            document.toolbar.enable('export');
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
            footer: true,
            selectColumn: true
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
                size: '10%',
                sortable: true
            },
            {
                field: 'username',
                caption: 'Annotator',
                size: '10%',
                sortable: true
            },
            {
                field: 'retweet',
                caption: 'Retweet',
                size: '5%',
                sortable: true
            },
            {
                field: 'unclear',
                caption: 'Unclear',
                size: '5%',
                sortable: true
            },
            {
                field: 'skip',
                caption: 'Skip',
                size: '5%',
                sortable: true
            },
            {
                field: 'issue',
                caption: 'Issue',
                size: '10%',
                sortable: true
            },
            {
                field: 'abstract_issue',
                caption: 'Abstract Issue',
                size: '10%',
                sortable: true
            },
            {
                field: 'comment',
                caption: 'Comment',
                size: '10%',
                sortable: true
            },
            {
                field: 'timestamp',
                caption: 'Timestamp',
                size: '10%',
                sortable: true
            }
        ],
        searches: [
            {field: 'tid', caption: 'Tweet ID', type: 'text'},
            {field: 'username', caption: 'Annotator', type: 'text'},
        ],
        toolbar: {
            items: [
                {
                    id: 'split',
                    type: 'spacer'
                },
                {
                    id: 'unclear',
                    type: 'check',
                    checked: false,
                    caption: 'Show unclear',
                    icon: 'fa fa-check-square-o'
                },
                {
                    id: 'skip',
                    type: 'check',
                    checked: false,
                    caption: 'Show skip',
                    icon: 'fa fa-check-square-o'
                },
                {
                    id: 'export',
                    type: 'button',
                    caption: 'Export',
                    icon: 'fa fa-floppy-o',
                    onClick: function () {
                        var document = w2ui.document;
                        var selection = document.getSelection();
                        var id_list = [];
                        $.each(selection, function (i, recid) {
                            var record = document.get(recid);
                            id_list.push(record['_id']);
                        });
                        $.post('/export', {id_list: JSON.stringify(id_list)},
                            function (response) {
                            var filename = response.filename;
                                window.open('/download/' + filename);
                            }, 'json');
                    }
                }
            ],
            onClick: function (event) {
                event.done(function() {
                    if (event.target === 'unclear') {
                        show_unclear = event.item.checked;
                        select_dataset();
                    } else if (event.target === 'skip') {
                        show_skip = event.item.checked;
                        select_dataset();
                    }
                });

            }
        },
        onSelect: function(event) {selectListener(event);},
        onUnselect: function(event) {selectListener(event);}
    });

    w2ui.document.toolbar.disable('export');
}

function select_dataset() {
    var username = $('#main').attr('username');
    var dataset = w2ui.toolbar.get('dataset:' + w2ui.toolbar.get('dataset').selected).id;
    $.post('/progress', {
        dataset: dataset,
        username: username
    }, function(response) {
        if (response.code === 200) {
            var doc_list = response.result;
            var filter_doc_list = [];
            $.each(doc_list, function (i, doc) {
                var show = true;
                if (show_unclear === false && doc.unclear === '●') {
                    show = false;
                }
                if (show_skip === false && doc.skip === '●') {
                    show = false;
                }
                if (show) {
                    filter_doc_list.push(doc);
                }
            });
            w2ui.document.clear();
            w2ui.document.add(filter_doc_list);
        }
    }, 'json');
}